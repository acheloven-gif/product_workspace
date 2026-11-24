import json
from hq import q
E="lower(coalesce(toString(person.properties.email),''))"
sets={
"buyers":f"select person_id, {E} email, timestamp, properties.$os, properties.$device_type, properties.$geoip_country_code, properties.platform, properties.is_test, properties.environment from events where properties.project='foxiq' and event='subscription_started' and timestamp > '2026-10-01' order by timestamp limit 100000",
"funnel":f"select {E} email, timestamp, properties.utm_source, properties.utm_campaign, properties.$geoip_country_code from events where properties.project='foxiq_ff' and event='funnel_purchase_success' and timestamp > '2026-10-01' order by timestamp limit 100000",
"cancels":f"select person_id, {E} email, event, timestamp, properties.reason from events where properties.project='foxiq' and event in ('subscription_cancelled','subscription_expired','subscription_renewed','subscription_cancel_click','subscription_cancel_confirm') and timestamp > '2026-10-01' order by timestamp limit 100000",
"activity":f"select {E} email, event, timestamp, properties.$pathname from events where properties.project='foxiq' and properties.$lib='web' and timestamp > '2026-10-01' and {E} != '' and event in ('game_started','test_started','lesson_completed','$pageview','screen_view','app_opened','certificate_click','certificate_name_submitted','certificate_downloaded','certificate_shared','iq_result_shown') order by timestamp limit 300000",
}
for k,s in sets.items():
    c,r=q(s); json.dump({"columns":c,"rows":r},open(f"raw/{k}.json","w")); print(k,len(r))
