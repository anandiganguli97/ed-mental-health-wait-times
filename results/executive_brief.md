# Psychiatric emergency department time: a national benchmark

For October 2024–September 2025, the median hospital-level difference between psychiatric and non-psychiatric, non-transfer discharged ED visits was **83 minutes** (IQR 39–146) across 3,023 hospitals. This is a subtraction of two separately reported hospital medians. It is not an individual patient’s extra wait or an admitted-patient boarding measure.

## What stands out

**The psychiatric gap changes rank from year to year.** Among the same 2,566 hospitals, 38.5% stayed in the top decile and 31.5% in the bottom decile from 2024 to 2025. OP-18b was steadier in those same hospitals: 80.5% and 75.9% stayed in their respective deciles. Against each hospital’s mean across earlier annual windows, psychiatric-gap overlap was 41.8% top and 28.6% bottom, compared with 74.5% and 70.4% for OP-18b. The difference is descriptive. Turnover combines real changes with noise; sample sizes 11–49 show broadly similar residual variation, which falls mainly above 50.

**The expanded model finds a psych-unit association, with a composition caveat.** Hospitals reporting any psychiatric-unit bed had a 10.5-minute smaller reported gap (95% CI 20.1 to 0.8 minutes smaller). The p99-capped sensitivity gives a similar estimate: 8.8 minutes smaller (95% CI 16.7 to 0.9 minutes smaller). OP-18c counts psychiatric visits discharged from the ED and excludes transfers. Hospitals with psych units may admit their sickest patients, leaving a different acuity mix in the discharged group. CAHs may transfer patients who are excluded too. The observed difference can reflect who is counted as much as how quickly care happens; the public data cannot distinguish these explanations.

**Extreme values change some driver estimates.** The primary model retains all observations. A sensitivity caps 31 of 3,023 latest-period gaps at the 99th percentile (602.34 minutes). The psych-unit association remains similar. Bed size (+7.5 minutes per log unit) and nonmetro status (+12.5 minutes) are positive in the capped model, while their primary-model intervals include zero. The proprietary estimate falls from +32.4 to +12.3 minutes. Since the outcome changes under capping, the R² shift from 5.8% to 10.7% and residual SD shift from 172 to 105 minutes are influence diagnostics, not directly comparable fit scores.

The CAH estimate changes from −17.3 minutes in the baseline model to −13.0 (95% CI −28.7 to +2.7) in the expanded model. CMS limits CAHs to 25 inpatient/swing beds, so CAH status overlaps structurally with size ([CMS CAH requirements](https://www.cms.gov/medicare/health-safety-standards/certification-compliance/critical-access-hospitals)). The association is exploratory, not causal.

## Reviewing the extreme values

Applying the 24-hour rule to the selected annual panel flags **21 hospital-period values across 12 facilities**; all meet the 11-case threshold. Eleven are from three HCA Houston facilities. The West and Southeast CCNs are distinct: 450644 and 450097. The Southeast CCN appears as Bayshore Medical Center in 2018 and under its HCA name in later periods, so the broader CCN crosswalk remains open. For the six Houston facilities, the annual file gives the CCN, name, component medians, gap, and sample. A second analysis removes all six from the Texas never-treated control in the mobile-crisis model; the event-time 0 estimate changes from +3.1 to +2.1 minutes, with both intervals including zero. See the [annual outlier and rank audit](historical_outlier_and_rank_stability.md).

## What leaders can do with this

Use the 83-minute national median to prompt local measurement, not as a target or hospital rating. Review OP-18 results alongside patient-level timestamps, disposition, acuity, boarding, staffing, and transfer decisions. Separate discharged-visit time from time after an admission decision, and define a baseline before evaluating an operational change.

## Mobile-crisis authorization

The pooled event-time 0 estimate was +3.1 minutes (95% state-cluster bootstrap interval −9.2 to +15.7), based on Medicaid SPA effective dates. The event-time −6 pre-period estimate was +13.9 minutes (interval 0.5 to 26.6), which excludes zero and warns against assuming parallel pre-trends. Statewide service launch dates are unverified for most states, so the model estimates authorization timing rather than teams actually operating. The result is exploratory, not evidence of no effect.

## Data and limitations

The analysis uses 31 archived CMS releases and 145,833 hospital-snapshot rows. Annual panels retain the latest snapshot for each hospital-window and exclude transition windows. An 11-case threshold is applied to both OP-18 components. Shrinkage modestly improves held-out prediction of multi-year averages (RMSE reduction 2.7% in 2024 and 1.4% in 2025); dropping the six HCA Houston facilities leaves similarly small reductions (3.4% and 1.6%). The model does not produce validated uncertainty intervals or facility rankings. Annual residuals mix real changes and measurement noise. Current bed and HPSA data do not align perfectly with the 2025 outcome; HPSA is county-level, not a hospital workforce measure.

See the [interactive dashboard](https://anandiganguli97.github.io/ed-mental-health-wait-times/site/dashboard.html), [driver analysis](hospital_driver_analysis.md), [historical outlier and rank audit](hospital_outlier_and_rank_stability.md), [mobile-crisis analysis](mobile_crisis_policy_analysis.md), and [analysis plan](../analysis-plan.md).

