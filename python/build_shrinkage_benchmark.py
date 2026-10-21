"""Explore reliability-weighted hospital-gap estimates from repeated annual windows.

This estimates within-hospital annual residual variation after period effects,
then asks whether a simple empirical-Bayes shrinkage improves prediction of a
held-out annual gap. It is a stability model, not a patient-level sampling CI.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "data" / "processed" / "hospital_op18_archive_panel.csv"
RESULTS = ROOT / "results"
YEARS = [2018, 2020, 2021, 2022, 2023, 2024, 2025]
MIN_SAMPLE = 11
HCA_HOUSTON = {"450644", "450097", "450617", "450775", "670106", "450638"}
SAMPLE_BINS = [(11, 19), (20, 29), (30, 49), (50, 99), (100, 199), (200, 10**9)]


def load_annual_panel() -> pd.DataFrame:
    d = pd.read_csv(PANEL, dtype={"facility_id": str}, low_memory=False)
    d["start_date"] = pd.to_datetime(d.start_date, errors="coerce")
    d["end_date"] = pd.to_datetime(d.end_date, errors="coerce")
    d["snapshot_date"] = pd.to_datetime(d.snapshot_date, errors="coerce")
    d["year"] = d.end_date.dt.year
    d = d.loc[d.year.isin(YEARS) & d.start_date.dt.month.eq(10) & d.start_date.dt.day.eq(1)
              & d.end_date.dt.month.eq(9) & d.end_date.dt.day.eq(30)].copy()
    d = d.sort_values("snapshot_date").drop_duplicates(["facility_id", "year"], keep="last")
    d["sample_n"] = pd.to_numeric(d.sample_min_op18bc, errors="coerce")
    d["sample_n_op18b"] = pd.to_numeric(d.sample_n_OP_18b, errors="coerce")
    d["gap"] = pd.to_numeric(d.psych_gap_minutes, errors="coerce")
    d["op18b"] = pd.to_numeric(d.score_minutes_OP_18b, errors="coerce")
    return d


def load_panel() -> pd.DataFrame:
    d = load_annual_panel()
    return d.loc[d.gap.notna() & d.sample_n.ge(MIN_SAMPLE),
                 ["facility_id", "facility_name", "state", "year", "gap", "op18b", "sample_n", "sample_n_op18b"]].copy()


def audit_annual_panel(annual: pd.DataFrame) -> dict:
    outliers = annual.loc[annual.gap.gt(1440), ["snapshot_date", "facility_id", "facility_name", "state",
        "start_date", "end_date", "year", "gap", "sample_n", "sample_n_op18b", "sample_n_OP_18c"]].copy()
    outliers["flag_rule"] = "positive OP-18c minus OP-18b gap > 1,440 minutes"
    outliers["meets_analysis_minimum_11"] = outliers.sample_n.ge(MIN_SAMPLE)
    outliers.sort_values(["year", "facility_name"]).to_csv(RESULTS / "hospital_gap_outliers_over_24h.csv", index=False)
    ids = sorted(HCA_HOUSTON)
    hca = annual.loc[annual.facility_id.isin(ids), ["snapshot_date", "facility_id", "facility_name", "state",
        "start_date", "end_date", "year", "score_minutes_OP_18b", "score_minutes_OP_18c", "gap",
        "sample_n", "sample_n_op18b"]].copy()
    hca.sort_values(["facility_name", "year"]).to_csv(RESULTS / "hca_houston_facility_annual_audit.csv", index=False)
    raw_path = ROOT / "data" / "processed" / "cms_op18_history_raw.csv"
    if raw_path.exists():
        raw = pd.read_csv(raw_path, dtype={"facility_id": str}, low_memory=False)
        raw = raw.loc[raw.facility_id.isin(ids)]
        identity = raw.groupby("facility_id").agg(
            raw_names=("facility_name", lambda x: " | ".join(sorted(set(x.dropna().astype(str))))),
            distinct_raw_names=("facility_name", "nunique"), raw_rows=("facility_name", "size"),
            raw_reporting_periods=("end_date", "nunique")).reset_index()
        panel_names = annual.loc[annual.facility_id.isin(ids)].groupby("facility_id").agg(
            annual_panel_names=("facility_name", lambda x: " | ".join(sorted(set(x.dropna().astype(str))))),
            distinct_annual_panel_names=("facility_name", "nunique"),
            annual_panel_years=("year", "nunique")).reset_index()
        identity = panel_names.merge(identity, on="facility_id", how="left")
        identity.to_csv(RESULTS / "hca_houston_ccn_name_audit.csv", index=False)
        raw_focus = identity.loc[identity.facility_id.isin(["450097", "450644"])]
        focus_raw_names_stable = bool(raw_focus.distinct_raw_names.eq(1).all())
        panel_aliases = {str(r.facility_id): r.annual_panel_names for r in identity.itertuples()
                         if r.distinct_annual_panel_names > 1}
    else:
        focus_raw_names_stable = None
        panel_aliases = {}
    return {"selected_annual_hospital_period_rows": int(len(annual)),
        "reportable_gap_rows": int(annual.gap.notna().sum()),
        "rows_over_24h": int(len(outliers)), "unique_hospitals_over_24h": int(outliers.facility_id.nunique()),
        "hca_houston_rows_over_24h": int(outliers.facility_id.isin(HCA_HOUSTON).sum()),
        "hca_houston_unique_facilities_over_24h": int(outliers.loc[outliers.facility_id.isin(HCA_HOUSTON), "facility_id"].nunique()),
        "outlier_rows_meeting_sample_minimum_11": int(outliers.meets_analysis_minimum_11.sum()),
        "flag_rule": "positive OP-18c minus OP-18b gap > 1,440 minutes, applied to selected annual windows 2018 and 2020-2025 after retaining the latest CMS snapshot for each hospital-window",
        "southeast_and_west_raw_ccn_names_stable": focus_raw_names_stable,
        "hca_houston_panel_name_aliases_by_ccn": panel_aliases,
        "outputs": ["hospital_gap_outliers_over_24h.csv", "hca_houston_facility_annual_audit.csv", "hca_houston_ccn_name_audit.csv"]}


def two_way_residuals(d: pd.DataFrame) -> np.ndarray:
    """Alternating projection for hospital and year fixed effects."""
    r = d.gap.to_numpy(float).copy()
    h = d.facility_id.to_numpy(str)
    y = d.year.to_numpy(int)
    for _ in range(100):
        old = r.copy()
        r -= pd.Series(r).groupby(h, sort=False).transform("mean").to_numpy()
        r -= pd.Series(r).groupby(y, sort=False).transform("mean").to_numpy()
        if np.max(np.abs(r - old)) < 1e-8:
            break
    return r


def fit_noise_model(d: pd.DataFrame) -> tuple[float, float, list[dict]]:
    residual = two_way_residuals(d)
    x = d.sample_n.to_numpy(float)
    points = []
    for low, high in SAMPLE_BINS:
        v = np.abs(residual[(x >= low) & (x <= high)])
        if len(v) < 100:
            continue
        # Normal-consistent robust residual scale, then square to get variance.
        scale = float(np.median(v) / 0.67448975)
        points.append({"sample_bin": f"{low}+" if high > 10**8 else f"{low}-{high}",
                       "n_rows": len(v), "median_sample": float(np.median(x[(x >= low) & (x <= high)])),
                       "residual_scale_minutes": scale, "residual_variance_minutes2": scale**2})
    if len(points) < 3:
        raise ValueError("Too few sample-size bins to estimate a noise relationship")
    # Model residual variance as a + b / sample size, with nonnegative coefficients.
    X = np.column_stack([np.ones(len(points)), 1 / np.array([p["median_sample"] for p in points])])
    v = np.array([p["residual_variance_minutes2"] for p in points])
    beta = np.linalg.lstsq(X, v, rcond=None)[0]
    beta = np.maximum(beta, 0)
    return float(beta[0]), float(beta[1]), points


def estimate_effects(train: pd.DataFrame, a: float, b: float) -> tuple[pd.DataFrame, float]:
    year_means = train.groupby("year").gap.mean()
    tmp = train.copy()
    tmp["year_mean"] = tmp.year.map(year_means)
    tmp["deviation"] = tmp.gap - tmp.year_mean
    rows = []
    for hid, group in tmp.groupby("facility_id", sort=False):
        k = len(group)
        effect = float(group.deviation.mean())
        pred_vars = a + b / group.sample_n.to_numpy(float)
        measurement_var = float(pred_vars.sum() / k**2)
        rows.append({"facility_id": hid, "facility_name": group.facility_name.iloc[-1],
                     "state": group.state.iloc[-1], "n_years": k,
                     "hospital_effect_raw": effect, "measurement_variance_mean": measurement_var})
    effects = pd.DataFrame(rows)
    raw_var = float(effects.hospital_effect_raw.var(ddof=1))
    noise_mean = float(effects.measurement_variance_mean.mean())
    tau2 = max(0.0, raw_var - noise_mean)
    effects["shrinkage_weight"] = np.where(tau2 + effects.measurement_variance_mean > 0,
                                             tau2 / (tau2 + effects.measurement_variance_mean), 0)
    effects["hospital_effect_shrunk"] = effects.hospital_effect_raw * effects.shrinkage_weight
    return effects, tau2


def holdout_validation(d: pd.DataFrame, test_year: int) -> dict:
    train = d.loc[d.year.lt(test_year)].copy()
    test = d.loc[d.year.eq(test_year)].copy()
    a, b, bins = fit_noise_model(train)
    effects, tau2 = estimate_effects(train, a, b)
    test_mean = test.groupby("year").gap.mean().iloc[0]
    test["observed_effect"] = test.gap - test_mean
    merged = test.merge(effects, on="facility_id", how="inner", validate="one_to_one")
    raw_rmse = float(np.sqrt(np.mean((merged.hospital_effect_raw - merged.observed_effect) ** 2)))
    shrunk_rmse = float(np.sqrt(np.mean((merged.hospital_effect_shrunk - merged.observed_effect) ** 2)))
    return {"test_year": int(test_year), "train_rows": int(len(train)), "test_hospitals": int(len(merged)),
            "noise_variance_intercept": a, "noise_variance_reciprocal_sample_slope": b,
            "between_hospital_variance": tau2, "unshrunk_rmse_minutes": raw_rmse,
            "shrunk_rmse_minutes": shrunk_rmse, "rmse_change_percent": 100 * (shrunk_rmse / raw_rmse - 1),
            "noise_bins": bins}


def _overlap(frame: pd.DataFrame, current: str, comparison: str) -> dict:
    x = frame[["facility_id", current, comparison]].dropna().copy()
    x["facility_id"] = x.facility_id.astype(str)
    n = len(x); k = int(np.ceil(.10 * n))
    a = set(x.sort_values([current, "facility_id"]).tail(k).facility_id)
    b = set(x.sort_values([comparison, "facility_id"]).tail(k).facility_id)
    c = set(x.sort_values([current, "facility_id"]).head(k).facility_id)
    e = set(x.sort_values([comparison, "facility_id"]).head(k).facility_id)
    return {"matched_hospitals": n, "decile_size": k,
            "top_overlap_n": len(a & b), "top_overlap_share": len(a & b) / k,
            "bottom_overlap_n": len(c & e), "bottom_overlap_share": len(c & e) / k}


def rank_churn(d: pd.DataFrame) -> dict:
    # Use one common paired-measure sample so OP-18b and psychiatric-gap overlap are comparable.
    complete = d.loc[d.gap.notna() & d.op18b.notna() & d.sample_n.ge(MIN_SAMPLE)
                     & d.sample_n_op18b.ge(MIN_SAMPLE)].copy()
    wide = complete.pivot(index="facility_id", columns="year", values=["gap", "op18b"])
    prior_years = [year for year in YEARS if year < 2025]
    latest = complete.loc[complete.year.eq(2025), ["facility_id", "gap", "op18b"]].copy()
    prior = complete.loc[complete.year.lt(2025)].groupby("facility_id").agg(
        prior_gap_mean=("gap", "mean"), prior_op18b_mean=("op18b", "mean"), prior_year_count=("year", "nunique")).reset_index()
    multi = latest.merge(prior, on="facility_id", how="inner", validate="one_to_one")
    multi_gap = _overlap(multi.rename(columns={"gap": "current", "prior_gap_mean": "reference"}), "current", "reference")
    multi_op18b = _overlap(multi.rename(columns={"op18b": "current", "prior_op18b_mean": "reference"}), "current", "reference")
    multi_result = {"comparison": "2025 versus each hospital's mean across all available earlier selected annual windows",
        "median_number_of_prior_years": float(multi.prior_year_count.median()),
        "psychiatric_gap": multi_gap, "op18b_median": multi_op18b}
    by_year = complete.loc[complete.year.isin([2024, 2025])].pivot(index="facility_id", columns="year", values=["gap", "op18b"])
    yy = by_year.dropna(subset=[("gap", 2024), ("gap", 2025), ("op18b", 2024), ("op18b", 2025)]).reset_index()
    year_frame = pd.DataFrame({"facility_id": yy.facility_id.astype(str), "gap_2024": yy[("gap", 2024)],
        "gap_2025": yy[("gap", 2025)], "op18b_2024": yy[("op18b", 2024)], "op18b_2025": yy[("op18b", 2025)]})
    year_gap = _overlap(year_frame.rename(columns={"gap_2025": "current", "gap_2024": "reference"}), "current", "reference")
    year_op18b = _overlap(year_frame.rename(columns={"op18b_2025": "current", "op18b_2024": "reference"}), "current", "reference")
    yy_result = {"comparison": "2024 versus 2025 annual reporting windows", "psychiatric_gap": year_gap, "op18b_median": year_op18b}
    without_hca = multi.loc[~multi.facility_id.isin(HCA_HOUSTON)].copy()
    multi_gap_no_hca = _overlap(without_hca.rename(columns={"gap": "current", "prior_gap_mean": "reference"}), "current", "reference")
    multi_op18b_no_hca = _overlap(without_hca.rename(columns={"op18b": "current", "prior_op18b_mean": "reference"}), "current", "reference")
    yy_no_hca = year_frame.loc[~year_frame.facility_id.isin(HCA_HOUSTON)].copy()
    yy_gap_no_hca = _overlap(yy_no_hca.rename(columns={"gap_2025": "current", "gap_2024": "reference"}), "current", "reference")
    yy_op18b_no_hca = _overlap(yy_no_hca.rename(columns={"op18b_2025": "current", "op18b_2024": "reference"}), "current", "reference")
    sensitivity = {"excluded_hca_houston_facility_ids": sorted(HCA_HOUSTON),
        "2025_vs_prior_year_mean": {"psychiatric_gap": multi_gap_no_hca, "op18b_median": multi_op18b_no_hca},
        "2024_vs_2025": {"psychiatric_gap": yy_gap_no_hca, "op18b_median": yy_op18b_no_hca}}
    result = {"sample_threshold": MIN_SAMPLE, "years": YEARS,
        "decile_rule": "ceil(10% of common matched hospitals); ties broken by six-digit CMS facility ID",
        "comparison_sample_rule": "Same hospitals with reportable OP-18b and OP-18c, at least 11 cases in both components, for both outcomes.",
        "multi_year_prior_mean": multi_result, "year_over_year": yy_result,
        "sensitivity_excluding_hca_houston": sensitivity,
        "interpretation_limit": "Decile turnover mixes true change with measurement noise; sample size alone does not explain all annual variation."}
    rows = []
    for key, label in [("psychiatric_gap", "Psychiatric gap (OP-18c minus OP-18b)"), ("op18b_median", "OP-18b median")]:
        rows.append({"comparison": "2025 vs prior-years mean", "measure": label,
            **multi_result[key]})
        rows.append({"comparison": "2024 vs 2025", "measure": label, **yy_result[key]})
    pd.DataFrame(rows).to_csv(RESULTS / "hospital_rank_churn_comparison.csv", index=False)
    (RESULTS / "hospital_rank_churn_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def write_historical_audit(annual: pd.DataFrame, churn: dict, audit: dict, validations: list[dict], validations_no_hca: list[dict]) -> None:
    years = YEARS
    hca = annual.loc[annual.facility_id.isin(HCA_HOUSTON)].copy()
    lines = []
    for hid, group in hca.groupby("facility_id", sort=True):
        names = " / ".join(sorted(group.facility_name.dropna().astype(str).unique()))
        prior = group.loc[group.year.lt(2025), "gap"].dropna()
        current = group.loc[group.year.eq(2025), "gap"].dropna()
        values = {int(row.year): row.gap for row in group.itertuples() if pd.notna(row.gap)}
        cells = ["—" if year not in values else f"{values[year]:,.0f}" for year in years]
        lines.append("| " + " | ".join([hid, names, f"{prior.mean():,.1f}" if len(prior) else "—",
            f"{current.iloc[0]:,.0f}" if len(current) else "—", *cells]) + " |")
    multi = churn["multi_year_prior_mean"]
    yoy = churn["year_over_year"]
    sens = churn["sensitivity_excluding_hca_houston"]
    pct = lambda x: f"{100*x:.1f}%"
    audit_text = f"""# Historical outlier and rank-stability audit

