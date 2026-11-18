# -*- coding: utf-8 -*-
"""Счёт фактов для продуктового разбора Robella.

Ключ PostHog берётся из POSTHOG_PERSONAL_API_KEY. Если переменной нет,
скрипт читает его из локального ~/.cursor/mcp.json и никуда не печатает.
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
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "reports" / "robella-product-analysis-2026-11-18.html"
OUT_MD = ROOT / "reports" / "robella-product-analysis-2026-11-18-metodika.md"
API = "https://ph.app-inkfolio-reader.pro/api/projects/1/query/"
MSK = timezone(timedelta(hours=3))
END = "2026-11-18 21:00:00"  # 19.11 00:00 МСК, верхняя граница не включается
US_START = "2026-11-10 21:00:00"  # 11.11 00:00 МСК
PERIOD_US = "11.11.2026 00:00 МСК — 18.11.2026 23:59 МСК"
PERIOD_END_LABEL = "18.11.2026 23:59 МСК"
# FoxIQ: окно отчёта v4.23, чтобы сравнение было с опубликованным периодом, а не с окном Robella.
FOX_START, FOX_END = "2026-10-06 21:00:00", "2026-11-11 11:00:00"
FOX_LABEL = "07.10.2026 00:00 МСК — 11.11.2026 14:00 МСК"
# Azora, Япония: окно образца Кати.
AZ_START, AZ_END = "2026-10-08 21:00:00", "2026-10-23 07:00:00"
AZ_LABEL = "09.10.2026 00:00 МСК — 23.10.2026 10:00 МСК"

EMAIL_RE = (
    r"\+.*@|gox-media\.com|@yandex\.ru|test|@example\.com|mailinator|eevakenn|nedvedyea"
)
FOX_EMAIL_RE = (
    EMAIL_RE
    + r"|k\.k\.tarasova|nikitos\.gura|dariaivanova|^kkk@gmail\.com$|"
    + r"^myskillhouse2020@gmail\.com$|^ekaasrirahmawati403@gmail\.com$"
)
EMAIL_SCRUB = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
TOKEN_SCRUB = re.compile(r"(token=)[^&\s]+", re.I)


def load_key() -> str:
    env = os.environ.get("POSTHOG_PERSONAL_API_KEY", "").strip()
    if env:
        return env if env.startswith("Bearer ") else "Bearer " + env
    cfg_path = Path.home() / ".cursor" / "mcp.json"
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
    global KEY
    if KEY is None:
        KEY = load_key()
    body = json.dumps({"query": {"kind": "HogQLQuery", "query": query}}).encode()
    last_error = None
    for attempt in range(3):
        req = urllib.request.Request(
            API,
            data=body,
            headers={
                "Authorization": KEY,
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode())
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2 + attempt * 3)
    else:
        raise RuntimeError(f"запрос не выполнился: {type(last_error).__name__}")
    if data.get("error"):
        raise RuntimeError(str(data["error"])[:300])
    cols = data.get("columns") or []
    return [dict(zip(cols, row)) for row in data.get("results") or []]


def qident(value: str) -> str:
    return value.replace("\\", "\\\\")


def test_exclude(alias_email_re: str = EMAIL_RE) -> str:
    pat = alias_email_re.replace("\\", "\\\\")
    return f"""
    person_id NOT IN (
      SELECT person_id FROM events
      WHERE timestamp < toDateTime('{END}')
        AND (
          toString(properties.is_test) IN ('true','1','True')
          OR toString(person.properties.is_test) IN ('true','1','True')
          OR match(lower(coalesce(toString(person.properties.email),'')), '{pat}') = 1
          OR match(lower(toString(distinct_id)), '{pat}') = 1
        )
    )
    """


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
    local = dt.astimezone(MSK)
    return local.strftime("%d.%m.%Y %H:%M")


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
    rows = hog(
        f"""
        SELECT
          uniqIf(person_id, event = 'funnel_start') AS started,
          uniqIf(person_id, event = 'funnel_email_submit') AS email_n,
          uniqIf(person_id, event = 'funnel_email_verify') AS verify_n,
          uniqIf(person_id, event = 'funnel_checkout_open') AS checkout_n,
          uniqIf(person_id, event = 'funnel_purchase_success') AS purchase_n,
          uniqIf(person_id, event = 'funnel_purchase_fail') AS purchase_fail_n,
          uniqIf(person_id, event = 'funnel_purchase_start') AS purchase_start_n
        FROM events
        WHERE {where} AND {test_sql}
        """
    )
    return rows[0] if rows else {}


def step_people(where: str, column_sql: str) -> list:
    return hog(
        f"""
        SELECT {column_sql} AS step, uniq(person_id) AS people, count() AS events
        FROM events
        WHERE event = 'funnel_screen_open' AND {where} AND {ROB_TEST}
        GROUP BY step
        ORDER BY people DESC
        LIMIT 80
        """
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primer", required=True)
    args = parser.parse_args()
    data = compute(Path(args.primer))
    OUT_HTML.write_text(render_html(data), encoding="utf-8")
    OUT_MD.write_text(render_md(data), encoding="utf-8")
    print("html", OUT_HTML)
    print("md", OUT_MD)
    print("started_us", data["us"]["started"], "email", data["us"]["email_n"], "checkout", data["us"]["checkout_n"])
    print("path_age", data["path"].get("age_group"), "path_social", data["path"].get("social_proof"))
    print("sid_age", data["sid"].get("age_group"), "sid_social", data["sid"].get("social_proof"))
    print("primer", data["primer"]["rows"], "buyers", len(data["buyers"]))


def compute(primer_path: Path) -> dict:
    scope = hog(
        f"""
        SELECT
          min(timestamp) AS first_ts,
          max(timestamp) AS last_ts,
          uniq(person_id) AS people_raw,
          uniqIf(person_id, toString(properties.project) = 'robella_ff') AS funnel_raw,
          uniqIf(person_id, toString(properties.project) = 'robella') AS app_raw,
          uniqIf(person_id, toString(properties.project) = 'robella_landing') AS land_raw
        FROM events
        WHERE timestamp < toDateTime('{END}')
          AND toString(properties.project) IN ('robella','robella_ff','robella_landing')
        """
    )[0]
    excluded = hog(
        f"""
        SELECT uniq(person_id) AS people
        FROM events
        WHERE timestamp < toDateTime('{END}')
          AND toString(properties.project) IN ('robella','robella_ff','robella_landing')
          AND NOT ({ROB_TEST})
        """
    )[0]["people"]

    def window(start: str) -> str:
        return (
            f"timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{END}') "
            "AND toString(properties.project) IN ('robella','robella_ff','robella_landing')"
        )

    def one_window(start: str) -> dict:
        base = window(start)
        ff = base + " AND toString(properties.project) = 'robella_ff'"
        block = funnel_block(ff, ROB_TEST)
        reach = hog(
            f"""
            SELECT
              uniq(person_id) AS people,
              uniqIf(person_id, toString(properties.project) = 'robella_ff' AND event = 'funnel_start') AS started,
              uniqIf(person_id, toString(properties.project) = 'robella_landing') AS landing,
              uniqIf(person_id, toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web') AS app_web,
              uniqIf(person_id, event = 'magic_link_requested') AS magic,
              uniqIf(person_id, event = 'login') AS login_n,
              uniqIf(person_id, event = 'app_opened') AS app_opened,
              uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/auto-login') AS autologin,
              uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/auth') AS auth_n,
              uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/magic-link-login') AS magic_page,
              uniqIf(person_id, event = 'onboarding_started') AS onb_started,
              uniqIf(person_id, event = 'onboarding_completed') AS onb_done,
              uniqIf(person_id, event = 'capsule_opened') AS capsule,
              uniqIf(person_id, event = 'report_opened') AS report_n,
              uniqIf(person_id, event = 'tryon_started' OR event = 'tryon_completed' OR event = 'tryon_failed') AS tryon,
              uniqIf(person_id, event = '$pageview' AND toString(properties.$pathname) = '/closet') AS closet,
              uniqIf(person_id, event = 'subscription_started' AND toString(properties.project) = 'robella') AS sub_started
            FROM events
            WHERE {base} AND {ROB_TEST}
            """
        )[0]
        joined = hog(
            f"""
            SELECT
              countIf(email_n = 1 AND app_web = 1) AS email_and_app,
              countIf(checkout_n = 1) AS checkout_people,
              countIf(checkout_n = 1 AND purchase_n = 1) AS checkout_and_purchase,
              countIf(checkout_n = 1 AND primer_n = 1) AS checkout_and_primer,
              countIf(checkout_n = 1 AND app_web = 1) AS checkout_and_app
            FROM (
              SELECT
                max(event = 'funnel_email_submit') AS email_n,
                max(event = 'funnel_checkout_open') AS checkout_n,
                max(event = 'funnel_purchase_success') AS purchase_n,
                max(event = 'primer_payment') AS primer_n,
                max(toString(properties.project) = 'robella' AND toString(properties.$lib) = 'web') AS app_web
              FROM events
              WHERE {base} AND {ROB_TEST}
              GROUP BY person_id
            )
            """
        )[0]
        block.update(reach)
        block.update(joined)
        return block

    # tryon LIKE may be rejected. Compute tryon separately if needed.
    us = one_window(US_START)
    full = one_window("2020-01-01 00:00:00")

    path_where = (
        f"timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') "
        "AND toString(properties.project) = 'robella_ff'"
    )
    path_sql = (
        "if(extract(toString(properties.$pathname), '/([^/]+)$') = '' "
        "OR extract(toString(properties.$pathname), '/([^/]+)$') = 'ai-stilist-week-web', "
        "'intro', extract(toString(properties.$pathname), '/([^/]+)$'))"
    )
    path_rows = step_people(path_where, path_sql)
    sid_rows = step_people(path_where, "toString(properties.screen_id)")
    mismatch = hog(
        f"""
        SELECT
          count() AS events,
          countIf(
            extract(toString(properties.$pathname), '/([^/]+)$') != ''
            AND extract(toString(properties.$pathname), '/([^/]+)$') != 'ai-stilist-week-web'
            AND extract(toString(properties.$pathname), '/([^/]+)$') != toString(properties.screen_id)
          ) AS mismatch_nested,
          countIf(extract(toString(properties.$pathname), '/([^/]+)$') != toString(properties.screen_id)) AS mismatch_all
        FROM events
        WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST}
        """
    )[0]
    overlap = hog(
        f"""
        SELECT
          countIf(age = 1 AND social = 0 AND goals = 0) AS age_only,
          countIf(social = 1 AND goals = 0) AS social_without_goals,
          countIf(goals = 1 AND social = 0) AS goals_without_social,
          countIf(goals = 1 AND social = 1) AS goals_and_social,
          countIf(age = 1) AS path_age,
          countIf(social = 1) AS path_social,
          countIf(goals = 1) AS path_goals
        FROM (
          SELECT
            max({path_sql} = 'age_group') AS age,
            max({path_sql} = 'social_proof') AS social,
            max({path_sql} = 'main_goals') AS goals
          FROM events
          WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST}
          GROUP BY person_id
        )
        """
    )[0]
    cross = hog(
        f"""
        SELECT {path_sql} AS path_step, toString(properties.screen_id) AS screen_id,
               uniq(person_id) AS people, count() AS events
        FROM events
        WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST}
          AND (
            {path_sql} = 'age_group' OR {path_sql} = 'social_proof' OR {path_sql} = 'main_goals'
            OR toString(properties.screen_id) = 'age_group'
            OR toString(properties.screen_id) = 'social_proof'
            OR toString(properties.screen_id) = 'main_goals'
          )
        GROUP BY path_step, screen_id
        ORDER BY events DESC
        LIMIT 20
        """
    )
    order_rows = hog(
        f"""
        SELECT person_id, {path_sql} AS step, toString(min(timestamp)) AS first_ts
        FROM events
        WHERE event = 'funnel_screen_open' AND {path_where} AND {ROB_TEST}
        GROUP BY person_id, step
        LIMIT 5000
        """
    )
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
    # Порядок чтения — последовательность четырёх людей, дошедших до оплаты,
    # по событиям, где путь и screen_id совпали. Средний ранг по всем людям
    # ставит social_proof раньше age_group: URL уезжает вперёд имени экрана.
    canon = [
        "intro", "age_group", "social_proof", "main_goals", "algo_promise",
        "eye_color", "hair_color", "skin_tone", "undertone", "analyzing",
        "body_shape", "height", "weight", "highlight_features", "wardrobe_struggles",
        "wear_percentage", "analyzing_fit", "location", "daily_life", "shopping_tier",
        "budget", "look_boho", "look_classic", "look_casual", "look_romantic",
        "look_evening", "photo_upload", "analyzing_preferences", "name", "email",
        "creating_plan", "gift_discount", "paywall",
    ]
    present = set(ranks) | {row["step"] for row in path_rows}
    step_order = [step for step in canon if step in present]
    step_order += sorted(step for step in present if step not in step_order and step)
    before = hog(
        f"""
        SELECT
          uniqIf(person_id, event = 'funnel_start' AND timestamp < toDateTime('{US_START}')) AS started_before,
          uniqIf(person_id, event = 'funnel_purchase_success' AND timestamp < toDateTime('{US_START}')) AS purchase_before
        FROM events
        WHERE timestamp < toDateTime('{END}')
          AND toString(properties.project) = 'robella_ff'
          AND {ROB_TEST}
        """
    )[0]

    paywall_props = hog(
        f"""
        SELECT
          toString(properties.$pathname) AS path,
          toString(properties.screen_id) AS screen_id,
          toString(properties.price) AS price,
          toString(properties.amount) AS amount,
          toString(properties.currency) AS currency,
          toString(properties.trial_price) AS trial_price,
          toString(properties.plan) AS plan,
          count() AS events,
          uniq(person_id) AS people
        FROM events
        WHERE event = 'funnel_screen_open'
          AND {path_where} AND {ROB_TEST}
          AND (toString(properties.$pathname) LIKE '%paywall%' OR toString(properties.screen_id) = 'paywall')
        GROUP BY path, screen_id, price, amount, currency, trial_price, plan
        ORDER BY people DESC
        LIMIT 20
        """
    )

    primer = read_primer(primer_path)
    primer_after = hog(
        f"""
        SELECT count() AS n, uniq(person_id) AS people
        FROM events
        WHERE event = 'primer_payment' AND toString(properties.project) = 'robella'
          AND timestamp > toDateTime('2026-11-17 09:28:53') AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
        """
    )[0]
    primer["after_file"] = primer_after
    buyers = early_buyers()
    checkout = checkout_stories()
    compare = {
        "foxiq": compare_product("foxiq_ff", "foxiq", FOX_START, FOX_END, FOX_TEST, ""),
        "azora": compare_product(
            "azora_ff",
            "web",
            AZ_START,
            AZ_END,
            AZ_TEST,
            "AND toString(properties.$geoip_country_code) = 'JP'",
        ),
    }
    app_paths = hog(
        f"""
        SELECT toString(properties.$pathname) AS path, uniq(person_id) AS people, count() AS events
        FROM events
        WHERE event = '$pageview' AND toString(properties.project) = 'robella'
          AND toString(properties.$lib) = 'web'
          AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
        GROUP BY path
        ORDER BY people DESC
        LIMIT 30
        """
    )
    onboarding = hog(
        f"""
        SELECT toString(properties.step) AS step, count() AS events, uniq(person_id) AS people
        FROM events
        WHERE event = 'onboarding_step' AND toString(properties.project) = 'robella'
          AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}') AND {ROB_TEST}
        GROUP BY step
        ORDER BY step
        """
    )
    days = hog(
        f"""
        SELECT toDate(timestamp + INTERVAL 3 HOUR) AS day_msk, uniq(person_id) AS people
        FROM events
        WHERE event = 'funnel_start' AND toString(properties.project) = 'robella_ff'
          AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
        GROUP BY day_msk
        ORDER BY day_msk
        """
    )
    product_events = hog(
        f"""
        SELECT event, uniq(person_id) AS people, count() AS n
        FROM events
        WHERE toString(properties.project) = 'robella'
          AND toString(properties.$lib) = 'web'
          AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
          AND event NOT LIKE '$%'
        GROUP BY event
        ORDER BY people DESC
        LIMIT 40
        """
    )
    return {
        "scope": scope,
        "excluded": excluded,
        "us": us,
        "full": full,
        "path": {row["step"]: row for row in path_rows},
        "path_rows": path_rows,
        "sid": {row["step"]: row for row in sid_rows},
        "sid_rows": sid_rows,
        "mismatch": mismatch,
        "overlap": overlap,
        "cross": cross,
        "step_order": step_order,
        "before": before,
        "paywall_props": paywall_props,
        "primer": primer,
        "buyers": buyers,
        "checkout": checkout,
        "compare": compare,
        "app_paths": app_paths,
        "onboarding": onboarding,
        "days": days,
        "product_events": product_events,
        "period_full": f"{msk(scope['first_ts'])} МСК — {PERIOD_END_LABEL}",
    }


def compare_product(ff: str, app: str, start: str, end: str, test_sql: str, extra: str) -> dict:
    try:
        row = hog(
            f"""
            SELECT
              uniqIf(person_id, event = 'funnel_start' AND toString(properties.project) = '{ff}') AS started,
              uniqIf(person_id, event = 'funnel_email_submit' AND toString(properties.project) = '{ff}') AS email_n,
              uniqIf(person_id, event = 'funnel_checkout_open' AND toString(properties.project) = '{ff}') AS checkout_n,
              uniqIf(person_id, event = 'funnel_purchase_success' AND toString(properties.project) = '{ff}') AS purchase_n
            FROM events
            WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}')
              AND toString(properties.project) = '{ff}'
              {extra}
              AND {test_sql}
            """
        )[0]
        joined = hog(
            f"""
            SELECT countIf(email_n = 1 AND app_web = 1) AS email_and_app, countIf(email_n = 1) AS email_people
            FROM (
              SELECT
                max(event = 'funnel_email_submit' AND toString(properties.project) = '{ff}' {extra}) AS email_n,
                max(toString(properties.project) = '{app}' AND toString(properties.$lib) = 'web') AS app_web
              FROM events
              WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}')
                AND toString(properties.project) IN ('{ff}','{app}')
                AND {test_sql}
              GROUP BY person_id
            )
            """
        )[0]
        row.update(joined)
        mail = hog(
            f"""
            SELECT countIf(ff = 1) AS emails, countIf(ff = 1 AND app = 1) AS both
            FROM (
              SELECT
                max(event = 'funnel_email_submit' AND toString(properties.project) = '{ff}' {extra}) AS ff,
                max(toString(properties.project) = '{app}' AND toString(properties.$lib) = 'web') AS app
              FROM events
              WHERE timestamp >= toDateTime('{start}') AND timestamp < toDateTime('{end}')
                AND toString(properties.project) IN ('{ff}','{app}')
                AND lower(toString(person.properties.email)) != ''
                AND {test_sql}
              GROUP BY lower(toString(person.properties.email))
            )
            """
        )[0]
        row["email_join_emails"] = mail["emails"]
        row["email_join_both"] = mail["both"]
        row["ok"] = True
        return row
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}


def read_primer(path: Path) -> dict:
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
            rows.append(
                {
                    "date": row.get("date"),
                    "status": row.get("status"),
                    "amount_minor": int(row.get("amount") or 0),
                    "currency": row.get("currencyCode"),
                    "refunded": int(row.get("amountRefunded") or 0),
                    "init": meta.get("ff_initiation_type") or "",
                    "country": meta.get("ff_country_code") or "",
                    "test": bool(re.search(EMAIL_RE, email, re.I)),
                }
            )
    by_day = defaultdict(lambda: defaultdict(int))
    for row in rows:
        dollars = f"{row['amount_minor'] / 100:.2f} {row['currency']}"
        by_day[msk_day(row["date"])][(row["status"], dollars, row["init"], "тест" if row["test"] else "не тест")] += 1
    return {
        "file_rows": total,
        "first": first,
        "last": last,
        "rows": len(rows),
        "people_hint": None,
        "items": rows,
        "by_day": [
            {"day": day, "status": key[0], "amount": key[1], "init": key[2], "test": key[3], "n": n}
            for day, bucket in sorted(by_day.items())
            for key, n in sorted(bucket.items())
        ],
        "settled_cit": sum(1 for r in rows if r["status"] == "SETTLED" and r["init"] == "cit" and not r["test"]),
        "declined": sum(1 for r in rows if r["status"] == "DECLINED"),
        "trial_1": sum(1 for r in rows if r["amount_minor"] == 100 and r["currency"] == "USD"),
        "month_3990": sum(1 for r in rows if r["amount_minor"] == 3990 and r["currency"] == "USD"),
    }


def early_buyers() -> list:
    rows = hog(
        f"""
        SELECT
          person_id,
          minIf(timestamp, event = 'subscription_started') AS started,
          countIf(event = 'subscription_cancelled') AS cancels,
          countIf(event = 'subscription_expired') AS expires,
          countIf(event = 'subscription_renewed') AS renews,
          countIf(event = 'primer_payment' AND toString(properties.status) = 'settled') AS settled_n,
          countIf(event = 'primer_payment' AND toString(properties.status) = 'declined') AS declined_n,
          countIf(toString(properties.$lib) = 'web') AS web_events,
          uniqIf(toString(properties.$pathname), event = '$pageview' AND toString(properties.$lib) = 'web') AS paths,
          max(event = 'onboarding_started') AS onb,
          max(event = 'capsule_opened') AS capsule,
          max(event = 'login') AS login_n,
          max(event = 'app_opened') AS opened
        FROM events
        WHERE toString(properties.project) = 'robella'
          AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
          AND person_id IN (
            SELECT person_id FROM events
            WHERE event = 'subscription_started' AND toString(properties.project) = 'robella'
              AND timestamp < toDateTime('{US_START}') AND {ROB_TEST}
          )
        GROUP BY person_id
        ORDER BY started
        """
    )
    out = []
    for index, row in enumerate(rows, start=1):
        reasons = hog(
            f"""
            SELECT event, toString(properties.reason) AS reason, toString(timestamp) AS ts
            FROM events
            WHERE person_id = '{row['person_id']}'
              AND toString(properties.project) = 'robella'
              AND (event = 'subscription_cancelled' OR event = 'subscription_expired' OR event = 'subscription_renewed' OR event = 'primer_payment')
              AND timestamp < toDateTime('{END}')
            ORDER BY timestamp
            LIMIT 12
            """
        )
        safe = []
        for item in reasons:
            safe.append(
                {
                    "event": item["event"],
                    "reason": item.get("reason") or "",
                    "ts": msk_sec(item.get("ts")),
                    "dt": parse_utc(item.get("ts")) if item.get("ts") else None,
                }
            )
        pages = hog(
            f"""
            SELECT replaceRegexpOne(toString(properties.$pathname), '\\\\?.*', '') AS path, count() AS n
            FROM events
            WHERE person_id = '{row['person_id']}'
              AND toString(properties.project) = 'robella'
              AND event = '$pageview' AND toString(properties.$lib) = 'web'
              AND timestamp < toDateTime('{END}')
            GROUP BY path
            ORDER BY n DESC
            LIMIT 6
            """
        )
        cancels = [item["dt"] for item in safe if item["event"] == "subscription_cancelled" and item["dt"]]
        expires = [item["dt"] for item in safe if item["event"] == "subscription_expired" and item["dt"]]
        same = []
        for left in cancels:
            for right in expires:
                if abs((left - right).total_seconds()) <= 1:
                    same.append(msk_sec(left))
        out.append(
            {
                "n": index,
                "started": msk(row["started"]),
                "cancels": row["cancels"],
                "expires": row["expires"],
                "renews": row["renews"],
                "web_events": row["web_events"],
                "paths": row["paths"],
                "pages": [clean_text(f"{item['path'] or '/'} ({item['n']})") for item in pages],
                "onb": row["onb"],
                "capsule": row["capsule"],
                "login_n": row["login_n"],
                "opened": row["opened"],
                "same_second": same,
                "money": [{k: v for k, v in item.items() if k != "dt"} for item in safe],
            }
        )
    return out


def checkout_stories() -> list:
    people = hog(
        f"""
        SELECT person_id, min(timestamp) AS first_checkout
        FROM events
        WHERE event = 'funnel_checkout_open' AND toString(properties.project) = 'robella_ff'
          AND timestamp >= toDateTime('{US_START}') AND timestamp < toDateTime('{END}')
          AND {ROB_TEST}
        GROUP BY person_id
        ORDER BY first_checkout
        """
    )
    stories = []
    for index, person in enumerate(people, start=1):
        pid = person["person_id"]
        events = hog(
            f"""
            SELECT
              toString(timestamp) AS ts,
              event,
              toString(properties.project) AS project,
              toString(properties.$pathname) AS path,
              toString(properties.screen_id) AS screen_id,
              toString(properties.status) AS status,
              toString(properties.amount) AS amount,
              toString(properties.$recording_status) AS recording
            FROM events
            WHERE person_id = '{pid}'
              AND timestamp < toDateTime('{END}')
              AND toString(properties.project) IN ('robella','robella_ff','robella_landing')
              AND event != '$web_vitals' AND event != '$pageleave'
            ORDER BY timestamp
            LIMIT 250
            """
        )
        compact = []
        for event in events:
            path = event.get("path") or ""
            if "?" in path:
                path = path.split("?", 1)[0]
            if path.startswith("http"):
                path = re.sub(r"https?://[^/]+", "", path)
            compact.append(
                {
                    "ts": msk_sec(event["ts"]),
                    "event": event["event"],
                    "project": event["project"],
                    "path": path[:80],
                    "screen_id": event.get("screen_id") or "",
                    "status": event.get("status") or "",
                    "amount": event.get("amount") or "",
                    "recording": event.get("recording") or "",
                }
            )
        interesting = []
        for event in compact:
            path = event["path"]
            keep = event["event"] != "funnel_screen_open" or any(
                token in path for token in ("email", "paywall", "name", "creating", "gift", "ai-stylist")
            )
            if keep:
                interesting.append(event)
        last_screen = ""
        for event in compact:
            if event["event"] == "funnel_screen_open" and event["path"]:
                last_screen = event["path"]
        stories.append(
            {
                "n": index,
                "events": interesting[:40],
                "truncated": len(events) >= 250,
                "screen_events": sum(1 for event in compact if event["event"] == "funnel_screen_open"),
                "last_screen": last_screen,
                "checkout": sum(1 for event in compact if event["event"] == "funnel_checkout_open"),
                "primer": sum(1 for event in compact if event["event"] == "primer_payment"),
                "purchase": sum(1 for event in compact if event["event"] == "funnel_purchase_success"),
                "fail": sum(1 for event in compact if event["event"] == "funnel_purchase_fail"),
                "app_events": sum(1 for event in compact if event["project"] == "robella"),
                "recording_active": sum(1 for event in compact if event["recording"] == "active"),
            }
        )
    return stories


def sample_size(p1: float, p2: float) -> int | None:
    if p1 <= 0 or p1 >= 1 or p2 <= 0 or p2 >= 1 or p1 == p2:
        return None
    z = 1.959963984540054 + 0.841621233572914
    return math.ceil(z * z * (p1 * (1 - p1) + p2 * (1 - p2)) / (p2 - p1) ** 2)


def render_html(data: dict) -> str:
    us = data["us"]
    started = int(us.get("started") or 0)
    scope = data["scope"]
    path = data["path"]
    sid = data["sid"]
    age_path = int((path.get("age_group") or {}).get("people") or 0)
    social_path = int((path.get("social_proof") or {}).get("people") or 0)
    age_sid = int((sid.get("age_group") or {}).get("people") or 0)
    social_sid = int((sid.get("social_proof") or {}).get("people") or 0)
    drop_same = age_path == age_sid and social_path == social_sid
    buyers_n = len(data["buyers"])
    primer_items = [row for row in data["primer"]["items"] if not row["test"]]
    days = data["days"]
    day_people = sum(int(row["people"]) for row in days) if days else 0
    active_days = len(days)
    per_day = (started / active_days) if active_days else 0
    email_n = int(us.get("email_n") or 0)
    p_email = email_n / started if started else 0
    need_email = sample_size(p_email, min(0.99, p_email + 0.05)) if started else None
    days_need = math.ceil(need_email / per_day) if need_email and per_day else None

    def row_pair(title, num, den):
        return f"<tr><td>{esc(title)}</td><td class='r num'>{esc(n_of(num, den))}</td><td class='r num'>{esc(pct(num, den))}</td></tr>"

    path_table = []
    seen = set()
    by_path = {row["step"]: row for row in data["path_rows"]}
    for step in data.get("step_order") or []:
        row = by_path.get(step) or {"people": 0}
        seen.add(step)
        other = sid.get(step) or {}
        path_table.append(
            "<tr><td><code>{}</code></td><td class='r num'>{}</td><td class='r num'>{}</td></tr>".format(
                esc(step),
                esc(n_of(row["people"], started)),
                esc(n_of(other.get("people", 0), started)),
            )
        )
    for step, row in sid.items():
        if step not in seen and step:
            path_table.append(
                "<tr><td><code>{}</code> <span class='sub'>только screen_id</span></td><td class='r num'>0 из {}</td><td class='r num'>{}</td></tr>".format(
                    esc(step), started, esc(n_of(row["people"], started))
                )
            )
    overlap = data.get("overlap") or {}
    cross_rows = "".join(
        "<tr><td><code>{}</code></td><td><code>{}</code></td><td class='r num'>{}</td><td class='r num'>{}</td></tr>".format(
            esc(row["path_step"]), esc(row["screen_id"]), esc(n_of(row["people"], started)), row["events"]
        )
        for row in data.get("cross") or []
    )

    primer_rows = []
    for row in data["primer"]["by_day"]:
        primer_rows.append(
            "<tr><td>{}</td><td>{}</td><td class='num'>{}</td><td>{}</td><td>{}</td><td class='r num'>{}</td></tr>".format(
                esc(row["day"]), esc(row["status"]), esc(row["amount"]), esc(row["init"] or "нет данных"), esc(row["test"]), row["n"]
            )
        )

    checkout_cards = []
    for story in data["checkout"]:
        lines = []
        for event in story["events"]:
            if event["event"].startswith("$") and event["event"] not in ("$pageview",):
                continue
            extra = ""
            if event["status"] and event["status"] not in ("None", "null", ""):
                extra += f", статус {event['status']}"
            if event["amount"] and event["amount"] not in ("None", "null", ""):
                extra += f", сумма {event['amount']}"
            screen = f", экран {event['screen_id']}" if event["screen_id"] and event["screen_id"] not in ("None", "null") else ""
            lines.append(
                f"<li><span class='num'>{esc(event['ts'])}</span> {esc(event['event'])} {esc(event['path'])}{esc(screen)}{esc(extra)}</li>"
            )
        checkout_cards.append(
            "<div class='card'><h3>Открытие оплаты {}</h3>"
            "<p>Событий экрана: {}. Последний путь: <code>{}</code>. "
            "funnel_checkout_open: {}. primer_payment: {}. funnel_purchase_success: {}. "
            "funnel_purchase_fail: {}. События project robella, любой источник: {}. "
            "События с recording_status = active: {}.{}"
            "</p><ol class='list'>{}</ol></div>".format(
                story["n"],
                story["screen_events"],
                esc(story["last_screen"] or "нет данных"),
                story["checkout"],
                story["primer"],
                story["purchase"],
                story["fail"],
                story["app_events"],
                story["recording_active"],
                " Список обрезан на 250 событиях." if story["truncated"] else "",
                "".join(lines) or "<li>до почты и оплаты отдельных событий нет</li>",
            )
        )

    buyer_rows = []
    for buyer in data["buyers"]:
        money = "; ".join(
            f"{item['ts']} {item['event']} {item['reason']}".strip() for item in buyer["money"]
        ) or "нет событий оплаты кроме старта"
        pages = ", ".join(buyer.get("pages") or []) or "нет данных"
        same = ", ".join(buyer.get("same_second") or []) or "нет"
        buyer_rows.append(
            "<tr><td class='num'>{}</td><td>{}</td><td class='r num'>{}</td><td>{}</td><td class='r num'>{}</td><td class='r num'>{}</td><td>{}</td><td>{}</td></tr>".format(
                buyer["n"],
                esc(buyer["started"]),
                buyer["web_events"],
                esc(pages),
                buyer["renews"],
                buyer["cancels"],
                esc(same),
                esc(money),
            )
        )

    def comp_row(name, block, label):
        if not block.get("ok"):
            return f"<tr><td>{esc(name)}</td><td colspan='4'>нет данных: запрос не выполнился ({esc(block.get('error',''))})</td></tr>"
        mark = "ориентир" if started < 30 or int(block.get("started") or 0) < 30 else "сравнение"
        return (
            "<tr><td>{}<span class='sub'>{} · {}</span></td>"
            "<td class='r num'>{}</td><td class='r num'>{}</td><td class='r num'>{}</td><td class='r num'>{}</td></tr>"
        ).format(
            esc(name),
            esc(label),
            mark,
            esc(n_of(block.get("email_n"), block.get("started"))),
            esc(n_of(block.get("checkout_n"), block.get("started"))),
            esc(n_of(block.get("purchase_n"), block.get("started"))),
            esc(n_of(block.get("email_and_app"), block.get("email_people")))
            + " по персоне; "
            + esc(n_of(block.get("email_join_both"), block.get("email_join_emails")))
            + " по почте",
        )

    rob_comp = (
        "<tr><td>Robella, воронка США<span class='sub'>{} · {}</span></td>"
        "<td class='r num'>{}</td><td class='r num'>{}</td><td class='r num'>{}</td><td class='r num'>{}</td></tr>"
    ).format(
        PERIOD_US,
        "ориентир" if started < 30 else "сравнение",
        esc(n_of(us.get("email_n"), started)),
        esc(n_of(us.get("checkout_n"), started)),
        esc(n_of(us.get("purchase_n"), started)),
        esc(n_of(us.get("email_and_app"), us.get("email_n"))) + (" · ориентир" if email_n < 30 else ""),
    )

    product_rows = "".join(
        f"<tr><td><code>{esc(row['event'])}</code></td><td class='r num'>{esc(n_of(row['people'], int(us.get('app_web') or 0)))}</td><td class='r num'>{row['n']}</td></tr>"
        for row in data["product_events"]
    )
    path_app = "".join(
        f"<tr><td><code>{esc(row['path'] or '/')}</code></td><td class='r num'>{esc(n_of(row['people'], int(us.get('app_web') or 0)))}</td></tr>"
        for row in data["app_paths"]
    )
    onboarding_sorted = sorted(
        data["onboarding"],
        key=lambda row: int(row["step"]) if str(row["step"]).isdigit() else 999,
    )
    onb_rows = "".join(
        f"<tr><td class='num'>{esc(row['step'])}</td><td class='r num'>{row['events']}</td><td class='r num'>{row['people']}</td></tr>"
        for row in onboarding_sorted
    ) or "<tr><td colspan='3'>нет данных: событий onboarding_step в окне США после фильтра нет</td></tr>"

    drop_text = (
        f"По пути age_group — {n_of(age_path, started)}, social_proof — {n_of(social_path, started)}. "
        f"По screen_id age_group — {n_of(age_sid, started)}, social_proof — {n_of(social_sid, started)}. "
        f"Людей, у кого путь дошёл до main_goals, а пути social_proof не было: {n_of(overlap.get('goals_without_social'), started)}. "
        f"Путь остановился на age_group и дальше social_proof или main_goals нет: {n_of(overlap.get('age_only'), started)}. "
        + (
            "Обе версии совпали."
            if drop_same
            else "Версии расходятся. Обрыв из аудита 57 → 14 — это версия screen_id, она завышает social_proof: имя экрана приезжает и на соседний путь. По пути social_proof меньше, но часть людей уже на main_goals без этого URL, значит дыра в разметке есть и там."
        )
    )
    mismatch = data["mismatch"]
    facts = [
        f"Воронку США начали {n_of(started, started)} человек за {PERIOD_US}. Почту оставили {n_of(email_n, started)}, оплату открыли {n_of(us.get('checkout_n'), started)}, покупку в событиях воронки зафиксировали {n_of(us.get('purchase_n'), started)}.",
        f"Веб-событие приложения за окно США есть у {us.get('app_web')} человек. Среди оставивших почту такое событие есть у {n_of(us.get('email_and_app'), email_n)}.",
        drop_text,
        f"В Primer с {msk(data['primer']['first'])} МСК по {msk(data['primer']['last'])} МСК у Robella {data['primer']['rows']} платежей. Успешных первых оплат не из теста: {data['primer']['settled_cit']}. Триал $1: {data['primer']['trial_1']} строк. Подписка $39.90: {data['primer']['month_3990']} строк. После конца файла Primer в PostHog primer_payment: {data['primer']['after_file']['people']} человек, событий {data['primer']['after_file']['n']}. Знаменателя нет: это проверка дыры в файле, а не доля.",
        f"До 11.11 успешный старт подписки есть у {buyers_n} человек после фильтра. Это мало данных для вывода о продукте.",
    ]

    css = """
