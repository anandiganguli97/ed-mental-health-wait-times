# ED mental health wait-time benchmark

An open, reproducible analysis of U.S. hospital emergency department time for psychiatric and mental health visits. The project is designed to answer three distinct questions: how hospitals compare, which hospital/community characteristics are associated with the gap, and whether state Medicaid mobile crisis coverage changed the gap.

## Status

**Stage 1 — source panel wired.** The supplied `Timely_and_Effective_Care-National.csv` is a national summary (45 measures) with no hospital identifier. It is retained as context, not used for hospital rankings. For Oct. 1, 2024–Sep. 30, 2025, its reported OP-18c value is 257 minutes and OP-18b is 162 minutes, a 95-minute national difference. Footnote 25 means the national average includes VHA hospital data; footnote 26 means it includes DoD hospital data, so the national comparator populations must be interpreted with care. The pipeline now targets the provider-level CMS hospital dataset (`yv7e-xc69`) and extracts OP-18a/b/c/d observations with the CMS-reported sample field and footnotes. The R pipeline still needs to be run in an R environment, and historical releases and comparability remain to be validated.

## Questions

1. **Benchmark:** What is each hospital's OP-18c minus OP-18b median-time gap, and how much do raw rankings change after uncertainty-aware shrinkage?
2. **Drivers:** Which hospital and community characteristics are associated with larger gaps after accounting for state and year?
3. **Policy:** Did adoption of Medicaid's ARPA mobile crisis benefit change psychiatric ED time relative to non-psychiatric ED time?

OP-18 is a discharged-patient ED time measure. It is not a direct measure of admitted-patient boarding. CMS does not publish the visit counts and acuity information needed to fully assess precision or case mix; suppressed and small-cell values will be retained in the data-quality log and excluded from rankings unless a defensible uncertainty model can be built.

## Reproduce

Install R (4.3 or newer) and run once to restore the locked package environment:

```r
install.packages("renv")
renv::restore()
targets::tar_make()
```

The CMS pull is public and requires no API key. The supplied national summary is included as a small public source file; future raw downloads are ignored by Git and the pipeline records retrieval time and source URL alongside each extract. `targets::tar_make()` downloads the hospital dataset, validates its known schema, builds a hospital-period OP-18 table, and summarizes the national reference.

## Repository map

- `analysis-plan.md` — pre-analysis decisions and causal design, dated before model fitting.
- `data-quality-log.csv` — source, transformation, suppression, definition and linkage decisions.
- `policy/mobile-crisis-adoption.csv` — state-level treatment dates, source and verification status.
- `_targets.R`, `R/` — reproducible pipeline.
- `site/` — Quarto narrative site, to be populated after validated estimates exist.
- `renv.lock` — package lockfile, generated with `renv::snapshot()` on a machine with R.

## Planned outputs

1. National benchmark with raw and empirical-Bayes estimates, intervals and rank movement.
2. Peer-group comparisons and mixed-model associations.
3. Staggered-adoption event study with transparent assumptions and sensitivity checks.
4. Nontechnical hospital/state brief and technical appendix.

## Data sources

CMS Timely and Effective Care (current and archived), CMS Hospital General Information, CMS Provider of Services / inpatient psychiatric facility files, HRSA HPSA, Area Health Resources Files, Census ACS, USDA rural-urban classifications, and a primary-source-verified state mobile crisis adoption table. The project will not use N-SUMHSS work-adjacent data.

## Data quality and interpretation

See `data-quality-log.csv` and `analysis-plan.md`. Hospital identifiers will be standardized to CCN, but mergers, identifier changes, suppressed values, and measure-definition changes will be explicitly tracked. Estimates and rankings will be presented with uncertainty; no rank will be treated as a quality score.
