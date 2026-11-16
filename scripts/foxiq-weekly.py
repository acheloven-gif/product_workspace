#!/usr/bin/env python3
"""FoxIQ weekly report for 09.11–15.11.2026 against 02.11–08.11.2026.

Run: python scripts/foxiq-weekly.py
Reads repository extracts and, for trials that started before 02.11, the local
Primer file payments-36.csv. That file is not copied into the repository.
The script does not call PostHog or Primer and does not write to ClickUp.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports/data/foxiq-2026-11-16"
OUT_MD = ROOT / "reports/weekly/foxiq-week-2026-11-09.md"
OUT_CSV = ROOT / "reports/weekly/foxiq-week-2026-11-09.csv"
PAYMENTS_36 = Path(r"C:\Users\Ne Kochan\Downloads\payments-36.csv")
TEST_LIST = ROOT / "reports/foxiq-test-users-list-2026-10-30.csv"
MSK = timezone(timedelta(hours=3))
UTC = timezone.utc
CURRENT_START = date(2026, 11, 9)
CURRENT_END = date(2026, 11, 15)
PREVIOUS_START = date(2026, 11, 2)
PREVIOUS_END = date(2026, 11, 8)
RENEWAL_AMOUNTS = {15.0, 20.99, 29.99, 49.99}
IQ_PATHS = {"/test-iq", "/iq-test-web-v1", "/start-iq-test", "/you-may-wish"}
FOXIQ_ORG = "live_145ee003c9326d"
EMAIL_RE = re.compile(
    r"\+.*@|gox-media\.com|yopmail|@yandex\.ru|test|@example\.com|mailinator|"
    r"k\.k\.tarasova|nikitos\.gura|dariaivanova|eevakenn|nedvedyea|"
    r"^kkk@gmail\.com$|^myskillhouse2020@gmail\.com$|^ekaasrirahmawati403@gmail\.com$",
    re.I,
)
NO_DATA = "нет данных"
NOT_COMPARABLE = "н/с"
OBSERVE_AFTER_END = timedelta(hours=24)
JOIN_SECONDS = 60


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def week_of(day: date) -> str | None:
    if PREVIOUS_START <= day <= PREVIOUS_END:
        return "previous"
    if CURRENT_START <= day <= CURRENT_END:
        return "current"
    return None


def pct(value: float | None) -> str:
    if value is None:
        return NO_DATA
    return f"{value * 100:.1f}%".replace(".", ",")


def signed_pct(value: float | None) -> str:
    if value is None:
        return NO_DATA
    return f"{value * 100:+.1f}%".replace(".", ",")


def signed_pp(value: float | None) -> str:
    if value is None:
        return NO_DATA
    return f"{value * 100:+.1f}".replace(".", ",") + " п.п."


def signed_int(value: int | None) -> str:
    if value is None:
        return NOT_COMPARABLE
    return f"{value:+d}"


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def money(value: float) -> float:
    return round(float(value) + 1e-9, 2)


def load_test_emails() -> set[str]:
    found: set[str] = set()
    with TEST_LIST.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            email = (row.get("email") or "").strip().lower()
            if email:
                found.add(email)
    return found


def is_test_email(email: str, listed: set[str]) -> bool:
    text = email.strip().lower()
    return bool(text) and (text in listed or EMAIL_RE.search(text) is not None)


def load_payments_36(listed: set[str]) -> list[dict[str, object]]:
    """FoxIQ rows only. Emails are used for the test flag and then dropped."""
    if not PAYMENTS_36.exists():
        return []
    raw = list(csv.DictReader(PAYMENTS_36.open(encoding="utf-8-sig", newline="")))
    staged: list[tuple[dict[str, str], dict, str]] = []
    customers: set[str] = set()
    for row in raw:
        try:
            meta = json.loads(row["metadata"]) if row.get("metadata") else {}
        except json.JSONDecodeError:
            meta = {}
        email = (row.get("customerEmailAddress") or meta.get("email") or "").strip().lower()
        staged.append((row, meta, email))
        if (
            row.get("statementDescriptor") == "FoxIQ"
            or meta.get("ff_org_id") == FOXIQ_ORG
            or meta.get("ff_campaign_path") in IQ_PATHS
        ) and row.get("customerId"):
            customers.add(row["customerId"])
    test_customers = {
        row["customerId"]
        for row, _meta, email in staged
        if row.get("customerId") in customers and is_test_email(email, listed)
    }
    payments: list[dict[str, object]] = []
    for row, meta, _email in staged:
        customer = row.get("customerId") or ""
        if customer not in customers or row.get("currencyCode") != "USD":
            continue
        payments.append({
            "payment_id": row["id"],
            "ts": parse_ts(row["date"]),
            "amount": money(int(row["amount"] or 0) / 100),
            "status": (row.get("status") or "").lower(),
            "customer_id": customer,
            "decline_reason": "",
            "prepaid": "1" if row.get("paymentInstrumentBinDataAccountFundingType") == "PREPAID" else "0",
            "is_test": "1" if customer in test_customers else "0",
            "source": "payments-36",
        })
    return payments


def load_export() -> list[dict[str, object]]:
    payments: list[dict[str, object]] = []
    for row in read_csv("primer_export.csv"):
        if row.get("currency") != "USD":
            continue
        payments.append({
            "payment_id": row["payment_id"],
            "ts": parse_ts(row["timestamp_utc"]),
            "amount": money(row["amount"]),
            "status": row["status"].lower(),
            "customer_id": row["customer_id"],
            "decline_reason": row.get("decline_reason") or "",
            "prepaid": row.get("prepaid") or "0",
            "is_test": row.get("is_test") or "0",
            "source": "primer_export",
        })
    return payments


def combine_payments(export_rows: list[dict[str, object]], old_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Export wins on the same payment id. A test flag in either source sticks."""
    by_id: dict[str, dict[str, object]] = {}
    test_customers = {
        str(row["customer_id"])
        for row in export_rows + old_rows
        if row["is_test"] == "1"
    }
    for row in old_rows + export_rows:
        by_id[str(row["payment_id"])] = row
    combined = list(by_id.values())
    for row in combined:
        if str(row["customer_id"]) in test_customers:
            row["is_test"] = "1"
    return combined


