# Historical benchmark: psychiatric ED visit time

CMS maintains quarterly hospital-data snapshots. The archived OP-18 records provide 31 snapshots from 2019-03-04 through 2026-08-13, covering reporting periods beginning in 2017. The latest release with OP-18 data covers **2024-10-01 to 2025-09-30**. The 2026-09-30 archive did not update this dataset, so 2026-08-13 is the newest OP-18 snapshot available in CMS's archive as retrieved on 2026-10-20.

## Selected reporting periods

The table keeps one hospital-level summary for each selected reporting period. Repeated archived snapshots of the same period are de-duplicated by retaining the latest release. These are unweighted medians across hospitals, not patient-weighted national medians.

| Reporting period | Hospitals with both measures | Median hospital gap | IQR |
|---|---:|---:|---:|
| 2018-01-01 to 2018-12-31 | 3,034 | 76 min | 36–136 min |
| 2019-01-01 to 2019-12-31 | 3,055 | 79 min | 38–140 min |
| 2019-10-01 to 2020-09-30 | 1,594 | 96 min | 45–181 min |
| 2021-01-01 to 2021-12-31 | 3,284 | 85 min | 38–156 min |
| 2022-01-01 to 2022-12-31 | 3,084 | 90 min | 41–170 min |
| 2023-01-01 to 2023-12-31 | 3,081 | 87 min | 42–159 min |
| 2024-01-01 to 2024-12-31 | 3,004 | 83 min | 39–150 min |
| 2024-10-01 to 2025-09-30 | 3,023 | 83 min | 39–146 min |

The median hospital gap rose from 76 minutes in calendar 2018 to 90 minutes in 2022, then declined to 83 minutes in the latest 12-month period. The 2019-10 through 2020-09 reporting period, which overlaps the first pandemic year, had a 96-minute median gap. These patterns are descriptive: the reporting windows overlap, release coverage is not uniform, and they do not identify causes or policy effects. The 2020-07 through 2020-12 snapshot is a six-month period and is omitted from the selected annual comparison.

## Small-sample sensitivity

CMS's `Sample` field is the measure-specific count of sampled eligible patients; it is not total ED volume. These illustrative thresholds are sensitivity checks, not validated exclusions or a correction for measurement error.

| Minimum sample in each component | Hospitals retained | Share retained | Median gap | Change vs all hospitals |
|---:|---:|---:|---:|---:|
| 11 | 3,023 | 100.0% | 83.0 min | +0.0 min |
| 20 | 1,381 | 45.7% | 93.0 min | +10.0 min |
| 30 | 543 | 18.0% | 87.0 min | +4.0 min |
| 50 | 192 | 6.4% | 73.5 min | -9.5 min |
| 100 | 69 | 2.3% | 67.0 min | -16.0 min |

At a minimum of 20 cases in both components, the sample falls from 3,023 to 1,381 hospitals and the median gap changes from 83 to 93 minutes. This does not establish which estimate is less biased; it shows why a threshold alone cannot resolve small-sample uncertainty.

## Latest release detail

The August 2026 archive contains 4,658 hospital-period records with OP-18. Both OP-18b and OP-18c were usable at 3,023 hospitals (64.9%); the median gap was 83 minutes (IQR 39–146). The median reported OP-18c `Sample` value was 19 (minimum 11) among hospitals with both scores. The patient-level visit times and dispersion are not released, so sample counts alone do not recover the sampling distribution of each hospital median or of the gap. CMS states that sample sizes can support confidence intervals for reported measures, but the method for the OP-18 median gap must be validated before publishing shrinkage estimates.

The supplied national CMS file reports OP-18c at 257 minutes and OP-18b at 162 minutes for this same latest reporting period, a 95-minute national aggregate difference. That is not directly comparable to the 83-minute median of hospital-level differences.

## Measure limits

OP-18c is median ED arrival-to-departure time for discharged psychiatric/mental-health visits and excludes transfers. OP-18b is the corresponding measure excluding psychiatric/mental-health patients and transfers. Neither measures boarding among patients admitted to the hospital. Results are descriptive, not case-mix adjusted, causal, or an overall quality ranking. Hospitals with unavailable/suppressed scores are missing from the paired gap.

The archived hospital panel and release-level files remain under ignored `data/processed/`. Committed outputs include the national release summary, de-duplicated reporting-period summary, and state-by-release summary. Run `python python/build_historical_panel.py` to re-download the CMS annual archives and rebuild those outputs.

Sources: [CMS hospital archives](https://data.cms.gov/provider-data/archived-data/hospitals), [Timely & Effective Care measure definitions](https://data.cms.gov/provider-data/topics/hospitals/timely-effective-care/), and [CMS Hospital Data Dictionary (July 2026)](https://data.cms.gov/provider-data/sites/default/files/data_dictionaries/hospital/HOSPITAL_Data_Dictionary.pdf).

