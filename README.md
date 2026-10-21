# Mental-health emergency department time in U.S. hospitals

![Median hospital gap across selected annual reporting periods](results/figures/national-gap-trend.svg)

CMS data show a persistent difference between reported emergency department times for discharged psychiatric visits and the non-psychiatric, non-transfer comparison group. The latest common hospital reporting period covered October 2024–September 2025.

## Three findings

1. **The typical hospital reported an 83-minute gap.** Across 3,023 hospitals with both measures, the median difference was 83 minutes (IQR 39–146).
2. **Single-year decile membership turns over.** Among 2,933 hospitals with a 2025 result and at least one prior annual result, 41.8% of the top decile and 28.6% of the bottom decile also fell in the corresponding decile using their mean prior-year gap. This churn mixes real change with measurement noise; residual variation is broadly flat for sample sizes 11–49 and is lower above 50.
3. **The expanded model points to a size and psychiatric-unit pattern.** Each one-unit increase in log(1 + certified beds) corresponds to +4.5 minutes (95% CI −2.2 to +11.2); reporting any psychiatric-unit bed corresponds to −10.5 minutes versus none (95% CI −20.1 to −0.8). The CAH estimate falls from −17.3 to −13.0 minutes (95% CI −28.7 to +2.7) after adding bed count. Because CMS limits CAHs to 25 inpatient/swing beds, this attenuation is consistent with structural overlap between CAH status and hospital size.

The Medicaid mobile-crisis authorization analysis is exploratory and inconclusive; the event-time −6 pre-period estimate is +13.9 minutes (95% interval 0.5 to 26.6), a warning against assuming parallel pre-trends. See the [brief](results/executive_brief.md), [driver analysis](results/hospital_driver_analysis.md), and [limitations](results/mobile_crisis_policy_analysis.md).

## Why this matters

These results can help hospitals and health systems decide where to investigate their own behavioral-health ED pathways. They do not tell a CMO how long an individual patient waited, whether a patient boarded after admission, or which hospital provides better care. The measure covers discharged ED visits and compares two separately reported hospital medians.

**[Open the interactive dashboard](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/dashboard.html)** for the national trend, state and peer comparisons, model estimates, event study, and hospital search. The [hospital lookup](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/hospital_lookup.html) is also available.

## Analysis and limitations

The project harmonizes 31 archived CMS releases (145,833 hospital-snapshot rows), preserving reporting periods, release dates, measure identifiers, sampled-patient counts, and footnotes. Descriptive hospital comparisons use a minimum sample threshold of 11 in each measure. Raising the threshold changes the hospitals represented: the median gap is 83 minutes at 11, 93 at 20, and 67 at 100. This is selection into different hospital groups, not evidence that larger samples remove measurement noise.

An exploratory empirical-Bayes model uses repeated annual windows to estimate how hospital gaps vary across years by sample size. In held-out-year prediction, shrinkage reduced RMSE by 2.7% for 2024 and 1.4% for 2025, so it is a modest improvement for multi-year averages. Annual residual variation includes genuine hospital change as well as measurement error; it is not a validated sampling variance or confidence interval for a difference of medians. The annual decile overlap summary is descriptive and is not a hospital quality ranking.

The expanded driver model explains 5.8% of observed gap variation. It includes log CMS certified beds, a binary indicator for any psychiatric-unit bed, and a county-level mental-health HPSA designation. A valid county FIPS with no current geographic HPSA designation is coded “No”; the measure remains county-level, not a hospital-specific workforce measure. These covariates use 2026 sources against a 2025 outcome, so timing is imperfect. The policy analysis estimates SPA authorization timing, not verified statewide mobile-crisis operations. OP-18 is not an admitted-patient boarding measure. The current measure is being replaced by a new CMS emergency care access and timeliness measure, so the historical series is not a validated crosswalk to its successor.

## Reproduce

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

The archive script retrieves CMS annual hospital archives, adapts early column-name changes, and builds the longitudinal OP-18 panel. The driver script joins current CMS Hospital General Information and USDA 2023 Rural-Urban Continuum Codes to the latest period only. Raw downloads and hospital-level panels are excluded from Git; aggregate outputs are committed. The GitHub Pages workflow rebuilds the dashboard from these committed results before publishing.

## Repository map

- `analysis-plan.md` — analysis decisions and dated decision log.
- `data-quality-log.csv` — source, transformation, suppression, and linkage decisions.
- `policy/mobile-crisis-adoption.csv` — state policy dates, sources, and verification status.
- `python/` — data preparation and analysis scripts.
- `results/` — reports, aggregate tables, model outputs, and chart.
- `site/` — dashboard and rendered analysis pages.

## Data sources

CMS Timely and Effective Care (current and archived), CMS Hospital General Information, the 2026 Q2 CMS Provider of Services file, the current HRSA mental-health HPSA file, USDA Rural-Urban Continuum Codes, and state Medicaid SPA documents are used. CMS limits CAHs to 25 inpatient/swing beds, making CAH status structurally related to bed count ([CMS CAH requirements](https://www.cms.gov/medicare/health-safety-standards/certification-compliance/critical-access-hospitals)). The CMS psychiatric-unit-bed field is a facility-specific unit count; the county HPSA indicator is a geographic designation, not a direct measure of hospital staffing or nearby bed capacity.