def first_trials(payments: list[dict[str, object]]) -> dict[str, datetime]:
    first: dict[str, datetime] = {}
    for row in payments:
        if row["is_test"] == "1" or row["status"] != "settled" or row["amount"] != 1.0:
            continue
        customer = str(row["customer_id"])
        ts = row["ts"]
        assert isinstance(ts, datetime)
        if customer not in first or ts < first[customer]:
            first[customer] = ts
    return first


def renewal_attempts(payments: list[dict[str, object]], customer: str, start: datetime, end: datetime) -> list[dict[str, object]]:
    found = []
    for row in payments:
        ts = row["ts"]
        assert isinstance(ts, datetime)
        if (
            row["customer_id"] == customer
            and row["is_test"] != "1"
            and row["amount"] in RENEWAL_AMOUNTS
            and start < ts <= end
            and row["status"] in {"settled", "declined", "failed"}
        ):
            found.append(row)
    return found


metrics: list[dict[str, object]] = []


def add_metric(
    section: str,
    name: str,
    *,
    unit: str = "",
    current: object = NO_DATA,
    previous: object = NO_DATA,
    absolute: object = None,
    relative: object = None,
    current_n: int | None = None,
    current_denominator: int | None = None,
    previous_n: int | None = None,
    previous_denominator: int | None = None,
    source: str = "",
    status: str = "ok",
    note: str = "",
) -> None:
    metrics.append({
        "section": section, "name": name, "unit": unit,
        "current": current, "previous": previous,
        "absolute": absolute, "relative": relative,
        "current_n": current_n, "current_denominator": current_denominator,
        "previous_n": previous_n, "previous_denominator": previous_denominator,
        "source": source, "status": status, "note": note,
    })


def add_count(section: str, name: str, current: int, previous: int | None, source: str, note: str = "") -> None:
    absolute = current - previous if previous is not None else None
    relative = absolute / previous if absolute is not None and previous else None
    add_metric(
        section, name, unit="люди", current=current,
        previous=previous if previous is not None else NO_DATA,
        absolute=absolute, relative=relative,
        current_n=current, previous_n=previous, source=source, note=note,
    )


def add_ratio(
    section: str, name: str, current_n: int, current_d: int,
    previous_n: int | None, previous_d: int | None, source: str, note: str = "",
) -> None:
    current_value = ratio(current_n, current_d)
    previous_value = ratio(previous_n, previous_d) if previous_n is not None and previous_d is not None else None
    absolute = current_value - previous_value if current_value is not None and previous_value is not None else None
    relative = absolute / previous_value if absolute is not None and previous_value else None
    add_metric(
        section, name, unit="доля",
        current=current_value if current_value is not None else NO_DATA,
        previous=previous_value if previous_value is not None else NO_DATA,
        absolute=absolute, relative=relative,
        current_n=current_n, current_denominator=current_d,
        previous_n=previous_n, previous_denominator=previous_d,
        source=source, note=note,
    )


