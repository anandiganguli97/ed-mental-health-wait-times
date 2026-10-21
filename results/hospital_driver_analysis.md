# Hospital characteristics and psychiatric ED time gap

## Model scope

This is a cross-sectional analysis of the latest common OP-18 period ending 2025-09-30. The analysis includes 3,023 hospitals with reportable OP-18b and OP-18c scores and at least 11 sampled patients in both components. Current CMS Hospital General Information and USDA 2023 RUCC are joined to that latest period only; they are not assigned retrospectively to earlier observations.

The outcome is OP-18c minus OP-18b, in minutes. It is the difference between two separately reported medians, not the median of patient-level paired differences. Predictors are hospital type, ownership, emergency-service status, metro/nonmetro classification, log(1 + certified beds), a binary indicator for any psychiatric-unit bed, and county mental-health geographic HPSA designation. Bed counts come from the CMS Provider of Services Q2 2026 file; HRSA HPSA designations are current at download and county-linked. The model includes state fixed effects and state-clustered CR1 standard errors. Certified beds enter as log(1 + count); psychiatric-unit beds enter as a yes/no indicator (any reported bed versus none). Confidence intervals and p-values use a normal approximation. Coefficients are conditional associations, not causal effects or rankings.

## Main finding and expanded-model sensitivity

Values above 1,440 minutes are flagged for review. The primary OLS retains all observations; a separate sensitivity caps the outcome at its 99th percentile (602.34 minutes), affecting 31 of 3,023 latest-period outcomes. The full annual flags and latest-period rows are in `hospital_gap_outliers_over_24h.csv` and `hospital_gap_outliers_latest_over_24h.csv`; the winsorized coefficients are in `hospital_driver_model_winsorized_coefficients.csv`. The capped outcome has R² 10.7% and residual SD 105 minutes, versus 5.8% and 172 for the primary outcome. Because capping changes the outcome, this comparison is an influence diagnostic.

In the baseline specification, Critical Access Hospitals had an adjusted gap **17.3 minutes lower** than acute care hospitals (95% CI 7.3 to 27.2 minutes lower), conditional on ownership, emergency-service status, metro status, and state fixed effects. It was the only baseline estimate with an interval excluding zero. After adding bed count, psychiatric-unit presence, and county mental-health HPSA, the CAH estimate attenuated to -13.0 minutes (95% CI -28.7 to +2.7). CAHs are limited to 25 inpatient/swing beds by CMS rules, so the category and bed-count terms overlap structurally; the attenuation is consistent with bed-size adjustment absorbing part of the CAH contrast, rather than evidence that the association is unstable. [CMS describes the 25-bed limit](https://www.cms.gov/medicare/health-safety-standards/certification-compliance/critical-access-hospitals). The expanded model explains 5.8% of observed gap variation, compared with 5.7% in the baseline. Most variation remains unexplained.

The psych-unit estimate is similar under the p99 cap (-8.8 minutes, 95% CI -16.7 to -0.9). Bed size and nonmetro status are positive only in the capped model (+7.5 per log unit, 95% CI +1.6 to +13.4; nonmetro +12.5, CI +1.5 to +23.5). The proprietary coefficient moves from +32.4 to +12.3 minutes under the cap.

A one-unit increase in log(1 + certified beds) is associated with +4.5 minutes (95% CI -2.2 to +11.2). Hospitals reporting any psychiatric-unit bed have an estimated -10.5-minute difference versus none (95% CI -20.1 to -0.8). Both estimates are imprecise.

Ownership contrasts use **Voluntary non-profit - Private** as the reference. Federal-government, physician-owned, and tribal hospitals are combined into one small “Other” category. Remaining coefficients are exploratory associations, not causal effects.

The expanded-model coefficients are in `hospital_driver_model_coefficients.csv`; the robust sensitivity is in `hospital_driver_model_winsorized_coefficients.csv`; the baseline specification is in `hospital_driver_model_base_coefficients.csv`. Model metadata: `hospital_driver_model_metadata.json`.

## Peer groups

Peer groups are defined before looking at outcomes as CMS hospital type × USDA metro/nonmetro category. Groups with fewer than 20 hospitals are marked below the minimum and their group-level distribution is suppressed. Facility-level differences from the peer median are descriptive comparison aids, not adjusted rankings or quality scores. See `peer_group_summary.csv` and `hospital_peer_comparison.csv`.

## Limitations

The CMS Hospital General Information characteristics are current (retrieved 2026-10-20); the POS file describes 2026 Q2; HRSA HPSA designations are current at retrieval; and RUCC is a 2023 county classification. Covariate timing therefore does not exactly match the September 2025 outcome, and hospital conditions may have changed. Psychiatric-unit presence is based on CMS POS reported unit-bed counts, not a census of inpatient psychiatric capacity at nearby facilities. HPSA is a county-level geographic designation, not a hospital-specific workforce measure; a valid county FIPS with no currently designated geographic or high-needs geographic record is coded “No,” and the full indicator coverage is 100.0%. OP-18c includes only discharged psychiatric visits, so hospitals with psychiatric units may admit their sickest patients and leave a lower-acuity discharged group in the measure. CAHs may transfer psychiatric patients, and transferred visits are excluded too. The observed differences can therefore reflect who remains in the measured group as well as throughput; these data cannot separate those mechanisms. There is no causal identification, no adjustment for patient acuity, and no validated uncertainty model for the median gap. Refresh files and audit coverage before reuse.

Sources: [CMS Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u), [CMS Provider of Services](https://data.cms.gov/provider-characteristics/hospitals-and-other-facilities/provider-of-services-file-quality-improvement-and-evaluation-system), [HRSA mental-health HPSA downloads](https://data.hrsa.gov/data/download?AHRF=&data=AHRF), and [USDA 2023 Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/).

