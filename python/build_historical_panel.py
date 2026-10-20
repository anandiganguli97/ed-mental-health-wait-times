"""Build a reproducible OP-18 panel from CMS hospital archive snapshots."""

from __future__ import annotations

import argparse
import io
import json
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = ROOT / "data" / "raw" / "cms_archives"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
ARCHIVE_URL = "https://data.cms.gov/provider-data/sites/default/files/dataset-archives/theme/hospitals/hospitals_annual_{year}.zip"
MEASURES = ["OP_18a", "OP_18b", "OP_18c", "OP_18d"]


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "ED-Mental-Health-Benchmark/0.2 (public CMS data)"})
    for attempt in range(7):
        try:
            with urlopen(request, timeout=180) as response, destination.open("wb") as out:
                total = int(response.headers.get("Content-Length") or 0)
                received = 0
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
                    received += len(chunk)
                print(f"Downloaded {destination.name}: {received:,}/{total:,} bytes", flush=True)
            return
        except (HTTPError, URLError, TimeoutError) as exc:
            destination.unlink(missing_ok=True)
            if attempt == 6:
                raise RuntimeError(f"CMS archive download failed: {url}: {exc}") from exc
            wait = min(2**attempt, 30)
            print(f"CMS archive download failed ({exc}); retrying in {wait}s", flush=True)
            time.sleep(wait)


def normalize_columns(data: pd.DataFrame) -> pd.DataFrame:
    data.columns = [str(c).strip().lower().replace(" ", "_").replace("/", "") for c in data.columns]
    aliases = {
        "provider_id": "facility_id", "hospital_name": "facility_name",
        "measure_start_date": "start_date", "measure_end_date": "end_date",
        "county_name": "countyparish",
    }
    data = data.rename(columns={old: new for old, new in aliases.items() if old in data.columns and new not in data.columns})
    return data


def archived_measure_file(archive: zipfile.ZipFile) -> str | None:
    candidates = []
    for filename in archive.namelist():
        normalized = re.sub(r"[^a-z]", "", Path(filename).name.lower())
        if "timelyandeffectivecarehospitalcsv" in normalized and not re.search(r"REH[_ -]*Timely", Path(filename).name, re.IGNORECASE):
            candidates.append(filename)
    return next((name for name in candidates if not name.startswith("__MACOSX/")), None)


def read_archived_snapshot(outer: zipfile.ZipFile, nested_name: str, release_date: str) -> pd.DataFrame:
    with outer.open(nested_name) as nested_bytes, zipfile.ZipFile(nested_bytes) as nested:
        source_name = archived_measure_file(nested)
        if source_name is None:
            return pd.DataFrame()
        with nested.open(source_name) as source:
            try:
                data = pd.read_csv(source, dtype=str, low_memory=False)
            except UnicodeDecodeError:
                source.seek(0)
                data = pd.read_csv(source, dtype=str, low_memory=False, encoding="cp1252")
    data = normalize_columns(data)
    required = {"facility_id", "facility_name", "state", "measure_id", "score", "sample", "footnote", "start_date", "end_date"}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Schema change in {nested_name}: missing {missing}")
    data = data.loc[data["measure_id"].isin(MEASURES)].copy()
    if data.empty:
        return data
    data.insert(0, "snapshot_date", release_date)
    data["archive_source"] = nested_name
    return data


def load_archives(start_year: int, end_year: int, archive_dir: Path) -> pd.DataFrame:
    all_rows: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        archive_path = archive_dir / f"hospitals_annual_{year}.zip"
        if not archive_path.exists() or archive_path.stat().st_size < 1_000_000:
            download(ARCHIVE_URL.format(year=year), archive_path)
        with zipfile.ZipFile(archive_path) as outer:
            nested_names = [name for name in outer.namelist() if name.lower().endswith(".zip")]
            for name in nested_names:
                match = re.search(r"(20\d{2}-\d{2}-\d{2})", name)
                if not match:
                    continue
                rows = read_archived_snapshot(outer, name, match.group(1))
                if not rows.empty:
                    all_rows.append(rows)
                    print(f"{match.group(1)}: {len(rows):,} OP-18 records", flush=True)
    if not all_rows:
        raise ValueError("No OP-18 records were found in the CMS archive range.")
    return pd.concat(all_rows, ignore_index=True)


