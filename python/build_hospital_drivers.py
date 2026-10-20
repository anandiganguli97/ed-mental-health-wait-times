"""Build a current-period hospital driver and peer-group analysis.

This is intentionally a single-period association analysis. Current CMS hospital
characteristics are not backcast onto the historical panel, and coefficients are
not causal effects or hospital quality ratings.
"""

from __future__ import annotations

import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
CMS_ID = "xubh-q36u"
CMS_METADATA = f"https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{CMS_ID}?show-reference-ids"
RUCC_URL = "https://ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=35069"
POS_URL = "https://data.cms.gov/sites/default/files/2026-07/7780b4e3-4c4b-4811-8884-65ca23b7a4e8/Hospital_and_other.DATA.Q2_2026.csv"
HPSA_MH_URL = "https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_MH.csv"
MIN_SAMPLE = 11
MIN_PEER_N = 20


def get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "ED-Mental-Health-Benchmark/0.3 (public data analysis)"})
    for attempt in range(6):
        try:
            with urlopen(request, timeout=90) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 5:
                raise RuntimeError(f"Download failed for {url}: {exc}") from exc
            time.sleep(min(2**attempt, 20))
    raise AssertionError("unreachable")


def download_sources() -> tuple[Path, Path, Path, Path, dict]:
    RAW.mkdir(parents=True, exist_ok=True)
    meta = json.loads(get_bytes(CMS_METADATA))
    dists = meta.get("distribution", [])
    cms_url = next((d.get("data", {}).get("downloadURL") for d in dists
                    if d.get("data", {}).get("downloadURL", "").lower().endswith(".csv")), None)
    if not cms_url:
        raise ValueError("CMS metadata did not include a hospital CSV URL")
    cms_path = RAW / "Hospital_General_Information-current.csv"
    rucc_path = RAW / "USDA_RUCC_2023.csv"
    pos_path = RAW / "cms_pos_q2_2026.csv"
    hpsa_path = RAW / "hrsa_hpsa_mh_current.csv"
    cms_path.write_bytes(get_bytes(cms_url))
    rucc_path.write_bytes(get_bytes(RUCC_URL))
    pos_path.write_bytes(get_bytes(POS_URL))
    hpsa_path.write_bytes(get_bytes(HPSA_MH_URL))
    metadata = {"cms_dataset_id": CMS_ID, "cms_metadata_url": CMS_METADATA,
                "cms_download_url": cms_url, "rucc_download_url": RUCC_URL,
                "pos_download_url": POS_URL, "pos_period": "2026 Q2",
                "hrsa_hpsa_mh_download_url": HPSA_MH_URL,
                "retrieved_utc": datetime.now(timezone.utc).isoformat()}
    (RAW / "hospital_drivers_sources.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return cms_path, rucc_path, pos_path, hpsa_path, metadata


def norm_county(value: object) -> str:
    value = str(value or "").upper().strip()
    value = re.sub(r"\b(COUNTY|PARISH|BOROUGH|CENSUS AREA|MUNICIPALITY|CITY AND BOROUGH|CITY)\b", "", value)
    return re.sub(r"[^A-Z0-9]", "", value)


def load_hospital_characteristics(cms_path: Path, rucc_path: Path, pos_path: Path, hpsa_path: Path) -> pd.DataFrame:
    hosp = pd.read_csv(cms_path, dtype=str, low_memory=False)
    hosp.columns = [str(c).strip().lower().replace("/", "").replace(" ", "_") for c in hosp.columns]
    required = {"facility_id", "state", "countyparish", "hospital_type", "hospital_ownership", "emergency_services"}
    if not required.issubset(hosp.columns):
        raise ValueError(f"CMS hospital-information schema changed; missing {sorted(required - set(hosp.columns))}")
    hosp["facility_id"] = hosp["facility_id"].astype(str).str.strip().str.zfill(6)
    rucc = pd.read_csv(rucc_path, dtype=str, low_memory=False, encoding="cp1252")
    rucc["county_key"] = rucc["County_Name"].map(norm_county)
    wide = rucc.pivot_table(index=["FIPS", "State", "County_Name", "county_key"], columns="Attribute", values="Value", aggfunc="first").reset_index()
    if "RUCC_2023" not in wide:
        raise ValueError("USDA RUCC file is missing RUCC_2023")
    wide["rucc_2023"] = pd.to_numeric(wide["RUCC_2023"], errors="coerce")
    wide["rurality"] = np.where(wide["rucc_2023"].between(1, 3), "Metro", np.where(wide["rucc_2023"].between(4, 9), "Nonmetro", "Unknown"))
    wide = wide.rename(columns={"State": "state", "County_Name": "rucc_county_name"})
    # Some county-equivalent names collide within a state (notably independent cities).
    # Do not guess which FIPS/urbanicity applies when the CMS file gives only a name.
    ambiguous = wide.duplicated(["state", "county_key"], keep=False)
    wide = wide.loc[~ambiguous]
    hosp["county_key"] = hosp["countyparish"].map(norm_county)
    hosp = hosp.merge(wide[["state", "county_key", "FIPS", "rucc_2023", "rurality"]], on=["state", "county_key"], how="left", validate="many_to_one")
    pos = pd.read_csv(pos_path, dtype=str, low_memory=False, encoding="cp1252")
    pos = pos.loc[pos["PRVDR_CTGRY_CD"].eq("01")].copy()
    pos["facility_id"] = pos["PRVDR_NUM"].astype(str).str.strip().str.zfill(6)
    pos["county_fips"] = (pos["FIPS_STATE_CD"].fillna("").str.zfill(2)
                           + pos["FIPS_CNTY_CD"].fillna("").str.zfill(3))
    for c in ["BED_CNT", "PSYCH_UNIT_BED_CNT"]:
        pos[c] = pd.to_numeric(pos[c], errors="coerce")
    pos = pos[["facility_id", "BED_CNT", "PSYCH_UNIT_BED_CNT", "county_fips"]].drop_duplicates("facility_id")
    hosp = hosp.merge(pos, on="facility_id", how="left", validate="one_to_one")
    hpsa = pd.read_csv(hpsa_path, dtype=str, low_memory=False, encoding="utf-8-sig")
    hpsa = hpsa.loc[hpsa["Designation Type"].isin(["Geographic HPSA", "High Needs Geographic HPSA"])].copy()
    hpsa["county_fips"] = hpsa["Common State County FIPS Code"].astype(str).str.replace(r"\\.0$", "", regex=True).str.zfill(5)
    hpsa["HPSA Score"] = pd.to_numeric(hpsa["HPSA Score"], errors="coerce")
    hpsa["mh_hpsa_designated"] = hpsa["HPSA Status"].eq("Designated")
    county_hpsa = hpsa.groupby("county_fips", as_index=False).agg(
        mh_hpsa_designated=("mh_hpsa_designated", "max"), mh_hpsa_score=("HPSA Score", "max"))
    hosp = hosp.merge(county_hpsa, on="county_fips", how="left", validate="many_to_one")
    hosp["mh_hpsa_designated"] = hosp["mh_hpsa_designated"].map({True: "Yes", False: "No"}).fillna("Unknown")
    keep = ["facility_id", "facility_name", "state", "countyparish", "hospital_type", "hospital_ownership", "emergency_services", "FIPS", "rucc_2023", "rurality", "BED_CNT", "PSYCH_UNIT_BED_CNT", "county_fips", "mh_hpsa_designated", "mh_hpsa_score"]
    return hosp[keep].drop_duplicates("facility_id", keep="first")


def build_driver_panel(characteristics: pd.DataFrame) -> pd.DataFrame:
    panel = pd.read_csv(PROCESSED / "hospital_op18_current.csv", dtype={"facility_id": str}, low_memory=False)
    panel["facility_id"] = panel["facility_id"].astype(str).str.strip().str.zfill(6)
    data = panel.merge(characteristics, on="facility_id", how="left", suffixes=("_op18", "_cms"), validate="one_to_one")
    data["state"] = data["state_cms"].fillna(data["state_op18"])
    for col in ["hospital_type", "hospital_ownership", "emergency_services", "rurality", "mh_hpsa_designated"]:
        data[col] = data[col].fillna("Unknown").replace("", "Unknown")
    data["sample_min_op18bc"] = pd.to_numeric(data["sample_min_op18bc"], errors="coerce")
    usable = data["psych_gap_minutes"].notna() & (data["sample_min_op18bc"] >= MIN_SAMPLE)
    return data.loc[usable].copy()


def make_design(data: pd.DataFrame, include_contextual_covariates: bool = True) -> tuple[np.ndarray, list[str], list[str]]:
    x = pd.DataFrame({"Intercept": np.ones(len(data))}, index=data.index)
    exposure_columns: list[str] = []
    ownership = data["hospital_ownership"].fillna("Unknown").astype(str)
    ownership = ownership.replace({
        "Government - Federal": "Other (federal, physician, tribal)",
        "Physician": "Other (federal, physician, tribal)",
        "Tribal": "Other (federal, physician, tribal)",
    })
    data = data.copy()
    data["hospital_ownership"] = ownership
    categorical = ["hospital_type", "hospital_ownership", "rurality", "emergency_services"]
    if include_contextual_covariates:
        categorical.append("mh_hpsa_designated")
    for variable in categorical:
        values = data[variable].fillna("Unknown").astype(str)
        levels = sorted(values.unique())
        if "Unknown" in levels and len(levels) > 1:
            values = values.replace("Unknown", "Other/Unknown")
            levels = sorted(values.unique())
        reference = "Voluntary non-profit - Private" if variable == "hospital_ownership" else levels[0]
        for level in [level for level in levels if level != reference]:
            col = f"{variable}[{level}]"
            x[col] = (values == level).astype(float)
            exposure_columns.append(col)
    if include_contextual_covariates:
        for variable, source in [("log_bed_count", "BED_CNT"), ("log_psych_unit_beds", "PSYCH_UNIT_BED_CNT")]:
            x[variable] = np.log1p(pd.to_numeric(data[source], errors="coerce").fillna(0).clip(lower=0))
            exposure_columns.append(variable)
    # State fixed effects absorb broad state policy and market differences.
    states = data["state"].fillna("Unknown").astype(str)
    for state in sorted(states.unique())[1:]:
        x[f"state[{state}]"] = (states == state).astype(float)
    return x.to_numpy(dtype=float), list(x.columns), exposure_columns


def fit_clustered_ols(data: pd.DataFrame, include_contextual_covariates: bool = True) -> tuple[pd.DataFrame, dict]:
    x, names, exposures = make_design(data, include_contextual_covariates)
    y = pd.to_numeric(data["psych_gap_minutes"], errors="coerce").to_numpy(dtype=float)
    states = data["state"].fillna("Unknown").astype(str).to_numpy()
    n, k = x.shape
    rank = int(np.linalg.matrix_rank(x))
    if rank < k or n <= k + 5:
        raise ValueError(f"Model design is rank deficient or too small (n={n}, k={k}, rank={rank})")
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    resid = y - x @ beta
    groups = np.unique(states)
    meat = np.zeros((k, k))
    for group in groups:
        mask = states == group
        score = x[mask].T @ resid[mask]
        meat += np.outer(score, score)
    correction = (len(groups) / (len(groups) - 1)) * ((n - 1) / (n - k))
    covariance = correction * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.maximum(np.diag(covariance), 0))
    z = np.divide(beta, se, out=np.full_like(beta, np.nan), where=se > 0)
    # Two-sided normal approximation is reported with an explicit, reproducible CI.
    p = np.array([math.erfc(abs(float(v)) / np.sqrt(2)) if np.isfinite(v) else np.nan for v in z])
    out = pd.DataFrame({"term": names, "estimate_minutes": beta, "cluster_se_state": se,
                        "ci95_low": beta - 1.96 * se, "ci95_high": beta + 1.96 * se,
                        "p_value_normal_approx": p})
    out = out[out["term"].isin(exposures)].copy()
    out.insert(1, "predictor", out["term"].str.extract(r"^([^\[]+)", expand=False))
    out = out.sort_values(["predictor", "estimate_minutes"])
    ybar = y.mean()
    r2 = float(1 - (resid @ resid) / np.sum((y - ybar) ** 2))
    meta = {"n_hospitals": int(n), "state_clusters": int(len(groups)), "design_columns": int(k),
            "r_squared_including_state_fixed_effects": r2, "residual_sd_minutes": float(np.sqrt(np.sum(resid**2)/(n-k))),
            "sample_threshold_both_components": MIN_SAMPLE, "period_end": str(pd.to_datetime(data["end_date"]).max().date()),
            "covariance": "CR1 state-clustered sandwich; normal-approximation 95% intervals and p-values"}
    return out, meta


