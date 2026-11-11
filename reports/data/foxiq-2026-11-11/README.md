# FoxIQ data, 11.11.2026

The report that uses these files is `reports/foxiq-product-journeys-2026-11-11-v4.1.html`. Version 4 (`reports/foxiq-product-journeys-2026-11-11.html`) is the short summary and is left as it was.

Window: 07.10.2026 00:00 MSK through 11.11.2026 14:00 MSK.
People, not events, except where a file has an events column.
The raw Primer file stays on the local machine. It contains emails and card data, so it is not in the repository. Counts are in `primer_summary.json`.

## Money

`primer_summary.json`. A FoxIQ customer is someone whose first payment has funnel path `/test-iq`, `/iq-test-web-v1`, `/start-iq-test` or `/you-may-wish`. Later charges are taken by `customerId`. Tests are the email filter in `playbook/posthog.md` plus `reports/foxiq-test-users-list-2026-10-30.csv`: 18 customers removed. No separate mailbox list for Danya, Maxim and Natasha on 09–11.11 was supplied; those names are already represented in that list (plus-addresses, gox-media, the Natasha mailbox).

Real trial buyers: 226. The file also has 227 settled $1 events before the test filter. Declined $1 events on the IQ paths: 300 before the test filter, 276 after it. The figure 307 is not a Primer count. It is the PostHog `primer_payment` declined-$1 event count in `primer_payments.csv` (210 people, 307 events), which is a different source and a different filter. Version 4.1 uses 300 / 276 from the Primer file. Renewals match the check: $29.99 is 21 settled and 68 declined, $20.99 is 53 declined, $15 is 7 settled and 37 declined, $49.99 is 1 settled and 2 declined.

Of 118 buyers whose trial had ended by 11.11 (purchase at least 7 days earlier): 29 renewed, 62 were declined, 27 had no renewal attempt. Prepaid cards among those 118: 22, and 0 renewed.

## Buyers and the early gap

`buyers.csv` is the PostHog `subscription_started` list: 207 kept people. `exclusions.csv` is the two PostHog people removed earlier (gox-media on 03.11, Armenia account on 28.10).

Primer 226 and PostHog 207 are not the same set. Sixteen Primer buyers paid before 12.10. Five of them have `subscription_started` somewhere in the window. Six have app events and no subscription. Five have no FoxIQ events. `early_buyers.csv` has these counts and no emails.

## Recordings

`recordings_summary.csv`. The recordings API and `raw_session_replay_events` do have FoxIQ recordings. The earlier empty result was the wrong table filter.

530 recordings, 418 distinct ids, for the whole window. Before 12.10: 41 recordings, 30 ids. Fifteen of the sixteen early Primer buyers have a recording; one has neither a recording nor events, so that path is unknown. Rage taps (3 clicks in one place within 1.5 seconds) were not recomputed. Mean active time on later buyer recordings is 195 seconds. The median, recomputed for version 4.1, is 41 seconds across 199 buyers with a recording after 12.10 (query: sum of active_milliseconds per distinct_id, then quantile 0.5). On the 64 buyers through 03.11 the median was 42 seconds. Rage taps were not recomputed: the table has click counts, not a place and a 1.5-second gap, and $rageclick is not in the project.

## Funnel

`funnel_definition.csv` is the only definition used in version 4. `funnel_weekly.csv` and `funnel_totals.csv` use it. `funnel_daily.csv` and `funnel_paid_by_source.csv` are the earlier unfiltered extract and are not the comparison.

The first recount (47.1% / 9.1% / 4.3% for Azora) counted every screen whose id contains `paywall`, including failure screens, and did not apply the test filter. With the exact paywall screen and the shared filter, the version 3.2 window reproduces the printed rates.

Whole window: FoxIQ 37.9% to the paywall, 9.5% pay from the paywall, 3.6% through. Azora 47.7%, 8.7%, 4.1%.

The rise from the first screen to the first question follows the traffic mix. In the week of 12.10 Google was 3 724 of 4 156 first screens and almost nobody from Google paid. By the week of 09.11 Google is gone and Meta is 1 208 of 1 373. Inside Meta only, the paywall rate still rises from 39% to 56%. No IQ-quiz or copy change for that step was found in the repository or the journal. That part is unresolved.

## Other files

`unpaid_entry.csv`, `cancel_funnel_daily.csv`, `cancel_survey.csv`, `buyer_behavior.csv` and `coverage.json` are the earlier PostHog extract. Behavior there is any event in the window, not the first hour.
