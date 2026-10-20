# Hospital characteristics and psychiatric ED time gap

## Model scope

This is a cross-sectional analysis of the latest common OP-18 period ending 2025-09-30. The analysis includes 3,023 hospitals with reportable OP-18b and OP-18c scores and at least 11 sampled patients in both components. Current CMS Hospital General Information and USDA 2023 RUCC are joined to that latest period only; they are not assigned retrospectively to earlier observations.

The outcome is OP-18c minus OP-18b, in minutes. It is the difference between two separately reported medians, not the median of patient-level paired differences. Predictors are hospital type, ownership, emergency-service status, and metro/nonmetro classification. The model includes state fixed effects and state-clustered CR1 standard errors. Confidence intervals and p-values use a normal approximation. Coefficients are conditional associations, not causal effects or rankings. Current snapshots do not measure inpatient psychiatric bed availability, hospital size, safety-net status, or mental-health workforce/HPSA at the hospital level; those are not imputed.

## Largest adjusted contrasts

These coefficients compare each category with the first alphabetical reference category for its predictor, holding other listed variables and state fixed effects constant.

- `hospital_ownership[Physician]`: -75.1 minutes (95% CI -146.8 to -3.5); state-clustered, normal-approximation p=0.0397.
- `hospital_ownership[Government - Hospital District or Authority]`: -54.8 minutes (95% CI -114.1 to +4.5); state-clustered, normal-approximation p=0.0699.
- `hospital_ownership[Voluntary non-profit - Church]`: -46.7 minutes (95% CI -103.1 to +9.7); state-clustered, normal-approximation p=0.105.
- `hospital_ownership[Tribal]`: +46.5 minutes (95% CI -9.2 to +102.1); state-clustered, normal-approximation p=0.102.
- `hospital_ownership[Voluntary non-profit - Other]`: -44.5 minutes (95% CI -98.2 to +9.2); state-clustered, normal-approximation p=0.105.
- `hospital_ownership[Voluntary non-profit - Private]`: -38.6 minutes (95% CI -94.2 to +16.9); state-clustered, normal-approximation p=0.173.
- `hospital_ownership[Government - Local]`: -38.6 minutes (95% CI -92.9 to +15.6); state-clustered, normal-approximation p=0.163.
- `hospital_ownership[Government - State]`: -19.7 minutes (95% CI -78.4 to +39.1); state-clustered, normal-approximation p=0.512.

Full coefficient table: `hospital_driver_model_coefficients.csv`. Model metadata: `hospital_driver_model_metadata.json`.

## Peer groups

Peer groups are defined before looking at outcomes as CMS hospital type × USDA metro/nonmetro category. Groups with fewer than 20 hospitals are marked below the minimum and their group-level distribution is suppressed. Facility-level differences from the peer median are descriptive comparison aids, not adjusted rankings or quality scores. See `peer_group_summary.csv` and `hospital_peer_comparison.csv`.

## Limitations

The CMS hospital characteristics are current (retrieved 2026-10-20) and some hospitals may have changed ownership or classification since the reporting period. The county Rural-Urban Continuum Code is a 2023 county classification; USDA cautions that code definitions change across decades. County matching relies on state and normalized county/parish names; unmatched locations remain unknown. There is no causal identification, no adjustment for patient acuity, and no validated uncertainty model for the median gap. CMS files and covariate values should be refreshed before reuse.

Sources: [CMS Hospital General Information](https://data.cms.gov/provider-data/dataset/xubh-q36u) and [USDA 2023 Rural-Urban Continuum Codes](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes/).

