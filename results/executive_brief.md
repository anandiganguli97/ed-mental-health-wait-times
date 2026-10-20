# Psychiatric emergency department time: executive brief

## What the data show

In the latest available CMS hospital reporting period, October 1, 2024 through September 30, 2025, 3,023 hospitals reported both psychiatric and comparison results. The median hospital-level difference was **83 minutes** (interquartile range 39–146): at the typical hospital, the reported median time for discharged psychiatric/mental-health visits was 83 minutes longer than the separately reported median for non-psychiatric, non-transfer visits.

This is a difference between two hospital-level medians. It is not the average extra time experienced by an individual patient. It also does not measure boarding after a patient is admitted. The CMS national aggregate difference for the same period is 95 minutes, a distinct statistic that should not be substituted for the median across hospitals.

## How the pattern changed

Across selected calendar-year periods, the median hospital gap was 76 minutes in 2018, 90 minutes in 2022, and 83 minutes in 2024. The latest year-long period through September 2025 was also 83 minutes. A pandemic-overlap period was 96 minutes. These are descriptive comparisons; reporting windows and hospital coverage vary, and the pattern does not identify why the gap changed.

## Hospital and community comparisons

An exploratory latest-period model adjusted for hospital type, ownership, emergency-service status, metro status, and state. The model explained about 5.7% of the observed variation in hospital gaps. Most category estimates were imprecise; the physician-owned category had an adjusted estimate 75 minutes below the reference ownership category, with a wide 95% interval (−147 to −4 minutes) and a normal-approximation p-value near 0.04. This small-category association is not evidence that ownership causes shorter waits. Peer comparisons are descriptive and should not be read as hospital quality ratings.

## Medicaid mobile-crisis policy analysis

The exploratory event-time-zero estimate was **+3.1 minutes** (state-cluster bootstrap 95% interval −9.3 to +15.8). Treatment timing is the effective date of a Medicaid state plan amendment (SPA), not a verified date when mobile-crisis teams were operating statewide. The interval includes zero, but the design has few adopting states in early cohorts and only three supported post-policy event times. The result should not be interpreted as evidence that mobile crisis had no effect, or as an estimate of the effect of operational team coverage.

## What this can support

The data support monitoring differences between psychiatric and comparison discharged-visit times and identifying where follow-up measurement would be useful. They do not support an unadjusted “best/worst hospital” league table, causal claims about hospital characteristics, or a causal claim about actual mobile-crisis service availability.

CMS has finalized a transition away from the legacy discharged-ED time measure beginning with the 2028 reporting period; the new Emergency Care Access & Timeliness eCQM is voluntary in 2027 and mandatory in 2028. This historical series is a baseline and is not a validated crosswalk to the new measure. See the [CMS 2026 OPPS final-rule fact sheet](https://www.cms.gov/newsroom/fact-sheets/calendar-year-2026-hospital-outpatient-prospective-payment-system-opps-ambulatory-surgical-center).

## Methods and source detail

The project assembled 31 archived CMS releases with 145,833 hospital-snapshot rows. The latest release containing OP-18 was retrieved August 13, 2026. The full details, data-quality decisions, and reproducible scripts are in the [historical benchmark](national_historical_benchmark.md), [driver analysis](hospital_driver_analysis.md), [mobile-crisis analysis](mobile_crisis_policy_analysis.md), [analysis plan](../analysis-plan.md), and [source audit table](../policy/mobile-crisis-adoption.csv).