def build_gap_panel(data: pd.DataFrame) -> pd.DataFrame:
    data["score_minutes"] = pd.to_numeric(data["score"], errors="coerce")
    data["sample_n"] = pd.to_numeric(data["sample"], errors="coerce")
    data["start_date"] = pd.to_datetime(data["start_date"], format="mixed", errors="coerce")
    data["end_date"] = pd.to_datetime(data["end_date"], format="mixed", errors="coerce")
    keys = ["snapshot_date", "facility_id", "measure_id", "start_date", "end_date"]
    duplicate_mask = data.duplicated(keys, keep=False)
    if duplicate_mask.any():
        sample = data.loc[duplicate_mask, keys].head(10).to_dict(orient="records")
        raise ValueError(f"Duplicate hospital/measure/snapshot/period records; refusing to collapse: {sample}")
    index = ["snapshot_date", "facility_id", "facility_name", "state", "start_date", "end_date"]
    values = ["score", "score_minutes", "sample", "sample_n", "footnote"]
    panel = data.pivot(index=index, columns="measure_id", values=values)
    panel.columns = [f"{value}_{measure}" for value, measure in panel.columns]
    panel = panel.reset_index()
    for measure in MEASURES:
        for value in values:
            column = f"{value}_{measure}"
            if column not in panel:
                panel[column] = pd.NA
    panel["psych_gap_minutes"] = panel["score_minutes_OP_18c"] - panel["score_minutes_OP_18b"]
    panel["sample_min_op18bc"] = panel[["sample_n_OP_18b", "sample_n_OP_18c"]].min(axis=1, skipna=True)
    panel["gap_status"] = "available"
    panel.loc[panel["psych_gap_minutes"].isna(), "gap_status"] = "missing_or_suppressed_component"
    return panel