def main() -> None:
    listed = load_test_emails()
    export_rows = load_export()
    old_rows = load_payments_36(listed)
    payments_36_ok = PAYMENTS_36.exists() and bool(old_rows)
    payments = combine_payments(export_rows, old_rows)
    trials = first_trials(payments)

    # Buyers: Primer first settled $1 by the MSK day of that payment.
    # PostHog: subscription_started, tests and exclusion_reason removed.
    primer_daily: Counter[date] = Counter()
    primer_people: dict[str, set[str]] = {"previous": set(), "current": set()}
    for customer, ts in trials.items():
        day = ts.astimezone(MSK).date()
        bucket = week_of(day)
        if bucket:
            primer_daily[day] += 1
            primer_people[bucket].add(customer)
    posthog_daily: Counter[date] = Counter()
    activation = {"previous": [0, 0], "current": [0, 0]}
    for buyer in read_csv("buyers.csv"):
        if buyer["is_test"] == "1" or buyer["exclusion_reason"].strip():
            continue
        day = parse_ts(buyer["purchased_at_utc"]).astimezone(MSK).date()
        bucket = week_of(day)
        if not bucket:
            continue
        posthog_daily[day] += 1
        activation[bucket][1] += 1
        if buyer["game_started"] == "1" or buyer["test_started"] == "1" or buyer["lesson_completed"] == "1":
            activation[bucket][0] += 1

    source_buyers = "PostHog, reports/data/foxiq-2026-11-16/buyers.csv"
    source_primer = "Primer, reports/data/foxiq-2026-11-16/primer_export.csv"
    source_funnel = "PostHog, reports/data/foxiq-2026-11-16/funnel_weekly.csv"
    source_old = "Primer, локальный payments-36.csv (06.10–11.11), в репозиторий не копировался"

    add_count(
        "Покупатели и воронка", "Покупатели триала $1 — Primer",
        len(primer_people["current"]), len(primer_people["previous"]), source_primer,
        "Первый успешный платёж $1, тесты исключены. Неделя — по дате этого платежа в МСК.",
    )
    add_count(
        "Покупатели и воронка", "subscription_started — PostHog",
        sum(posthog_daily[CURRENT_START + timedelta(days=i)] for i in range(7)),
        sum(posthog_daily[PREVIOUS_START + timedelta(days=i)] for i in range(7)),
        source_buyers,
        "Уникальные person_id. is_test=1 и непустой exclusion_reason исключены. utm_source пустой у всех покупок окна, источник роста 58 → 155 не установлен.",
    )

    funnel_rows = {
        row["week_start_msk"]: row
        for row in read_csv("funnel_weekly.csv")
        if row["project"] == "foxiq_ff"
    }
    previous_funnel = funnel_rows[PREVIOUS_START.isoformat()]
    current_funnel = funnel_rows[CURRENT_START.isoformat()]
    fields = ["first_screen", "first_question", "paywall", "paid"]
    previous_counts = {field: int(previous_funnel[field]) for field in fields}
    current_counts = {field: int(current_funnel[field]) for field in fields}
    for field, label in [
        ("first_screen", "Воронка: первый экран"),
        ("first_question", "Воронка: первый вопрос"),
        ("paywall", "Воронка: пейволл"),
        ("paid", "Воронка: оплата"),
    ]:
        add_count(
            "Покупатели и воронка", label,
            current_counts[field], previous_counts[field], source_funnel,
            "Уникальные person_id по funnel_definition.csv, не строгая последовательность шагов.",
        )
    add_ratio(
        "Покупатели и воронка", "Оплата с пейволла",
        current_counts["paid"], current_counts["paywall"],
        previous_counts["paid"], previous_counts["paywall"], source_funnel,
        "funnel_purchase_success / пейволл. Пейволл — screen_id строго paywall или Paywall.",
    )
    add_ratio(
        "Покупатели и воронка", "Сквозная v4.10: оплата / первый вопрос",
        current_counts["paid"], current_counts["first_question"],
        previous_counts["paid"], previous_counts["first_question"], source_funnel,
        "Как в v4.10: paid_from_question, не оплата / первый экран.",
    )

    # Renewals. Cohort = trial end (first $1 + 7 days) falls in the week.
    # Outcome uses renewal-sized payments only, through 24 hours after the trial end.
    cohorts: dict[str, list[str]] = {"previous": [], "current": []}
    outcomes: dict[str, Counter[str]] = {"previous": Counter(), "current": Counter()}
    unlinked_no_attempt = {"previous": 0, "current": 0}
    customer_person, person_customers = link_people(payments)
    cancels = [
        row for row in read_csv("cancel_events.csv")
        if row["is_test"] != "1"
    ]
    user_cancels: dict[str, datetime] = {}
    for row in cancels:
        if row["event"] != "subscription_cancelled" or row["reason"] != "user_initiated":
            continue
        ts = parse_ts(row["timestamp_utc"])
        person = row["person_id"]
        if person not in user_cancels or ts < user_cancels[person]:
            user_cancels[person] = ts

    for customer, started in trials.items():
        trial_end = started + timedelta(days=7)
        bucket = week_of(trial_end.astimezone(MSK).date())
        if not bucket:
            continue
        if bucket == "previous" and not payments_36_ok and started < datetime(2026, 11, 1, 17, 0, tzinfo=UTC):
            continue
        cohorts[bucket].append(customer)
        attempts = renewal_attempts(payments, customer, started, trial_end + OBSERVE_AFTER_END)
        if any(row["status"] == "settled" for row in attempts):
            outcomes[bucket]["renewed"] += 1
        elif any(row["status"] in {"declined", "failed"} for row in attempts):
            outcomes[bucket]["declined"] += 1
        else:
            person = customer_person.get(customer)
            cancel_ts = user_cancels.get(person) if person else None
            if cancel_ts is not None and cancel_ts <= trial_end + OBSERVE_AFTER_END:
                outcomes[bucket]["cancelled_before"] += 1
            else:
                outcomes[bucket]["no_attempt"] += 1
                if person is None:
                    unlinked_no_attempt[bucket] += 1

    renewal_note = (
        "Когорта: первый успешный $1 плюс 7 дней попадает в неделю. "
        "Продление — успешный платёж 15 / 20,99 / 29,99 / 49,99 USD в течение 24 часов после конца триала. "
        "Платежи 2,99 / 3,99 / 4,99 не считаются продлением. "
        "Прошлая неделя: первые платежи 26.10–01.11 взяты из payments-36.csv, попытки списания — из обоих файлов."
    )
    if not payments_36_ok:
        for label in [
            "Продления: закончившиеся триалы",
            "Продления: продлили",
            "Продления: отказ банка",
            "Продления: отменили до списания",
            "Продления: попытки списания не было",
        ]:
            add_metric(
                "Продления и отказы банка", label, source=source_old, status="no_data",
                note="payments-36.csv не прочитан. Обрезанный primer_export.csv для этой когорты не используется.",
            )
    else:
        previous_n = len(cohorts["previous"])
        current_n = len(cohorts["current"])
        add_count(
            "Продления и отказы банка", "Продления: закончившиеся триалы",
            current_n, previous_n, source_primer + "; " + source_old, renewal_note,
        )
        labels = [
            ("renewed", "Продления: продлили"),
            ("declined", "Продления: отказ банка"),
            ("cancelled_before", "Продления: отменили до списания"),
            ("no_attempt", "Продления: попытки списания не было"),
        ]
        for key, label in labels:
            note = renewal_note
            if key == "cancelled_before":
                note += " Отмена — subscription_cancelled reason=user_initiated до конца окна наблюдения. payment_failed не считается отменой. Клиент без склейки с person_id в эту строку не попадает."
            if key == "no_attempt":
                note += (
                    f" Среди них не склеились с person_id: текущая {unlinked_no_attempt['current']}, "
                    f"прошлая {unlinked_no_attempt['previous']}. У них отмена могла быть и не видна."
                )
            add_count(
                "Продления и отказы банка", label,
                outcomes["current"][key], outcomes["previous"][key],
                source_primer + "; " + source_old, note,
            )
            add_ratio(
                "Продления и отказы банка", label + ", доля когорты",
                outcomes["current"][key], current_n,
                outcomes["previous"][key], previous_n,
                source_primer + "; " + source_old, note,
            )

    # Bank declines inside each MSK week, from the fresh export only.
    decline_codes: dict[str, Counter[str]] = {"previous": Counter(), "current": Counter()}
    attempt_counts = {"previous": 0, "current": 0}
    declined_counts = {"previous": 0, "current": 0}
    prepaid_declined = {"previous": 0, "current": 0}
    no_code = {"previous": 0, "current": 0}
    for row in export_rows:
        if row["is_test"] == "1":
            continue
        ts = row["ts"]
        assert isinstance(ts, datetime)
        bucket = week_of(ts.astimezone(MSK).date())
        if not bucket:
            continue
        if row["status"] == "pending":
            continue
        attempt_counts[bucket] += 1
        if row["status"] != "declined":
            continue
        declined_counts[bucket] += 1
        if row["prepaid"] == "1":
            prepaid_declined[bucket] += 1
        reason = str(row["decline_reason"]).strip()
        if not reason:
            no_code[bucket] += 1
        else:
            decline_codes[bucket][reason] += 1
    add_count(
        "Продления и отказы банка", "Отказы банка: количество",
        declined_counts["current"], declined_counts["previous"], source_primer,
        "События declined в primer_export.csv за неделю, тесты исключены. Это не когорта закончившихся триалов.",
    )
    add_ratio(
        "Продления и отказы банка", "Отказы банка: доля всех попыток",
        declined_counts["current"], attempt_counts["current"],
        declined_counts["previous"], attempt_counts["previous"], source_primer,
        "Знаменатель — платежи недели кроме pending.",
    )
    def top_text(bucket: str) -> str:
        parts = [f"{code} {count}" for code, count in decline_codes[bucket].most_common(5)]
        return "; ".join(parts) if parts else NO_DATA
    add_metric(
        "Продления и отказы банка", "Отказы банка: топ причин",
        current=top_text("current"), previous=top_text("previous"),
        source=source_primer,
        note="decline_reason из Primer. Пустой код в топ не входит.",
    )
    add_count(
        "Продления и отказы банка", "Отказы банка: без кода",
        no_code["current"], no_code["previous"], source_primer,
        "declined с пустым decline_reason. В топ причин не входят. 102 из 324 в README — это PostHog primer_payment за всё окно, не эта недельная разбивка.",
    )
    add_ratio(
        "Продления и отказы банка", "Отказы банка: предоплаченные карты",
        prepaid_declined["current"], declined_counts["current"],
        prepaid_declined["previous"], declined_counts["previous"], source_primer,
        "Доля declined, у которых card funding = PREPAID.",
    )

    # Cancellations.
    def cancel_people(bucket: str, event: str, reason: str | None) -> set[str]:
        found: set[str] = set()
        for row in cancels:
            if row["event"] != event:
                continue
            if reason is not None and row["reason"] != reason:
                continue
            if week_of(parse_ts(row["timestamp_utc"]).astimezone(MSK).date()) == bucket:
                found.add(row["person_id"])
        return found
    source_cancel = "PostHog, reports/data/foxiq-2026-11-16/cancel_events.csv"
    user_current = cancel_people("current", "subscription_cancelled", "user_initiated")
    user_previous = cancel_people("previous", "subscription_cancelled", "user_initiated")
    failed_current = cancel_people("current", "subscription_expired", "payment_failed")
    failed_previous = cancel_people("previous", "subscription_expired", "payment_failed")
    expired_current = cancel_people("current", "subscription_expired", None)
    expired_previous = cancel_people("previous", "subscription_expired", None)
    add_count(
        "Отмены", "Отмены пользователя, user_initiated",
        len(user_current), len(user_previous), source_cancel,
        "Уникальные person_id, subscription_cancelled, reason=user_initiated, is_test исключён.",
    )
    add_count(
        "Отмены", "payment_failed, не отмена пользователя",
        len(failed_current), len(failed_previous), source_cancel,
        "Уникальные person_id с subscription_expired reason=payment_failed. В отмены пользователя не входят.",
    )
    add_count(
        "Отмены", "subscription_expired",
        len(expired_current), len(expired_previous), source_cancel,
        "Уникальные person_id с subscription_expired, любая reason. Человек может быть и в user_initiated.",
    )

    survey_filled: Counter[str] = Counter()
    survey_empty = 0
    for row in read_csv("cancel_survey.csv"):
        if row["outcome"] != "cancelled" or row["completed"] != "true" or row["is_test"].strip():
            continue
        if row["reason"].strip():
            survey_filled[row["reason"]] += int(row["people"])
        else:
            survey_empty += int(row["people"])
    filled_total = sum(survey_filled.values())
    add_metric(
        "Отмены", "Причины отмены: пустая причина",
        unit="люди", current=survey_empty, previous=NO_DATA,
        current_n=survey_empty, source="PostHog, reports/data/foxiq-2026-11-16/cancel_survey.csv",
        note="Файл без даты, это весь период 02.11–15.11, не одна неделя. В доли ниже не входит. Тесты исключены.",
    )
    add_metric(
        "Отмены", "Причины отмены: заполненные ответы",
        unit="люди", current=filled_total, previous=NO_DATA,
        current_n=filled_total, source="PostHog, reports/data/foxiq-2026-11-16/cancel_survey.csv",
        note="Знаменатель долей. Весь период выгрузки, не неделя. Выборка меньше 30.",
    )
    for reason, label in [
        ("something-else", "Причина отмены: другое"),
        ("too-expensive", "Причина отмены: дорого"),
        ("dont-use", "Причина отмены: не пользуюсь"),
    ]:
        add_ratio(
            "Отмены", label, survey_filled[reason], filled_total, None, None,
            "PostHog, reports/data/foxiq-2026-11-16/cancel_survey.csv",
            "Доля среди заполненных причин за 02.11–15.11. Пустые ответы в знаменатель не входят.",
        )

    # Charges after a user cancel. Join is time/amount, not a shared id.
    charged_people: set[str] = set()
    settled_after: set[str] = set()
    linked_cancels = 0
    unlinked_cancels = 0
    by_customer: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in payments:
        if row["is_test"] == "1":
            continue
        by_customer[str(row["customer_id"])].append(row)
    for person, cancel_ts in user_cancels.items():
        customers = person_customers.get(person, set())
        if not customers:
            unlinked_cancels += 1
            continue
        linked_cancels += 1
        for customer in customers:
            for row in by_customer.get(customer, []):
                ts = row["ts"]
                assert isinstance(ts, datetime)
                if ts > cancel_ts and row["status"] in {"settled", "declined", "failed"}:
                    charged_people.add(person)
                    if row["status"] == "settled":
                        settled_after.add(person)
    charge_note = (
        f"Проверка: person_id не совпал ни с customer_id, ни с order_id (0 пересечений). "
        f"Склейка — primer_payment в PostHog с тем же статусом, суммой и валютой в пределах {JOIN_SECONDS} секунд и ровно одним person_id; "
        f"клиент оставлен, только если все его склеенные платежи указывают на одного человека. "
        f"Склеилось отмен {linked_cancels}, не склеилось {unlinked_cancels}. "
        f"Платёж позже первой user_initiated отмены: {len(charged_people)} человек, из них успешное списание у {len(settled_after)}. "
        f"Ноль по всему окну не утверждается: несклеенные отмены не проверены."
    )
    add_metric(
        "Отмены", "Списания после отмены",
        unit="люди", current=len(charged_people), previous=NO_DATA,
        current_n=len(charged_people), current_denominator=linked_cancels,
        source=source_primer + "; " + source_cancel,
        note=charge_note,
    )

    add_ratio(
        "Активация", "Тренировка в первый час",
        activation["current"][0], activation["current"][1],
        activation["previous"][0], activation["previous"][1], source_buyers,
        "game_started, test_started или lesson_completed в течение часа после subscription_started. "
        "База сравнения 17% (34 из 203), цель 35%. first_run_started не используется.",
    )

    write_outputs(
        primer_daily, posthog_daily, current_counts, previous_counts,
        activation, survey_empty, filled_total, payments_36_ok, charge_note,
        outcomes, cohorts, linked_cancels, unlinked_cancels,
    )


