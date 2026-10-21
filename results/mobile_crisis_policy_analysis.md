# Medicaid mobile-crisis authorization and the psychiatric ED time gap

## Result

The pooled event-time 0 estimate is +3.1 minutes (state-cluster bootstrap 95% interval -9.2 to +15.7). This is an exploratory estimate of Medicaid SPA authorization, not statewide operational availability. The earliest four-state cohort (AZ, NC, NY, OR) is negative in its supported post windows: event time 0 -16.9 minutes (95% interval -52.9 to +11.4); event time 2 -18.8 minutes (95% interval -72.0 to +14.3). These cohort-specific estimates are imprecise and should not be treated as a confirmed subgroup effect.

The outcome is the hospital-level OP-18c minus OP-18b gap in minutes, a difference between separately reported medians. OP-18 is for discharged ED visits, not admitted-patient boarding.

## Design and support

The estimator uses group-time ATT comparisons for staggered SPA effective-date cohorts, with never-authorized and not-yet-authorized states as controls. Annual, non-overlapping reporting windows ending September 30 are used for 2018 and 2020–2025; the 2019 September window is absent. Repeated snapshots of the same hospital and reporting window are reduced to the latest CMS release. The sample requires a reportable gap and at least 11 sampled patients in each component. Hospitals must be observed in both their cohort baseline and comparison windows.

The policy-overlap reporting window is dropped. Each cohort is compared with its last common fully pre-policy annual window, set to the first full treated reporting year minus two. Cohort-time ATT estimates are hospital-weighted and then aggregated by event time. Percentile intervals resample states, not hospitals. 9 pre-policy cohort-time diagnostics are available. They assess departures from parallel trends but cannot prove the assumption. The event-time −6 estimate is +13.9 minutes (95% interval +0.5 to +26.6), which excludes zero and is a warning against assuming parallel pre-trends.

CMS SPA effective dates indicate authorization under the Medicaid plan. Most state-level service launch dates are not verified. Accordingly, this estimates the effect of policy authorization availability (an intention-to-implement measure), not the effect of mobile crisis teams actually operating or covering the whole state. See the source audit table at policy/mobile-crisis-adoption.csv.

## Dynamic group-time ATT

| Event time (years; 0 = first full treated reporting window) | Period | ATT (minutes) | State-cluster bootstrap 95% interval | Cohort-time cells | Minimum treated states |
|---:|---|---:|---:|---:|---:|
| -7 | pre-period diagnostic | -1.5 | -57.8 to +17.8 | 1 | 5 |
| -6 | pre-period diagnostic | +13.9 | +0.5 to +26.6 | 1 | 12 |
| -5 | pre-period diagnostic | -0.8 | -18.0 to +15.0 | 2 | 4 |
| -4 | pre-period diagnostic | +2.1 | -20.7 to +19.6 | 2 | 5 |
| -3 | pre-period diagnostic | +5.0 | -9.2 to +14.8 | 3 | 4 |
| 0 | post-policy | +3.1 | -9.2 to +15.7 | 3 | 4 |
| 1 | post-policy | -0.3 | -14.0 to +12.1 | 2 | 4 |
| 2 | post-policy | -18.8 | -72.3 to +14.5 | 1 | 4 |

Pre-period estimates are displayed as diagnostics and must be considered when assessing parallel trends. They are not proof that parallel trends holds. There are 15 supported post-policy group-time cells. Full pre- and post-period support appears in mobile_crisis_group_time_att.csv and mobile_crisis_event_study.csv. An approval-date sensitivity analysis is reported in mobile_crisis_event_study_approval_date.csv; approval dates shift treatment timing later than effective dates in some states.


Approval-date timing sensitivity: event time 0: +0.2 minutes (95% interval -20.2 to +14.8; minimum 2 treated states); event time 2: -18.5 minutes (95% interval -29.3 to -9.7; minimum 2 treated states). Event-time 2 has very limited treated-state support, so its interval is not a stable policy-effect estimate. Full pre- and post-period estimates are in `mobile_crisis_event_study_approval_date.csv`.

A control-group sensitivity removes the six HCA Houston facilities (the IDs listed in the HCA annual audit) from all years. Event time 0 is +2.1 minutes (95% state-cluster bootstrap interval -9.7 to +14.6). This checks the influence of that Texas system cluster; it does not establish that the flagged reporting pattern is an error.

## Limits

This is exploratory. SPA adoption can respond to changing crisis needs; actual team deployment and geographic availability are mostly unknown; only a few post-policy windows are available for later cohorts; outcomes are missing or suppressed for some hospitals; the gap has no validated patient-level uncertainty interval; and the earliest policy cohort has few adopting states. The bootstrap intervals do not remove these design limits. A non-significant result should not be described as evidence that mobile crisis has no effect.

## Reproduce

Run python python/build_mobile_crisis_did.py after python python/build_historical_panel.py. Treatment dates come from CMS SPA documents; statewide service launch dates are added only when an official state source verifies them.

