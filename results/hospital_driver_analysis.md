# Hospital characteristics and psychiatric ED time gap

## Model scope

This is a cross-sectional analysis of the latest common OP-18 period ending 2025-09-30. The analysis includes 3,023 hospitals with reportable OP-18b and OP-18c scores and at least 11 sampled patients in both components. Current CMS Hospital General Information and USDA 2023 RUCC are joined to that latest period only; they are not assigned retrospectively to earlier observations.

The outcome is OP-18c minus OP-18b, in minutes. It is the difference between two separately reported medians, not the median of patient-level paired differences. Predictors are hospital type, ownership, emergency-service status, metro/nonmetro classification, certified bed count, psychiatric-unit beds, and county mental-health geographic HPSA designation. Bed counts come from the CMS Provider of Services Q2 2026 file; HRSA HPSA designations are current at download and county-linked. The model includes state fixed effects and state-clustered CR1 standard errors. Bed counts enter as log(1 + count). Confidence intervals and p-values use a normal approximation. Coefficients are conditional associations, not causal effects or rankings.

## Main finding and expanded-model sensitivity

In the baseline specification, Critical Access Hospitals had an adjusted gap **17.3 minutes lower** than acute care hospitals (95% CI 7.3 to 27.2 minutes lower), conditional on ownership, emergency-service status, metro status, and state fixed effects. It was the only baseline estimate with an interval excluding zero. After adding certified bed count, psychiatric-unit beds, and county mental-health HPSA, the CAH estimate attenuated to -12.3 minutes (95% CI -27.9 to +3.3); this interval includes zero. The expanded model explains 5.8% of observed gap variation, compared with 5.7% in the baseline. Most variation remains unexplained.

Ownership contrasts use **Voluntary non-profit - Private** as the reference. Federal-government, physician-owned, and tribal hospitals are combined into one small “Other” category. Remaining coefficients are exploratory associations, not causal effects.

The expanded-model coefficients are in `hospital_driver_model_coefficients.csv`; the baseline specification is in `hospital_driver_model_base_coefficients.csv`. Model metadata: `hospital_driver_model_metadata.json`.

## Peer groups

Peer groups are defined before looking at outcomes as CMS hospital type × USDA metro/nonmetro category. Groups with fewer than 20 hospitals are marked below the minimum and their group-level distribution is suppressed. Facility-level differences from the peer median are descriptive comparison aids, not adjusted rankings or quality scores. See `peer_group_summary.csv` and `hospital_peer_comparison.csv`.

## Limitations

The CMS Hospital General Information characteristics are current (retrieved 2026-10-20); the POS file describes 2026 Q2; HRSA HPSA designations are current at retrieval; and RUCC is a 2023 county classification. Covariate timing therefore does not exactly match the September 2025 outcome, and hospital conditions may have changed. Psychiatric-unit beds are CMS unit-bed counts, not a census of inpatient psychiatric capacity at nearby facilities. HPSA is a county-level geographic designation, not a hospital-specific workforce measure. There is no causal identification, no adjustment for patient acuity, and no validated uncertainty model for the median gap. Refresh files and audit coverage before reuse.

Sources: [CMS Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u), [CMS Provider of Services](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-quality-improvement-and-evaluation-system), [HRSA mental-health HPSA downloads](https://data.hrsa.gov/data/download?AHRF=&data=AHRF), and [USDA 2023 Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/).