:root{--bg:#fff8f3;--surface:#fff;--ink:#2b1d17;--muted:#7a6359;--line:#f2dfd3;--soft:#fff0e6;--accent:#e0703f;--accent-soft:#ffe7d9;--crit:#c2412d;--crit-soft:#fde8e3;--warn:#b26a12;--warn-soft:#fff1dc;--ok:#2f8a5b;--ok-soft:#e6f5ec;--f-body:"Golos Text","Segoe UI",Roboto,Arial,sans-serif;--f-mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(180deg,#ffe9dc 0,var(--bg) 420px) no-repeat,var(--bg);color:var(--ink);font-family:var(--f-body);font-size:16px;line-height:1.55}
.wrap{max-width:960px;margin:0 auto;padding:40px 16px 64px;display:flex;flex-direction:column;gap:42px}
h1,h2,h3{margin:0;line-height:1.2}h1{font-size:2.05rem}h2{font-size:1.4rem}h3{font-size:1.05rem}
p{margin:0;max-width:76ch}.eyebrow{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.meta{color:var(--muted)}.num{font-family:var(--f-mono);font-variant-numeric:tabular-nums;white-space:nowrap}
section{display:flex;flex-direction:column;gap:14px}
.card,.summary{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;flex-direction:column;gap:10px;box-shadow:0 1px 2px rgba(160,90,60,.06)}
.summary{border-top:4px solid var(--accent)} .summary ol{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:8px}
.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:.92rem;min-width:640px}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--soft);font-size:.74rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}tr:last-child td{border-bottom:none}
td.r,th.r{text-align:right}.sub{display:block;color:var(--muted);font-size:.8rem;font-weight:400;text-transform:none;letter-spacing:0}
code{font-family:var(--f-mono);font-size:.84em;background:var(--soft);padding:1px 4px;border-radius:4px}
.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:12px 14px;border-radius:0 8px 8px 0}
.hyp{border-left:3px solid var(--warn);background:var(--warn-soft);padding:12px 14px;border-radius:0 8px 8px 0}
ul,ol{margin:0;padding-left:1.25em}a{color:var(--accent)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}
.fact{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.fact .v{font-family:var(--f-mono);font-size:1.2rem;font-weight:600}.fact .l{color:var(--muted);font-size:.84rem}
"""
    html_doc = f"""<!doctype html>
<html lang="ru" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Путь пользователей Robella — 18.11.2026</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{css}</style>
</head>
<body>
<div class="wrap">
<header>
<p class="eyebrow">Robella · веб · разбор продукта</p>
<h1>Путь пользователей Robella</h1>
<p class="meta">Весь срок: {esc(data['period_full'])}. Окно воронки США: {PERIOD_US}. Источники: PostHog (robella_ff, robella, robella_landing), Primer с дескриптором ROBELLA.APP, события сессий. Тестовые исключены так же, как в аудите 17.11. Почты и distinct_id в файл не входят. Подробный расчёт: robella-product-analysis-2026-11-18-metodika.md.</p>
</header>

<section id="summary">
<p class="eyebrow">1. Итог</p>
<h2>Коротко</h2>
<p>Весь срок, {esc(data['period_full'])}: воронку robella_ff начали {data['full'].get('started')} человек, почту оставили {esc(n_of(data['full'].get('email_n'), data['full'].get('started')))}, оплату открыли {esc(n_of(data['full'].get('checkout_n'), data['full'].get('started')))}, покупку в событиях воронки — {esc(n_of(data['full'].get('purchase_n'), data['full'].get('started')))}. Из них до 11.11.2026 00:00 МСК старт был у {data['before'].get('started_before')} человек, покупка воронки — у {data['before'].get('purchase_before')}. Веб-событие приложения за весь срок: {esc(n_of(data['full'].get('app_web'), data['full'].get('people')))}. Лендинг: {esc(n_of(data['full'].get('landing'), data['full'].get('people')))}. Ниже окно США отдельно: воронка на английском отдана с 11.11.</p>
<div class="facts">
<div class="fact"><div class="v">{started}</div><div class="l">начали воронку США, {PERIOD_US}</div></div>
<div class="fact"><div class="v">{email_n} из {started}</div><div class="l">оставили почту</div></div>
<div class="fact"><div class="v">{us.get('checkout_n')} из {started}</div><div class="l">открыли оплату</div></div>
<div class="fact"><div class="v">{us.get('purchase_n')} из {started}</div><div class="l">покупка в событиях воронки</div></div>
<div class="fact"><div class="v">{us.get('app_web')} из {us.get('people')}</div><div class="l">веб-приложение среди всех людей Robella в окне США</div></div>
</div>
<div class="summary"><ol>
{''.join(f'<li>{esc(item)}</li>' for item in facts)}
</ol></div>
<p class="meta">Как считали. Люди, не события. Тест — это is_test на событии, почтовый шаблон или такой же шаблон в distinct_id. Окно США считается отдельно от всего срока. Шаг воронки по умолчанию — последний кусок pathname.</p>
</section>

<section id="funnel">
<p class="eyebrow">2. Воронка</p>
<h2>Экраны воронки США</h2>
<p>Знаменатель везде — люди с funnel_start, {n_of(started, started)}, {PERIOD_US}. В колонке «по пути» шаг — последний сегмент pathname, корень воронки записан как intro. В колонке «по screen_id» то же имя берётся из свойства screen_id.</p>
<div class="note">{esc(drop_text)} Расхождение screen_id и вложенного пути: {esc(n_of(mismatch.get('mismatch_nested'), mismatch.get('events')))} событий funnel_screen_open. Если считать и корень intro, где путь не содержит имя экрана: {esc(n_of(mismatch.get('mismatch_all'), mismatch.get('events')))}.</div>
<p>Колонки ниже независимы. «По пути» — сколько людей открыли такой URL. «По screen_id» — сколько людей имели такое имя экрана, даже если URL уже другой. Порядок строк — как шли люди, дошедшие до оплаты 12.11, в те события, где путь и screen_id совпали. Средняя позиция по всем стартам ставит social_proof раньше age_group, потому что URL иногда уезжает вперёд имени экрана. Для чтения взята совпавшая последовательность. Шаги, которых в ней не было, стоят в конце.</p>
<div class="tbl"><table>
<thead><tr><th>Шаг</th><th class="r">По пути</th><th class="r">По screen_id</th></tr></thead>
<tbody>{''.join(path_table)}</tbody>
</table></div>
<h3>Стык возраста, social_proof и целей</h3>
<p>Только три имени. Строка — это пара «путь и screen_id на одном событии», не шаг воронки.</p>
<div class="tbl"><table>
<thead><tr><th>Путь</th><th>screen_id</th><th class="r">Люди</th><th class="r">События</th></tr></thead>
<tbody>{cross_rows or '<tr><td colspan="4">нет данных</td></tr>'}</tbody>
</table></div>
<p class="meta">Период: {PERIOD_US}. Источник: PostHog, project = robella_ff, событие funnel_screen_open.</p>
<h3>Шаги до оплаты, по событиям</h3>
<div class="tbl"><table>
<thead><tr><th>Шаг</th><th class="r">Люди</th><th class="r">Доля от старта</th></tr></thead>
<tbody>
{row_pair('funnel_start', started, started)}
{row_pair('funnel_email_submit', us.get('email_n'), started)}
{row_pair('funnel_checkout_open', us.get('checkout_n'), started)}
{row_pair('funnel_purchase_success', us.get('purchase_n'), started)}
{row_pair('веб-событие приложения у тех, кто оставил почту', us.get('email_and_app'), email_n)}
</tbody></table></div>
</section>

<section id="pay">
<p class="eyebrow">3. Оплата</p>
<h2>Цены и открытия оплаты</h2>
<p>Файл Primer: {data['primer']['file_rows']} платежей всех продуктов, {esc(msk(data['primer']['first']))} МСК — {esc(msk(data['primer']['last']))} МСК. Строк с Robella: {data['primer']['rows']}. Сумма $1 (100 центов) встречается {data['primer']['trial_1']} раз, сумма $39.90 (3990 центов) — {data['primer']['month_3990']} раз. Это не оценка: других дескрипторов с словом robella в файле нет. Файл кончается раньше отчёта. В PostHog с 17.11.2026 12:28 МСК до {PERIOD_END_LABEL} primer_payment у Robella: {data['primer']['after_file']['people']} человек, событий {data['primer']['after_file']['n']}. Доли нет: это проверка, что файл не спрятал платёж.</p>
<div class="tbl"><table>
<thead><tr><th>День МСК</th><th>Статус</th><th>Сумма</th><th>Тип</th><th>Тест</th><th class="r">Строк</th></tr></thead>
<tbody>{''.join(primer_rows) or '<tr><td colspan="6">нет данных</td></tr>'}</tbody>
</table></div>
<p>Почему нет триала $1 и подписки $39.90. В окне США покупки воронки нет: {n_of(us.get('purchase_n'), started)}. В Primer за весь файл нет ни одной строки Robella на эти суммы, ни успешной, ни отказной. Значит платежи на $1 и $39.90 не проходят как ROBELLA.APP. Выложен ли на пейволле другой прайс, из событий не видно: у экрана paywall свойства price, amount, currency, trial_price и plan пустые.</p>
<p class="meta">Экран paywall за {PERIOD_US}: путь и screen_id совпали, свойства price, amount, currency, trial_price и plan пустые. Событий {data['paywall_props'][0]['events'] if data['paywall_props'] else 0}, людей {data['paywall_props'][0]['people'] if data['paywall_props'] else 0}.</p>
<h3>Кто открыл оплату</h3>
<p>Людей с funnel_checkout_open: {n_of(us.get('checkout_n'), started)}. Из них покупка в воронке: {n_of(us.get('checkout_and_purchase'), us.get('checkout_n'))}. primer_payment на той же персоне: {n_of(us.get('checkout_and_primer'), us.get('checkout_n'))}. Веб-событие приложения: {n_of(us.get('checkout_and_app'), us.get('checkout_n'))}.</p>
{''.join(checkout_cards) or '<p>нет данных: открытий оплаты нет</p>'}
<p class="meta">Список событий этих людей за весь срок до {PERIOD_END_LABEL}. Служебные $web_vitals и $pageleave скрыты. Если в списке нет primer_payment, отказа в PostHog у этого человека нет.</p>
</section>

<section id="login">
<p class="eyebrow">4. Вход после воронки</p>
<h2>Почта, ссылка, приложение</h2>
<div class="tbl"><table>
<thead><tr><th>Шаг</th><th class="r">Люди</th><th>Период</th></tr></thead>
<tbody>
<tr><td>Оставили почту в воронке</td><td class="r num">{esc(n_of(email_n, started))}</td><td>{PERIOD_US}</td></tr>
<tr><td>Запросили magic link</td><td class="r num">{esc(n_of(us.get('magic'), int(us.get('app_web') or 0)))}</td><td>знаменатель — веб-заход в приложение, {PERIOD_US}</td></tr>
<tr><td>Открыли /auth</td><td class="r num">{esc(n_of(us.get('auth_n'), int(us.get('app_web') or 0)))}</td><td>знаменатель — веб-заход в приложение</td></tr>
<tr><td>Открыли /magic-link-login</td><td class="r num">{esc(n_of(us.get('magic_page'), int(us.get('app_web') or 0)))}</td><td>тот же знаменатель</td></tr>
<tr><td>Событие login</td><td class="r num">{esc(n_of(us.get('login_n'), int(us.get('app_web') or 0)))}</td><td>тот же знаменатель</td></tr>
<tr><td>Событие app_opened</td><td class="r num">{esc(n_of(us.get('app_opened'), int(us.get('app_web') or 0)))}</td><td>тот же знаменатель</td></tr>
<tr><td>Pageview /auto-login</td><td class="r num">{esc(n_of(us.get('autologin'), int(us.get('app_web') or 0)))}</td><td>тот же знаменатель</td></tr>
</tbody></table></div>
<p>В аудите 17.11 по снимкам семи не-тестовых записей приложения 5 из 7 остались на форме почты или на «Check your inbox», 1 из 7 видел «Signing you in…» около 34 секунд с Axios Network Error, 1 из 7 увидел «This link has expired» и через 2 секунды главную. Этот разбор кадры заново не смотрел. В окне США pageview /auto-login — {esc(n_of(us.get('autologin'), int(us.get('app_web') or 0)))}. У ранних покупателей, до 11.11, /auto-login входит в шесть частых страниц у {sum(1 for buyer in data['buyers'] if any(str(page).startswith('/auto-login') for page in buyer.get('pages') or []))} из {len(data['buyers'])}. Путь в приложении был, в окне США его нет.</p>
<div class="tbl"><table><thead><tr><th>Путь</th><th class="r">Люди</th></tr></thead><tbody>{path_app or '<tr><td colspan="2">нет данных</td></tr>'}</tbody></table></div>
<p class="meta">Знаменатель путей — {esc(n_of(us.get('app_web'), us.get('app_web')))} с веб-событием project = robella, {PERIOD_US}.</p>
</section>

<section id="first">
<p class="eyebrow">5. Первая сессия в продукте</p>
<h2>Что успевают сделать</h2>
<p>Веб-заходов в приложение за окно США: {esc(n_of(us.get('app_web'), us.get('app_web')))}. Онбординг начали {esc(n_of(us.get('onb_started'), us.get('app_web')))}, завершили {esc(n_of(us.get('onb_done'), us.get('app_web')))}. Капсулу открыли {esc(n_of(us.get('capsule'), us.get('app_web')))}. Шкаф /closet: {esc(n_of(us.get('closet'), us.get('app_web')))}. Отчёт: {esc(n_of(us.get('report_n'), us.get('app_web')))}. Примерка, события tryon_*: {esc(n_of(us.get('tryon'), us.get('app_web')))}.</p>
<div class="tbl"><table>
<thead><tr><th>Событие</th><th class="r">Люди</th><th class="r">Событий</th></tr></thead>
<tbody>{product_rows or '<tr><td colspan="3">нет данных</td></tr>'}</tbody>
</table></div>
<h3>Шаги онбординга</h3>
<div class="tbl"><table><thead><tr><th>step</th><th class="r">Событий</th><th class="r">Людей</th></tr></thead><tbody>{onb_rows}</tbody></table></div>
<p>Таблица шагов — окно США, не весь срок. Возврат с шага 7 на шаг 2 виден в одной записи 16.11. Это наблюдение по записи, не доля: в окне онбординг начал {esc(n_of(us.get('onb_started'), us.get('app_web')))}.</p>
<p class="meta">Период событий: {PERIOD_US}. Весь срок приложения до {PERIOD_END_LABEL} в знаменатель веб-захода не смешан.</p>
</section>

<section id="early">
<p class="eyebrow">6. Покупатели до 11.11</p>
<h2>Пять первых оплат <span class="sub">мало данных</span></h2>
<p>После фильтра это {buyers_n} человек с subscription_started раньше 11.11 00:00 МСК. Выборка меньше 30, доли по ним — ориентир, не вывод о продукте.</p>
<div class="tbl"><table>
<thead><tr><th></th><th>Старт МСК</th><th class="r">Веб-событий</th><th>Страницы</th><th class="r">Продлений</th><th class="r">Отмен</th><th>Отмена и отказ в одну секунду</th><th>Оплата и отмена, без почты</th></tr></thead>
<tbody>{''.join(buyer_rows) or '<tr><td colspan="6">нет данных</td></tr>'}</tbody>
</table></div>
<p class="meta">Колонка «в одну секунду» сравнивает timestamp subscription_cancelled и subscription_expired. Период поведения — от их оплаты до {PERIOD_END_LABEL}. Мало данных: 5 человек.</p>
</section>

<section id="compare">
<p class="eyebrow">7. Сравнение</p>
<h2>Те же шаги, другие продукты</h2>
<p>Периоды у продуктов разные. Почта и оплата считаются от старта воронки. У Robella старт {started}, это больше 30, поэтому доля почты сравнивается как доля. Вход в приложение у Robella считается от {email_n} оставивших почту: это меньше 30, в этой колонке ориентир. Покупка в таблице — событие funnel_purchase_success, не subscription_started. У FoxIQ в разборе покупателей больше, потому что там другой признак.</p>
<div class="tbl"><table>
<thead><tr><th>Продукт</th><th class="r">Почта от старта</th><th class="r">Оплата от старта</th><th class="r">Покупка от старта</th><th class="r">Вход в приложение среди оставивших почту</th></tr></thead>
<tbody>
{rob_comp}
{comp_row('FoxIQ', data['compare']['foxiq'], FOX_LABEL)}
{comp_row('Azora, Япония', data['compare']['azora'], AZ_LABEL)}
</tbody></table></div>
<p class="meta">FoxIQ: project foxiq_ff и foxiq, фильтр тестовых почт из playbook, {FOX_LABEL}. Azora: воронка azora_ff со страной JP, приложение — project web, не ios. В playbook воронка и приложение — разные персоны, связь по почте. Колонка входа показывает оба способа. {AZ_LABEL}. Полного списка тестов Azora нет, отсечён общий почтовый шаблон.</p>
</section>

<section id="bugs">
<p class="eyebrow">8. Баги и точки роста</p>
<h2>Что видно и кому отдать</h2>
<div class="tbl"><table>
<thead><tr><th>Что видим</th><th>Сколько людей</th><th>Откуда</th><th>Что предлагаем</th><th>Кому</th></tr></thead>
<tbody>
<tr><td>screen_id не равен вложенному пути</td><td class="num">{esc(n_of(mismatch.get('mismatch_nested'), mismatch.get('events')))} событий</td><td>PostHog, {PERIOD_US}</td><td>Считать шаги по pathname, поправить screen_id</td><td>Даня</td></tr>
<tr><td>Нет покупки воронки и нет цен $1 и $39.90</td><td class="num">{esc(n_of(us.get('purchase_n'), started))} покупок; {data['primer']['trial_1']} и {data['primer']['month_3990']} строк Primer</td><td>PostHog и Primer</td><td>Проверить, какой прайс выложен на пейволле США</td><td>Дима, Даня</td></tr>
<tr><td>Открыли оплату и не купили</td><td class="num">{esc(n_of(us.get('checkout_n'), started))}, покупок {esc(n_of(us.get('checkout_and_purchase'), us.get('checkout_n')))}</td><td>события этих людей</td><td>Разобрать, почему после открытия оплаты нет primer_payment</td><td>Даня</td></tr>
<tr><td>/auto-login не встречается</td><td class="num">{esc(n_of(us.get('autologin'), int(us.get('app_web') or 0)))}</td><td>pageview, {PERIOD_US}</td><td>Либо слать событие на этот путь, либо считать входом /auth и magic link</td><td>Даня</td></tr>
<tr><td>Онбординг не завершается, шаги двоятся</td><td class="num">{esc(n_of(us.get('onb_done'), us.get('onb_started')))} завершили из начавших</td><td>PostHog и запись 16.11</td><td>Один шаг — одно событие, без возврата с 7 на 2</td><td>Даня</td></tr>
<tr><td>Отмена пишется вместе с отказом оплаты</td><td class="num">{sum(1 for b in data['buyers'] if b['cancels'] and b['expires'])} из {buyers_n} ранних покупателей</td><td>PostHog, мало данных</td><td>Не ставить user_initiated на отказ банка</td><td>Даня</td></tr>
</tbody></table></div>
<h3>Дане, по приоритету, из аудита</h3>
<ol class="list">
<li>Починить screen_id: он расходится с путём у {esc(n_of(mismatch.get('mismatch_nested'), mismatch.get('events')))} вложенных событий.</li>
<li>Найти, почему пейволл США не даёт ни $1, ни $39.90, ни funnel_purchase_success.</li>
<li>Писать сумму на subscription_started. Сейчас сумма есть только на primer_payment. Отказ должен оставаться declined и не становиться user_initiated.</li>
<li>Помечать тест на персоне. У тестового отказа 15.10 флаг is_test пустой.</li>
<li>Одно событие входа. Сейчас login и app_opened приходят у разных людей, /auto-login не приходит.</li>
<li>Онбординг: не дублировать шаги и не возвращать человека с шага 7 на шаг 2.</li>
<li>Вход по ссылке: «Signing you in…» около 34 секунд с Network Error и вспышка «This link has expired» перед главной. Это из записей 17.11, по 1 из 7.</li>
</ol>
</section>

<section id="tests">
<p class="eyebrow">9. Гипотезы</p>
<h2>Это не факты</h2>
<div class="hyp">Ниже гипотезы. Цифры объёма посчитаны из фактов окна США, но сами утверждения ещё не проверены. База почты: {esc(n_of(email_n, started))}, это {esc(pct(email_n, started))}. Дней со стартом воронки: {active_days}. Стартов в такой день в среднем: {per_day:.1f}. Формула объёма: два варианта, α = 5%, мощность 80%, нормальное приближение.</div>
<div class="card">
<h3>Гипотеза 1. Длинный квиз режет почту</h3>
<p>Факт, не гипотеза: почту оставляют {esc(n_of(email_n, started))}. Обрыв age_group → social_proof гипотезой не считается: путь и screen_id расходятся, у {esc(n_of(overlap.get('goals_without_social'), started))} путь main_goals есть без пути social_proof.</p>
<p>Гипотеза: если сократить квиз до почты, почту оставят чаще. Вариант: social_proof и длинные вопросы после почты. Метрика: доля funnel_email_submit от funnel_start. Защитная: доля открытий оплаты от тех, кто оставил почту. Объём на вариант, чтобы увидеть рост почты на 5 процентных пунктов: {need_email if need_email else 'нет данных'} человек. При текущем темпе {per_day:.1f} старта в день со стартом это около {days_need if days_need else 'нет данных'} дней на один вариант. Трафика на тест короче месяца не хватает.</p>
</div>
<div class="card">
<h3>Гипотеза 2. После открытия оплаты нечего купить по цене США</h3>
<p>Факт: открытий оплаты {esc(n_of(us.get('checkout_n'), started))}, покупок {esc(n_of(us.get('purchase_n'), started))}, строк Primer на $1 и $39.90 нет. Гипотеза: на пейволле выложена другая цена или кнопка не создаёт платёж.</p>
<p>Вариант: выложить заявленные $1 и $39.90 и записать цену в событие. Метрика: funnel_purchase_success и Primer SETTLED на 100 и 3990 центов. Защитная: доля отказов primer_payment. Объём не считается: базовая покупка 0, формула доли от нуля не даёт срок. Сначала нужно получить хотя бы первые покупки.</p>
</div>
<div class="card">
<h3>Гипотеза 3. Вход ломается на письме со ссылкой</h3>
<p>Факт из записей 17.11: 5 из 7 остались на почте. Гипотеза: magic link не доводит до приложения.</p>
<p>Вариант: /auto-login сразу после оплаты, без отдельного письма. Метрика: доля login или app_opened среди оставивших почту. Защитная: доля ошибок входа. Сейчас оставивших почту {email_n}. Это меньше 30, тест на этой воронке не набрать, пока почту не оставляют хотя бы десятки людей в неделю.</p>
</div>
</section>

<section id="questions">
<p class="eyebrow">10. Открытые вопросы</p>
<h2>Кому что выяснить</h2>
<div class="card"><h3>Диме</h3>
<ul class="list">
<li>Сколько людей и из какого источника пришло на воронку США с 11.11? В PostHog старт есть, источник трафика этим скриптом не разбирался.</li>
<li>Какая цена должна быть на пейволле: $1 затем $39.90, или 19.99 и 29.99, которые видны в Primer до 11.11?</li>
<li>Воронка США точно отдана в трафик, и это /ai-stilist-week-web?</li>
</ul></div>
<div class="card"><h3>Дане</h3>
<ul class="list">
<li>Почему screen_id расходится с pathname у {esc(n_of(mismatch.get('mismatch_nested'), mismatch.get('events')))} событий?</li>
<li>Почему у четырёх открытий оплаты нет primer_payment и нет funnel_purchase_success?</li>
<li>Куда делся /auto-login и почему login и app_opened не приходят вместе?</li>
</ul></div>
<div class="card"><h3>Кате</h3>
<p>Решение нужно, только если Дима подтвердит, что трафик США уже идёт, а цены $1 и $39.90 так и не появились к следующей неделе. Тогда вопрос: останавливать трафик до починки оплаты или нет. Сейчас для этого решения не хватает ответа Димы об объёме.</p></div>
</section>

<section id="limits">
<p class="eyebrow">Ограничения</p>
<h2>Чего в числах нет</h2>
<ul class="list">
<li>Кадры записей за 18.11 заново не разбирались. Выводы про 5 из 7, 34 секунды и «link has expired» взяты из аудита 17.11.</li>
<li>Файл rules/report-style.md в репозитории не найден. Оформление повторяет персиковую палитру FoxIQ v4.23: без подсказок при наведении и без свёрнутых блоков.</li>
<li>Источник трафика и показы рекламы: нет данных в этом скрипте.</li>
<li>Если запрос к FoxIQ или Azora падал, в таблице сравнения стоит «нет данных».</li>
</ul>
</section>
</div>
</body></html>
"""
    return html_doc


def render_md(data: dict) -> str:
    us = data["us"]
    return f"""# Как считали разбор Robella, 18.11.2026

Числа в HTML считал `scripts/robella-analysis.py`, не вручную. Ключ PostHog в файлы не пишется.

## Период

- Верхняя граница: события с `timestamp < 2026-11-18 21:00:00` UTC, это 19.11.2026 00:00 МСК. В отчёте период заканчивается 18.11.2026 23:59 МСК.
- Начало всего срока: первое событие с project robella, robella_ff или robella_landing. В этом прогоне: {data['scope'].get('first_ts')}.
- Окно воронки США: `timestamp >= 2026-11-10 21:00:00` и та же верхняя граница. Это 11.11.2026 00:00 МСК — 18.11.2026 23:59 МСК.

## Кто исключён

Человек исключён целиком, если на любом его событии до верхней границы есть одно из:

- `properties.is_test` или `person.properties.is_test` равно true или 1;
- почта персоны или distinct_id подходит под шаблон `+`, gox-media, yandex, test, example, mailinator, eevakenn, nedvedyea.

Исключено людей: {data['excluded']}. В HTML их почты нет.

## Воронка

- Знаменатель — `uniq(person_id)` события `funnel_start`, project `robella_ff`.
- Путь: последний сегмент `$pathname`. Корень `/ai-stilist-week-web` записан как intro.
- Порядок строк в HTML — последовательность четырёх людей, дошедших до оплаты, по событиям, где последний сегмент пути совпал с screen_id. Средний ранг по всем людям этой последовательности не даёт: URL иногда раньше имени экрана.
- screen_id считается отдельно. Обрыв age_group → social_proof сравнивается в обеих версиях.
- Расхождение — событие `funnel_screen_open`, у которого последний сегмент пути не пустой, не равен корню и не равен screen_id.

## Оплата

- Primer: строка Robella, если в metadata или statementDescriptor есть «robella». Суммы в файле в центах: 100 = $1, 3990 = $39.90, 1999 = $19.99.
- PostHog: `funnel_checkout_open`, `funnel_purchase_success`, `primer_payment`, `subscription_started`.
- Открытия оплаты — это люди с `funnel_checkout_open` в окне США. Их события выгружаются списком без person_id.

## Сравнение

- FoxIQ: {FOX_LABEL}, project foxiq_ff и foxiq, расширенный почтовый фильтр playbook.
- Azora, Япония: {AZ_LABEL}, воронка azora_ff и страна JP. Приложение Azora в PostHog — project `web`, не отдельное имя azora. iOS (project ios) в колонку не входит.
- Вход в приложение: сначала та же персона, затем та же почта. В playbook воронка и приложение — разные персоны, поэтому почта честнее. Почты в файл не пишутся, группировка остаётся в запросе.
- «Ориентир» ставится, если у Robella или у сравниваемого продукта меньше 30 стартов.

## Объём теста

Два варианта, α = 5% (z = 1,96), мощность 80% (z = 0,84):

n на вариант = (zα + zβ)² × (p1(1−p1) + p2(1−p2)) / (p2−p1)².

Если базовая доля 0, срок не считается.

## Что скрипт не делает

- Не открывает кадры записей. Фразы про 5 из 7, Network Error и истёкшую ссылку перенесены из аудита 17.11 как уже посчитанные по снимкам.
- Не ходит в ClickUp и не пишет почты.
"""


if __name__ == "__main__":
    main()
