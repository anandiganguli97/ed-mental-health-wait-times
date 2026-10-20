"""Group-time ATT for Medicaid mobile-crisis SPA authorization.

Uses annual, non-overlapping CMS OP-18 windows and an intention-to-treat
definition based on the SPA effective date. Actual statewide deployment is
mostly unverified and is not imputed.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "hospital_op18_archive_panel.csv"
POLICY = ROOT / "policy" / "mobile-crisis-adoption.csv"
RESULTS = ROOT / "results"
YEARS = [2018, 2020, 2021, 2022, 2023, 2024, 2025]
MIN_SAMPLE = 11
MIN_CONTROL_STATES = 10
N_BOOT = 999
SEED = 20261020


def load_policy():
    p = pd.read_csv(POLICY, dtype=str, keep_default_na=False)
    p["treatment_date"] = pd.to_datetime(p["treatment_date"], errors="coerce")
    if p.state.duplicated().any():
        raise ValueError("Duplicate state records in mobile-crisis policy table")
    return p


def load_panel():
    d = pd.read_csv(PANEL, dtype={"facility_id": str}, low_memory=False)
    d["start_date"] = pd.to_datetime(d.start_date, errors="coerce")
    d["end_date"] = pd.to_datetime(d.end_date, errors="coerce")
    d["snapshot_date"] = pd.to_datetime(d.snapshot_date, errors="coerce")
    d["end_year"] = d.end_date.dt.year
    d = d.loc[
        d.end_year.isin(YEARS)
        & d.start_date.dt.month.eq(10) & d.start_date.dt.day.eq(1)
        & d.end_date.dt.month.eq(9) & d.end_date.dt.day.eq(30)
    ].copy()
    d = d.sort_values("snapshot_date").drop_duplicates(
        ["facility_id", "start_date", "end_date"], keep="last"
    )
    d["sample_min_op18bc"] = pd.to_numeric(d.sample_min_op18bc, errors="coerce")
    d = d.loc[d.psych_gap_minutes.notna() & d.sample_min_op18bc.ge(MIN_SAMPLE)].copy()
    return d[["facility_id", "facility_name", "state", "start_date", "end_date",
              "end_year", "psych_gap_minutes", "sample_min_op18bc"]]


def cohort_end_year(date, periods):
    if pd.isna(date):
        return None
    eligible = periods.loc[periods.start_date.ge(date), "end_year"]
    return int(eligible.min()) if len(eligible) else None


def state_stats(d, base_year, time_year, treated, controls):
    base = d.loc[d.end_year.eq(base_year), ["facility_id", "state", "psych_gap_minutes"]].rename(
        columns={"psych_gap_minutes": "y0"})
    post = d.loc[d.end_year.eq(time_year), ["facility_id", "state", "psych_gap_minutes"]].rename(
        columns={"psych_gap_minutes": "y1"})
    pair = base.merge(post, on=["facility_id", "state"], how="inner", validate="one_to_one")
    pair["change"] = pair.y1 - pair.y0

    def summarize(states, arm):
        x = pair.loc[pair.state.isin(states)].groupby("state").change.agg(["sum", "count"]).reset_index()
        return x.rename(columns={"sum": f"sum_{arm}", "count": f"n_{arm}"})
    return summarize(treated, "tr"), summarize(controls, "co")


def mean_state(stats, arm, mult=None):
    if stats.empty:
        return np.nan
    ns = stats[f"n_{arm}"].to_numpy(float)
    sums = stats[f"sum_{arm}"].to_numpy(float)
    w = np.ones(len(stats)) if mult is None else np.array([mult.get(s, 0) for s in stats.state], float)
    denom = float((w * ns).sum())
    return float((w * sums).sum() / denom) if denom else np.nan


def bootstrap_weights(states, rng):
    values, counts = np.unique(rng.choice(states, len(states), replace=True), return_counts=True)
    return dict(zip(values.tolist(), counts.astype(int).tolist()))


def estimate(d, periods, policy):
    tdates = dict(zip(policy.state, policy.treatment_date))
    observed_states = sorted(d.state.dropna().unique())
    cohorts = {}
    for state in observed_states:
        g = cohort_end_year(tdates.get(state, pd.NaT), periods)
        if g is not None:
            cohorts[state] = g

    rng = np.random.default_rng(SEED)
    records, cache = [], {}
    for g in sorted(set(cohorts.values())):
        treated = {s for s, cohort in cohorts.items() if cohort == g}
        base_year = g - 2
        if base_year not in YEARS:
            continue
        base_end = periods.loc[periods.end_year.eq(base_year), "end_date"].max()
        for year in YEARS:
            if year == base_year or year == g - 1:
                continue  # reference period and policy-window transition
            target_period = periods.loc[periods.end_year.eq(year)]
            if target_period.empty:
                continue
            end = target_period.end_date.max()
            controls = {
                s for s in observed_states if s not in treated
                and (pd.isna(tdates.get(s, pd.NaT)) or tdates[s] > end)
            }
            tr, co = state_stats(d, base_year, year, treated, controls)
            nt = int(tr.n_tr.sum()) if len(tr) else 0
            nc = int(co.n_co.sum()) if len(co) else 0
            key = (g, year)
            cache[key] = (tr, co)
            if nt == 0 or nc == 0 or len(co) < MIN_CONTROL_STATES:
                records.append(dict(cohort=g, report_end_year=year, event_time=year-g,
                                    att_minutes=np.nan, ci95_low=np.nan, ci95_high=np.nan,
                                    treated_hospitals=nt, control_hospitals=nc,
                                    treated_states=len(tr), control_states=len(co),
                                    status="insufficient paired support"))
                continue
            point = mean_state(tr, "tr") - mean_state(co, "co")
            boots = []
            for _ in range(N_BOOT):
                w = bootstrap_weights(observed_states, rng)
                a, b = mean_state(tr, "tr", w), mean_state(co, "co", w)
                if np.isfinite(a) and np.isfinite(b):
                    boots.append(a-b)
            low, high = np.quantile(boots, [.025, .975]) if len(boots) >= 100 else (np.nan, np.nan)
            records.append(dict(cohort=g, report_end_year=year, event_time=year-g,
                                att_minutes=point, ci95_low=float(low), ci95_high=float(high),
                                treated_hospitals=nt, control_hospitals=nc,
                                treated_states=len(tr), control_states=len(co),
                                status="pre-trend diagnostic" if year < g-1 else "post-policy group-time ATT"))

    gt = pd.DataFrame(records)
    post = gt.loc[gt.status.eq("post-policy group-time ATT") & gt.att_minutes.notna()].copy()
    dynamic_rows = []
    for event_time, frame in post.groupby("event_time"):
        frame = frame.copy()
        frame["weight"] = frame.groupby("cohort").treated_hospitals.transform("first").astype(float)
        point = float(np.average(frame.att_minutes, weights=frame.weight))
        boots = []
        for _ in range(N_BOOT):
            w = bootstrap_weights(observed_states, rng)
            effects, weights = [], []
            for row in frame.itertuples(index=False):
                tr, co = cache[(int(row.cohort), int(row.report_end_year))]
                a, b = mean_state(tr, "tr", w), mean_state(co, "co", w)
                if np.isfinite(a) and np.isfinite(b):
                    effects.append(a-b)
                    weights.append(float(row.weight))
            if effects:
                boots.append(float(np.average(effects, weights=weights)))
        low, high = np.quantile(boots, [.025, .975]) if len(boots) >= 100 else (np.nan, np.nan)
        dynamic_rows.append(dict(event_time=int(event_time), att_minutes=point,
                                 ci95_low=float(low), ci95_high=float(high),
                                 cohort_time_cells=len(frame),
                                 min_treated_states=int(frame.treated_states.min()),
                                 min_control_states=int(frame.control_states.min())))
    dynamic = pd.DataFrame(dynamic_rows).sort_values("event_time") if dynamic_rows else pd.DataFrame()
    meta = {
        "cohort_first_full_reporting_end_year": {s: g for s, g in cohorts.items()},
        "panel_states": len(observed_states),
        "panel_hospitals": int(d.facility_id.nunique()),
        "report_end_years": YEARS,
        "sample_threshold_both_components": MIN_SAMPLE,
        "bootstrap_draws": N_BOOT,
        "bootstrap_seed": SEED,
        "minimum_not_yet_treated_control_states": MIN_CONTROL_STATES,
        "estimand": "group-time ATT for SPA effective-date authorization, using within-hospital changes in OP-18c minus OP-18b",
        "control_rule": "never-authorized or not-yet-authorized through the end of the comparison window",
        "transition_rule": "exclude report window containing the policy effective date",
        "inference": "percentile bootstrap resampling states with replacement",
        "important_limit": "SPA authorization is not statewide service availability; most operational dates are unknown",
    }
    return gt, dynamic, meta


def write_report(gt, dynamic, meta, policy):
    cells = int(gt.att_minutes.notna().sum()) if not gt.empty else 0
    pre = gt.loc[gt.status.eq("pre-trend diagnostic") & gt.att_minutes.notna()] if not gt.empty else pd.DataFrame()
    if dynamic.empty:
        main = "No post-policy group-time ATT had adequate paired-hospital and not-yet-treated state support; no effect is reported."
        rows = "| — | — | — | 0 | — |"
    else:
        first = dynamic.loc[dynamic.event_time.eq(0)]
        main = ("No event-time 0 estimate was supported." if first.empty else
                f"The pooled event-time 0 estimate is {first.iloc[0].att_minutes:+.1f} minutes "
                f"(state-cluster bootstrap 95% interval {first.iloc[0].ci95_low:+.1f} to {first.iloc[0].ci95_high:+.1f}). "
                "This is an exploratory estimate of Medicaid SPA authorization, not statewide operational availability.")
        rows = "\n".join(
            f"| {int(r.event_time)} | {r.att_minutes:+.1f} | {r.ci95_low:+.1f} to {r.ci95_high:+.1f} | {int(r.cohort_time_cells)} | {int(r.min_treated_states)} |"
            for r in dynamic.itertuples(index=False))
    pre_note = (f"{len(pre)} pre-policy cohort-time diagnostics are available. They assess departures from parallel trends but cannot prove the assumption."
                if len(pre) else "There is insufficient pre-policy support to assess differential trends.")
    report = f"""# Medicaid mobile-crisis authorization and the psychiatric ED time gap

