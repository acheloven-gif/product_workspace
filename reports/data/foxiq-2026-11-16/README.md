# FoxIQ data, 16.11.2026

Window: 02.11.2026 00:00 MSK through 15.11.2026 23:59:59 MSK.
PostHog timestamps are UTC: 01.11.2026 21:00:00 through 15.11.2026 20:59:59.
Project filter: `foxiq` for buyers, cancels, the survey and `primer_payment`; `foxiq_ff` for the funnel.
No emails. Test people stay in the raw files and are marked `is_test=1`.
This folder is an export only. Outcomes such as оплатил / отказ / отменил were not calculated.

## Buyers

`buyers.csv`. One row per `subscription_started`: 214 events, 214 people.
Columns match the 11.11 file, plus `game_started`, `test_started` and `lesson_completed` for the hour after purchase.
`status` is empty. `source` is `unknown`: `utm_source` is null on every `subscription_started` in this window.
`broken_menu=1` when the purchase is before 02.11.2026 16:07 UTC. That is 4 people, all on 02.11 MSK.
One buyer is excluded: person `0b5b097e-45b1-5638-8368-53767b182c49`, purchase 03.11.2026 17:34 UTC, reason `email matches the FoxIQ test filter`. The property `is_test` on the event is false; the email filter is what marks them.
The Armenia account of 28.10 is not a buyer in this window.

Moscow weeks, same split as `subscription_started` in PostHog:
- 02.11–08.11: 59 people, 1 excluded, 58 kept.
- 09.11–15.11: 155 people, 0 excluded, 155 kept.

## Funnel

`funnel_definition.csv` is the definition. `funnel_weekly.csv` has the two Monday weeks only, because `scripts/foxiq-weekly.py` looks up a week by `week_start_msk`. Daily rows are in `funnel_daily.csv`.
Counts are unique `person_id` per step, not an ordered funnel. The paywall is `screen_id` exactly `paywall` or `Paywall`.
The week of 02.11 matches the 11.11 file: 1670, 998, 522, 511, 130, 57.

## Cancels

`cancel_survey.csv`: `cancellation_survey_completed` with `outcome=cancelled` and `completed=true`.
48 real people have an empty reason. That is what the event stored. Test rows have `is_test=true`; real rows leave `is_test` blank so the weekly script keeps them.

`cancel_events.csv`: raw `subscription_cancelled` and `subscription_expired`.
- 02.11–08.11: 38 cancelled, 20 expired.
- 09.11–15.11: 113 cancelled, 33 expired.
Reasons in the file: `user_initiated` 151, `payment_failed` 53. Six rows are tests, including the Armenia account on 04.11 and the gox-media buyer.

## Primer payments

`primer_payment_events.csv`: 567 raw `primer_payment` events. This is not a Primer export.
The event has no `is_test` property. The column is the email filter plus the Armenia account.
`prepaid=1` only when `card_type` is `PREPAID` (135 events). Other card types in the file are CREDIT, DEBIT and UNKNOWN.
Decline reason is `decline_code` and `decline_type`. Of 324 declined events, 222 have a code and 102 have none. One of those 102 has a `decline_message` and no code; that text is not in the file. `decline_message` was not exported.

## Coverage

`coverage.json`. No day in 02.11–15.11 looks like the 11–13.10 outage. The quietest day is 02.11: 2089 events, 150 people, 4 subscription starts.
