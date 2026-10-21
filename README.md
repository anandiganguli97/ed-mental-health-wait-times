# Psychiatric emergency department time in U.S. hospitals

CMS hospital data show a persistent difference between reported emergency-department times for discharged psychiatric visits and the non-psychiatric, non-transfer comparison group. The latest common period is October 2024–September 2025.

**[Open the interactive dashboard](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/dashboard.html)** · [Hospital lookup](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/hospital_lookup.html)

## Three findings

1. **The typical hospital reported an 83-minute gap.** The median difference was 83 minutes (IQR 39–146) across 3,023 hospitals with both results.
2. **Psychiatric-gap deciles turn over more than OP-18b deciles.** From 2024 to 2025, 38.5% of hospitals stayed in the top decile and 31.5% stayed in the bottom decile for the psychiatric gap. In the same 2,566 hospitals, OP-18b overlap was 80.5% and 75.9%. Comparing 2025 with each hospital’s prior-years mean gives the same pattern: 41.8%/28.6% for the psychiatric gap and 74.5%/70.4% for OP-18b. Turnover can reflect true change and noise; residual variation is flat across sample sizes 11–49 and lower above 50.
3. **Psychiatric-unit presence is associated with a shorter reported gap.** Hospitals reporting a psych unit had a 10.5-minute smaller gap (95% CI 20.1 to 0.8 minutes smaller). This association is similar after capping extreme values. It describes discharged visits; it does not show that an individual patient was seen faster.

## What changes when extreme values are capped

The primary driver model keeps all reported values. A separate model caps the top 1% at 602.34 minutes; that affects 31 of 3,023 latest-period observations. In that sensitivity, the psych-unit estimate remains smaller (−8.8 minutes, 95% CI −16.7 to −0.9), while bed size (+7.5 minutes per log unit, CI 1.6 to 13.4) and nonmetro status (+12.5 minutes, CI 1.5 to 23.5) are positive only in the capped model. The capped outcome’s R² is 10.7% versus 5.8% in the primary model, and its residual SD is 105 versus 172 minutes; these are influence diagnostics on a changed outcome, not a like-for-like fit comparison. The proprietary-ownership estimate falls from +32.4 to +12.3 minutes after capping.

The CAH estimate falls from −17.3 minutes in the baseline model to −13.0 (95% CI −28.7 to +2.7) in the expanded model. CMS limits CAHs to 25 inpatient/swing beds, so hospital size and CAH status overlap by design. The size-adjusted estimate is exploratory, not a causal effect. [CMS CAH requirements](https://www.cms.gov/medicare/health-safety-standards/certification-compliance/critical-access-hospitals).

## Data quality and measure limits

The 24-hour rule was applied to the selected annual panel, not just 2025. It flags 21 hospital-period values across 12 facilities; all meet the 11-case reporting threshold. Eleven flags are in three HCA Houston facilities: West, Southeast, and Clear Lake. West (CCN 450644) and Southeast (CCN 450097) are distinct in the year-by-year records. The Southeast CCN appears under the 2018 name Bayshore Medical Center, which is why the dated CCN crosswalk remains open. The [full flag list](results/hospital_gap_outliers_over_24h.csv) and [HCA annual identity audit](results/hca_houston_facility_annual_audit.csv) show the values by reporting year.

OP-18c includes psychiatric patients discharged from the ED and excludes transfers. Hospitals with psych units may admit their sickest patients, leaving a different group in the discharged measure; CAHs may transfer patients who are excluded as well. The observed gap can reflect who is counted as much as throughput. The public data cannot separate those explanations. This measure is not admitted-patient boarding and is not an individual patient’s wait.

The mobile-crisis authorization analysis is exploratory. Its event-time −6 pre-period estimate is +13.9 minutes (95% interval 0.5 to 26.6), a warning about the parallel-trends assumption. Excluding the six HCA Houston facilities from the Texas never-treated control changes the event-time 0 estimate from +3.1 to +2.1 minutes; both intervals include zero.

## Analysis and reproduction

The project harmonizes 31 archived CMS releases (145,833 hospital-snapshot rows). Descriptive comparisons require at least 11 sampled patients in both OP-18 components. Shrinkage modestly improves held-out prediction of multi-year averages (RMSE reduction 2.7% in 2024 and 1.4% in 2025). Removing all six HCA Houston facilities leaves similarly small reductions (3.4% and 1.6%). Annual residuals mix real change with measurement noise.

Install Python 3.10+ and dependencies, then run from this directory:

```powershell
python -m pip install -r python/requirements.txt
python python/download_and_build_panel.py
python python/build_historical_panel.py
python python/build_hospital_drivers.py
python python/build_shrinkage_benchmark.py
python python/build_mobile_crisis_did.py
python python/build_hospital_lookup.py
python python/build_dashboard.py
```

The archive scripts preserve release dates, reporting periods, measure IDs, samples, and footnotes. Raw downloads and facility-level data stay out of Git; aggregate results and the dashboard are committed. See the [executive brief](results/executive_brief.md), [driver analysis](results/hospital_driver_analysis.md), [historical outlier and rank audit](results/hospital_outlier_and_rank_stability.md), and [analysis plan](analysis-plan.md).

## Repository map

- `analysis-plan.md` — analysis decisions and dated amendments.
- `data-quality-log.csv` — source, transformation, suppression, and linkage decisions.
- `policy/mobile-crisis-adoption.csv` — state policy dates and source audit.
- `python/` — data preparation and analysis scripts.
- `results/` — reports, aggregate tables, model outputs, and charts.
- `site/` — dashboard and hospital lookup.

Sources include CMS Timely and Effective Care, CMS Hospital General Information, CMS Provider of Services, HRSA mental-health HPSA data, USDA Rural-Urban Continuum Codes, and state Medicaid SPA documents. The HPSA measure is county-level; psychiatric-unit beds are not a census of nearby capacity.