## Rule and findings

The rule flags a positive OP-18c minus OP-18b gap above 1,440 minutes (24 hours). It was applied to the latest CMS snapshot for each selected non-overlapping annual hospital window, 2018 and 2020–2025. The 2019 September window is not in the selected panel. There are **{audit['rows_over_24h']} hospital-period flags across {audit['unique_hospitals_over_24h']} CCNs**; all {audit['outlier_rows_meeting_sample_minimum_11']} flagged rows meet the 11-case minimum in both components. Eleven flags occur at three HCA Houston CCNs: West (450644), Southeast (450097), and Clear Lake (450617). These values are retained in primary analyses and are flagged for review, not presumed reporting errors. The [full flagged rows](hospital_gap_outliers_over_24h.csv) include reporting dates, latest snapshot, component samples, and facility IDs.

The latest-period p99 model caps **31 of 3,023** hospital outcomes at 602.34 minutes. This sensitivity checks influence; it does not recode the primary data. In the mobile-crisis analysis, all six HCA Houston CCNs are removed in a targeted sensitivity because Texas is a never-treated control state.

## HCA Houston by annual window

The table uses the same selected annual panel that feeds the shrinkage, churn, and DiD analyses. It groups by six-digit CCN rather than exact hospital name, includes all available years, and reports the prior-window mean and 2025 value. A dash means no reportable annual gap in that selected window.

