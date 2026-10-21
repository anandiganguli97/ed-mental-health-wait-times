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
SAMPLE_BINS = [(11, 19), (20, 29), (30, 49), (50, 99), (100, 199), (200, 10**9)]


def load_panel() -> pd.DataFrame:
    d = pd.read_csv(PANEL, dtype={"facility_id": str}, low_memory=False)
    d["start_date"] = pd.to_datetime(d.start_date, errors="coerce")
    d["end_date"] = pd.to_datetime(d.end_date, errors="coerce")
    d["snapshot_date"] = pd.to_datetime(d.snapshot_date, errors="coerce")
    d["year"] = d.end_date.dt.year
    d = d.loc[d.year.isin(YEARS) & d.start_date.dt.month.eq(10) & d.start_date.dt.day.eq(1)
              & d.end_date.dt.month.eq(9) & d.end_date.dt.day.eq(30)].copy()
    d = d.sort_values("snapshot_date").drop_duplicates(["facility_id", "year"], keep="last")
    d["sample_n"] = pd.to_numeric(d.sample_min_op18bc, errors="coerce")
    d["gap"] = pd.to_numeric(d.psych_gap_minutes, errors="coerce")
    return d.loc[d.gap.notna() & d.sample_n.ge(MIN_SAMPLE),
                 ["facility_id", "facility_name", "state", "year", "gap", "sample_n"]].copy()


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


def rank_churn(d: pd.DataFrame) -> dict:
    latest = d.loc[d.year.eq(2025), ["facility_id", "gap"]].rename(columns={"gap": "gap_2025"})
    prior = d.loc[d.year.lt(2025)].groupby("facility_id").agg(
        prior_year_mean_gap=("gap", "mean"), prior_years=("year", "nunique")).reset_index()
    matched = latest.merge(prior, on="facility_id", how="inner", validate="one_to_one")
    # One prior annual window is sufficient for inclusion; the mean uses all available
    # earlier selected annual windows. Ties are broken reproducibly by CMS facility ID.
    matched = matched.sort_values(["gap_2025", "facility_id"]).reset_index(drop=True)
    n = len(matched); k = int(np.ceil(.10 * n))
    top_2025 = set(matched.tail(k).facility_id)
    bottom_2025 = set(matched.head(k).facility_id)
    by_prior = matched.sort_values(["prior_year_mean_gap", "facility_id"])
    top_prior = set(by_prior.tail(k).facility_id)
    bottom_prior = set(by_prior.head(k).facility_id)
    summary = {"matched_hospitals": n, "decile_size": k,
        "prior_years_minimum": 1, "prior_year_mean_years_median": float(matched.prior_years.median()),
        "top_decile_overlap_n": len(top_2025 & top_prior),
        "top_decile_overlap_share": len(top_2025 & top_prior) / k,
        "bottom_decile_overlap_n": len(bottom_2025 & bottom_prior),
        "bottom_decile_overlap_share": len(bottom_2025 & bottom_prior) / k,
        "definition": "Top/bottom decile of 2025 gap versus top/bottom decile of each matched hospital's mean across all available selected annual windows before 2025; at least one prior year; ceil(10% of matched hospitals), ties broken by facility ID.",
        "interpretation_limit": "Annual rank churn mixes true hospital change with measurement noise and is not a hospital quality rating."}
    (RESULTS / "hospital_rank_churn_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    d = load_panel()
    churn = rank_churn(d)
    validations = [holdout_validation(d, year) for year in (2024, 2025)]
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
            "rank_churn": churn,
            "noise_variance_intercept": a, "noise_variance_reciprocal_sample_slope": b,
            "between_hospital_variance": tau2, "noise_bins": bins,
            "validation": validations,
            "validation_rule": "predict each held-out year's hospital deviation from prior years and compare RMSE with the unshrunk prior-year mean; this validates prediction only, not patient-level uncertainty"}
    (RESULTS / "hospital_gap_shrinkage_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps({"rows": len(d), "latest_hospitals": len(latest), "validation": validations,
                      "rank_churn": churn,
            "noise_variance_intercept": a, "noise_variance_reciprocal_sample_slope": b,
                      "between_hospital_variance": tau2}, indent=2))


if __name__ == "__main__":
    main()
