"""Промежуточный замер T1/T2/T3 FoxIQ: выгрузка из PostHog в raw/ (raw/ не коммитится)."""
import json, os
from hq import q
os.makedirs("raw", exist_ok=True)
E = "lower(coalesce(toString(person.properties.email),''))"
S = "'2026-11-10'"
sets = {
 "buyers": f"select person_id, {E} email, timestamp, properties.is_test, properties.environment, properties.trial, properties.price from events where properties.project='foxiq' and event='subscription_started' and timestamp > {S} order by timestamp limit 100000",
 "subs": f"select person_id, {E} email, event, timestamp, properties.reason from events where properties.project='foxiq' and event in ('subscription_cancelled','subscription_expired','subscription_renewed','subscription_cancel_click','subscription_cancel_confirm','purchase_refunded','primer_refund') and timestamp > {S} order by timestamp limit 100000",
 "activity": f"select {E} email, person_id, event, timestamp, toString(properties.t1_variant), toString(properties.t3_variant), toString(properties.iq_score), properties.is_test, properties.environment from events where properties.project='foxiq' and properties.$lib='web' and timestamp > {S} and event in ('game_started','test_started','lesson_started','lesson_completed','iq_result_shown','brain_profile_shown','brain_score_shown','certificate_click','certificate_name_submitted','certificate_downloaded','first_game_skip_click','day1_done_shown','app_opened','login') order by timestamp limit 300000",
 "cancel_flow": f"select person_id, {E} email, timestamp, properties.funnel, properties.outcome, properties.offer, properties.offer_accepted, properties.reason, properties.is_test from events where properties.project='foxiq' and event='cancellation_survey_completed' and timestamp > '2026-11-09' order by timestamp limit 100000",
 "cancel_screens": f"select person_id, {E} email, timestamp, properties.$current_url, properties.project from events where event='funnel_screen_open' and properties.$current_url like '%cancellation-flow%' and timestamp > '2026-11-09' order by timestamp limit 100000",
}
for k, s in sets.items():
    c, r = q(s); json.dump({"columns": c, "rows": r}, open(f"raw/{k}.json", "w")); print(k, len(r))
