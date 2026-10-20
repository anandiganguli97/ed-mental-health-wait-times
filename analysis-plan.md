# Pre-analysis plan

**Version:** 0.1 scaffold, 2026-10-20  
**Status:** decisions recorded before estimation; update by dated amendment only.

## Population and outcome

The observational unit will be hospital (CCN) × reporting period. Primary outcome is the psychiatric stratum median ED arrival-to-departure time (OP-18c). The within-hospital contrast is OP-18c minus OP-18b, where OP-18b is the non-psychiatric/non-transfer stratum only if the contemporaneous CMS specification confirms that definition. OP-18a (all discharged patients) is secondary. The measure excludes patients who do not meet the measure's discharged-visit denominator; it must not be described as admitted-patient boarding.

## Layer 1: descriptive benchmark

- Preserve CMS-reported periods, measure IDs, footnotes, suppression codes, and source release identifiers.
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

1. Confirm historical measure definitions and comparability before constructing a long panel.
2. Confirm raw CMS schema and stable CCN before joining covariates.
3. Confirm policy implementation dates from primary sources before treatment coding.
4. Confirm outcome availability, number of adopting states, and pre-period support before causal estimation. If support is inadequate, report descriptive policy timing instead of a causal effect.