## Result

{main}

The outcome is the hospital-level OP-18c minus OP-18b gap in minutes, a difference between separately reported medians. OP-18 is for discharged ED visits, not admitted-patient boarding.

## Design and support

The estimator uses group-time ATT comparisons for staggered SPA effective-date cohorts, with never-authorized and not-yet-authorized states as controls. Annual, non-overlapping reporting windows ending September 30 are used for 2018 and 2020–2025; the 2019 September window is absent. Repeated snapshots of the same hospital and reporting window are reduced to the latest CMS release. The sample requires a reportable gap and at least {MIN_SAMPLE} sampled patients in each component. Hospitals must be observed in both their cohort baseline and comparison windows.

The policy-overlap reporting window is dropped. Each cohort is compared with its last common fully pre-policy annual window, set to the first full treated reporting year minus two. Cohort-time ATT estimates are hospital-weighted and then aggregated by event time. Percentile intervals resample states, not hospitals. {pre_note}

CMS SPA effective dates indicate authorization under the Medicaid plan. Most state-level service launch dates are not verified. Accordingly, this estimates the effect of policy authorization availability (an intention-to-implement measure), not the effect of mobile crisis teams actually operating or covering the whole state. See the source audit table at policy/mobile-crisis-adoption.csv.

## Dynamic group-time ATT

