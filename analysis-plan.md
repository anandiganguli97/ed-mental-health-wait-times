# Pre-analysis plan

**Version:** 0.1 scaffold, 2026-10-20  
**Status:** decisions recorded before estimation; update by dated amendment only.

## Dated amendment — 2026-10-20, after first driver-model fit

CMS Hospital General Information and USDA 2023 Rural-Urban Continuum Codes are used for an exploratory latest-period cross-section only, not projected backward to historical releases. The model outcome is the OP-18c minus OP-18b difference in separately reported hospital medians. It includes hospital type, ownership, emergency-service status, metro/nonmetro classification, state fixed effects, and state-clustered CR1 standard errors. Report normal-approximation intervals and p-values as approximate. Peer groups are hospital type × metro/nonmetro; publish group distributions only for cells with at least 20 hospitals. This post-estimation amendment documents the implemented model and does not represent a pre-registered driver specification. We do not call associations causal or report hospital ranks. Bed count, safety-net status, psychiatric-bed supply, and mental-health workforce/HPSA are omitted because valid linked measures were not assembled.

The mobile-crisis model was estimated after treatment-date audit, as an explicitly exploratory amendment. CMS SPA effective dates are used as authorization timing because statewide operational dates were not verified for most states; the estimand is therefore intention-to-implement, not actual service availability. The model uses non-overlapping annual OP-18 windows ending 2018 and 2020–2025, excludes transition windows, requires at least 11 sampled patients for each measure, and compares within-hospital gap changes against never/not-yet-authorized controls. Cohort-time ATT estimates are aggregated by event time, with state-cluster percentile bootstrap intervals. Event time zero pools three cohort-time cells, including a four-state early cohort; only three post-policy event times are supported and later cohorts have short follow-up. Pre-policy diagnostics are not proof of parallel trends. Results must be described as exploratory and not as evidence of no effect when intervals include zero.

## Dated amendment — 2026-10-20

CMS hospital archive snapshots have now been assembled from March 2019 through August 2026. They cover reporting periods beginning in 2017 and provide repeated snapshots with rolling and annual reporting windows. We retain the release date and the measure's own start/end dates separately. For descriptive year-to-year summaries, select comparable 12-month periods and label calendar-year windows; overlapping windows are not independent outcomes. The reported sample field is retained as a measure-specific sampled-patient count, not total ED volume. Threshold sensitivity at 11, 20, 30, 50, and 100 patients is reported descriptively; no threshold is treated as an uncertainty correction. Sample counts without patient-level spread do not recover the sampling distribution of a median difference. The one-period limitation is removed for trend description; causal policy and driver models remain gated on comparability, treatment dates, and covariate availability.

## Population and outcome

The observational unit will be hospital (CCN) × reporting period. Primary outcome is the psychiatric stratum median ED arrival-to-departure time (OP-18c). The within-hospital contrast is OP-18c minus OP-18b. CMS describes OP-18b as excluding psychiatric/mental health patients and transfers, so it is a non-psychiatric/non-transfer comparator, not every other ED visit. OP-18a (all patients, including psychiatric and transfer patients) and OP-18d (transfer patients) are secondary. These are discharged-visit measures; they must not be described as admitted-patient boarding.

## Layer 1: descriptive benchmark

- Preserve CMS-reported periods, measure IDs, footnotes, suppression codes, source release identifiers, and archive snapshot dates. CMS describes the public `Sample` field for eligible patients and sampling rules; treat it as a measure-specific case count, not total ED volume. Preserve the field, but validate a confidence-interval procedure for the median before using it for uncertainty estimates.
- Compare raw hospital gaps to an empirical-Bayes/shrinkage estimate with interval. If CMS does not provide denominators or standard errors, do not invent precision from the median; estimate reliability only where defensible auxiliary counts/variance inputs are available. Otherwise show stratified raw distributions, suppress unstable ranks, and label the shrinkage model's assumptions.
- Show sample-size sensitivity only when a valid denominator is available. Provide raw ordering next to uncertainty-aware estimates and rank movement.
- No “best/worst hospital” claim; rankings are descriptive and not causal or risk-adjusted quality ratings.

## Layer 2: associations and peers

Candidate predictors: ownership, hospital type/size, emergency services, rurality, safety-net proxy, nearby psychiatric bed supply, county mental-health HPSA/workforce, state Medicaid expansion, and period. Use hospital and state structure appropriate to the final panel; report adjusted associations, uncertainty, missingness, and collinearity. Define peer groups using pre-specified observable characteristics and minimum cell sizes, not outcome values.

## Layer 3: policy evaluation

Treatment is state adoption of the ARPA Section 9813 Medicaid mobile crisis option. Build adoption dates from state primary sources (approved SPA/waiver and implementation date); planned dates are not treatment dates. Because adoption is staggered, use a modern group-time ATT estimator (Callaway–Sant'Anna) and event-study aggregation with never-treated/not-yet-treated comparisons as supported by the data. Add OP-18b as a within-hospital comparison in a stacked/long specification, with inference clustered at state level. Establish pre-trends and overlap before interpreting effects. Do not use conventional two-way fixed effects as the sole causal estimate.

## Sensitivity and falsification

Pre-specified: alternative confirmed policy dates; exclude transition period; balanced-panel subset; placebo outcomes/strata not plausibly affected; alternative comparison (OP-18b); leave-one-state-out; and missing/suppressed-data bounds. If valid volume/precision is unavailable, omit sample-threshold sensitivity and state why.

## Decision gates

1. Confirm historical measure definitions and comparability before interpreting the long panel.
2. Confirm raw CMS schema and stable CCN before joining covariates.
3. Confirm policy implementation dates from primary sources before treatment coding.
4. Confirm outcome availability, number of adopting states, and pre-period support before causal estimation. If support is inadequate, report descriptive policy timing instead of a causal effect.

