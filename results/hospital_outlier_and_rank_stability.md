# Historical outlier and rank-stability audit

## Rule and findings

The rule flags a positive OP-18c minus OP-18b gap above 1,440 minutes (24 hours). It was applied to the latest CMS snapshot for each selected non-overlapping annual hospital window, 2018 and 2020–2025. The 2019 September window is not in the selected panel. There are **21 hospital-period flags across 12 CCNs**; all 21 flagged rows meet the 11-case minimum in both components. Eleven flags occur at three HCA Houston CCNs: West (450644), Southeast (450097), and Clear Lake (450617). These values are retained in primary analyses and are flagged for review, not presumed reporting errors. The [full flagged rows](hospital_gap_outliers_over_24h.csv) include reporting dates, latest snapshot, component samples, and facility IDs.

The latest-period p99 model caps **31 of 3,023** hospital outcomes at 602.34 minutes. This sensitivity checks influence; it does not recode the primary data. In the mobile-crisis analysis, all six HCA Houston CCNs are removed in a targeted sensitivity because Texas is a never-treated control state.

## HCA Houston by annual window

The table uses the same selected annual panel that feeds the shrinkage, churn, and DiD analyses. It groups by six-digit CCN rather than exact hospital name, includes all available years, and reports the prior-window mean and 2025 value. A dash means no reportable annual gap in that selected window.

| CCN | Names in annual panel | Prior-window mean | 2025 gap | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 450097 | BAYSHORE MEDICAL CENTER / HCA HOUSTON HEALTHCARE SOUTHEAST | 2,915.8 | 384 | 281 | 7,797 | 2,939 | 2,489 | 3,359 | 630 | 384 |
| 450617 | HCA HOUSTON HEALTHCARE CLEAR LAKE | 920.8 | 227 | 276 | 2,525 | 1,165 | 166 | 1,118 | 275 | 227 |
| 450638 | HCA HOUSTON HEALTHCARE NORTHWEST | 243.0 | 678 | 139 | 92 | 89 | 175 | 465 | 498 | 678 |
| 450644 | HCA HOUSTON HEALTHCARE WEST | 3,300.5 | 2,904 | 789 | 6,110 | 4,236 | 3,417 | 2,201 | 3,050 | 2,904 |
| 450775 | HCA HOUSTON HEALTHCARE KINGWOOD / KINGWOOD MEDICAL CENTER | 268.0 | 1,078 | 127 | -26 | 117 | 177 | 819 | 394 | 1,078 |
| 670106 | HCA HOUSTON HEALTHCARE PEARLAND | 304.0 | 620 | 609 | 95 | 130 | 468 | 316 | 206 | 620 |

CCN 450097 is named **Bayshore Medical Center** in the 2018 window and **HCA Houston Healthcare Southeast** later. CCN 450775 also appears as **Kingwood Medical Center** and **HCA Houston Healthcare Kingwood**. The annual data do not show West and Southeast swapping IDs: West remains CCN 450644 and Southeast 450097. Across the selected windows, Southeast’s prior mean by CCN is 2,915.8 minutes, near West’s 2025 value of 2,904; the values arise from distinct CCNs, and 2018’s Bayshore name needs a dated crosswalk. See the [CCN/name audit](hca_houston_ccn_name_audit.csv) and [full annual file](hca_houston_facility_annual_audit.csv).

## Decile overlap benchmark

Top and bottom deciles are defined on the same matched hospitals for psychiatric gap and OP-18b. Decile size is the ceiling of 10% of the sample; ties are broken by CMS facility ID.

| Comparison | Outcome | Hospitals | Top overlap | Bottom overlap |
|---|---|---:|---:|---:|
| 2025 vs prior-years mean | Psychiatric gap | 2,933 | 41.8% | 28.6% |
| 2025 vs prior-years mean | OP-18b median | 2,933 | 74.5% | 70.4% |
| 2024 vs 2025 | Psychiatric gap | 2,566 | 38.5% | 31.5% |
| 2024 vs 2025 | OP-18b median | 2,566 | 80.5% | 75.9% |

Excluding the six HCA Houston facilities leaves the pattern similar: psychiatric-gap overlap is 41.0% top and 28.7% bottom for 2025 versus prior-years mean, and 37.9%/31.2% for 2024 versus 2025. Rank turnover mixes true hospital change and measurement noise; this table is not a quality ranking.