def build_peers(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    peers = data.copy()
    peers["peer_group"] = peers["hospital_type"].astype(str) + " | " + peers["rurality"].astype(str)
    stats = peers.groupby("peer_group", dropna=False).agg(
        hospitals=("facility_id", "nunique"), median_gap_minutes=("psych_gap_minutes", "median"),
        gap_p25_minutes=("psych_gap_minutes", lambda x: x.quantile(.25)),
        gap_p75_minutes=("psych_gap_minutes", lambda x: x.quantile(.75)),
        median_psych_sample=("sample_n_OP_18c", "median"),
    ).reset_index()
    stats["peer_group_meets_minimum"] = stats["hospitals"] >= MIN_PEER_N
    stats.loc[~stats["peer_group_meets_minimum"], ["median_gap_minutes", "gap_p25_minutes", "gap_p75_minutes"]] = np.nan
    peers = peers.merge(stats, on="peer_group", how="left", validate="many_to_one")
    peers["gap_vs_peer_median_minutes"] = peers["psych_gap_minutes"] - peers["median_gap_minutes"]
    peers["peer_percentile"] = peers.groupby("peer_group")["psych_gap_minutes"].rank(pct=True, method="average") * 100
    peers.loc[~peers["peer_group_meets_minimum"], "peer_percentile"] = np.nan
    return stats.sort_values("hospitals", ascending=False), peers


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    cms_path, rucc_path, pos_path, hpsa_path, meta = download_sources()
    chars = load_hospital_characteristics(cms_path, rucc_path, pos_path, hpsa_path)
    data = build_driver_panel(chars)
    base_coeffs, base_meta = fit_clustered_ols(data, include_contextual_covariates=False)
    coeffs, model_meta = fit_clustered_ols(data, include_contextual_covariates=True)
    peer_summary, peer_rows = build_peers(data)
    chars.to_csv(PROCESSED / "hospital_characteristics_current.csv", index=False)
    coeffs.to_csv(RESULTS / "hospital_driver_model_coefficients.csv", index=False)
    base_coeffs.to_csv(RESULTS / "hospital_driver_model_base_coefficients.csv", index=False)
    peer_summary.to_csv(RESULTS / "peer_group_summary.csv", index=False)
    peer_rows[["facility_id", "facility_name_op18", "state", "hospital_type", "hospital_ownership", "rurality",
               "rucc_2023", "psych_gap_minutes", "sample_min_op18bc", "peer_group", "hospitals",
               "median_gap_minutes", "gap_vs_peer_median_minutes", "peer_percentile"]].to_csv(
                   RESULTS / "hospital_peer_comparison.csv", index=False)
    model_meta.update(meta)
    model_meta["base_model_r_squared_including_state_fixed_effects"] = base_meta["r_squared_including_state_fixed_effects"]
    model_meta.update({"joined_characteristics": int(data["hospital_type"].ne("Unknown").sum()),
                       "county_rucc_match_share": float(data["rucc_2023"].notna().mean()),
                       "pos_bed_count_match_share": float(data["BED_CNT"].notna().mean()),
                       "pos_psych_bed_match_share": float(data["PSYCH_UNIT_BED_CNT"].notna().mean()),
                       "county_mh_hpsa_match_share": float(data["mh_hpsa_designated"].ne("Unknown").mean()),
                       "county_mh_hpsa_designated_share": float(data["mh_hpsa_designated"].eq("Yes").mean()),
                       "cms_characteristics_as_of": meta["retrieved_utc"][:10],
                       "interpretation": "Cross-sectional adjusted associations, not causal effects. Contemporary characteristics are joined only to the latest common OP-18 reporting period."})
    (RESULTS / "hospital_driver_model_metadata.json").write_text(json.dumps(model_meta, indent=2), encoding="utf-8")
    cab = coeffs.loc[coeffs.term.eq("hospital_type[Critical Access Hospitals]")].iloc[0]
    cab_base = base_coeffs.loc[base_coeffs.term.eq("hospital_type[Critical Access Hospitals]")].iloc[0]
    report = f"""# Hospital characteristics and psychiatric ED time gap

## Model scope

This is a cross-sectional analysis of the latest common OP-18 period ending {model_meta['period_end']}. The analysis includes {model_meta['n_hospitals']:,} hospitals with reportable OP-18b and OP-18c scores and at least {MIN_SAMPLE} sampled patients in both components. Current CMS Hospital General Information and USDA 2023 RUCC are joined to that latest period only; they are not assigned retrospectively to earlier observations.

The outcome is OP-18c minus OP-18b, in minutes. It is the difference between two separately reported medians, not the median of patient-level paired differences. Predictors are hospital type, ownership, emergency-service status, metro/nonmetro classification, certified bed count, psychiatric-unit beds, and county mental-health geographic HPSA designation. Bed counts come from the CMS Provider of Services Q2 2026 file; HRSA HPSA designations are current at download and county-linked. The model includes state fixed effects and state-clustered CR1 standard errors. Bed counts enter as log(1 + count). Confidence intervals and p-values use a normal approximation. Coefficients are conditional associations, not causal effects or rankings.

## Main finding and expanded-model sensitivity

In the baseline specification, Critical Access Hospitals had an adjusted gap **{abs(cab_base.estimate_minutes):.1f} minutes lower** than acute care hospitals (95% CI {abs(cab_base.ci95_high):.1f} to {abs(cab_base.ci95_low):.1f} minutes lower), conditional on ownership, emergency-service status, metro status, and state fixed effects. It was the only baseline estimate with an interval excluding zero. After adding certified bed count, psychiatric-unit beds, and county mental-health HPSA, the CAH estimate attenuated to {cab.estimate_minutes:+.1f} minutes (95% CI {cab.ci95_low:+.1f} to {cab.ci95_high:+.1f}); this interval includes zero. The expanded model explains {100*model_meta['r_squared_including_state_fixed_effects']:.1f}% of observed gap variation, compared with {100*base_meta['r_squared_including_state_fixed_effects']:.1f}% in the baseline. Most variation remains unexplained.

Ownership contrasts use **Voluntary non-profit - Private** as the reference. Federal-government, physician-owned, and tribal hospitals are combined into one small “Other” category. Remaining coefficients are exploratory associations, not causal effects.

The expanded-model coefficients are in `hospital_driver_model_coefficients.csv`; the baseline specification is in `hospital_driver_model_base_coefficients.csv`. Model metadata: `hospital_driver_model_metadata.json`.

## Peer groups

Peer groups are defined before looking at outcomes as CMS hospital type × USDA metro/nonmetro category. Groups with fewer than {MIN_PEER_N} hospitals are marked below the minimum and their group-level distribution is suppressed. Facility-level differences from the peer median are descriptive comparison aids, not adjusted rankings or quality scores. See `peer_group_summary.csv` and `hospital_peer_comparison.csv`.

## Limitations

The CMS Hospital General Information characteristics are current (retrieved {model_meta['cms_characteristics_as_of']}); the POS file describes 2026 Q2; HRSA HPSA designations are current at retrieval; and RUCC is a 2023 county classification. Covariate timing therefore does not exactly match the September 2025 outcome, and hospital conditions may have changed. Psychiatric-unit beds are CMS unit-bed counts, not a census of inpatient psychiatric capacity at nearby facilities. HPSA is a county-level geographic designation, not a hospital-specific workforce measure. There is no causal identification, no adjustment for patient acuity, and no validated uncertainty model for the median gap. Refresh files and audit coverage before reuse.

Sources: [CMS Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u), [CMS Provider of Services](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-quality-improvement-and-evaluation-system), [HRSA mental-health HPSA downloads](https://data.hrsa.gov/data/download?AHRF=&data=AHRF), and [USDA 2023 Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/).
"""
    (RESULTS / "hospital_driver_analysis.md").write_text(report, encoding="utf-8")
    print(json.dumps(model_meta, indent=2))


if __name__ == "__main__":
    main()