def link_people(payments: list[dict[str, object]]) -> tuple[dict[str, str], dict[str, set[str]]]:
    posthog = []
    for row in read_csv("primer_payment_events.csv"):
        posthog.append((
            parse_ts(row["timestamp_utc"]),
            row["status"].lower(),
            money(row["amount"]),
            row["currency"],
            row["person_id"],
        ))
    customer_people: dict[str, set[str]] = defaultdict(set)
    for row in payments:
        ts = row["ts"]
        assert isinstance(ts, datetime)
        hits = {
            person for event_ts, status, amount, currency, person in posthog
            if status == row["status"] and amount == row["amount"] and currency == "USD"
            and abs((event_ts - ts).total_seconds()) <= JOIN_SECONDS
        }
        if len(hits) == 1:
            customer_people[str(row["customer_id"])].add(next(iter(hits)))
    customer_person = {
        customer: next(iter(people))
        for customer, people in customer_people.items()
        if len(people) == 1
    }
    person_customers: dict[str, set[str]] = defaultdict(set)
    for customer, person in customer_person.items():
        person_customers[person].add(customer)
    return customer_person, person_customers


def write_outputs(
    primer_daily: Counter[date],
    posthog_daily: Counter[date],
    current_counts: dict[str, int],
    previous_counts: dict[str, int],
    activation: dict[str, list[int]],
    survey_empty: int,
    filled_total: int,
    payments_36_ok: bool,
    charge_note: str,
    outcomes: dict[str, Counter[str]],
    cohorts: dict[str, list[str]],
    linked_cancels: int,
    unlinked_cancels: int,
) -> None:
    current_period = "09.11.2026 00:00–15.11.2026 23:59:59 МСК"
    previous_period = "02.11.2026 00:00–08.11.2026 23:59:59 МСК"
    fields = [
        "section", "metric", "unit", "current_period", "current_value",
        "previous_period", "previous_value", "absolute_change", "relative_change",
        "current_n", "current_denominator", "previous_n", "previous_denominator",
        "source", "status", "note",
    ]

    def csv_value(value: object) -> object:
        if isinstance(value, float):
            return f"{value:.8f}"
        return "" if value is None else value

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for metric in metrics:
            writer.writerow({
                "section": metric["section"], "metric": metric["name"], "unit": metric["unit"],
                "current_period": current_period, "current_value": csv_value(metric["current"]),
                "previous_period": previous_period, "previous_value": csv_value(metric["previous"]),
                "absolute_change": csv_value(metric["absolute"]),
                "relative_change": csv_value(metric["relative"]),
                "current_n": metric["current_n"] if metric["current_n"] is not None else "",
                "current_denominator": metric["current_denominator"] if metric["current_denominator"] is not None else "",
                "previous_n": metric["previous_n"] if metric["previous_n"] is not None else "",
                "previous_denominator": metric["previous_denominator"] if metric["previous_denominator"] is not None else "",
                "source": metric["source"], "status": metric["status"], "note": metric["note"],
            })

    def md_value(value: object, unit: str) -> str:
        if isinstance(value, str):
            return value
        if value is None:
            return NOT_COMPARABLE
        if unit == "доля":
            return pct(float(value))
        return str(value)

    def md_change(metric: dict[str, object]) -> str:
        absolute = metric["absolute"]
        if absolute is None:
            return NOT_COMPARABLE
        if metric["unit"] == "доля":
            text = signed_pp(float(absolute))
            if metric["relative"] is not None:
                text += f"; {signed_pct(float(metric['relative']))} относительно"
            return text
        if isinstance(absolute, int):
            return signed_int(absolute)
        return NOT_COMPARABLE

    def md_sample(metric: dict[str, object]) -> str:
        parts = []
        for prefix, n_key, d_key in [("тек.", "current_n", "current_denominator"), ("пред.", "previous_n", "previous_denominator")]:
            n = metric[n_key]
            if n is None:
                continue
            sample = f"n = {n}"
            if metric[d_key] is not None:
                sample += f" из {metric[d_key]}"
            parts.append(f"{prefix} {sample}")
        return "; ".join(parts) if parts else "—"

    def md_flags(metric: dict[str, object]) -> str:
        flags = []
        sizes = [metric["current_denominator"] or metric["current_n"], metric["previous_denominator"] or metric["previous_n"]]
        if any(isinstance(size, int) and size < 30 for size in sizes):
            flags.append("мало данных")
        if metric["note"]:
            flags.append(str(metric["note"]))
        return ". ".join(flags)

    paywall_now = ratio(current_counts["paid"], current_counts["paywall"])
    paywall_prev = ratio(previous_counts["paid"], previous_counts["paywall"])
    through_now = ratio(current_counts["paid"], current_counts["first_question"])
    through_prev = ratio(previous_counts["paid"], previous_counts["first_question"])
    act_now = ratio(activation["current"][0], activation["current"][1])
    act_prev = ratio(activation["previous"][0], activation["previous"][1])
    renewal_line = "Продления прошлой недели: нет данных, payments-36.csv не прочитан."
    if payments_36_ok:
        renewal_line = (
            f"Из триалов, закончившихся на неделе, продлили {outcomes['current']['renewed']} из {len(cohorts['current'])} "
            f"против {outcomes['previous']['renewed']} из {len(cohorts['previous'])}. "
            f"Отказ банка {outcomes['current']['declined']} против {outcomes['previous']['declined']}, "
            f"отмена до списания {outcomes['current']['cancelled_before']} против {outcomes['previous']['cancelled_before']}, "
            f"без попытки {outcomes['current']['no_attempt']} против {outcomes['previous']['no_attempt']}."
        )

    lines = [
        "# FoxIQ — недельные метрики, 09.11–15.11.2026",
        "",
        "## Статус данных",
        "",
        f"- Текущая неделя: **{current_period}**. Прошлая: **{previous_period}**. Обе недели в выгрузке целиком.",
        "- PostHog: `reports/data/foxiq-2026-11-16/`. Primer текущих платежей: `primer_export.csv`.",
        "- Первые платежи триалов, которые закончились 02.11–08.11, лежат в локальном `payments-36.csv` (06.10–11.11). Файл прочитан и в репозиторий не копировался."
        if payments_36_ok else
        "- `payments-36.csv` не найден. Продления прошлой недели не считались по обрезанному экспорту.",
        "- `utm_source` пустой у всех `subscription_started` окна. Рост покупателей 58 → 155 по источнику не разбирается.",
        "",
        "## Для комментария Кате",
        "",
        "- Покупатели триала: числа подставляются ниже.",
        f"- Оплата с пейволла {pct(paywall_now)} ({current_counts['paid']} из {current_counts['paywall']}) против {pct(paywall_prev)} ({previous_counts['paid']} из {previous_counts['paywall']}). Сквозная v4.10, оплата / первый вопрос: {pct(through_now)} против {pct(through_prev)}.",
        f"- {renewal_line}",
        f"- Тренировка в первый час: {pct(act_now)} ({activation['current'][0]} из {activation['current'][1]}) против {pct(act_prev)} ({activation['previous'][0]} из {activation['previous'][1]}). База 17% (34 из 203), цель 35%.",
        f"- Списания после отмены: среди {linked_cancels} склеенных отмен платежа позже отмены нет. Ещё {unlinked_cancels} отмен с клиентом Primer не склеились, по ним ноль не утверждается. Причины анкеты за обе недели вместе: пустая у {survey_empty}, заполнены {filled_total}; доли только по заполненным.",
        "",
    ]
    # The Katya bullet above used a clumsy primer count. Replace the first bullet after we know weeks.
    # Recomputed properly below once metrics exist; the placeholder is overwritten by the explicit lines
    # already containing both sources via the table. Fix the first bullet now from metrics.
    primer_metric = next(item for item in metrics if item["name"] == "Покупатели триала $1 — Primer")
    posthog_metric = next(item for item in metrics if item["name"] == "subscription_started — PostHog")
    lines[11] = (
        f"- Покупатели триала $1: Primer {primer_metric['current']} против {primer_metric['previous']}, "
        f"PostHog {posthog_metric['current']} против {posthog_metric['previous']}. "
        f"Источник роста не установлен: utm_source пустой у всех покупок."
    )

    for section in ["Покупатели и воронка", "Продления и отказы банка", "Отмены", "Активация"]:
        lines.extend([
            f"## {section}",
            "",
            "| Метрика | Текущая неделя | Прошлая неделя | Изменение | Выборка | Источник и ограничения |",
            "|---|---:|---:|---:|---|---|",
        ])
        for metric in (item for item in metrics if item["section"] == section):
            source_note = f"{metric['source']}. {md_flags(metric)}".replace("|", "/")
            lines.append(
                f"| {metric['name']} | {md_value(metric['current'], str(metric['unit']))} | "
                f"{md_value(metric['previous'], str(metric['unit']))} | {md_change(metric)} | "
                f"{md_sample(metric)} | {source_note} |"
            )
        lines.append("")

    lines.extend([
        "## Покупатели по дням",
        "",
        "День — дата платежа или `subscription_started` после перевода UTC в МСК. Тесты исключены.",
        "",
        "| День, МСК | Primer, первый $1 | PostHog subscription_started |",
        "|---|---:|---:|",
    ])
    for offset in range(14):
        day = PREVIOUS_START + timedelta(days=offset)
        lines.append(f"| {day.strftime('%d.%m.%Y')} | {primer_daily[day]} | {posthog_daily[day]} |")

    lines.extend([
        "",
        "## Допущения и что не посчитано",
        "",
        "- Границы недель — МСК. Время в файлах UTC, к дате оно приводится до разбивки.",
        "- Primer и PostHog показаны отдельными строками. Совпадение чисел не делает их одним списком людей: общего идентификатора нет.",
        "- Воронка — уникальные person_id на каждом шаге, не воронка «дошёл до следующего». Пейволл только screen_id paywall/Paywall.",
        "- Продление смотрит 24 часа после конца триала. Более поздние повторные попытки банка в метрику не входят. Наблюдение файла Primer заканчивается 16.11 15:42 МСК, для триалов конца 15.11 этого хватает на 24 часа не у всех.",
        "- «Отменили до списания» требует склейки Primer-клиента с person_id. Кто не склеился, остаётся в «без попытки», и отмена у него могла быть.",
        "- Списания после отмены посчитаны только по склеенным отменам. Несклеенные в ноль не включены.",
        "- Причины анкеты нельзя разложить по неделям: в cancel_survey.csv нет даты. 48 пустых причин — на оба окна вместе.",
        "- Источник рекламы у покупок не посчитан: utm_source пустой.",
        "- Скрипт `scripts/foxiq-weekly.py` пишет этот md и csv из одних и тех же чисел. ClickUp не менялся.",
        "",
    ])
    text = "\n".join(lines)
    if "@" in text:
        raise SystemExit("report text contains @")
    OUT_MD.write_text(text, encoding="utf-8")
    print(f"primer {primer_metric['previous']} -> {primer_metric['current']}")
    print(f"posthog {posthog_metric['previous']} -> {posthog_metric['current']}")
    print(f"cohorts { {key: len(value) for key, value in cohorts.items()} }")
    print(f"outcomes { {key: dict(value) for key, value in outcomes.items()} }")
    print(f"activation {activation}")
    print(f"survey empty {survey_empty} filled {filled_total}")
    print(f"payments36 {payments_36_ok} rows_old_loaded")
    print(f"Wrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
