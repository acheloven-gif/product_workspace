# FoxIQ data extract, 11.11.2026

Window: 07.10.2026 00:00 MSK through 11.11.2026 14:00 MSK.
UTC bounds used in queries: 2026-10-06 21:00:00 to 2026-11-11 11:00:00.
Counts are people (`person_id`), not events, unless a file has an `events` column.
Projects: `foxiq` for the app and server events, `foxiq_ff` for the purchase funnel, `azora_ff` for the Azora funnel.
Emails are not stored. Test accounts are flagged and removed by the filter in `playbook/posthog.md`.

## buyers.csv

Kept trial buyers from `subscription_started` in `foxiq`.

- `person_id` — PostHog person.
- `purchased_at_utc`, `purchased_at_msk` — first `subscription_started` in the window.
- `device` — `platform` on that event (`ios` or `web`). Browser and app are not on this server event.
- `country` — `$geoip_country_code` on that event. Empty when PostHog did not send it.
- `source` — `unknown` on every row. `utm_source` on `subscription_started` is empty. Source of funnel payments is in `funnel_paid_by_source.csv` and is not the same set of people.
- `status` — `оплатил` if `subscription_renewed` exists; `отменил` if `subscription_cancelled` is more than 120 seconds before `subscription_expired`, or there is no expiry; `отказ` if cancel and `payment_failed` expiry arrive together; `триал_не_закрыт` if neither renewal, cancel nor expiry has arrived.
- `is_test` — `0` for kept rows. The property `is_test` was not used: in FoxIQ it is not a reliable flag.
- `broken_menu` — `1` when the purchase is inside 27.10 08:12 UTC through 02.11 16:07 UTC. These 28 people stay in the file.
- `exclusion_reason` — empty here. Excluded people are in `exclusions.csv`.

207 kept people: 28 оплатил, 30 отказ, 62 отменил, 87 триал не закрыт. 28 of them are in the broken-menu week.

## exclusions.csv

Two people removed from `buyers.csv`.

- `0b5b097e-45b1-5638-8368-53767b182c49` — email matches the gox-media test filter. Purchase 03.11 20:34 MSK.
- `9a2bfd0d-b22f-53e5-91e0-9c2bab06ef35` — own Armenia account, 28.10, cancelled about 9 minutes later.

No other address matched the test filter on 10–11.11. If Danya, Maxim or Natasha used a normal mailbox, that person is still inside the 207.

## funnel_daily.csv, funnel_weekly.csv, funnel_totals.csv

People in `foxiq_ff` and `azora_ff`.

- `first_screen` — `funnel_start`.
- `first_question` — `funnel_screen_open` with `screen_index = 1`.
- `paywall` — `funnel_screen_open` whose `screen_id` contains `paywall`.
- `opened_payment` — `funnel_checkout_open`.
- `started_payment` — `funnel_purchase_start`.
- `paid` — `funnel_purchase_success`.

Daily and weekly numbers must not be added: a person is counted once per day or week, and again in another period. `funnel_totals.csv` has the unique people. `full_period` is the whole window. `v32_window` is 17.10 00:00 through 02.11 24:00 MSK. `after_v32` is the rest of the window. A person can appear in both slices.

FoxIQ funnel events start on 16.10. There is no funnel for 07–15.10.
The funnel files are not filtered by the test-email rule.

Whole window, FoxIQ: 12 116 first screen, 5 205 first question, 1 998 paywall, 1 957 opened payment, 478 started payment, 191 paid.
Paywall / first question 38.4%. Paid / paywall 9.6%. Paid / first question 3.7%.
Azora, same window: 74 075, 32 619, 15 711, 14 862, 3 108, 1 479. Rates 48.2%, 9.4%, 4.5%.

## funnel_paid_by_source.csv

`funnel_purchase_success` only. Meta 165, Google 2, other or empty 24. Total 191, the same as the unfiltered paid count.

## buyer_behavior.csv

Kept buyers, any product event in the window, not the first hour. The first hour was not calculated.

- `played_game` — `game_started`.
- `started_test` — `test_started`.
- `completed_lesson` — `lesson_completed`. There is no separate lesson-start event in this extract.
- `downloaded_certificate` — `certificate_downloaded`.
- `opened_page` — `$pageview`. This is not a confirmed home screen.
- `opened_settings` — `settings_open`. This is the closest profile event.
- `active_on_2_plus_days` — product events on two or more Moscow dates. Billing and email events are not counted.
- `clicked_cancel` — `subscription_cancel_click`.

`broken_menu` is the 28 purchases inside the broken-menu window. `other` is the other 179.

## unpaid_entry.csv

People with `funnel_screen_open` on `cta_skip_paywall` or `failed_payment_message`.
315 people saw one of those screens. 47 of the same `person_id` later have `subscription_started`. 268 do not.
264 of the non-payers are visible in project `foxiq`: 50 opened the app, 19 started a game, 11 started a test, 7 completed a lesson, 0 downloaded a certificate, 44 saw `paywall_shown`.
The app and the funnel often use different person ids. This file does not stitch by email, so the app counts are a lower bound.

## cancel_funnel_daily.csv, cancel_survey.csv

From 09.11 07:45 UTC through 11.11 14:00 MSK.
Screens found: `discount`, `cancel-done`, `cancel-error`, `discount-done`. No screen named as the first “are you sure” step. Daily `discount` people are the best available entry count: 18, 11 and 11. Unique people on `discount` for the whole slice: 39.
`subscription_cancel_click` in the app, same days: 14, 8 and 10 people. It is not the same set.
`cancel_survey.csv` is `cancellation_survey_completed` with `outcome`, `reason`, `completed` and `is_test` as stored. `is_test` is true on part of these rows. Rows were not dropped. People are not unique across rows.

## primer_payments.csv

`primer_payment` in `foxiq` for the whole window. 726 events. `billing_reason` is empty on every row, so the decline reason is not in PostHog. No Primer export was attached. Do not treat these amounts as the money total.

## coverage.json

Daily FoxIQ events, people and buyers for 07–14.10, plus the recording and Primer gaps.

07–09.10 have events and no `subscription_started`. The first four kept buyers are on 10.10. 11–12.10 are almost empty (23 and 9 events). One more buyer appears on 13.10. Funnel tracking starts on 16.10.
`session_replay_events` has 0 rows on 13.10 MSK and 0 rows whose URL contains `foxiq` in the whole window. `$snapshot` is not an event in this project. Paths for 07–11.10 cannot be restored from recordings in this extract.

## Compared with report 3.2

Report: 65 buyers from 12.10 through 03.11, broken-menu week excluded. This extract, same exclusion rules, purchases from 12.10 through 03.11 12:00 MSK outside that week: 59. Four more kept buyers are on 10.10, before the report’s start. The sets were not forced to match. Likely causes: the report also used Primer and merged two persons per buyer; this file is one `subscription_started` person.

Report funnel, 17.10–02.11: FoxIQ paid / first question 2.0% and paid / paywall about 7%. Recount of that window: 65 paid, 3 239 first question, 940 paywall, so 2.0% and 6.9%. Azora in the same recount is 47.1%, 9.1% and 4.3%, not the printed 46%, 7.8% and 3.6%. The Azora definition or window in the report is not fully reproduced.

Report money runs through 06.11 from Primer. This folder has PostHog `primer_payment` only, through 11.11 14:00 MSK, with no decline reason and no Primer check.