| Event time (years; 0 = first full treated reporting window) | ATT (minutes) | State-cluster bootstrap 95% interval | Cohort-time cells | Minimum treated states |
|---:|---:|---:|---:|---:|
{rows}

There are {cells} supported group-time cells. Full support appears in mobile_crisis_group_time_att.csv, mobile_crisis_event_study.csv, and mobile_crisis_did_metadata.json.

## Limits

This is exploratory. SPA adoption can respond to changing crisis needs; actual team deployment and geographic availability are mostly unknown; only a few post-policy windows are available for later cohorts; outcomes are missing or suppressed for some hospitals; the gap has no validated patient-level uncertainty interval; and the earliest policy cohort has few adopting states. The bootstrap intervals do not remove these design limits. A non-significant result should not be described as evidence that mobile crisis has no effect.

## Reproduce

Run python python/build_mobile_crisis_did.py after python python/build_historical_panel.py. Treatment dates come from CMS SPA documents; statewide service launch dates are added only when an official state source verifies them.
"""
    (RESULTS / "mobile_crisis_policy_analysis.md").write_text(report, encoding="utf-8")


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    policy = load_policy()
    d = load_panel()
    periods = d[["start_date", "end_date", "end_year"]].drop_duplicates().sort_values("end_year")
    gt, dynamic, meta = estimate(d, periods, policy)
    gt.to_csv(RESULTS / "mobile_crisis_group_time_att.csv", index=False)
    dynamic.to_csv(RESULTS / "mobile_crisis_event_study.csv", index=False)
    meta.update({
        "input_hospital_period_rows_after_threshold": int(len(d)),
        "input_hospitals": int(d.facility_id.nunique()),
        "spa_effective_dates_in_source_table": int(policy.treatment_date.notna().sum()),
        "last_outcome_period_end": str(d.end_date.max().date()),
    })
    (RESULTS / "mobile_crisis_did_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    write_report(gt, dynamic, meta, policy)
    print(json.dumps(meta, indent=2))
    if not dynamic.empty:
        print(dynamic.to_string(index=False))


if __name__ == "__main__":
    main()