| CCN | Names in annual panel | Prior-window mean | 2025 gap | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

CCN 450097 is named **Bayshore Medical Center** in the 2018 window and **HCA Houston Healthcare Southeast** later. CCN 450775 also appears as **Kingwood Medical Center** and **HCA Houston Healthcare Kingwood**. The annual data do not show West and Southeast swapping IDs: West remains CCN 450644 and Southeast 450097. Across the selected windows, Southeast’s prior mean by CCN is {float(hca.loc[hca.facility_id.eq('450097') & hca.year.lt(2025), 'gap'].mean()):,.1f} minutes, near West’s 2025 value of {float(hca.loc[hca.facility_id.eq('450644') & hca.year.eq(2025), 'gap'].iloc[0]):,.0f}; the values arise from distinct CCNs, and 2018’s Bayshore name needs a dated crosswalk. See the [CCN/name audit](hca_houston_ccn_name_audit.csv) and [full annual file](hca_houston_facility_annual_audit.csv).

## Decile overlap benchmark

Top and bottom deciles are defined on the same matched hospitals for psychiatric gap and OP-18b. Decile size is the ceiling of 10% of the sample; ties are broken by CMS facility ID.

| Comparison | Outcome | Hospitals | Top overlap | Bottom overlap |
|---|---|---:|---:|---:|
| 2025 vs prior-years mean | Psychiatric gap | {multi['psychiatric_gap']['matched_hospitals']:,} | {pct(multi['psychiatric_gap']['top_overlap_share'])} | {pct(multi['psychiatric_gap']['bottom_overlap_share'])} |
| 2025 vs prior-years mean | OP-18b median | {multi['op18b_median']['matched_hospitals']:,} | {pct(multi['op18b_median']['top_overlap_share'])} | {pct(multi['op18b_median']['bottom_overlap_share'])} |
| 2024 vs 2025 | Psychiatric gap | {yoy['psychiatric_gap']['matched_hospitals']:,} | {pct(yoy['psychiatric_gap']['top_overlap_share'])} | {pct(yoy['psychiatric_gap']['bottom_overlap_share'])} |
| 2024 vs 2025 | OP-18b median | {yoy['op18b_median']['matched_hospitals']:,} | {pct(yoy['op18b_median']['top_overlap_share'])} | {pct(yoy['op18b_median']['bottom_overlap_share'])} |