def summarize(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    observed = panel.loc[panel["psych_gap_minutes"].notna()].copy()
    by_release = observed.groupby("snapshot_date", as_index=False).agg(
        hospitals_with_both_measures=("facility_id", "nunique"),
        median_gap_minutes=("psych_gap_minutes", "median"),
        mean_gap_minutes=("psych_gap_minutes", "mean"),
        gap_p25_minutes=("psych_gap_minutes", lambda x: x.quantile(.25)),
        gap_p75_minutes=("psych_gap_minutes", lambda x: x.quantile(.75)),
        gap_p90_minutes=("psych_gap_minutes", lambda x: x.quantile(.90)),
        positive_gap_share=("psych_gap_minutes", lambda x: float((x > 0).mean())),
    )
    periods = panel.groupby("snapshot_date").agg(
        period_start=("start_date", "min"), period_end=("end_date", "max"),
        hospitals_in_extract=("facility_id", "nunique"),
        hospitals_missing_gap=("psych_gap_minutes", lambda x: int(x.isna().sum())),
    ).reset_index()
    by_release = by_release.merge(periods, on="snapshot_date", how="left")
    by_release["period_start"] = pd.to_datetime(by_release["period_start"]).dt.strftime("%Y-%m-%d")
    by_release["period_end"] = pd.to_datetime(by_release["period_end"]).dt.strftime("%Y-%m-%d")
    by_period = by_release.dropna(subset=["period_start", "period_end"]).sort_values("snapshot_date")
    by_period = by_period.drop_duplicates(["period_start", "period_end"], keep="last")
    by_period = by_period.sort_values(["period_end", "period_start"])
    state = observed.groupby(["snapshot_date", "state"], as_index=False).agg(
        hospitals_with_both_measures=("facility_id", "nunique"),
        median_gap_minutes=("psych_gap_minutes", "median"),
        mean_gap_minutes=("psych_gap_minutes", "mean"),
        positive_gap_share=("psych_gap_minutes", lambda x: float((x > 0).mean())),
    )
    latest_date = panel["snapshot_date"].max()
    latest = panel[panel["snapshot_date"] == latest_date]
    latest_observed = latest[latest["psych_gap_minutes"].notna()]
    overall = {
        "source": "CMS Provider Data Catalog Hospitals archived annual snapshot files",
        "archive_url": "https://data.cms.gov/provider-data/archived-data/hospitals",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "first_release_date": str(panel["snapshot_date"].min()),
        "latest_release_with_op18_date": str(latest_date),
        "snapshot_count": int(panel["snapshot_date"].nunique()),
        "hospital_snapshot_period_rows": int(len(panel)),
        "distinct_hospitals_across_snapshots": int(panel["facility_id"].nunique()),
        "periods_missing_gap": int(panel["psych_gap_minutes"].isna().sum()),
        "latest_reporting_period_start": str(latest["start_date"].min().date()) if latest["start_date"].notna().any() else None,
        "latest_reporting_period_end": str(latest["end_date"].max().date()) if latest["end_date"].notna().any() else None,
        "latest_hospitals_in_extract": int(latest["facility_id"].nunique()),
        "latest_hospitals_with_both_measures": int(latest_observed["facility_id"].nunique()),
        "latest_hospital_median_gap_minutes": float(latest_observed["psych_gap_minutes"].median()),
        "latest_gap_p25_minutes": float(latest_observed["psych_gap_minutes"].quantile(.25)),
        "latest_gap_p75_minutes": float(latest_observed["psych_gap_minutes"].quantile(.75)),
        "latest_op18c_sample_median": float(latest_observed["sample_n_OP_18c"].median()),
        "latest_op18c_sample_minimum": float(latest_observed["sample_n_OP_18c"].min()),
        "sample_field_note": "CMS describes the public Sample field for eligible hospital patients and notes that hospitals may sample under CMS rules. The count does not provide the patient-level dispersion needed to recover a median's sampling uncertainty.",
        "interpretation": "Descriptive discharged-visit measure; OP-18b excludes psychiatric and transfer patients. No causal or case-mix-adjusted interpretation.",
    }
    return by_release, by_period, state, overall


def write_historical_report(by_period: pd.DataFrame, overall: dict, sensitivity: pd.DataFrame) -> None:
    annual = by_period.loc[
        by_period["period_start"].str.endswith("-01-01")
        & by_period["period_end"].str.endswith("-12-31")
    ].copy()
    pandemic = by_period.loc[
        (by_period["period_start"] == "2019-10-01")
        & (by_period["period_end"] == "2020-09-30")
    ]
    latest = by_period.loc[
        (by_period["period_start"] == overall["latest_reporting_period_start"])
        & (by_period["period_end"] == overall["latest_reporting_period_end"])
    ]
    selected = pd.concat([annual, pandemic, latest]).drop_duplicates(["period_start", "period_end"])
    selected = selected.sort_values(["period_end", "period_start"])
    table = [
        "| Reporting period | Hospitals with both measures | Median hospital gap | IQR |",
        "|---|---:|---:|---:|",
    ]
    for row in selected.itertuples(index=False):
        label = f"{row.period_start} to {row.period_end}"
        table.append(
            f"| {label} | {row.hospitals_with_both_measures:,} | {row.median_gap_minutes:.0f} min | {row.gap_p25_minutes:.0f}–{row.gap_p75_minutes:.0f} min |"
        )
    sensitivity_table = [
        "| Minimum sample in each component | Hospitals retained | Share retained | Median gap | Change vs all hospitals |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in sensitivity.itertuples(index=False):
        sensitivity_table.append(
            f"| {row.minimum_sample_in_both_components} | {row.hospitals_retained:,} | {row.share_of_hospitals_with_gap:.1%} | {row.median_gap_minutes:.1f} min | {row.median_shift_from_all_minutes:+.1f} min |"
        )
    report = f'''# Historical benchmark: psychiatric ED visit time\n\nCMS maintains quarterly hospital-data snapshots. The archived OP-18 records provide {overall['snapshot_count']} snapshots from {overall['first_release_date']} through {overall['latest_release_with_op18_date']}, covering reporting periods beginning in 2017. The latest release with OP-18 data covers **{overall['latest_reporting_period_start']} to {overall['latest_reporting_period_end']}**. The 2026-09-30 archive did not update this dataset, so 2026-08-13 is the newest OP-18 snapshot available in CMS's archive as retrieved on {overall['retrieved_utc'][:10]}.\n\n## Selected reporting periods\n\nThe table keeps one hospital-level summary for each selected reporting period. Repeated archived snapshots of the same period are de-duplicated by retaining the latest release. These are unweighted medians across hospitals, not patient-weighted national medians.\n\n{chr(10).join(table)}\n\nThe median hospital gap rose from 76 minutes in calendar 2018 to 90 minutes in 2022, then declined to 83 minutes in the latest 12-month period. The 2019-10 through 2020-09 reporting period, which overlaps the first pandemic year, had a 96-minute median gap. These patterns are descriptive: the reporting windows overlap, release coverage is not uniform, and they do not identify causes or policy effects. The 2020-07 through 2020-12 snapshot is a six-month period and is omitted from the selected annual comparison.\n\n## Latest release detail\n\nThe August 2026 archive contains {overall['latest_hospitals_in_extract']:,} hospital-period records with OP-18. Both OP-18b and OP-18c were usable at {overall['latest_hospitals_with_both_measures']:,} hospitals ({overall['latest_hospitals_with_both_measures']/overall['latest_hospitals_in_extract']:.1%}); the median gap was {overall['latest_hospital_median_gap_minutes']:.0f} minutes (IQR {overall['latest_gap_p25_minutes']:.0f}–{overall['latest_gap_p75_minutes']:.0f}). The median reported OP-18c `Sample` value was {overall['latest_op18c_sample_median']:.0f} (minimum {overall['latest_op18c_sample_minimum']:.0f}) among hospitals with both scores. The patient-level visit times and dispersion are not released, so sample counts alone do not recover the sampling distribution of each hospital median or of the gap. CMS states that sample sizes can support confidence intervals for reported measures, but the method for the OP-18 median gap must be validated before publishing shrinkage estimates.\n\nThe supplied national CMS file reports OP-18c at 257 minutes and OP-18b at 162 minutes for this same latest reporting period, a 95-minute national aggregate difference. That is not directly comparable to the 83-minute median of hospital-level differences.\n\n## Measure limits\n\nOP-18c is median ED arrival-to-departure time for discharged psychiatric/mental-health visits and excludes transfers. OP-18b is the corresponding measure excluding psychiatric/mental-health patients and transfers. Neither measures boarding among patients admitted to the hospital. Results are descriptive, not case-mix adjusted, causal, or an overall quality ranking. Hospitals with unavailable/suppressed scores are missing from the paired gap.\n\nThe archived hospital panel and release-level files remain under ignored `data/processed/`. Committed outputs include the national release summary, de-duplicated reporting-period summary, and state-by-release summary. Run `python python/build_historical_panel.py` to re-download the CMS annual archives and rebuild those outputs.\n\nSources: [CMS hospital archives](https://data.cms.gov/provider-data/archived-data/hospitals), [Timely & Effective Care measure definitions](https://data.cms.gov/provider-data/topics/hospitals/timely-effective-care/), and [CMS Hospital Data Dictionary (July 2026)](https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/hospital/HOSPITAL_Data_Dictionary.pdf).\n'''
    sensitivity_section = (
        "## Small-sample sensitivity\n\n"
        "CMS's `Sample` field is the measure-specific count of sampled eligible patients; it is not total ED volume. "
        "These illustrative thresholds are sensitivity checks, not validated exclusions or a correction for measurement error.\n\n"
        + "\n".join(sensitivity_table)
        + "\n\nAt a minimum of 20 cases in both components, the sample falls from 3,023 to 1,381 hospitals and the median gap changes from 83 to 93 minutes. "
        "This does not establish which estimate is less biased; it shows why a threshold alone cannot resolve small-sample uncertainty.\n\n"
    )
    report = report.replace("## Latest release detail", sensitivity_section + "## Latest release detail")
    (RESULTS / "national_historical_benchmark.md").write_text(report, encoding="utf-8")


def build_sample_sensitivity(panel: pd.DataFrame) -> pd.DataFrame:
    latest_date = panel["snapshot_date"].max()
    latest = panel.loc[
        (panel["snapshot_date"] == latest_date)
        & panel["psych_gap_minutes"].notna()
        & panel["sample_n_OP_18b"].notna()
        & panel["sample_n_OP_18c"].notna()
    ].copy()
    latest["minimum_component_sample"] = latest[["sample_n_OP_18b", "sample_n_OP_18c"]].min(axis=1)
    base_median = float(latest["psych_gap_minutes"].median()) if len(latest) else None
    results = []
    for threshold in [11, 20, 30, 50, 100]:
        subset = latest.loc[latest["minimum_component_sample"] >= threshold].copy()
        gap = subset["psych_gap_minutes"]
        results.append({
            "minimum_sample_in_both_components": threshold,
            "hospitals_retained": int(len(subset)),
            "share_of_hospitals_with_gap": float(len(subset) / len(latest)) if len(latest) else None,
            "median_gap_minutes": float(gap.median()) if len(gap) else None,
            "gap_p25_minutes": float(gap.quantile(.25)) if len(gap) else None,
            "gap_p75_minutes": float(gap.quantile(.75)) if len(gap) else None,
            "positive_gap_share": float((gap > 0).mean()) if len(gap) else None,
            "median_shift_from_all_minutes": float(gap.median() - base_median) if len(gap) and base_median is not None else None,
        })
    return pd.DataFrame(results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--archive-dir", type=Path, default=ARCHIVE_DIR)
    args = parser.parse_args()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = load_archives(args.start_year, args.end_year, args.archive_dir)
    panel = build_gap_panel(rows)
    panel.to_csv(PROCESSED / "hospital_op18_archive_panel.csv", index=False)
    by_release, by_period, state, overall = summarize(panel)
    by_release.to_csv(RESULTS / "national_op18_snapshot_summary.csv", index=False)
    by_period.to_csv(RESULTS / "national_op18_period_summary.csv", index=False)
    state.to_csv(RESULTS / "state_op18_snapshot_summary.csv", index=False)
    sensitivity = build_sample_sensitivity(panel)
    sensitivity.to_csv(RESULTS / "sample_size_sensitivity.csv", index=False)
    (RESULTS / "historical_panel_metadata.json").write_text(json.dumps(overall, indent=2), encoding="utf-8")
    write_historical_report(by_period, overall, sensitivity)
    print(json.dumps(overall, indent=2))


if __name__ == "__main__":
    main()

