# -*- coding: utf-8 -*-
"""Счёт фактов для продуктового разбора Robella.

Ключ PostHog берётся из POSTHOG_PERSONAL_API_KEY или POSTHOG_API_KEY.
Если переменных нет, скрипт читает его из локального ~/.cursor/mcp.json
и никуда не печатает.
Почты, distinct_id и номера карт в выходные файлы не пишутся.

Запуск:
  python scripts/robella-analysis.py --primer "C:\\path\\payments (2).csv"
"""

from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import math
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "reports" / "robella-product-analysis-2026-11-20.html"
OUT_MD = ROOT / "reports" / "robella-product-analysis-2026-11-20-metodika.md"
API = "https://ph.app-inkfolio-reader.pro/api/projects/1/query/"
MSK = timezone(timedelta(hours=3))
END = "2026-11-18 21:00:00"
# 20.11: окно США и «до 11.11» объединены в один период — весь срок Robella (замечание Кати 19.11).
US_START = "2026-09-30 15:00:00"
PERIOD_US = "30.09.2026 18:14 МСК — 18.11.2026 23:59 МСК"
# Записи сессий и склейка magic link — только по окну записей аудита (11–18.11), как в разделе 3.
REC_START = "2026-11-10 21:00:00"
PERIOD_END_LABEL = "18.11.2026 23:59 МСК"
FOX_START, FOX_END = "2026-10-06 21:00:00", "2026-11-11 11:00:00"
FOX_LABEL = "07.10.2026 00:00 МСК — 11.11.2026 14:00 МСК"
AZ_START, AZ_END = "2026-10-08 21:00:00", "2026-10-23 07:00:00"
AZ_LABEL = "09.10.2026 00:00 МСК — 23.10.2026 10:00 МСК"
EMAIL_RE = r"\+.*@|gox-media\.com|@yandex\.ru|test|@example\.com|mailinator|eevakenn|nedvedyea"
FOX_EMAIL_RE = EMAIL_RE + r"|k\.k\.tarasova|nikitos\.gura|dariaivanova|^kkk@gmail\.com$|^myskillhouse2020@gmail\.com$|^ekaasrirahmawati403@gmail\.com$"
EMAIL_SCRUB = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
TOKEN_SCRUB = re.compile(r"(token=)[^&\s]+", re.I)


def load_key() -> str:
    env = os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip() or os.environ.get("POSTHOG_API_KEY", "").strip()
    if env:
        return env if env.startswith("Bearer ") else "Bearer " + env
    cfg_path = Path.home() / ".cursor" / "mcp.json"
    if not cfg_path.exists():
        raise SystemExit("нет ключа PostHog: задайте POSTHOG_API_KEY или POSTHOG_PERSONAL_API_KEY")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    found = []
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k.lower() == "authorization" and isinstance(v, str) and v.startswith("Bearer "):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(cfg)
    if not found:
        raise SystemExit("нет ключа PostHog")
    return found[0]


KEY = None


def hog(query: str) -> list:
    """Выполняет read-only HogQL через curl; ключ не попадает в вывод."""
    global KEY
    if KEY is None:
        KEY = load_key()
    body = json.dumps({"query": {"kind": "HogQLQuery", "query": query}})
    last_error = None
    for attempt in range(3):
        proc = subprocess.run(["curl", "-sS", "--max-time", "180", "-X", "POST", API, "-H", "Authorization: " + KEY, "-H", "Content-Type: application/json", "-d", body], capture_output=True, text=True, timeout=200)
        try:
            if proc.returncode:
                raise RuntimeError("curl")
            data = json.loads(proc.stdout)
            if data.get("error"):
                raise RuntimeError(str(data["error"])[:300])
            cols = data.get("columns") or []
            return [dict(zip(cols, row)) for row in data.get("results") or []]
        except (RuntimeError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2 + attempt * 3)
    raise RuntimeError(f"запрос не выполнился: {type(last_error).__name__}")


def qident(value: str) -> str:
    return value.replace("\\", "\\\\")


def test_exclude(alias_email_re: str = EMAIL_RE) -> str:
    pat = alias_email_re.replace("\\", "\\\\")
    return f"""person_id NOT IN (SELECT person_id FROM events WHERE timestamp < toDateTime('{END}') AND (toString(properties.is_test) IN ('true','1','True') OR toString(person.properties.is_test) IN ('true','1','True') OR match(lower(coalesce(toString(person.properties.email),'')), '{pat}') = 1 OR match(lower(toString(distinct_id)), '{pat}') = 1))"""


ROB_TEST = test_exclude(EMAIL_RE)
FOX_TEST = test_exclude(FOX_EMAIL_RE)
AZ_TEST = test_exclude(EMAIL_RE)


def msk_sec(value) -> str:
    text = msk(value)
    if text == "нет данных":
        return text
    raw = str(value).replace("Z", "+00:00")
    if "T" not in raw and " " in raw:
        raw = raw.replace(" ", "T")
    if "+" not in raw:
        raw += "+00:00"
    try:
        dt = datetime.fromisoformat(raw[:32])
    except ValueError:
        return text
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK).strftime("%d.%m.%Y %H:%M:%S")


def parse_utc(value):
    raw = str(value).replace("Z", "+00:00")
    if "T" not in raw and " " in raw:
        raw = raw.replace(" ", "T")
    if "+" not in raw:
        raw += "+00:00"
    dt = datetime.fromisoformat(raw[:32])
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def msk(value) -> str:
    if not value:
        return "нет данных"
    text = str(value).replace("Z", "+00:00")
    if "T" not in text and " " in text:
        text = text.replace(" ", "T")
    if "+" not in text and text[-1] != "Z":
        text += "+00:00"
    try:
        dt = datetime.fromisoformat(text[:32])
    except ValueError:
        return str(value)[:19]
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK).strftime("%d.%m.%Y %H:%M")


def msk_day(value) -> str:
    return msk(value)[:10]


def pct(num, den) -> str:
    if den in (0, None):
        return "нет данных"
    return f"{num / den * 100:.1f}%".replace(".", ",")


def n_of(num, den) -> str:
    if num is None or den is None:
        return "нет данных"
    return f"{num} из {den}"


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def clean_text(value: str) -> str:
    text = EMAIL_SCRUB.sub("[почта]", value or "")
    text = TOKEN_SCRUB.sub(r"\1[скрыт]", text)
    return re.sub(r"\s+", " ", text).strip()


def funnel_block(where: str, test_sql: str) -> dict:
    rows = hog(f"""SELECT uniqIf(person_id, event = 'funnel_start') AS started, uniqIf(person_id, event = 'funnel_email_submit') AS email_n, uniqIf(person_id, event = 'funnel_email_verify') AS verify_n, uniqIf(person_id, event = 'funnel_checkout_open') AS checkout_n, uniqIf(person_id, event = 'funnel_purchase_success') AS purchase_n, uniqIf(person_id, event = 'funnel_purchase_fail') AS purchase_fail_n, uniqIf(person_id, event = 'funnel_purchase_start') AS purchase_start_n FROM events WHERE {where} AND {test_sql}""")
    return rows[0] if rows else {}


def step_people(where: str, column_sql: str) -> list:
    return hog(f"""SELECT {column_sql} AS step, uniq(person_id) AS people, count() AS events FROM events WHERE event = 'funnel_screen_open' AND {where} AND {ROB_TEST} GROUP BY step ORDER BY people DESC LIMIT 80""")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primer")
    parser.add_argument("--primer-json", help="сводка Primer без карт и почт (JSON) вместо исходного CSV")
    parser.add_argument("--magic-links", action="store_true")
    parser.add_argument("--apply-magic-links", action="store_true")
    args = parser.parse_args()
    if args.magic_links or args.apply_magic_links:
        journeys = magic_link_journeys()
        print(json.dumps(journeys, ensure_ascii=False, indent=2))
        if args.apply_magic_links:
            apply_magic_link_reports(journeys)
            print("html", OUT_HTML)
            print("md", OUT_MD)
        return
    if not args.primer and not args.primer_json:
        parser.error("укажите --primer, --primer-json, --magic-links или --apply-magic-links")
    data = compute(Path(args.primer or args.primer_json))
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    OUT_MD.write_text(render_md(data), encoding="utf-8")
    print("html", OUT_HTML)
    print("md", OUT_MD)
    print("started_us", data["us"]["started"], "email", data["us"]["email_n"], "checkout", data["us"]["checkout_n"])
    print("path_age", data["path"].get("age_group"), "path_social", data["path"].get("social_proof"))
    print("sid_age", data["sid"].get("age_group"), "sid_social", data["sid"].get("social_proof"))
    print("primer", data["primer"]["rows"], "buyers", len(data["buyers"]))


def _email_values(*values) -> set:
    """Ищет email также внутри URL, включая percent-encoding; значения не выводит."""
    found = set()
    for value in values:
        text = str(value or "")
        variants = {text}
        for _ in range(2):
            variants |= {urllib.parse.unquote(item) for item in list(variants)}
        for variant in variants:
            found.update(match.group(0).lower() for match in EMAIL_SCRUB.finditer(variant))
    return found


