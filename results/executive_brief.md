# Psychiatric emergency department time: executive brief

## What the measure says

For October 2024 through September 2025, 3,023 hospitals reported both CMS OP-18b and OP-18c results. The median hospital-level difference was **83 minutes** (interquartile range 39–146). This is the difference between two separately reported hospital medians for discharged ED visits. It is not the average extra time experienced by a patient and does not measure admitted-patient boarding. CMS's national aggregate difference for the same period is 95 minutes, a separate statistic.

## What stands out

The median hospital gap was 76 minutes in the selected 2018 reporting period, 90 in 2022, 83 in 2024, and 83 in the latest year ending September 2025. Hospital coverage changes across years and windows overlap, so the pattern describes reported results rather than a causal trend.

In the baseline model of 3,023 hospitals, Critical Access Hospitals had a gap **17.3 minutes smaller** than acute care hospitals (95% CI 7.3–27.2 minutes smaller), after adjustment for ownership, emergency-service status, metro status, and state fixed effects. It was the only baseline contrast with an interval excluding zero. Adding certified bed count, psychiatric-unit beds, and county HPSA reduced the estimate to 12.1 minutes lower; its interval (27.5 minutes lower to 3.3 higher) includes zero. The expanded model explains 5.8% of observed variation, compared with 5.7% for the baseline model. The CAH association is conditional and exploratory: it does not show that CAH status causes shorter waits or that these hospitals deliver better care. The added covariates have important limits: beds and HPSA status are from 2026 sources against a 2025 outcome; HPSA is county-level, not a hospital-specific workforce measure. A valid county FIPS with no current geographic HPSA designation is coded “No.” Psychiatric-unit beds are not a census of nearby psychiatric capacity.

## What leaders can do with this

Treat the national result as a prompt to measure local performance, not as a target for individual patients. A hospital or health system can:

1. Review its own OP-18 reporting alongside patient-level timestamps, disposition, boarding, staffing, and acuity. Separate discharged-visit time from time after an admission decision.
2. Compare psychiatric and non-psychiatric pathways locally, then inspect where the difference arises: medical clearance, consultation, placement search, transport, or discharge planning.
3. Pair any operational change with a defined outcome, a baseline period, and follow-up. Use subgroup checks to see whether changes improve access equitably.

National hospital-level associations are not enough to select an intervention or rank individual facilities. Local process data are needed to identify bottlenecks.

## Mobile-crisis policy analysis

The pooled estimate at event time zero was +3.1 minutes (state-cluster bootstrap 95% interval −9.2 to +15.7), using SPA effective dates as authorization timing. Pre-period estimates are now shown in the event study. The earliest four-state cohort (Arizona, North Carolina, New York, and Oregon) was lower in its supported post windows: −16.9 minutes at event time zero (95% interval −52.9 to +11.4) and −18.8 at event time two (−72.3 to +14.5). Those estimates are imprecise. An approval-date sensitivity shifts timing later and has only two treated states in event time zero and event time two; it does not support a stable effect estimate. Most states' statewide service launch dates are unverified, so this is not an estimate of mobile-crisis teams actually operating.

## Limits and next measurement work

The gap is a difference between reported medians, and CMS does not provide the patient-level distribution needed for a conventional interval around that difference. An exploratory shrinkage model uses repeated annual windows and sample size to improve held-out-year prediction modestly (RMSE reduction 2.7% for 2024, 1.4% for 2025). Its year-to-year residual variation also includes genuine changes in hospitals; it is not a validated sampling-uncertainty model and does not justify public rankings.

Minimum-sample sensitivity also changes which hospitals are included: the median is 83 minutes at threshold 11, 93 at 20, and 67 at 100. That movement reflects selection into different hospital groups as well as any precision differences. Next, improve the time alignment of the bed and HPSA measures, then assess whether stronger hospital-level workforce and nearby-capacity sources add useful explanatory power. The current additions do not materially change the model's limited explanatory power.

CMS is transitioning from the legacy discharged-ED measure to the Emergency Care Access & Timeliness eCQM. The historical series is a baseline, not a validated crosswalk to the new measure. See the [CMS 2026 OPPS final-rule fact sheet](https://www.cms.gov/newsroom/fact-sheets/calendar-year-2026-hospital-outpatient-prospective-payment-system-opps-ambulatory-surgical-center).

## Technical detail

The analysis uses 31 archived CMS releases and 145,833 hospital-snapshot rows. The latest release containing OP-18 was retrieved August 13, 2026. Details and reproducible scripts are in the [historical benchmark](national_historical_benchmark.md), [driver analysis](hospital_driver_analysis.md), [mobile-crisis analysis](mobile_crisis_policy_analysis.md), [analysis plan](../analysis-plan.md), and [state source audit](../policy/mobile-crisis-adoption.csv).