Excluding the six HCA Houston facilities leaves the pattern similar: psychiatric-gap overlap is {pct(sens['2025_vs_prior_year_mean']['psychiatric_gap']['top_overlap_share'])} top and {pct(sens['2025_vs_prior_year_mean']['psychiatric_gap']['bottom_overlap_share'])} bottom for 2025 versus prior-years mean, and {pct(sens['2024_vs_2025']['psychiatric_gap']['top_overlap_share'])}/{pct(sens['2024_vs_2025']['psychiatric_gap']['bottom_overlap_share'])} for 2024 versus 2025. Rank turnover mixes true hospital change and measurement noise; this table is not a quality ranking.

## Shrinkage validation without the HCA Houston facilities

The modest held-out RMSE improvement also remains modest when all six CCNs are removed from every year. For 2024, the reduction is {abs(validations[0]['rmse_change_percent']):.1f}% in the full sample and {abs(validations_no_hca[0]['rmse_change_percent']):.1f}% without the six facilities. For 2025, it is {abs(validations[1]['rmse_change_percent']):.1f}% and {abs(validations_no_hca[1]['rmse_change_percent']):.1f}%, respectively. This is a predictive sensitivity, not evidence that the HCA values are erroneous.
"""
    (RESULTS / "hospital_outlier_and_rank_stability.md").write_text(audit_text, encoding="utf-8")


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    annual = load_annual_panel()
    outlier_audit = audit_annual_panel(annual)
    d = annual.loc[annual.gap.notna() & annual.sample_n.ge(MIN_SAMPLE),
                   ["facility_id", "facility_name", "state", "year", "gap", "op18b", "sample_n", "sample_n_op18b"]].copy()
    churn = rank_churn(d)
    validations = [holdout_validation(d, year) for year in (2024, 2025)]
    no_hca = d.loc[~d.facility_id.isin(HCA_HOUSTON)].copy()
    validations_no_hca = [holdout_validation(no_hca, year) for year in (2024, 2025)]
    write_historical_audit(annual, churn, outlier_audit, validations, validations_no_hca)
    a, b, bins = fit_noise_model(d.loc[d.year.lt(2025)].copy())
    effects, tau2 = estimate_effects(d.loc[d.year.lt(2025)].copy(), a, b)
    latest = d.loc[d.year.eq(2025), ["facility_id", "facility_name", "state", "gap", "sample_n"]].copy()
    latest = latest.merge(effects, on="facility_id", how="inner", validate="one_to_one")
    latest["annual_mean_gap"] = latest.gap
    latest["shrunk_gap_estimate"] = float(d.loc[d.year.eq(2025), "gap"].mean()) + latest.hospital_effect_shrunk
    latest["unshrunk_gap_estimate"] = float(d.loc[d.year.eq(2025), "gap"].mean()) + latest.hospital_effect_raw
    latest.to_csv(RESULTS / "hospital_gap_shrinkage_exploration.csv", index=False)
    meta = {"model": "exploratory empirical-Bayes normal-means shrinkage, residual variance a + b/sample_n",
            "target": "hospital-level OP-18c minus OP-18b gap in 2025 reporting window",
            "sample_threshold": MIN_SAMPLE, "years": YEARS,
            "variance_source": "within-hospital deviations after additive year effects in repeated annual, non-overlapping windows",
            "interpretation_limit": "annual residual variation includes real hospital changes and measurement noise; it is not a validated sampling variance or confidence interval for a median difference",
            "rank_churn": churn, "historical_outlier_audit": outlier_audit,
            "noise_variance_intercept": a, "noise_variance_reciprocal_sample_slope": b,
            "between_hospital_variance": tau2, "noise_bins": bins,
            "validation": validations,
            "validation_excluding_hca_houston_six_facilities": validations_no_hca,
            "validation_rule": "predict each held-out year's hospital deviation from prior years and compare RMSE with the unshrunk prior-year mean; this validates prediction only, not patient-level uncertainty"}
    (RESULTS / "hospital_gap_shrinkage_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(d), "latest_hospitals": len(latest), "validation": validations,
                      "rank_churn": churn, "historical_outlier_audit": outlier_audit,
                      "validation_excluding_hca_houston_six_facilities": validations_no_hca,
            "noise_variance_intercept": a, "noise_variance_reciprocal_sample_slope": b,
                      "between_hospital_variance": tau2}, indent=2))


if __name__ == "__main__":
    main()

