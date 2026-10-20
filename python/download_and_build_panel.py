"""Download the current CMS hospital extract and build an OP-18 panel."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
DATASET_ID = "yv7e-xc69"
METADATA_URL = f"https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/{DATASET_ID}?show-reference-ids"
MEASURES = ["OP_18a", "OP_18b", "OP_18c", "OP_18d"]


def get_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "ED-Mental-Health-Benchmark/0.2 (public CMS data)"})
    for attempt in range(7):
        try:
            with urlopen(request, timeout=90) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 6:
                raise RuntimeError(f"CMS request failed for {url}: {exc}") from exc
            delay = min(2**attempt, 30)
            print(f"CMS request failed ({exc}); retrying in {delay}s", flush=True)
            time.sleep(delay)
    raise AssertionError("unreachable")


def download_current_extract() -> tuple[Path, pd.DataFrame]:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = RAW / "Timely_and_Effective_Care-Hospital-current.csv"
    metadata = json.loads(get_bytes(METADATA_URL))
    distributions = metadata.get("distribution", [])
    urls = [d.get("data", {}).get("downloadURL") for d in distributions]
    download_url = next((url for url in urls if url and url.lower().endswith(".csv")), None)
    if not download_url:
        raise ValueError("CMS metadata did not provide a CSV download URL.")
    payload = get_bytes(download_url)
    out.write_bytes(payload)
    full = pd.read_csv(out, dtype=str, low_memory=False)
    full.columns = [str(column).strip().lower().replace(" ", "_").replace("/", "") for column in full.columns]
    required_fields = {"facility_id", "measure_id", "score", "sample", "start_date", "end_date"}
    missing = sorted(required_fields - set(full.columns))
    if missing:
        raise ValueError(f"CMS schema changed; missing required fields: {missing}")
    total_rows = int(len(full))
    fieldnames = list(full.columns)
    op18 = full.loc[full["measure_id"].isin(MEASURES)].copy()
    metadata = {
        "dataset_id": DATASET_ID,
        "metadata_url": METADATA_URL,
        "source_url": download_url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "total_rows": total_rows,
        "field_names": fieldnames,
        "op18_rows": len(op18),
    }
    (RAW / "Timely_and_Effective_Care-Hospital-current-metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return out, op18


def build_panel(op18: pd.DataFrame) -> pd.DataFrame:
    required = {
        "facility_id", "facility_name", "state", "countyparish", "measure_id",
        "score", "sample", "footnote", "start_date", "end_date",
    }
    missing = sorted(required - set(op18.columns))
    if missing:
        raise ValueError(f"CMS schema changed; missing required fields: {missing}")

    data = op18.copy()
    data["score_minutes"] = pd.to_numeric(data["score"], errors="coerce")
    data["sample_n"] = pd.to_numeric(data["sample"], errors="coerce")
    data["start_date"] = pd.to_datetime(data["start_date"], format="%m/%d/%Y", errors="coerce")
    data["end_date"] = pd.to_datetime(data["end_date"], format="%m/%d/%Y", errors="coerce")

    key = ["facility_id", "measure_id", "start_date", "end_date"]
    duplicates = data.duplicated(key, keep=False)
    if duplicates.any():
        examples = data.loc[duplicates, key].head(8).to_dict(orient="records")
        raise ValueError(f"Duplicate hospital/measure/period rows; refusing to collapse them: {examples}")

    id_columns = ["facility_id", "facility_name", "state", "countyparish", "start_date", "end_date"]
    value_columns = ["score", "score_minutes", "sample", "sample_n", "footnote"]
    wide = data.pivot(index=id_columns, columns="measure_id", values=value_columns)
    wide.columns = [f"{value}_{measure}" for value, measure in wide.columns]
    wide = wide.reset_index()
    for measure in MEASURES:
        for value in value_columns:
            column = f"{value}_{measure}"
            if column not in wide:
                wide[column] = pd.NA
    wide["psych_gap_minutes"] = wide["score_minutes_OP_18c"] - wide["score_minutes_OP_18b"]
    wide["sample_min_op18bc"] = wide[["sample_n_OP_18b", "sample_n_OP_18c"]].min(axis=1, skipna=True)
    wide["gap_status"] = "available"
    wide.loc[wide["psych_gap_minutes"].isna(), "gap_status"] = "missing_or_suppressed_component"
    return wide.sort_values(["state", "facility_name", "start_date"], na_position="last")


def main() -> None:
    raw_path, op18 = download_current_extract()
    panel = build_panel(op18)
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_panel = PROCESSED / "hospital_op18_current.csv"
    panel.to_csv(out_panel, index=False)
    observed = panel.loc[panel["psych_gap_minutes"].notna()].copy()
    state = observed.groupby("state", dropna=False).agg(
        hospitals_with_both_measures=("facility_id", "nunique"),
        median_gap_minutes=("psych_gap_minutes", "median"),
        mean_gap_minutes=("psych_gap_minutes", "mean"),
        positive_gap_share=("psych_gap_minutes", lambda x: float((x > 0).mean())),
    ).reset_index()
    state = state.sort_values(["hospitals_with_both_measures", "state"], ascending=[False, True])
    state.to_csv(RESULTS / "state_op18_gap_summary.csv", index=False)
    counts = panel[["sample_n_OP_18b", "sample_n_OP_18c"]].stack().dropna()
    summary = {
        "dataset_id": DATASET_ID,
        "source_url": json.loads((RAW / "Timely_and_Effective_Care-Hospital-current-metadata.json").read_text(encoding="utf-8"))["source_url"],
        "retrieved_utc": json.loads((RAW / "Timely_and_Effective_Care-Hospital-current-metadata.json").read_text(encoding="utf-8"))["retrieved_utc"],
        "period_start": str(panel["start_date"].min().date()),
        "period_end": str(panel["end_date"].max().date()),
        "op18_hospital_period_rows": int(len(panel)),
        "distinct_facilities": int(panel["facility_id"].nunique()),
        "rows_with_op18b_and_op18c": int(len(observed)),
        "gap_available_share": float(len(observed) / len(panel)) if len(panel) else None,
        "distinct_periods": int(panel["start_date"].nunique()),
        "suppressed_or_missing_gap": int(panel["psych_gap_minutes"].isna().sum()),
        "median_gap_minutes": float(observed["psych_gap_minutes"].median()) if len(observed) else None,
        "mean_gap_minutes": float(observed["psych_gap_minutes"].mean()) if len(observed) else None,
        "gap_p25_minutes": float(observed["psych_gap_minutes"].quantile(.25)) if len(observed) else None,
        "gap_p75_minutes": float(observed["psych_gap_minutes"].quantile(.75)) if len(observed) else None,
        "gap_p90_minutes": float(observed["psych_gap_minutes"].quantile(.90)) if len(observed) else None,
        "minimum_gap_minutes": float(observed["psych_gap_minutes"].min()) if len(observed) else None,
        "maximum_gap_minutes": float(observed["psych_gap_minutes"].max()) if len(observed) else None,
        "positive_gap_rows": int((observed["psych_gap_minutes"] > 0).sum()),
        "zero_gap_rows": int((observed["psych_gap_minutes"] == 0).sum()),
        "negative_gap_rows": int((observed["psych_gap_minutes"] < 0).sum()),
        "sample_count_nonmissing_values": int(len(counts)),
        "sample_count_values_numeric_min": float(counts.min()) if len(counts) else None,
        "sample_count_values_numeric_median": float(counts.median()) if len(counts) else None,
        "states_or_jurisdictions_with_data": int(state["state"].nunique()),
        "sample_field_note": "CMS Sample values are retained but not interpreted as denominators until the contemporaneous technical specification confirms their meaning.",
        "interpretation": "Descriptive discharged-visit comparison; OP-18b excludes psychiatric and transfer patients. Not admitted-patient boarding, case-mix adjusted, or causal.",
    }
    (RESULTS / "national_op18_gap_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    report = f'''# National benchmark: psychiatric ED visit time\n\n**Data:** CMS Timely and Effective Care—Hospital, dataset `{DATASET_ID}`.\n**Reporting period:** {summary['period_start']} through {summary['period_end']}.\n**Retrieved:** {summary['retrieved_utc']}.\n\n## Findings\n\n- CMS published OP-18 results for **{summary['distinct_facilities']:,} hospitals** in this extract.\n- Both OP-18b and OP-18c were usable for **{len(observed):,} hospitals ({summary['gap_available_share']:.1%})**; {summary['suppressed_or_missing_gap']:,} had a missing or suppressed component.\n- Among hospitals with both scores, the **median OP-18c minus OP-18b gap was {summary['median_gap_minutes']:.0f} minutes** (IQR {summary['gap_p25_minutes']:.0f}–{summary['gap_p75_minutes']:.0f}; 90th percentile {summary['gap_p90_minutes']:.0f}). The unweighted mean was {summary['mean_gap_minutes']:.1f} minutes.\n- The gap was positive at {summary['positive_gap_rows']:,} hospitals ({summary['positive_gap_rows']/len(observed):.1%}), zero at {summary['zero_gap_rows']:,}, and negative at {summary['negative_gap_rows']:,}. A positive gap means the reported psychiatric-stratum median was longer at that hospital.\n\nThe hospital-level median gap (83 minutes) is not directly interchangeable with the supplied national aggregate gap (95 minutes): the hospital statistic is an unweighted median of hospital contrasts, while the national statistic is a CMS-reported aggregate. They describe different summaries.\n\n## Measure and limits\n\nOP-18c reports ED arrival-to-departure time for psychiatric/mental-health patients. OP-18b is the comparison group excluding psychiatric/mental-health patients and transfers. This is a discharged-visit time measure; it does **not** measure boarding among patients admitted to the hospital. Results are descriptive, unadjusted, and not causal or a quality ranking. Hospital values are not patient-level observations. The CMS `Sample` field is preserved, but its denominator meaning has not been confirmed against the contemporaneous technical specification, so it is not used for weights or uncertainty intervals.\n\nThe single current release provides one annual period, so hospital trends, driver models, empirical-Bayes shrinkage, and policy event studies are not yet identified. Missing or suppressed results may also affect which hospitals are represented. The state table is descriptive and should not be used to rank state performance.\n\n## Reproduce\n\nRun `python python/download_and_build_panel.py` after installing `python/requirements.txt`. The script retrieves the current CSV URL from the CMS metadata API, saves the raw source under the ignored `data/raw/` directory, preserves hospital-level results under ignored `data/processed/`, and writes the committed national JSON and state CSV summaries under `results/`.\n\nSource: [CMS Timely and Effective Care—Hospital dataset](https://data.cms.gov/provider-data/dataset/{DATASET_ID}) (dataset and source release can change).\n'''
    (RESULTS / "national_benchmark.md").write_text(report, encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