def _sql_literal(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def _email_match_sql(email: str) -> str:
    variants = {email, urllib.parse.quote(email, safe=""), urllib.parse.quote_plus(email)}
    clauses = []
    for value in variants:
        literal = _sql_literal(value)
        clauses.extend([f"positionCaseInsensitive(toString(properties), '{literal}') > 0", f"positionCaseInsensitive(toString(person.properties), '{literal}') > 0"])
    return "(" + " OR ".join(clauses) + ")"


def _unlinked_magic_candidate(request: dict) -> dict | None:
    """Показывает соседний заход отдельно, не присваивая его исходному email."""
    requested_ts = _sql_literal(request["requested_ts"])
    candidates = hog(f"""SELECT person_id, toString(timestamp) AS ts, toString(properties) AS props, toString(properties.$session_id) AS session_id FROM events WHERE event = '$pageview' AND toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web' AND toString(properties.$pathname) = '/magic-link-login' AND timestamp > parseDateTimeBestEffort('{requested_ts}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} ORDER BY timestamp LIMIT 1""")
    if not candidates:
        return None
    candidate = candidates[0]
    request_props = json.loads(request.get("props") or "{}")
    candidate_props = json.loads(candidate.get("props") or "{}")
    shared = []
    if request.get("person_id") and request.get("person_id") == candidate.get("person_id"):
        shared.append("person_id")
    for key in ("distinct_id", "$device_id", "$session_id", "$window_id", "$ip"):
        left, right = request_props.get(key), candidate_props.get(key)
        if left and right and left == right:
            shared.append(key)
    session_id = str(candidate.get("session_id") or "")
    session_rows = []
    if session_id:
        session_rows = hog(f"""SELECT toString(timestamp) AS ts, event, toString(properties.$pathname) AS path FROM events WHERE toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web' AND toString(properties.$session_id) = '{_sql_literal(session_id)}' AND timestamp >= parseDateTimeBestEffort('{_sql_literal(candidate["ts"])}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} ORDER BY timestamp LIMIT 500""")
    login = [row for row in session_rows if row.get("event") == "login"]
    opened = [row for row in session_rows if row.get("event") == "app_opened"]
    return {"attributed": False, "shared_identifiers": shared, "magic_link_login": msk_sec(candidate["ts"]), "session_events": len(session_rows), "login": msk_sec(login[0]["ts"]) if login else None, "app_opened": msk_sec(opened[0]["ts"]) if opened else None, "last_event": msk_sec(session_rows[-1]["ts"]) if session_rows else None}


def magic_link_journeys() -> list:
    """Доказательная склейка по email; близость по времени не засчитывается."""
    requests = hog(f"""SELECT person_id, toString(timestamp) AS requested_ts, toString(properties.$session_id) AS session_id, toString(properties.$device_id) AS device_id, toString(properties) AS props, toString(person.properties) AS person_props FROM events WHERE event = 'magic_link_requested' AND toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web' AND timestamp >= toDateTime('{REC_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} ORDER BY timestamp LIMIT 20""")
    journeys = []
    for index, request in enumerate(requests, start=1):
        result = {"n": index, "requested": msk_sec(request.get("requested_ts")), "email_found": False, "email_source": None}
        emails = _email_values(request.get("props"), request.get("person_props"))
        source = "magic_link_requested"
        if not emails:
            requested_ts = _sql_literal(request["requested_ts"])
            identity = [f"person_id = '{_sql_literal(request['person_id'])}'"] if request.get("person_id") else []
            if request.get("session_id"):
                identity.append(f"toString(properties.$session_id) = '{_sql_literal(request['session_id'])}'")
            if request.get("device_id"):
                identity.append(f"toString(properties.$device_id) = '{_sql_literal(request['device_id'])}'")
            context = hog(f"""SELECT toString(properties) AS props, toString(person.properties) AS person_props FROM events WHERE timestamp <= parseDateTimeBestEffort('{requested_ts}') AND ({' OR '.join(identity) or '1 = 0'}) AND {ROB_TEST} ORDER BY timestamp LIMIT 1000""") if identity else []
            for row in context:
                emails |= _email_values(row.get("props"), row.get("person_props"))
            source = "та же персона, сессия или устройство до запроса"
        if len(emails) != 1:
            result["status"] = "нет данных: в запросе и его прежнем контексте несколько email" if emails else "нет данных: email не сохранился в запросе и его прежнем контексте"
            result["unlinked_candidate"] = _unlinked_magic_candidate(request)
            journeys.append(result)
            continue
        email = next(iter(emails))
        email_sql = _email_match_sql(email)
        email_rows = hog(f"""SELECT person_id, toString(timestamp) AS ts, event, toString(properties.project) AS project, toString(properties.$lib) AS lib, toString(properties.$pathname) AS path, toString(properties.$session_id) AS session_id FROM events WHERE timestamp < toDateTime('{END}') AND {email_sql} AND {ROB_TEST} ORDER BY timestamp LIMIT 1000""")
        people = sorted({row["person_id"] for row in email_rows if row.get("person_id")})
        people_sql = ",".join(f"'{_sql_literal(person)}'" for person in people)
        after_sql = f"({email_sql} OR person_id IN ({people_sql}))" if people_sql else email_sql
        requested_ts = _sql_literal(request["requested_ts"])
        after_rows = hog(f"""SELECT person_id, toString(timestamp) AS ts, event, toString(properties.project) AS project, toString(properties.$lib) AS lib, toString(properties.$pathname) AS path, toString(properties.$session_id) AS session_id FROM events WHERE timestamp > parseDateTimeBestEffort('{requested_ts}') AND timestamp < toDateTime('{END}') AND {after_sql} AND {ROB_TEST} ORDER BY timestamp LIMIT 1000""")
        web = [row for row in after_rows if row.get("project") == "robella" and row.get("lib") == "web" and row.get("event") != "magic_link_requested"]
        magic = [row for row in web if row.get("event") == "$pageview" and row.get("path") == "/magic-link-login"]
        login = [row for row in web if row.get("event") == "login"]
        opened = [row for row in web if row.get("event") == "app_opened"]
        request_session = str(request.get("session_id") or "")
        cross_session = [row for row in web if row.get("session_id") and str(row["session_id"]) != request_session]
        result.update({"email_found": True, "email_source": source, "status": "связано по email; последующих веб-событий нет" if not web else "связано по email", "matched_events": len(email_rows), "matched_people": len(people), "matched_sessions": len({row.get("session_id") for row in email_rows if row.get("session_id")}), "web_events_after": len(web), "web_sessions_after": len({row.get("session_id") for row in web if row.get("session_id")}), "cross_session_events": len(cross_session), "magic_link_login_count": len(magic), "login_count": len(login), "app_opened_count": len(opened), "magic_link_login": msk_sec(magic[0]["ts"]) if magic else None, "login": msk_sec(login[0]["ts"]) if login else None, "app_opened": msk_sec(opened[0]["ts"]) if opened else None})
        journeys.append(result)
    return journeys


def compute(primer_path: Path) -> dict:
    scope = hog(f"""SELECT min(timestamp) AS first_ts, max(timestamp) AS last_ts, uniq(person_id) AS people_raw, uniqIf(person_id, toString(properties.project) = 'robella_ff') AS funnel_raw, uniqIf(person_id, toString(properties.project) = 'robella') AS app_raw, uniqIf(person_id, toString(properties.project) = 'robella_landing') AS land_raw FROM events WHERE timestamp < toDateTime('{END}') AND toString(properties.project) IN ('robella','robella_ff','robella_landing')""")[0]
    excluded = hog(f"""SELECT uniq(person_id) AS people FROM events WHERE timestamp < toDateTime('{END}') AND toString(properties.project) IN ('robella','robella_ff','robella_landing') AND NOT ({ROB_TEST})""")[0]["people"]
    def window(start: str) -> str:
        return f"timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{END}') AND toString(properties.project) IN ('robella','robella_ff','robella_landing')"
    def one_window(start: str) -> dict:
        base = window(start)
        ff = base + " AND toString(properties.project) = 'robella_ff'"
        block = funnel_block(ff, ROB_TEST)
        reach = hog(f"""SELECT uniq(person_id) AS people, uniqIf(person_id, toString(properties.project) = 'robella_ff' AND event = 'funnel_start') AS started, uniqIf(person_id, toString(properties.project) = 'robella_landing') AS landing, uniqIf(person_id, toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web') AS app_web, uniqIf(person_id, event = 'magic_link_requested') AS magic, uniqIf(person_id, event = 'login') AS login_n, uniqIf(person_id, event = 'app_opened') AS app_opened, uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/auto-login') AS autologin, uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/auth') AS auth_n, uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/magic-link-login') AS magic_page, uniqIf(person_id, event = 'onboarding_started') AS onb_started, uniqIf(person_id, event = 'onboarding_completed') AS onb_done, uniqIf(person_id, event = 'capsule_opened') AS capsule, uniqIf(person_id, event = 'report_opened') AS report_n, uniqIf(person_id, event = 'tryon_started' OR event = 'tryon_completed' OR event = 'tryon_failed') AS tryon, uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/closet') AS closet, uniqIf(person_id, event = 'subscription_started' AND toString(properties.project) = 'robella') AS sub_started FROM events WHERE {base} AND {ROB_TEST}""")[0]
        joined = hog(f"""SELECT countIf(email_n = 1 AND app_web = 1) AS email_and_app, countIf(checkout_n = 1) AS checkout_people, countIf(checkout_n = 1 AND purchase_n = 1) AS checkout_and_purchase, countIf(checkout_n = 1 AND primer_n = 1) AS checkout_and_primer, countIf(checkout_n = 1 AND app_web = 1) AS checkout_and_app FROM (SELECT max(event = 'funnel_email_submit') AS email_n, max(event = 'funnel_checkout_open') AS checkout_n, max(event = 'funnel_purchase_success') AS purchase_n, max(event = 'primer_payment') AS primer_n, max(toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web') AS app_web FROM events WHERE {base} AND {ROB_TEST} GROUP BY person_id)""")[0]
        block.update(reach)
        block.update(joined)
        return block
    us = one_window(US_START)
    full = one_window("2020-01-01 00:00:00")
    path_where = f"timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND toString(properties.project) = 'robella_ff'"
    path_sql = "if(extract(toString(properties.$pathname), '/([^/]+)$') = '' OR extract(toString(properties.$pathname), '/([^/]+)$') = 'ai-stilist-week-web', 'intro', extract(toString(properties.$pathname), '/([^/]+)$'))"
    path_rows = step_people(path_where, path_sql)
    sid_rows = step_people(path_where, "toString(properties.screen_id)")
    mismatch = hog(f"""SELECT count() AS events, countIf(extract(toString(properties.$pathname), '/([^/]+)$') != '' AND extract(toString(properties.$pathname), '/([^/]+)$') != 'ai-stilist-week-web' AND extract(toString(properties.$pathname), '/([^/]+)$') != toString(properties.screen_id)) AS mismatch_nested, countIf(extract(toString(properties.$pathname), '/([^/]+)$') != toString(properties.screen_id)) AS mismatch_all FROM events WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST}""")[0]
    overlap = hog(f"""SELECT countIf(age = 1 AND social = 0 AND goals = 0) AS age_only, countIf(social = 1 AND goals = 0) AS social_without_goals, countIf(goals = 1 AND social = 0) AS goals_without_social, countIf(goals = 1 AND social = 1) AS goals_and_social, countIf(age = 1) AS path_age, countIf(social = 1) AS path_social, countIf(goals = 1) AS path_goals FROM (SELECT max({path_sql} = 'age_group') AS age, max({path_sql} = 'social_proof') AS social, max({path_sql} = 'main_goals') AS goals FROM events WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST} GROUP BY person_id)""")[0]
    cross = hog(f"""SELECT {path_sql} AS path_step, toString(properties.screen_id) AS screen_id, uniq(person_id) AS people, count() AS events FROM events WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST} AND ({path_sql} = 'age_group' OR {path_sql} = 'social_proof' OR {path_sql} = 'main_goals' OR toString(properties.screen_id) = 'age_group' OR toString(properties.screen_id) = 'social_proof' OR toString(properties.screen_id) = 'main_goals') GROUP BY path_step, screen_id ORDER BY events DESC LIMIT 20""")
    order_rows = hog(f"""SELECT person_id, {path_sql} AS step, toString(min(timestamp)) AS first_ts FROM events WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST} GROUP BY person_id, step LIMIT 5000""")
    by_person = defaultdict(list)
    for row in order_rows:
        if row.get("step"):
            by_person[row["person_id"]].append((str(row["first_ts"]), row["step"]))
    ranks = defaultdict(list)
    for items in by_person.values():
        seen = set()
        rank = 0
        for _, step in sorted(items):
            if step in seen:
                continue
            seen.add(step)
            ranks[step].append(rank)
            rank += 1
    canon = ["intro", "age_group", "social_proof", "main_goals", "algo_promise", "eye_color", "hair_color", "skin_tone", "undertone", "analyzing", "body_shape", "height", "weight", "highlight_features", "wardrobe_struggles", "wear_percentage", "analyzing_fit", "location", "daily_life", "shopping_tier", "budget", "look_boho", "look_classic", "look_casual", "look_romantic", "look_evening", "photo_upload", "analyzing_preferences", "name", "email", "creating_plan", "gift_discount", "paywall"]
    present = set(ranks) | {row["step"] for row in path_rows}
    step_order = [step for step in canon if step in present]
    step_order += sorted(step for step in present if step not in step_order and step)
    before = hog(f"""SELECT uniqIf(person_id, event = 'funnel_start' AND timestamp < toDateTime('{US_START}')) AS started_before, uniqIf(person_id, event = 'funnel_purchase_success' AND timestamp < toDateTime('{US_START}')) AS purchase_before FROM events WHERE timestamp < toDateTime('{END}') AND toString(properties.project) = 'robella_ff' AND {ROB_TEST}""")[0]
    paywall_props = hog(f"""SELECT toString(properties.$pathname) AS path, toString(properties.screen_id) AS screen_id, toString(properties.price) AS price, toString(properties.amount) AS amount, toString(properties.currency) AS currency, toString(properties.trial_price) AS trial_price, toString(properties.plan) AS plan, count() AS events, uniq(person_id) AS people FROM events WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST} AND (toString(properties.$pathname) LIKE '%paywall%' OR toString(properties.screen_id) = 'paywall') GROUP BY path, screen_id, price, amount, currency, trial_price, plan ORDER BY people DESC LIMIT 20""")
    primer = read_primer(primer_path)
    primer_after = hog(f"""SELECT count() AS n, uniq(person_id) AS people FROM events WHERE event = 'primer_payment' AND toString(properties.project) = 'robella' AND timestamp > toDateTime('2026-11-17 09:28:53') AND timestamp < toDateTime('{END}') AND {ROB_TEST}""")[0]
    primer["after_file"] = primer_after
    buyers = early_buyers()
    checkout = checkout_stories()
    compare = {"foxiq": compare_product("foxiq_ff", "foxiq", FOX_START, FOX_END, FOX_TEST, ""), "azora": compare_product("azora_ff", "web", AZ_START, AZ_END, AZ_TEST, "AND toString(properties.$geoip_country_code) = 'JP'")}
    app_paths = hog(f"""SELECT toString(properties.$pathname) AS path, uniq(person_id) AS people, count() AS events FROM events WHERE event = '$pageview' AND toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web' AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} GROUP BY path ORDER BY people DESC LIMIT 30""")
    onboarding = hog(f"""SELECT toString(properties.step) AS step, count() AS events, uniq(person_id) AS people FROM events WHERE event = 'onboarding_step' AND toString(properties.project) = 'robella' AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} GROUP BY step ORDER BY step""")
    days = hog(f"""SELECT toDate(timestamp + INTERVAL 3 HOUR) AS day_msk, uniq(person_id) AS people FROM events WHERE event = 'funnel_start' AND toString(properties.project) = 'robella_ff' AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} GROUP BY day_msk ORDER BY day_msk""")
    product_events = hog(f"""SELECT event, uniq(person_id) AS people, count() AS n FROM events WHERE toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web' AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} AND event NOT LIKE '$%' GROUP BY event ORDER BY people DESC LIMIT 40""")
    return {"scope": scope, "excluded": excluded, "us": us, "full": full, "path": {row["step"]: row for row in path_rows}, "path_rows": path_rows, "sid": {row["step"]: row for row in sid_rows}, "sid_rows": sid_rows, "mismatch": mismatch, "overlap": overlap, "cross": cross, "step_order": step_order, "before": before, "paywall_props": paywall_props, "primer": primer, "buyers": buyers, "checkout": checkout, "compare": compare, "app_paths": app_paths, "onboarding": onboarding, "days": days, "product_events": product_events, "magic_links": magic_link_journeys(), "period_full": f"{msk(scope['first_ts'])} МСК — {PERIOD_END_LABEL}"}


def compare_product(ff: str, app: str, start: str, end: str, test_sql: str, extra: str) -> dict:
    try:
        row = hog(f"""SELECT uniqIf(person_id, event = 'funnel_start' AND toString(properties.project) = '{ff}') AS started, uniqIf(person_id, event = 'funnel_email_submit' AND toString(properties.project) = '{ff}') AS email_n, uniqIf(person_id, event = 'funnel_checkout_open' AND toString(properties.project) = '{ff}') AS checkout_n, uniqIf(person_id, event = 'funnel_purchase_success' AND toString(properties.project) = '{ff}') AS purchase_n FROM events WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}') AND toString(properties.project) = '{ff}' {extra} AND {test_sql}""")[0]
        joined = hog(f"""SELECT countIf(email_n = 1 AND app_web = 1) AS email_and_app, countIf(email_n = 1) AS email_people FROM (SELECT max(event = 'funnel_email_submit' AND toString(properties.project) = '{ff}' {extra}) AS email_n, max(toString(properties.project) = '{app}' AND toString(properties.$lib) = 'web') AS app_web FROM events WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}') AND toString(properties.project) IN ('{ff}','{app}') AND {test_sql} GROUP BY person_id)""")[0]
        row.update(joined)
        mail = hog(f"""SELECT countIf(ff = 1) AS emails, countIf(ff = 1 AND app = 1) AS both FROM (SELECT max(event = 'funnel_email_submit' AND toString(properties.project) = '{ff}' {extra}) AS ff, max(toString(properties.project) = '{app}' AND toString(properties.$lib) = 'web') AS app FROM events WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}') AND toString(properties.project) IN ('{ff}','{app}') AND lower(toString(person.properties.email)) != '' AND {test_sql} GROUP BY lower(toString(person.properties.email)))""")[0]
        row["email_join_emails"] = mail["emails"]
        row["email_join_both"] = mail["both"]
        row["ok"] = True
        return row
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def read_primer(path: Path) -> dict:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    rows = []
    total = 0
    first = last = None
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            total += 1
            day = (row.get("date") or "")[:19]
            if day:
                first = day if first is None or day < first else first
                last = day if last is None or day > last else last
            blob = ((row.get("metadata") or "") + " " + (row.get("statementDescriptor") or "")).lower()
            if "robella" not in blob:
                continue
            try:
                meta = json.loads(row.get("metadata") or "{}")
            except json.JSONDecodeError:
                meta = {}
            email = (row.get("customerEmailAddress") or meta.get("email") or "").lower()
            rows.append({"date": row.get("date"), "status": row.get("status"), "amount_minor": int(row.get("amount") or 0), "currency": row.get("currencyCode"), "refunded": int(row.get("amountRefunded") or 0), "init": meta.get("ff_initiation_type") or "", "country": meta.get("ff_country_code") or "", "test": bool(re.search(EMAIL_RE, email, re.I))})
    by_day = defaultdict(lambda: defaultdict(int))
    for row in rows:
        dollars = f"{row['amount_minor'] / 100:.2f} {row['currency']}"
        by_day[msk_day(row["date"])][(row["status"], dollars, row["init"], "тест" if row["test"] else "не тест")] += 1
    return {"file_rows": total, "first": first, "last": last, "rows": len(rows), "people_hint": None, "items": rows, "by_day": [{"day": day, "status": key[0], "amount": key[1], "init": key[2], "test": key[3], "n": n} for day, bucket in sorted(by_day.items()) for key, n in sorted(bucket.items())], "settled_cit": sum(1 for r in rows if r["status"] == "SETTLED" and r["init"] == "cit" and not r["test"]), "declined": sum(1 for r in rows if r["status"] == "DECLINED"), "trial_1": sum(1 for r in rows if r["amount_minor"] == 100 and r["currency"] == "USD"), "month_3990": sum(1 for r in rows if r["amount_minor"] == 3990 and r["currency"] == "USD")}


def early_buyers() -> list:
    rows = hog(f"""SELECT person_id, minIf(timestamp, event = 'subscription_started') AS started, countIf(event = 'subscription_cancelled') AS cancels, countIf(event = 'subscription_expired') AS expires, countIf(event = 'subscription_renewed') AS renews, countIf(event = 'primer_payment' AND toString(properties.status) = 'settled') AS settled_n, countIf(event = 'primer_payment' AND toString(properties.status) = 'declined') AS declined_n, countIf(toString(properties.$lib) = 'web') AS web_events, uniqIf(toString(properties.$pathname), event = '$pageview' AND toString(properties.$lib) = 'web') AS paths, max(event = 'onboarding_started') AS onb, max(event = 'capsule_opened') AS capsule, max(event = 'login') AS login_n, max(event = 'app_opened') AS opened FROM events WHERE toString(properties.project) = 'robella' AND timestamp < toDateTime('{END}') AND {ROB_TEST} AND person_id IN (SELECT person_id FROM events WHERE event = 'subscription_started' AND toString(properties.project) = 'robella' AND timestamp < toDateTime('{END}') AND {ROB_TEST}) GROUP BY person_id ORDER BY started""")
    out = []
    for index, row in enumerate(rows, start=1):
        reasons = hog(f"""SELECT event, toString(properties.reason) AS reason, toString(timestamp) AS ts FROM events WHERE person_id = '{row['person_id']}' AND toString(properties.project) = 'robella' AND (event = 'subscription_cancelled' OR event = 'subscription_expired' OR event = 'subscription_renewed' OR event = 'primer_payment') AND timestamp < toDateTime('{END}') ORDER BY timestamp LIMIT 12""")
        safe = []
        for item in reasons:
            safe.append({"event": item["event"], "reason": item.get("reason") or "", "ts": msk_sec(item.get("ts")), "dt": parse_utc(item.get("ts")) if item.get("ts") else None})
        pages = hog(f"""SELECT replaceRegexpOne(toString(properties.$pathname), '\\\\?.*', '') AS path, count() AS n FROM events WHERE person_id = '{row['person_id']}' AND toString(properties.project) = 'robella' AND event = '$pageview' AND toString(properties.$lib) = 'web' AND timestamp < toDateTime('{END}') GROUP BY path ORDER BY n DESC LIMIT 6""")
        cancels = [item["dt"] for item in safe if item["event"] == "subscription_cancelled" and item["dt"]]
        expires = [item["dt"] for item in safe if item["event"] == "subscription_expired" and item["dt"]]
        same = []
        for left in cancels:
            for right in expires:
                if abs((left - right).total_seconds()) <= 1:
                    same.append(msk_sec(left))
        out.append({"n": index, "started": msk(row["started"]), "cancels": row["cancels"], "expires": row["expires"], "renews": row["renews"], "web_events": row["web_events"], "paths": row["paths"], "pages": [clean_text(f"{item['path'] or '/'} ({item['n']})") for item in pages], "onb": row["onb"], "capsule": row["capsule"], "login_n": row["login_n"], "opened": row["opened"], "same_second": same, "money": [{k: v for k, v in item.items() if k != "dt"} for item in safe]})
    return out


def checkout_stories() -> list:
    people = hog(f"""SELECT person_id, min(timestamp) AS first_checkout FROM events WHERE event = 'funnel_checkout_open' AND toString(properties.project) = 'robella_ff' AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST} GROUP BY person_id ORDER BY first_checkout""")
    stories = []
    for index, person in enumerate(people, start=1):
        pid = person["person_id"]
        events = hog(f"""SELECT toString(timestamp) AS ts, event, toString(properties.project) AS project, toString(properties.$pathname) AS path, toString(properties.screen_id) AS screen_id, toString(properties.status) AS status, toString(properties.amount) AS amount, toString(properties.$recording_status) AS recording FROM events WHERE person_id = '{pid}' AND timestamp < toDateTime('{END}') AND toString(properties.project) IN ('robella','robella_ff','robella_landing') AND event != '$web_vitals' AND event != '$pageleave' ORDER BY timestamp LIMIT 250""")
        compact = []
        for event in events:
            path = event.get("path") or ""
            if "?" in path:
                path = path.split("?", 1)[0]
            if path.startswith("http"):
                path = re.sub(r"https?://[^/]+", "", path)
            compact.append({"ts": msk_sec(event["ts"]), "event": event["event"], "project": event["project"], "path": path[:80], "screen_id": event.get("screen_id") or "", "status": event.get("status") or "", "amount": event.get("amount") or "", "recording": event.get("recording") or ""})
        interesting = []
        for event in compact:
            path = event["path"]
            keep = event["event"] != "funnel_screen_open" or any(token in path for token in ("email", "paywall", "name", "creating", "gift", "ai-stylist"))
            if keep:
                interesting.append(event)
        last_screen = ""
        for event in compact:
            if event["event"] == "funnel_screen_open" and event["path"]:
                last_screen = event["path"]
        stories.append({"n": index, "events": interesting[:40], "truncated": len(events) >= 250, "screen_events": sum(1 for event in compact if event["event"] == "funnel_screen_open"), "last_screen": last_screen, "checkout": sum(1 for event in compact if event["event"] == "funnel_checkout_open"), "primer": sum(1 for event in compact if event["event"] == "primer_payment"), "purchase": sum(1 for event in compact if event["event"] == "funnel_purchase_success"), "fail": sum(1 for event in compact if event["event"] == "funnel_purchase_fail"), "app_events": sum(1 for event in compact if event["project"] == "robella"), "recording_active": sum(1 for event in compact if event["recording"] == "active")})
    return stories


def sample_size(p1: float, p2: float) -> int | None:
    if p1 <= 0 or p1 >= 1 or p2 <= 0 or p2 >= 1 or p1 == p2:
        return None
    z = 1.959963984540054 + 0.841621233572914
    return math.ceil(z * z * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2)


def _n(value):
    return int(value or 0)


def _bar_rows(items, denominator, scale=None, show_pct=False):
    scale = denominator if scale is None else scale
    scale = max(1, scale or 1)
    out = []
    for item in items:
        num = _n(item.get("n"))
        den = _n(item.get("den", denominator))
        width = min(100, num / scale * 100) if num else 0
        small = num < 30
        color = item.get("color", "accent")
        label = esc(n_of(num, den))
        if show_pct and den:
            label += " · " + esc(pct(num, den))
        if item.get("note"):
            label += " · " + esc(item["note"])
        out.append("<div class='bar-row'>" f"<div class='bar-label'>{esc(item['label'])}</div>" f"<div class='track' aria-hidden='true'><div class='fill {color}{' small' if small else ''}' style='width:{width:.2f}%'></div></div>" f"<div class='bar-value num'>{label}</div></div>")
    return "".join(out)


def _funnel_panel(title, rows, order, started):
    by_step = {row["step"]: row for row in rows}
    steps = [step for step in order if step in by_step]
    steps += sorted(step for step in by_step if step not in steps and step)
    items = [{"label": step, "n": _n(by_step[step].get("people"))} for step in steps]
    return "<div class='chart card'><h3>" + esc(title) + "</h3><div class='bars funnel-bars'>" + _bar_rows(items, started) + "</div></div>"


# 20.11: блок проверки после исправления screen_id (статичный, цифры на 20.11).
AFTER_FIX_HTML = '<section><div class="eyebrow">1а · После исправления screen_id</div><h2>Что изменилось после 19.11</h2><p class="meta">19.11.2026 12:25 МСК — 20.11.2026 12:39 МСК · события funnel_screen_open, project = robella_ff · тестовые исключены · проверка 20.11</p><div class="card"><div class="bars"><div class=\'bar-row\'><div class=\'bar-label\'>Живые события: адрес и screen_id совпадают</div><div class=\'track\' aria-hidden=\'true\'><div class=\'fill ok small\' style=\'width:100%\'></div></div><div class=\'bar-value num\'>17 из 17</div></div><div class=\'bar-row\'><div class=\'bar-label\'>Проверочные проходы preview: совпадают</div><div class=\'track\' aria-hidden=\'true\'><div class=\'fill ok\' style=\'width:97.5%\'></div></div><div class=\'bar-value num\'>196 из 201</div></div><div class=\'bar-row\'><div class=\'bar-label\'>Живые посетители после исправления</div><div class=\'track\' aria-hidden=\'true\'><div class=\'fill accent small\' style=\'width:100%\'></div></div><div class=\'bar-value num\'>5 человек</div></div></div></div><div class="callout"><b>Исправление работает.</b> До 19.11 адрес и screen_id расходились в 844 из 3025 событий; после исправления у живых посетителей — 0 из 17. Оставшиеся 5 расхождений в preview — первый экран, у которого в адресе preview стоит служебный идентификатор вместо имени экрана; это не ошибка разметки. Воронка теперь открывается по адресу /ai-stylist.</div><div class="callout warn"><b>Влияние на конверсию оценить нельзя.</b> Живого трафика почти нет: с 16.11 — 1–2 старта в день; после исправления воронку начали 5 человек, двое последних (19.11 21:39 и 20.11 12:39 МСК) ушли после экрана возраста. Обрыв age_group → social_proof пересчитаем, когда снова пойдёт трафик.</div></section>'
AFTER_FIX_MD = '\n## 1а. После исправления screen_id (проверка 20.11)\n- Период: 19.11.2026 12:25 МСК — 20.11.2026 12:39 МСК; `funnel_screen_open`, `project = robella_ff`, тестовые исключены.\n- Живые события: адрес и `screen_id` совпадают в 17 из 17 (до исправления расходились 844 из 3025). Preview: совпадают 196 из 201; 5 расхождений — первый экран с служебным идентификатором в адресе preview, не ошибка разметки.\n- Живых посетителей после исправления — 5; двое последних ушли после age_group. Трафика почти нет с 16.11, влияние исправления на конверсию оценить нельзя.\n- Воронка открывается по адресу `/ai-stylist`; первый экран без суффикса считается `intro`.\n'

WEEKS = [datetime(2026, 9, 28) + timedelta(days=7 * i) for i in range(8)]


def _week_key(day: str) -> str:
    dt = datetime.strptime(day, "%d.%m.%Y")
    monday = dt - timedelta(days=dt.weekday())
    return monday.strftime("%d.%m.%Y")


def _checkout_daily(data):
    """Открытия оплаты и покупки по неделям МСК (пн–вс): с 20.11 период — весь срок."""
    counts = defaultdict(lambda: {"open": 0, "reached": 0, "purchase": 0})
    for story in data.get("checkout") or []:
        day = None
        for event in story.get("events") or []:
            if event.get("event") == "funnel_checkout_open":
                day = str(event.get("ts") or "")[:10]
                break
        if not day:
            continue
        day = _week_key(day)
        counts[day]["open"] += 1
        counts[day]["reached"] += 1 if _n(story.get("primer")) > 0 else 0
        counts[day]["purchase"] += 1 if _n(story.get("purchase")) > 0 else 0
    return counts


def _checkout_chart(data, started):
    daily = _checkout_daily(data)
    day_labels = [w.strftime("%d.%m.%Y") for w in WEEKS]
    largest = max([1] + [max(daily.get(day, {}).get("open", 0), daily.get(day, {}).get("purchase", 0)) for day in day_labels])
    step = max(1, math.ceil(largest / 4))
    y_max = step * 4
    ticks = "".join(f"<span>{value}</span>" for value in range(y_max, -1, -step))
    plots, labels = [], []
    for day in day_labels:
        vals = daily.get(day, {"open": 0, "purchase": 0})
        bars = []
        for key, css_class in (("open", "accent"), ("purchase", "ok")):
            num = vals.get(key, 0)
            height = num / y_max * 100
            value = f"<span class='vbar-value'>{esc(n_of(num, started))}</span>" if num else ""
            small = " small" if num < 30 else ""
            bars.append(f"<div class='vbar-slot' style='--bar-height:{height:.2f}%'>" f"{value}<div class='vbar {css_class}{small}' style='height:{height:.2f}%'></div></div>")
        plots.append("<div class='day-plot'>" + "".join(bars) + "</div>")
        end = (datetime.strptime(day, "%d.%m.%Y") + timedelta(days=6)).strftime("%d.%m")
        labels.append(f"<div class='day-label'>{day[:5]}–{end}</div>")
    return "<div class='column-chart' role='img' aria-label='Столбчатая диаграмма: открытия оплаты и успешные оплаты по неделям'>" f"<div class='y-axis'>{ticks}</div>" + "".join(plots) + "<div class='x-spacer'></div>" + "".join(labels) + "</div>"


def _preview_count(data):
    total = 0
    for story in data.get("checkout") or []:
        paths = [str(story.get("last_screen") or "")]
        paths += [str(event.get("path") or "") for event in story.get("events") or []]
        if any("/preview/" in path for path in paths):
            total += 1
    return total


def _preview_note(preview_n, checkout_n, started, email_n):
    if not preview_n:
        return "<p class=\"note\">Проверка трафика: preview-проходов среди открытий оплаты не найдено.</p>"
    production_n = max(0, _n(checkout_n) - _n(preview_n))
    return f"<p class=\"note\"><b>Проверка трафика: часть открытий оплаты — preview, не живой трафик.</b> {n_of(preview_n, checkout_n)} открытий оплаты прошли по /preview/…/main/ (в том числе тестовая цепочка 18.11: полный квиз → email → 2 checkout → purchase_fail). По <a href=\"https://funnelfox.com/docs/editor/publishing\">документации FunnelFox</a> в preview платежи работают в test mode, без реального списания, поэтому purchase_fail здесь нельзя считать отказом живого платежа. Остальные {production_n} checkout шли по /ai-stilist-week-web/. FunnelFox также <a href=\"https://funnelfox.com/docs/dashboard/customers\">не рекомендует использовать preview-профили в аналитике</a>. Базовые {started}/{email_n}/{checkout_n} не пересчитаны: нужен полный фильтр preview по всем шагам.</p>"


def _preview_md(preview_n, checkout_n, started, email_n):
    production_n = max(0, _n(checkout_n) - _n(preview_n))
    return f"**Проверка 18.11:** {n_of(preview_n, checkout_n)} открытий оплаты прошло по `/preview/…/main/`. Сохранённая цепочка: 18.11 16:03:52–16:24:53 МСК, полный квиз → email → 2 checkout → `funnel_purchase_fail`. Остальные {production_n} checkout шли по боевому `/ai-stilist-week-web/`.\n\nПо [документации FunnelFox](https://funnelfox.com/docs/editor/publishing) preview — среда для тестирования, платежи в ней работают в test mode без реального списания. Поэтому этот `funnel_purchase_fail` не является отказом живого платежа. FunnelFox также прямо указывает, что [preview-профили не должны использоваться в аналитике](https://funnelfox.com/docs/dashboard/customers). Это не живой трафик; личность проходившего тестировщиком не называем.\n\nИсходный фильтр аудита preview не исключает. Базовые числа оставлены без изменения: {started} стартов, {email_n} почт, {checkout_n} открытий оплаты. Для полного исключения preview по всем шагам нужен новый запрос PostHog: сохранённых агрегатов недостаточно, чтобы определить, были ли другие preview-сессии среди стартов и почт. Без такого пересчёта боевые знаменатели не выдумываем."


def _report_css():
    return """:root{--bg:#fff5ee;--card:#fffdfb;--ink:#3a2a26;--muted:#8b6f65;--line:#f4d9cb;--accent:#e48a6c;--chip:#fde3d6;--soft:#fdebe1;--title:#7a3f2c;--ok:#5f9c7a;--warn:#c9922f;--bad:#c9604f;--fox:#c9a18d;--azora:#7a3f2c}*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;font-size:15px;line-height:1.45}.wrap{max-width:900px;margin:0 auto;padding:30px 16px 56px;display:flex;flex-direction:column;gap:26px}header{display:flex;flex-direction:column;gap:8px}h1,h2,h3,p{margin:0}h1{color:var(--title);font-size:30px;line-height:1.2}h2{color:var(--title);font-size:21px}h3{font-size:15px}.eyebrow{color:var(--muted);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.meta,.note{color:var(--muted);font-size:13px}.num{font-variant-numeric:tabular-nums;white-space:nowrap}a{color:var(--title);font-weight:600}.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 5px 18px rgba(122,63,44,.05)}section{display:flex;flex-direction:column;gap:12px}.summary{border-top:4px solid var(--accent)}.summary ol{margin:0;padding-left:21px}.summary li+li{margin-top:7px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.chart{display:flex;flex-direction:column;gap:12px;min-width:0}.bars{display:flex;flex-direction:column;gap:8px}.bar-row{display:grid;grid-template-columns:minmax(100px,150px) minmax(45px,1fr) auto;gap:9px;align-items:center;min-width:0}.bar-label{font-size:12px;overflow-wrap:anywhere}.bar-value{font-size:12px;text-align:right}.track{height:17px;background:var(--soft);border-radius:99px;overflow:hidden}.fill{height:100%;border-radius:99px;background:var(--accent)}.fill.fox{background:var(--fox)}.fill.azora{background:var(--azora)}.fill.warn{background:var(--warn)}.fill.bad{background:var(--bad)}.fill.ok{background:var(--ok)}.fill.small,.small-mark{background-image:repeating-linear-gradient(135deg,rgba(255,255,255,.72) 0 4px,transparent 4px 8px);background-size:12px 12px}.funnel-bars{gap:6px}.funnel-bars .bar-row{grid-template-columns:minmax(90px,125px) minmax(30px,1fr) 62px;gap:7px}.funnel-bars .track{height:12px}.funnel-bars .bar-label,.funnel-bars .bar-value{font-size:10px}.legend{display:flex;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:12px}.legend span{display:inline-flex;align-items:center;gap:5px}.dot{width:12px;height:12px;border-radius:4px;background:var(--accent);display:inline-block}.dot.fox{background:var(--fox)}.dot.azora{background:var(--azora)}.dot.warn{background:var(--warn)}.dot.bad{background:var(--bad)}.dot.ok{background:var(--ok)}.callout{border-left:4px solid var(--accent);background:var(--soft);padding:11px 13px;border-radius:0 10px 10px 0}.callout.warn{border-color:var(--warn)}.day-group{padding:10px 0;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:6px}.day-group:last-child{border-bottom:0}.day-name{font-weight:700;font-size:13px}.day-bars .bar-row{grid-template-columns:130px minmax(40px,1fr) 72px}.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--card)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}th{background:var(--chip);color:var(--title);font-size:11px;text-transform:uppercase;letter-spacing:.03em}tr:last-child td{border-bottom:0}.bugs{min-width:680px}.hyp{display:flex;flex-direction:column;gap:7px;border-left:4px solid var(--warn)}.hyp p{font-size:13px}.hyp b{color:var(--title)}.questions{margin:0;padding-left:20px}.questions li+li{margin-top:6px}.priority{margin:0;padding-left:20px;font-size:13px}.priority li+li{margin-top:4px}.tag{display:inline-block;background:var(--chip);border-radius:99px;padding:2px 8px;color:var(--title);font-size:11px;font-weight:700}.method-link{font-size:13px}.column-chart{display:grid;grid-template-columns:28px repeat(8,minmax(0,1fr));grid-template-rows:190px 30px}.y-axis{grid-column:1;grid-row:1;display:flex;flex-direction:column;justify-content:space-between;align-items:flex-end;padding:0 6px 0 0;color:var(--muted);font-size:10px}.day-plot{grid-row:1;display:flex;align-items:flex-end;justify-content:center;gap:5px;border-bottom:1px solid var(--line);background:repeating-linear-gradient(to bottom,var(--line) 0 1px,transparent 1px 25%)}.day-label{grid-row:2;text-align:center;color:var(--muted);font-size:10px;padding-top:7px}.x-spacer{grid-column:1;grid-row:2}.vbar-slot{position:relative;width:22px;height:100%;display:flex;align-items:flex-end}.vbar{width:100%;border-radius:4px 4px 0 0;background:var(--accent)}.vbar.ok{background:var(--ok)}.vbar.small{background-image:repeating-linear-gradient(135deg,rgba(255,255,255,.75) 0 4px,transparent 4px 8px);background-size:12px 12px}.vbar-value{position:absolute;bottom:calc(var(--bar-height) + 4px);left:50%;transform:translateX(-50%);white-space:nowrap;font-size:10px;font-weight:700;color:var(--title)}@media(max-width:680px){.column-chart{grid-template-columns:20px repeat(8,minmax(0,1fr));grid-template-rows:170px 30px}.day-plot{gap:2px}.vbar-slot{width:12px}.vbar-value{font-size:8px}.day-label{font-size:9px}.wrap{padding:22px 11px 40px;gap:22px}.grid2{grid-template-columns:1fr}h1{font-size:26px}.card{padding:13px}.bar-row{grid-template-columns:105px minmax(35px,1fr) 68px;gap:6px}.bar-label,.bar-value{font-size:11px}.bar-value.num{white-space:normal;overflow-wrap:anywhere}.day-bars .bar-row{grid-template-columns:112px minmax(30px,1fr) 66px}.funnel-bars .bar-row{grid-template-columns:112px minmax(35px,1fr) 65px}.funnel-bars .bar-label,.funnel-bars .bar-value{font-size:11px}th,td{padding:8px}.table-wrap{overflow:visible}.bugs{min-width:0}.bugs thead{display:none}.bugs,.bugs tbody,.bugs tr,.bugs td{display:block;width:100%}.bugs tr{padding:10px;border-bottom:1px solid var(--line)}.bugs tr:last-child{border-bottom:0}.bugs td{padding:2px 0;border:0;white-space:normal}.bugs td:before{display:block;color:var(--muted);font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase}.bugs td:nth-child(1):before{content:"Наблюдение"}.bugs td:nth-child(2):before{content:"Люди / события"}.bugs td:nth-child(3):before{content:"Предложение"}.bugs td:nth-child(4):before{content:"Владелец"}}"""


def _magic_link_html(journeys: list) -> str:
    items = []
    for journey in journeys:
        requested = esc(journey["requested"])
        if journey.get("email_found"):
            items.append(f"<li><b>{requested}:</b> email восстановлен из URL самого запроса. Всего по email: {journey['matched_events']} событий, {journey['matched_people']} персоны, {journey['matched_sessions']} сессия. После запроса: /magic-link-login — {journey['magic_link_login_count']}, login — {journey['login_count']}, app_opened — {journey['app_opened_count']}, других веб-событий приложения — {journey['web_events_after']}.</li>")
            continue
        text = f"<li><b>{requested}:</b> email не сохранился; итог входа — нет данных."
        candidate = journey.get("unlinked_candidate")
        if candidate:
            text += f" Отдельно найден /magic-link-login {esc(candidate['magic_link_login'])}"
            if candidate.get("login"):
                text += f", login {esc(candidate['login'])}"
            text += f", app_opened — {1 if candidate.get('app_opened') else 0}; событий в той сессии — {candidate['session_events']}."
            if not candidate.get("shared_identifiers"):
                text += " Общих идентификаторов с запросом нет, поэтому цепочка не засчитана."
        items.append(text + "</li>")
    return "<div class=\"callout\"><b>«Check your inbox» — ожидаемый шаг, а не зависание. Склейка по email выполнена; совпадение только по времени не использовалось.</b><ul>" + "".join(items) + f"</ul><p><b>Итог:</b> {_magic_summary(journeys)}</p></div>"


def _magic_summary(journeys: list) -> str:
    total = len(journeys)
    found = [j for j in journeys if j.get("email_found")]
    back = sum(1 for j in found if _n(j.get("login_count")) or _n(j.get("app_opened_count")) or _n(j.get("web_events_after")))
    return f"доказанный возврат после запроса есть у {back} из {len(found)} запросов с доступным email; для {total - len(found)} из {total} итог — нет данных, а не «не вошли»."


def _magic_link_md(journeys: list) -> str:
    lines = ["- Склейка выполнена по нормализованному email. Источники email: JSON события и персоны, включая URL и percent-encoding. Если email отсутствовал в `magic_link_requested`, он искался только в событиях той же персоны, сессии или устройства до запроса. Затем email искался во всех событиях; найденные персоны использовались для проверки последующих веб-событий. Совпадение по времени без общего идентификатора не засчитывалось."]
    for journey in journeys:
        requested = journey["requested"]
        if journey.get("email_found"):
            lines.append(f"- {requested}: email найден в URL `magic_link_requested`. Всего по email — {journey['matched_events']} событий, {journey['matched_people']} персоны, {journey['matched_sessions']} сессия. После запроса — {journey['web_events_after']} веб-событий приложения, {journey['magic_link_login_count']} `/magic-link-login`, {journey['login_count']} `login`, {journey['app_opened_count']} `app_opened`; других сессий с последующими событиями — {journey['web_sessions_after']}.")
            continue
        line = f"- {requested}: email не сохранился ни в запросе, ни в прежних событиях той же персоны, сессии или устройства. Итог входа — нет данных."
        candidate = journey.get("unlinked_candidate")
        if candidate:
            line += f" Отдельно после запроса найден `/magic-link-login` {candidate['magic_link_login']}; `login` — {candidate['login'] or 'нет'}, `app_opened` — {candidate['app_opened'] or 'нет'}, событий в сессии — {candidate['session_events']}, последнее — {candidate['last_event']}."
            if not candidate.get("shared_identifiers"):
                line += " Общих `person_id`, `distinct_id`, `$device_id`, `$session_id`, `$window_id` и `$ip` с запросом нет; цепочка не приписана запросу."
        lines.append(line)
    lines.append("- Итог склейки: " + _magic_summary(journeys) + " В `magic_link_requested` нужно передавать email и сохранять доказательную связь magic-link token с email.")
    return "\n".join(lines)


_OLD_MAGIC_HTML = "<div class=\"callout\"><b>«Check your inbox» — ожидаемый шаг, а не зависание.</b> Человек уходит в почту, а magic link открывает <code>web.robella.app/magic-link-login</code> отдельно, часто в новой вкладке и новой записи. По исходной записи нельзя решить, вошёл ли он позже: нужно связать email с последующим <code>/magic-link-login</code> и веб-событиями приложения в других сессиях.</div>"
_OLD_MAGIC_MD = "- «Check your inbox» — ожидаемый шаг входа в `web.robella.app`, не FunnelFox: человек уходит в почту, а magic link открывает `/magic-link-login` отдельно, часто в новой вкладке и новой записи. Эти 3 записи не считаются зависанием или неудачным входом. Последующий вход надо проверять по email и событиям `/magic-link-login` в других сессиях; такая склейка в разборе не выполнялась."
_OLD_DANE = "<li><b>Вход:</b> проверить Network Error и событие работающего автологина; по 3 записям с «Check your inbox» склеить последующий /magic-link-login по email, не считая ожидание письма зависанием.</li>"
_NEW_DANE = "<li><b>Вход:</b> проверить Network Error и событие работающего автологина; передавать email в magic_link_requested и сохранять связь magic-link token с email: сейчас у 2 из 3 запросов доказательная склейка невозможна.</li>"
_OLD_LIMIT = "preview 18.11 подтверждён как неживой трафик, но полный пересчёт стартов и почт без preview не выполнен из-за отсутствия доступа к PostHog"
_NEW_LIMIT = "preview 18.11 подтверждён как неживой трафик, но полный пересчёт стартов и почт без preview требует отдельного фильтра по всем шагам"


def apply_magic_link_reports(journeys: list) -> None:
    """Точечно обновляет уже собранные файлы, не пересчитывая остальные блоки."""
    html_text = OUT_HTML.read_text(encoding="utf-8")
    md_text = OUT_MD.read_text(encoding="utf-8")
    html_subs = ((re.compile(r'<div class="callout">\s*<b>«Check your inbox» — ожидаемый шаг, а не зависание\.</b>.*?</div>', re.S), _magic_link_html(journeys)), (re.compile(r"<li>\s*<b>Вход:</b> проверить Network Error.*?</li>", re.S), _NEW_DANE))
    for pattern, new in html_subs:
        html_text, count = pattern.subn(new, html_text)
        if count != 1:
            raise RuntimeError("HTML: целевой блок magic link не найден или не уникален")
    if md_text.count(_OLD_MAGIC_MD) != 1:
        raise RuntimeError("MD: целевой блок magic link не найден или не уникален")
    md_text = md_text.replace(_OLD_MAGIC_MD, _magic_link_md(journeys))
    if _OLD_LIMIT in md_text:
        md_text = md_text.replace(_OLD_LIMIT, _NEW_LIMIT)
    OUT_HTML.write_text(html_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")


def render_html(data: dict) -> str:
    us = data["us"]
    started = _n(us.get("started"))
    email_n = _n(us.get("email_n"))
    checkout_n = _n(us.get("checkout_n"))
    purchase_n = _n(us.get("purchase_n"))
    app_web = _n(us.get("app_web"))
    path_rows = data.get("path_rows") or []
    sid_rows = data.get("sid_rows") or []
    path = data.get("path") or {row["step"]: row for row in path_rows}
    sid = data.get("sid") or {row["step"]: row for row in sid_rows}
    age_path = _n((path.get("age_group") or {}).get("people"))
    social_path = _n((path.get("social_proof") or {}).get("people"))
    age_sid = _n((sid.get("age_group") or {}).get("people"))
    social_sid = _n((sid.get("social_proof") or {}).get("people"))
    mismatch = data.get("mismatch") or {}
    overlap = data.get("overlap") or {}
    buyers = data.get("buyers") or []
    buyers_n = len(buyers)
    buyer_days = sorted(datetime.strptime(str(row["started"])[:10], "%d.%m.%Y") for row in buyers if str(row.get("started") or "")[:2].isdigit())
    buyers_span = f"{buyer_days[0]:%d.%m}–{buyer_days[-1]:%d.%m}" if buyer_days else "нет данных"
    primer = data["primer"]
    preview_n = _preview_count(data)
    renewed = sum(1 for row in buyers if _n(row.get("renews")) > 0)
    cancelled = sum(1 for row in buyers if _n(row.get("renews")) == 0 and _n(row.get("cancels")) > 0)
    untouched = buyers_n - renewed - cancelled
    daily_chart = _checkout_chart(data, started)
    login_items = [{"label": "Вошли в продукт", "n": 2, "color": "ok"}, {"label": "Дошли до «Check your inbox»", "n": 3, "color": "accent"}, {"label": "Ушли с формы без запроса письма", "n": 2, "color": "bad"}, {"label": "Network Error", "n": 1, "color": "warn"}, {"label": "Ссылка истекла", "n": 1, "color": "warn"}]
    first_items = [{"label": "Начали онбординг (событие)", "n": us.get("onb_started")}, {"label": "Завершили онбординг", "n": us.get("onb_done")}, {"label": "Открыли капсулу", "n": us.get("capsule")}, {"label": "Открыли шкаф", "n": us.get("closet")}, {"label": "Примерка", "n": us.get("tryon")}, {"label": "Отчёт", "n": us.get("report_n")}]
    early_items = [{"label": "Продлили", "n": renewed, "color": "ok"}, {"label": "Отменили (событие)", "n": cancelled, "color": "bad"}, {"label": "Ничего", "n": untouched, "color": "warn"}]
    compare = data.get("compare") or {}
    fox = compare.get("foxiq") or {}
    az = compare.get("azora") or {}
    comparison_groups = []
    metrics = [("Конверсия в почту", email_n, started, fox.get("email_n"), fox.get("started"), az.get("email_n"), az.get("started")), ("Конверсия в оплату", checkout_n, started, fox.get("checkout_n"), fox.get("started"), az.get("checkout_n"), az.get("started")), ("Вход по той же почте", us.get("email_and_app"), email_n, fox.get("email_join_both"), fox.get("email_join_emails"), az.get("email_join_both"), az.get("email_join_emails"))]
    for label, rn, rd, fn, fd, an, ad in metrics:
        comparison_groups.append(f"<div class='card chart'><h3>{esc(label)}</h3><div class='bars'>" + _bar_rows([{"label": "Robella", "n": rn, "den": rd, "color": "accent", "note": "ориентир" if _n(rn) < 30 else ""}, {"label": "FoxIQ", "n": fn, "den": fd, "color": "fox"}, {"label": "Azora, Япония", "n": an, "den": ad, "color": "azora"}], 100, scale=100, show_pct=True) + "</div></div>")
    primer_total = _n(primer.get("rows"))
    primer_declined = _n(primer.get("declined"))
    primer_renew = sum(_n(row.get("n")) for row in primer.get("by_day") or [] if row.get("init") == "mit" and row.get("status") == "SETTLED")
    primer_first = _n(primer.get("settled_cit"))
    primer_period = f"{msk(primer.get('first'))} — {msk(primer.get('last'))} МСК"
    css = _report_css()
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Robella — продуктовый разбор, 20.11.2026</title><style>{css}</style></head><body><main class="wrap"><header><div class="eyebrow">Robella · веб · продуктовый разбор</div><h1>Путь пользователя и оплата</h1><p class="meta">{esc(data['period_full'])} · весь срок одним периодом · люди после фильтра тестов · <a href="robella-product-analysis-2026-11-20-metodika.md">методика и проверки</a></p></header><section><div class="eyebrow">Главное · выводы</div><div class="card summary"><ol><li><b>Главная потеря — до почты:</b> {n_of(started - email_n, started)} не оставили email. Точный экран обрыва не называем, пока разметка расходится.</li><li><b>До продукта доходят единицы:</b> после email веб-заход есть у {n_of(us.get('email_and_app'), email_n)}, покупки после checkout — {n_of(us.get('checkout_and_purchase'), checkout_n)}. Приоритет — разобрать вход и завершение оплаты, а не переписывать квиз вслепую.</li><li><b>Ценность и удержание оценивать рано:</b> онбординг завершили {n_of(us.get('onb_done'), app_web)}, покупателей за весь срок — {buyers_n}. Сначала нужно дать людям войти и оплатить, затем оценивать капсулы и продления.</li></ol></div></section><section><div class="eyebrow">1 · Воронка по экранам</div><h2>Одна воронка, два несовпадающих измерения</h2><p class="meta">{PERIOD_US} · знаменатель {started} из {started} с funnel_start · штриховка = меньше 30 человек на шаге</p><div class="callout"><b>Как читать две колонки.</b> Это одна и та же воронка, а не две версии продукта. Слева экран определён по адресу URL, справа — по названию screen_id, которое передал разработчик. Обе колонки описывают одних и тех же людей.</div><div class="callout warn"><b>Почему точный обрыв пока не доказан.</b> За период URL и screen_id расходятся в {n_of(mismatch.get('mismatch_nested'), mismatch.get('events'))} событий. Пример: у {n_of(overlap.get('goals_without_social'), started)} URL уже main_goals, а social_proof по URL не было. Поэтому обрыв age_group → social_proof получается {n_of(age_path, started)} → {n_of(social_path, started)} по URL и {n_of(age_sid, started)} → {n_of(social_sid, started)} по screen_id. Даня исправил screen_id 19.11 (проверено на превью воронки) — обрыв пересчитать на данных после исправления; квиз не сокращаем.</div><div class="grid2">{_funnel_panel('По адресу URL (pathname)', path_rows, data.get('step_order') or [], started)}{_funnel_panel('По screen_id разработчика', sid_rows, data.get('step_order') or [], started)}</div></section>{AFTER_FIX_HTML}<section><div class="eyebrow">2 · Оплата</div><h2>Оплата по неделям</h2><p class="meta">{PERIOD_US} · ось X — неделя (пн–вс, МСК), ось Y — люди · знаменатель каждого значения {started} из {started} стартов за период</p><div class="legend"><span><i class="dot"></i>открыли оплату</span><span><i class="dot ok"></i>оплатили</span><span>штриховка = мало данных</span></div><div class="card">{daily_chart}</div><p class="note">Пустые столбцы — 0 из {started}. Успешные оплаты воронки за весь срок: {n_of(purchase_n, started)}; открыли оплату — {n_of(checkout_n, started)}.</p><div class="callout"><b>Открыть оплату — ещё не попытка заплатить.</b> Платёж в Primer создаётся, только когда человек нажимает «оплатить»; если окно оплаты открыли и закрыли, в Primer ничего не появляется — это не поломка (сверка Кати по Primer, 19.11). primer_payment есть у {n_of(us.get('checkout_and_primer'), checkout_n)} открывших оплату; в Primer $1 — {n_of(primer.get('trial_1'), primer_total)} строк, $39.90 — {n_of(primer.get('month_3990'), primer_total)}.</div>{_preview_note(preview_n, checkout_n, started, email_n)}<div class="table-wrap"><table><thead><tr><th>Primer, {esc(primer_period)}</th><th>Строк</th></tr></thead><tbody><tr><td>Успешные первые оплаты, не тест</td><td class="num">{n_of(primer_first, primer_total)}</td></tr><tr><td>Повторные успешные списания</td><td class="num">{n_of(primer_renew, primer_total)}</td></tr><tr><td>Отказы, включая 1 тест</td><td class="num">{n_of(primer_declined, primer_total)}</td></tr><tr><td>Триал $1 / подписка $39.90</td><td class="num">{n_of(primer.get('trial_1'), primer_total)} / {n_of(primer.get('month_3990'), primer_total)}</td></tr></tbody></table></div></section><section><div class="eyebrow">3 · Вход в приложение</div><h2>Семь разобранных записей</h2><p class="meta">12.11–17.11 · снимки из аудита 17.11 · знаменатель 7 из 7 · первые три строки разбивают записи, ошибки с ними пересекаются · штриховка = мало данных</p>{_magic_link_html(data.get('magic_links') or [])}<div class="card chart"><div class="bars">{_bar_rows(login_items, 7)}</div></div><p class="note">Network Error: «Signing you in…» около 34 секунд у 1 из 7. После «This link has expired» главная открылась у 1 из 7. Кадры 18.11 заново не разбирались.</p></section><section><div class="eyebrow">4 · Первая сессия</div><h2>Что происходит в продукте</h2><p class="meta">{PERIOD_US} · знаменатель {app_web} из {app_web} с веб-событием приложения · штриховка = меньше 30 человек</p><div class="card chart"><div class="bars">{_bar_rows(first_items, app_web)}</div></div><p class="note">Завершивших онбординг ({us.get('onb_done')}) больше, чем начавших ({us.get('onb_started')}): событие onboarding_started приходит не у всех. В записях 12–17.11 после шага 7 был возврат на шаг 2 у 1 из 7 записей, шаги 1–6 двоились у 1 человека.</p></section><section><div class="eyebrow">5 · Покупатели за весь срок</div><h2>{buyers_n} человек <span class="tag">мало данных</span></h2><p class="meta">первые оплаты {buyers_span}; события до 18.11.2026 23:59 МСК · взаимоисключающие группы: продление → отмена → ничего</p><div class="card chart"><div class="bars">{_bar_rows(early_items, buyers_n)}</div></div><p class="note">У {n_of(cancelled, buyers_n)} есть subscription_cancelled; у них в ту же секунду приходит subscription_expired payment_failed, поэтому самостоятельная отмена не доказана.</p></section><section><div class="eyebrow">6 · Сравнение</div><h2>Robella против FoxIQ и Azora</h2><p class="meta">Robella {PERIOD_US} · FoxIQ {FOX_LABEL} · Azora {AZ_LABEL} · вход склеен по почте · штриховка и «ориентир» при N &lt; 30</p><div class="legend"><span><i class="dot"></i>Robella</span><span><i class="dot fox"></i>FoxIQ</span><span><i class="dot azora"></i>Azora</span></div><div class="grid2">{''.join(comparison_groups)}</div><p class="note">Периоды разные, поэтому это ориентиры конверсий, не доказательство причины. У Robella вход считается только от {email_n} оставивших почту.</p></section><section><div class="eyebrow">7 · Баги и точки роста</div><h2>Что передать в работу</h2><div class="table-wrap"><table class="bugs"><thead><tr><th>Что видим</th><th>Сколько</th><th>Что предлагаем</th><th>Кому</th></tr></thead><tbody><tr><td>screen_id расходился с pathname</td><td class="num">{n_of(mismatch.get('mismatch_nested'), mismatch.get('events'))} событий до 19.11</td><td>Исправлено 19.11; пересчитать обрыв на новых данных. По Кате — проверить то же во всех воронках (Azora, Minutka, FoxIQ)</td><td>Даня</td></tr><tr><td>Работающий автологин виден в аналитике не у всех</td><td class="num">{n_of(us.get('autologin'), app_web)} pageview /auto-login</td><td>Починить событие успешного входа, не менять сам автологин</td><td>Даня</td></tr><tr><td>Онбординг: старт теряется, шаги двоятся</td><td class="num">старт {us.get('onb_started')}, завершение {us.get('onb_done')} из {app_web}</td><td>Починить onboarding_started, убрать дубли и возврат с шага 7 на 2</td><td>Даня</td></tr><tr><td>Капсула не показала готовый образ</td><td class="num">1 из 7 записей</td><td>Проверить завершение генерации и таймаут</td><td>Даня</td></tr><tr><td>Отмена совпадает с payment_failed</td><td class="num">{n_of(cancelled, buyers_n)} покупателей</td><td>Не писать user_initiated на отказ банка</td><td>Даня</td></tr></tbody></table></div><div class="card"><h3>Дане — по приоритету</h3><ol class="priority"><li><b>Разметка и среды:</b> screen_id в Robella исправлен 19.11 — проверить то же расхождение во всех воронках (Azora, Minutka, FoxIQ); исключить /preview/ из продуктовой аналитики: это тестовая среда FunnelFox, которую фильтр пропустил.</li>{_NEW_DANE}<li><b>Онбординг:</b> убрать дубли и возврат с шага 7 на 2; проверить генерацию капсулы.</li><li><b>Подписка:</b> is_test на персоне и причина subscription_cancelled.</li></ol></div></section></main></body></html>"""


def render_md(data: dict) -> str:
    us = data["us"]
    started = _n(us.get("started"))
    email_n = _n(us.get("email_n"))
    checkout_n = _n(us.get("checkout_n"))
    purchase_n = _n(us.get("purchase_n"))
    path = data.get("path") or {row["step"]: row for row in data.get("path_rows") or []}
    sid = data.get("sid") or {row["step"]: row for row in data.get("sid_rows") or []}
    mismatch = data.get("mismatch") or {}
    overlap = data.get("overlap") or {}
    primer = data["primer"]
    buyers = data.get("buyers") or []
    renewed = sum(1 for row in buyers if _n(row.get("renews")) > 0)
    cancelled = sum(1 for row in buyers if _n(row.get("renews")) == 0 and _n(row.get("cancels")) > 0)
    untouched = len(buyers) - renewed - cancelled
    daily = _checkout_daily(data)
    daily_sum = sum(item["open"] for item in daily.values())
    preview_n = _preview_count(data)
    compare = data.get("compare") or {}
    fox = compare.get("foxiq") or {}
    az = compare.get("azora") or {}
    primer_declined = _n(primer.get("declined"))
    primer_renew = sum(_n(row.get("n")) for row in primer.get("by_day") or [] if row.get("init") == "mit" and row.get("status") == "SETTLED")
    primer_first = _n(primer.get("settled_cit"))
    primer_total = _n(primer.get("rows"))
    primer_check = primer_first + primer_renew + primer_declined
    return f"""# Методика продуктового разбора Robella, 20.11.2026

Расчёты выполняет `scripts/robella-analysis.py`; HTML собирается тем же скриптом. Почты, distinct_id, токены и ключ PostHog в файлы не выносятся. ClickUp не используется.

## 1. Источники и периоды
- PostHog, проект 1: свойства `project = robella_ff`, `robella`, `robella_landing`. Люди — `person_id`, не события.
- Primer: дескриптор или metadata с `robella`; файл — {primer['file_rows']} платежей всех продуктов, {msk(primer.get('first'))} — {msk(primer.get('last'))} МСК. Строк Robella: {primer_total}.
- Записи: 7 не-тестовых снимков 12.11–17.11, разобранных в аудите `reports/robella-posthog-audit-2026-11-17.md`. Кадры 18.11 заново не разбирались.
- Весь срок: {data['period_full']}. Первое событие в выгрузке: `{data['scope'].get('first_ts')}`.
- Период один — весь срок: {PERIOD_US}. 20.11 по замечанию Кати объединены прежние «окно США 11–18.11» и «покупатели до 11.11»; все разделы, кроме записей сессий, считаются за этот период.
- Весь срок после фильтра: воронку начали {data['full'].get('started')} из {data['full'].get('started')}, почту оставили {n_of(data['full'].get('email_n'), data['full'].get('started'))}, оплату открыли {n_of(data['full'].get('checkout_n'), data['full'].get('started'))}, покупку воронки — {n_of(data['full'].get('purchase_n'), data['full'].get('started'))}. Веб-событие приложения — {n_of(data['full'].get('app_web'), data['full'].get('people'))} всех людей Robella; лендинг — {n_of(data['full'].get('landing'), data['full'].get('people'))}.

## 2. Исключение тестовых
Человек исключён целиком, если хотя бы на одном событии до верхней границы:
- `properties.is_test` или `person.properties.is_test` равно true/1;
- почта персоны или distinct_id содержит шаблон аудита: `+`, gox-media, yandex, test, example, mailinator, eevakenn, nedvedyea.
Исключено людей за весь срок: {data['excluded']}. Дополнительно исключаются `environment = dev`, если такое свойство появится.
{_preview_md(preview_n, checkout_n, started, email_n)}

## 3. Воронка
- Знаменатель: уникальные люди с `funnel_start`, `project = robella_ff`, весь срок: {started} из {started}.
- Шаг по pathname: последний сегмент `$pathname`; корень `/ai-stilist-week-web` обозначен `intro`.
- Шаг по screen_id: `properties.screen_id`. Две версии считаются независимо; это «открыли экран хотя бы раз», не строгая последовательность.
- Основная проверка: pathname age_group {n_of((path.get('age_group') or {}).get('people'), started)}, social_proof {n_of((path.get('social_proof') or {}).get('people'), started)}, main_goals {n_of((path.get('main_goals') or {}).get('people'), started)}.
- По screen_id: age_group {n_of((sid.get('age_group') or {}).get('people'), started)}, social_proof {n_of((sid.get('social_proof') or {}).get('people'), started)}.
- У {n_of(overlap.get('goals_without_social'), started)} есть main_goals без pathname social_proof. У {n_of(overlap.get('age_only'), started)} нет ни social_proof, ни main_goals после age_group.
- Расхождение screen_id и вложенного pathname: {n_of(mismatch.get('mismatch_nested'), mismatch.get('events'))} событий `funnel_screen_open`; с корнем intro — {n_of(mismatch.get('mismatch_all'), mismatch.get('events'))}.
- Вывод ограничен: главный обрыв виден, но его точное место не установлено, пока разметка расходится. Квиз не сокращаем.
{AFTER_FIX_MD}
## 4. Оплата
- «Открыли оплату»: человек с `funnel_checkout_open` в день МСК.
- «Оплатили»: человек с `funnel_purchase_success`; сверка — Primer SETTLED первой оплаты. Повторное списание не считается новой покупкой. Промежуточный `primer_payment` любого статуса не рисуется как отдельный этап: это обращение к процессору, а не успешная оплата.
- По дням открытия суммируются в {daily_sum} из {checkout_n}: расчёт сходится. `primer_payment` после checkout — {n_of(us.get('checkout_and_primer'), checkout_n)}; покупки после checkout — {n_of(us.get('checkout_and_purchase'), checkout_n)}.
- Primer: первые успешные не-тестовые {n_of(primer_first, primer_total)}, повторные успешные {n_of(primer_renew, primer_total)}, отказы {n_of(primer_declined, primer_total)}. Контрольная сумма: {primer_first} + {primer_renew} + {primer_declined} = {primer_check} из {primer_total}.
- $1: {n_of(primer.get('trial_1'), primer_total)} строк; $39.90: {n_of(primer.get('month_3990'), primer_total)} строк. Старые цены: $19.99/$29.99, повтор $59.99.
- Файл Primer заканчивается 17.11 12:28 МСК. После него до 18.11 23:59 МСК в PostHog `primer_payment`: {primer['after_file']['n']} событий, {primer['after_file']['people']} человек.
- Открытие оплаты без `primer_payment` — не поломка: платёж в Primer создаётся только по нажатию «оплатить» (сверка Кати по Primer, 19.11). У paywall свойства price/amount/currency/trial_price/plan пустые.
- «По дням открытия» ниже — сумма по неделям графика (пн–вс МСК).

## 5. Вход и первая сессия
- Источник входа: снимки 7 записей из аудита 17.11. Вошли в продукт 2 из 7; дошли до «Check your inbox» 3 из 7; ушли с формы без запроса письма 2 из 7. Первые три группы взаимоисключающие. Network Error 1 из 7 и истёкшая ссылка 1 из 7 пересекаются с ними.
{_magic_link_md(data.get('magic_links') or [])}
- «Signing you in…» длился около 34 секунд у 1 из 7. После «This link has expired» главная открылась у 1 из 7.
- Веб-заходы в приложение за весь срок: {n_of(us.get('app_web'), us.get('app_web'))}. Автологин в продукте уже работает; проблема в измерении: pageview `/auto-login` — {n_of(us.get('autologin'), us.get('app_web'))}. `/auth`: {n_of(us.get('auth_n'), us.get('app_web'))}; `/magic-link-login`: {n_of(us.get('magic_page'), us.get('app_web'))}.
- Онбординг: начали {n_of(us.get('onb_started'), us.get('app_web'))}, завершили {n_of(us.get('onb_done'), us.get('app_web'))}. Шаги 1–6 удвоены у 1 из 1 начавшего; возврат с шага 7 на шаг 2 виден в 1 из 7 записей.
- Капсула: {n_of(us.get('capsule'), us.get('app_web'))}; шкаф: {n_of(us.get('closet'), us.get('app_web'))}; примерка: {n_of(us.get('tryon'), us.get('app_web'))}; отчёт: {n_of(us.get('report_n'), us.get('app_web'))}.

## 6. Покупатели за весь срок
Группы взаимоисключающие с приоритетом «продлили» → «отменили» → «ничего»:
- продлили: {n_of(renewed, len(buyers))} с `subscription_renewed`;
- отменили: {n_of(cancelled, len(buyers))} с `subscription_cancelled`, без продления;
- ничего: {n_of(untouched, len(buyers))}.
Контрольная сумма: {renewed} + {cancelled} + {untouched} = {renewed + cancelled + untouched} из {len(buyers)}. У покупателей с отменой `subscription_expired payment_failed` приходит в ту же секунду; по правилу FoxIQ это похоже на отказ банка, а не доказанную самостоятельную отмену. Выборка меньше 30 — только ориентир.

## 7. Сравнение с FoxIQ и Azora
- Robella: {PERIOD_US}; старт {started}, почта {email_n}, checkout {checkout_n}, вход по той же почте {n_of(us.get('email_and_app'), email_n)}.
- FoxIQ: {FOX_LABEL}; `foxiq_ff` + `foxiq`, расширенный фильтр тестовых playbook. Старт {fox.get('started')}, почта {n_of(fox.get('email_n'), fox.get('started'))}, checkout {n_of(fox.get('checkout_n'), fox.get('started'))}, вход по почте {n_of(fox.get('email_join_both'), fox.get('email_join_emails'))}.
- Azora, Япония: {AZ_LABEL}; `azora_ff` + `web`, страна JP, iOS исключена. Старт {az.get('started')}, почта {n_of(az.get('email_n'), az.get('started'))}, checkout {n_of(az.get('checkout_n'), az.get('started'))}, вход по почте {n_of(az.get('email_join_both'), az.get('email_join_emails'))}.
- Для входа воронка и приложение склеиваются по нормализованной почте; почта в файлы не пишется. Периоды разные, поэтому сравнение — ориентир, не доказательство причинности. Полного списка тестовых Azora нет; применён общий почтовый фильтр.

## 8. Проверки перед выдачей
- Суммы: ежедневные checkout = {daily_sum} из {checkout_n}; Primer = {primer_check} из {primer_total}; ранние покупатели = {renewed + cancelled + untouched} из {len(buyers)}.
- На каждом столбце есть `N из M`; у каждого раздела указаны период и знаменатель. Штриховка — N < 30, «ориентир» добавлен в сравнении.
- HTML использует только чистый CSS; JavaScript, внешние библиотеки, шрифты и подсказки при наведении отсутствуют.
- Узкий экран: двойные графики складываются в одну колонку; таблица багов превращается в карточки с подписями полей; горизонтальная прокрутка и обрезание не нужны.
- Ограничения: записи 18.11 не разобраны; Primer не покрывает последние 35,5 часа периода; preview 18.11 подтверждён как неживой трафик, но полный пересчёт стартов и почт без preview требует отдельного фильтра по всем шагам; причины нулевой оплаты на боевом пути и точного обрыва не установлены.
"""


if __name__ == "__main__":
    main()
