# ED mental health wait-time benchmark

**[Open the live interactive dashboard](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/dashboard.html)** · [Explore the source code](https://github.com/anandiganguli97/ed-mental-health-wait-times)

An open, reproducible analysis of U.S. hospital emergency department time for psychiatric and mental health visits. The project is designed to answer three distinct questions: how hospitals compare, which hospital/community characteristics are associated with the gap, and whether state Medicaid mobile crisis coverage changed the gap.

## Status

**Historical benchmark, first driver and peer analyses, and an exploratory mobile-crisis authorization analysis are complete.** We assembled 31 archived CMS releases spanning reporting periods from 2017 through Sep. 30, 2025, with 145,833 hospital-snapshot records. In the latest OP-18 release, both OP-18b and OP-18c were available for 3,023 hospitals; the median hospital gap was 83 minutes (IQR 39–146). Calendar-year medians rose from 76 minutes in 2018 to 90 in 2022, then fell to 83 in 2024; the latest 12-month period through Sep. 2025 was also 83 minutes. These comparisons are descriptive and reporting windows overlap. See [`results/national_historical_benchmark.md`](results/national_historical_benchmark.md), [`results/national_op18_period_summary.csv`](results/national_op18_period_summary.csv), and the state summaries. The latest-period driver model uses current hospital characteristics and 2023 county rurality, with state fixed effects; the results are associations, not causal effects. Peer groups are based on hospital type and metro status. The policy estimate uses SPA effective dates as authorization timing, not verified statewide service launch; event-time zero is +3.1 minutes (state-cluster bootstrap 95% interval −9.3 to +15.8) and is highly limited by adoption cohort support. The local and GitHub reproducible pipeline uses Python; R files remain an optional scaffold.

Read the integrated [executive brief](results/executive_brief.md) for a concise summary of findings and interpretation.

Open the [interactive dashboard](site/dashboard.html) for the national trend, state and peer comparisons, model estimates, policy event study, and hospital search. The [hospital lookup](site/hospital_lookup.html) is also available as a focused search page. Regenerate them with `python python/build_dashboard.py` and `python python/build_hospital_lookup.py` after rebuilding the analysis outputs.

## Questions

1. **Benchmark:** What is each hospital's OP-18c minus OP-18b median-time gap, and how much do raw rankings change after uncertainty-aware shrinkage? The raw hospital-period gaps are built. Shrinkage and rankings await a validated uncertainty method for the difference of medians; none are published yet.
2. **Drivers:** A latest-period cross-sectional model estimates associations with hospital type, ownership, emergency services, and rurality. Historical, staffing, bed-supply, and safety-net covariates remain unavailable in the current model.
3. **Policy:** An exploratory group-time ATT analysis estimates SPA authorization timing; most operational dates are unknown, so it is not an effect estimate of actual service availability. Short follow-up and few states in early cohorts make the findings tentative.

OP-18 is a discharged-patient ED time measure. It is not a direct measure of admitted-patient boarding. CMS's `Sample` field is retained as the measure-specific sampled-patient count, not as total ED volume or a case-mix adjustment. The current report includes transparent minimum-sample sensitivity checks; it does not claim that a threshold removes bias or use the sample count alone to construct intervals for the difference of medians.

## Reproduce

Install Python 3.10+ and dependencies, then run from this directory:

```powershell
python -m pip install -r python/requirements.txt
python python/download_and_build_panel.py
python python/build_historical_panel.py
python python/build_hospital_drivers.py
python python/build_mobile_crisis_did.py
python python/build_hospital_lookup.py
python python/build_dashboard.py
```

The current-release script uses CMS metadata to resolve the hospital CSV download. The archive script downloads CMS annual hospital archives (about 500 MB in total for 2019–2026), reads quarterly snapshots, adapts the early CMS column-name changes, retains OP-18a/b/c/d scores and footnotes, and builds the longitudinal hospital panel. The driver script downloads current CMS Hospital General Information and USDA 2023 Rural-Urban Continuum Codes and creates the latest-period model and peer summaries. Raw CMS downloads and hospital-level panels are ignored by Git; aggregate result files are committed. `R/` and `_targets.R` are an optional scaffold and have not been executed in this environment.

## Repository map

- `analysis-plan.md` — pre-analysis decisions and causal design, dated before model fitting.
- `data-quality-log.csv` — source, transformation, suppression, definition and linkage decisions.
- `policy/mobile-crisis-adoption.csv` — state-level treatment dates, source and verification status.
- `python/` — executed current-release and archived-snapshot download/analysis pipelines.
- `_targets.R`, `R/` — optional R scaffold; not the current source of truth.
- `results/` — descriptive national benchmark and state summary.
- `site/` — Quarto narrative site with benchmark, driver and policy results and their limitations.
- `renv/README.md` — instructions to generate the initial lockfile; commit `renv.lock` after that first setup.

## Planned outputs

1. Historical descriptive national and state summaries (completed; no rankings).
2. Uncertainty-aware benchmark, after validating a median-gap interval or an explicitly caveated shrinkage model.
3. Peer-group comparisons and mixed-model associations.
4. Exploratory staggered-adoption event study using SPA effective dates as an intention-to-implement measure; operational service dates remain unknown for most states.
5. Nontechnical hospital/state brief and technical appendix.

## Data sources

CMS Timely and Effective Care (current and archived), CMS Hospital General Information, and USDA Rural-Urban Continuum Codes are currently used. CMS Provider of Services / inpatient psychiatric facility files, HRSA HPSA, Area Health Resources Files, Census ACS, and a primary-source-verified state mobile crisis adoption table remain planned. The project will not use N-SUMHSS work-adjacent data.

## Data quality and interpretation

See `data-quality-log.csv` and `analysis-plan.md`. Hospital identifiers will be standardized to CCN, but mergers, identifier changes, suppressed values, and measure-definition changes will be explicitly tracked. Estimates and rankings will be presented with uncertainty; no rank will be treated as a quality score.
