# Medicaid mobile-crisis authorization and the psychiatric ED time gap

## Result

The pooled event-time 0 estimate is +3.1 minutes (state-cluster bootstrap 95% interval -9.3 to +15.8). This is an exploratory estimate of Medicaid SPA authorization, not statewide operational availability.

The outcome is the hospital-level OP-18c minus OP-18b gap in minutes, a difference between separately reported medians. OP-18 is for discharged ED visits, not admitted-patient boarding.

## Design and support

The estimator uses group-time ATT comparisons for staggered SPA effective-date cohorts, with never-authorized and not-yet-authorized states as controls. Annual, non-overlapping reporting windows ending September 30 are used for 2018 and 2020–2025; the 2019 September window is absent. Repeated snapshots of the same hospital and reporting window are reduced to the latest CMS release. The sample requires a reportable gap and at least 11 sampled patients in each component. Hospitals must be observed in both their cohort baseline and comparison windows.

The policy-overlap reporting window is dropped. Each cohort is compared with its last common fully pre-policy annual window, set to the first full treated reporting year minus two. Cohort-time ATT estimates are hospital-weighted and then aggregated by event time. Percentile intervals resample states, not hospitals. 9 pre-policy cohort-time diagnostics are available. They assess departures from parallel trends but cannot prove the assumption.

CMS SPA effective dates indicate authorization under the Medicaid plan. Most state-level service launch dates are not verified. Accordingly, this estimates the effect of policy authorization availability (an intention-to-implement measure), not the effect of mobile crisis teams actually operating or covering the whole state. See the source audit table at policy/mobile-crisis-adoption.csv.

## Dynamic group-time ATT

| Event time (years; 0 = first full treated reporting window) | ATT (minutes) | State-cluster bootstrap 95% interval | Cohort-time cells | Minimum treated states |
|---:|---:|---:|---:|---:|
| 0 | +3.1 | -9.3 to +15.8 | 3 | 4 |
| 1 | -0.3 | -12.8 to +11.5 | 2 | 4 |
| 2 | -18.8 | -72.4 to +15.0 | 1 | 4 |

There are 15 supported group-time cells. Full support appears in mobile_crisis_group_time_att.csv, mobile_crisis_event_study.csv, and mobile_crisis_did_metadata.json.

## Limits

This is exploratory. SPA adoption can respond to changing crisis needs; actual team deployment and geographic availability are mostly unknown; only a few post-policy windows are available for later cohorts; outcomes are missing or suppressed for some hospitals; the gap has no validated patient-level uncertainty interval; and the earliest policy cohort has few adopting states. The bootstrap intervals do not remove these design limits. A non-significant result should not be described as evidence that mobile crisis has no effect.

## Reproduce

Run python python/build_mobile_crisis_did.py after python python/build_historical_panel.py. Treatment dates come from CMS SPA documents; statewide service launch dates are added only when an official state source verifies them.

