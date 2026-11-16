#!/usr/bin/env python3
"""FoxIQ weekly report for 09.11–15.11.2026 from repository extracts only.

Run from any directory: python3 scripts/foxiq-weekly.py
The script never uses live PostHog/Primer and never writes to ClickUp.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports/data/foxiq-2026-11-11"
METHOD = ROOT / "reports/foxiq-product-journeys-2026-11-11-v4.10.html"
OUT_MD = ROOT / "reports/weekly/foxiq-week-2026-11-09.md"
OUT_CSV = ROOT / "reports/weekly/foxiq-week-2026-11-09.csv"
MSK = timezone(timedelta(hours=3))
CURRENT_START = date(2026, 11, 9)
CURRENT_END = date(2026, 11, 15)
PREVIOUS_START = date(2026, 11, 2)
PREVIOUS_END = date(2026, 11, 8)
PRIMER_REASON = "Нет свежего экспорта Primer за 02.11–15.11.2026; старые агрегаты не используются как недельный результат."
NO_DATA = "нет данных"
NOT_COMPARABLE = "н/с"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


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


def small_sample(*sizes: int | None) -> bool:
    return any(size is not None and size < 30 for size in sizes)


class TableParser(HTMLParser):
    """Small dependency-free HTML table parser for the v4.10 activation table."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def activation_weekly() -> dict[str, tuple[int, int]]:
    parser = TableParser()
    parser.feed(METHOD.read_text(encoding="utf-8"))
    for table in parser.tables:
        if not table or not table[0] or table[0][0] != "Неделя, МСК":
            continue
        result: dict[str, tuple[int, int]] = {}
        for row in table[1:]:
            if len(row) < 3:
                continue
            match = re.match(r"(\d{2})\.(\d{2})", row[0])
            trained = re.search(r"(\d+)", row[2])
            buyers = re.search(r"(\d+)", row[1])
            if match and trained and buyers:
                key = f"2026-{match.group(2)}-{match.group(1)}"
                result[key] = (int(trained.group(1)), int(buyers.group(1)))
        if result:
            return result
    raise RuntimeError("Activation weekly table not found in v4.10")


coverage = json.loads((DATA / "coverage.json").read_text(encoding="utf-8"))
primer_summary = json.loads((DATA / "primer_summary.json").read_text(encoding="utf-8"))
extract_end = datetime.fromisoformat(coverage["window_msk"][1])
current_coverage_end = min(datetime.combine(CURRENT_END, time(23, 59, 59), MSK), extract_end)
current_partial = current_coverage_end.date() < CURRENT_END
current_period = (
    f"09.11.2026 00:00–{current_coverage_end.strftime('%d.%m.%Y %H:%M')} МСК "
    "(часть недели 09.11–15.11)"
)
previous_period = "02.11.2026 00:00–08.11.2026 23:59:59 МСК"
source_buyers = "PostHog, reports/data/foxiq-2026-11-11/buyers.csv"
source_funnel = "PostHog, reports/data/foxiq-2026-11-11/funnel_weekly.csv"
source_activation = "PostHog, агрегат методики v4.10 (game_started/test_started/lesson_completed ≤ 1 часа)"
source_survey = "PostHog, reports/data/foxiq-2026-11-11/cancel_survey.csv"

# PostHog subscription_started: UTC is converted to MSK before the daily split.
daily_buyers: Counter[date] = Counter()
for buyer in read_csv("buyers.csv"):
    if buyer["is_test"] == "1" or buyer["exclusion_reason"].strip():
        continue
    purchased_utc = datetime.fromisoformat(buyer["purchased_at_utc"].replace("Z", "+00:00"))
    purchased_msk = purchased_utc.astimezone(MSK)
    if PREVIOUS_START <= purchased_msk.date() <= CURRENT_END:
        daily_buyers[purchased_msk.date()] += 1

previous_buyers = sum(daily_buyers[PREVIOUS_START + timedelta(days=i)] for i in range(7))
current_buyers = sum(
    count for day, count in daily_buyers.items()
    if CURRENT_START <= day <= current_coverage_end.date()
)

funnel_rows = {row["week_start_msk"]: row for row in read_csv("funnel_weekly.csv") if row["project"] == "foxiq_ff"}
previous_funnel = funnel_rows[PREVIOUS_START.isoformat()]
current_funnel = funnel_rows[CURRENT_START.isoformat()]
funnel_fields = ["first_screen", "first_question", "paywall", "paid"]
previous_counts = {field: int(previous_funnel[field]) for field in funnel_fields}
current_counts = {field: int(current_funnel[field]) for field in funnel_fields}
activation = activation_weekly()
previous_trained, previous_activation_base = activation[PREVIOUS_START.isoformat()]
current_trained, current_activation_base = activation[CURRENT_START.isoformat()]

survey_reasons: Counter[str] = Counter()
for row in read_csv("cancel_survey.csv"):
    if (
        row["outcome"] == "cancelled"
        and row["completed"] == "true"
        and not row["is_test"].strip()
        and row["reason"].strip()
    ):
        survey_reasons[row["reason"]] += int(row["people"])
survey_total = sum(survey_reasons.values())

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


def add_no_data(section: str, name: str, reason: str = PRIMER_REASON, source: str = "Primer") -> None:
    add_metric(section, name, source=source, status="no_data", note=reason)


def add_count(section: str, name: str, current: int, previous: int, source: str, note: str = "") -> None:
    add_metric(
        section, name, unit="люди", current=current, previous=previous,
        current_n=current, previous_n=previous, source=source,
        status="current_partial" if current_partial else "ok",
        note=(note + " Абсолютное изменение не сопоставимо: текущий период неполный.").strip(),
    )


def add_ratio(
    section: str, name: str, current_n: int, current_d: int,
    previous_n: int, previous_d: int, source: str, note: str = "",
) -> None:
    current_value = ratio(current_n, current_d)
    previous_value = ratio(previous_n, previous_d)
    absolute = current_value - previous_value if current_value is not None and previous_value is not None else None
    relative = absolute / previous_value if absolute is not None and previous_value else None
    add_metric(
        section, name, unit="доля", current=current_value, previous=previous_value,
        absolute=absolute, relative=relative,
        current_n=current_n, current_denominator=current_d,
        previous_n=previous_n, previous_denominator=previous_d,
        source=source, status="current_partial" if current_partial else "ok", note=note,
    )

# 1. Trial buyers and funnel.
add_no_data("Покупатели и воронка", "Покупатели триала $1 — Primer")
add_count(
    "Покупатели и воронка", "subscription_started — PostHog, справочно",
    current_buyers, previous_buyers, source_buyers,
    "Уникальные person_id; тестовые и исключённые записи удалены.",
)
for field, label in [
    ("first_screen", "Воронка: первый экран"),
    ("first_question", "Воронка: первый вопрос"),
    ("paywall", "Воронка: пейволл"),
    ("paid", "Воронка: оплата"),
]:
    add_count(
        "Покупатели и воронка", label,
        current_counts[field], previous_counts[field], source_funnel,
        "Уникальные person_id по определению funnel_definition.csv.",
    )
add_ratio(
    "Покупатели и воронка", "Конверсия: первый экран → первый вопрос",
    current_counts["first_question"], current_counts["first_screen"],
    previous_counts["first_question"], previous_counts["first_screen"], source_funnel,
)
add_ratio(
    "Покупатели и воронка", "Конверсия: первый вопрос → пейволл",
    current_counts["paywall"], current_counts["first_question"],
    previous_counts["paywall"], previous_counts["first_question"], source_funnel,
)
add_ratio(
    "Покупатели и воронка", "Оплата с пейволла",
    current_counts["paid"], current_counts["paywall"],
    previous_counts["paid"], previous_counts["paywall"], source_funnel,
    "Оплата — funnel_purchase_success; пейволл — строго screen_id paywall/Paywall.",
)
add_ratio(
    "Покупатели и воронка", "Сквозная конверсия по v4.10: первый вопрос → оплата",
    current_counts["paid"], current_counts["first_question"],
    previous_counts["paid"], previous_counts["first_question"], source_funnel,
    "В v4.10 сквозная конверсия — paid / первый вопрос (paid_from_question); исторический ориентир 3,6% воспроизводится именно так.",
)
add_ratio(
    "Покупатели и воронка", "Дополнительно: первый экран → оплата",
    current_counts["paid"], current_counts["first_screen"],
    previous_counts["paid"], previous_counts["first_screen"], source_funnel,
)

# 2. Renewal and bank metrics require the missing fresh Primer export.
for label in [
    "Продления: закончившиеся 7-дневные триалы",
    "Продления: продлили",
    "Продления: отказ банка",
    "Продления: отменили до списания",
    "Продления: попытки списания не было",
    "Отказы банка: количество",
    "Отказы банка: доля всех попыток списания",
    "Отказы банка: топ причин",
    "Отказы банка: предоплаченные карты",
]:
    add_no_data("Продления и отказы банка", label)

# 3. Cancellations. Aggregate cancel_funnel_daily.csv is deliberately not used:
# it has neither person_id nor is_test, so weekly unique people cannot be deduplicated/filtered.
add_no_data(
    "Отмены", "Отмены за неделю: событие приложения",
    "В выгрузке нет сырых subscription_cancelled с person_id и reason=user_initiated; недельные уникальные отмены не восстанавливаются из экранов воронки.",
    "PostHog",
)
add_no_data("Отмены", "Отмены за неделю: FunnelFox / Primer")
add_no_data(
    "Отмены", "Списания после отмены",
    PRIMER_REASON + " Нулевое значение без проверки платежей не подтверждается.",
)
add_metric(
    "Отмены", "Причины отмены: заполненные ответы",
    unit="люди", current=survey_total, previous=NO_DATA,
    current_n=survey_total, source=source_survey, status="current_partial",
    note="outcome=cancelled, completed=true, is_test пустой; причины записываются только с 09.11.",
)
reason_labels = {
    "something-else": "Причина отмены: другое",
    "too-expensive": "Причина отмены: дорого",
    "dont-use": "Причина отмены: не пользуюсь",
}
for reason, label in reason_labels.items():
    count = survey_reasons[reason]
    add_metric(
        "Отмены", label, unit="доля", current=ratio(count, survey_total), previous=NO_DATA,
        current_n=count, current_denominator=survey_total,
        source=source_survey, status="current_partial",
        note="Доля среди заполненных нетестовых ответов об отмене за доступную часть текущей недели.",
    )

# 4. Activation, exactly as v4.10: game/test/lesson within one hour.
add_ratio(
    "Активация", "Тренировка в первый час",
    current_trained, current_activation_base,
    previous_trained, previous_activation_base, source_activation,
    "game_started, test_started или lesson_completed в течение часа после subscription_started; first_run_started не используется. Цель — 35%.",
)

CSV_FIELDS = [
    "section", "metric", "unit", "current_period", "current_value",
    "previous_period", "previous_value", "absolute_change", "relative_change",
    "current_n", "current_denominator", "previous_n", "previous_denominator",
    "source", "status", "note",
]


def csv_value(value: object, unit: str) -> object:
    if value is None:
        return NOT_COMPARABLE
    if isinstance(value, float):
        return f"{value:.8f}"
    return value


OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for metric in metrics:
        unit = str(metric["unit"])
        writer.writerow({
            "section": metric["section"], "metric": metric["name"], "unit": unit,
            "current_period": current_period, "current_value": csv_value(metric["current"], unit),
            "previous_period": previous_period, "previous_value": csv_value(metric["previous"], unit),
            "absolute_change": csv_value(metric["absolute"], unit),
            "relative_change": csv_value(metric["relative"], "доля"),
            "current_n": metric["current_n"] if metric["current_n"] is not None else "",
            "current_denominator": metric["current_denominator"] if metric["current_denominator"] is not None else "",
            "previous_n": metric["previous_n"] if metric["previous_n"] is not None else "",
            "previous_denominator": metric["previous_denominator"] if metric["previous_denominator"] is not None else "",
            "source": metric["source"], "status": metric["status"], "note": metric["note"],
        })


def md_value(value: object, unit: str) -> str:
    if value is None:
        return NOT_COMPARABLE
    if isinstance(value, str):
        return value
    if unit == "доля":
        return pct(float(value))
    return str(value)


def md_change(metric: dict[str, object]) -> str:
    absolute = metric["absolute"]
    relative = metric["relative"]
    if absolute is None:
        return NOT_COMPARABLE
    if metric["unit"] == "доля":
        result = signed_pp(float(absolute))
        if relative is not None:
            result += f"; {signed_pct(float(relative))} относительно"
        return result
    return signed_int(int(absolute))


def md_sample(metric: dict[str, object]) -> str:
    parts: list[str] = []
    for prefix, n_key, d_key in [
        ("тек.", "current_n", "current_denominator"),
        ("пред.", "previous_n", "previous_denominator"),
    ]:
        n = metric[n_key]
        denominator = metric[d_key]
        if n is None:
            continue
        sample = f"n = {n}"
        if denominator is not None:
            sample += f" из {denominator}"
        parts.append(f"{prefix} {sample}")
    return "; ".join(parts) if parts else "—"


def md_flags(metric: dict[str, object]) -> str:
    flags: list[str] = []
    sizes = [metric["current_denominator"] or metric["current_n"], metric["previous_denominator"] or metric["previous_n"]]
    if small_sample(*[int(size) if size is not None else None for size in sizes]):
        flags.append("мало данных, тренд ненадёжен")
    if metric["status"] == "current_partial":
        flags.append("текущий период неполный; недельный тренд ненадёжен")
    if metric["note"]:
        flags.append(str(metric["note"]))
    return " ⚠ " + "; ".join(flags) if flags else ""


lines: list[str] = [
    "# FoxIQ — недельные метрики, 09.11–15.11.2026",
    "",
    "## Статус данных",
    "",
    f"- Запрошенная текущая неделя: **09.11–15.11.2026, МСК**. Доступно: **{current_period}**.",
    f"- Прошлая неделя: **{previous_period}**, покрыта полностью.",
    f"- {PRIMER_REASON}",
    "- Частичные значения не экстраполируются на полную неделю. Абсолютные изменения количеств между неполной текущей и полной прошлой неделей не рассчитываются (`н/с`).",
    "- Изменения долей рассчитаны арифметически для доступных окон, но не считаются полноценным недельным трендом.",
    "",
    "## Для комментария Кате",
    "",
    f"- Полный недельный расчёт пока невозможен: нет свежего Primer; PostHog за текущую неделю доступен только до {current_coverage_end.strftime('%d.%m %H:%M')} МСК.",
    f"- На доступной части текущей недели оплата с пейволла — {pct(ratio(current_counts['paid'], current_counts['paywall']))} ({current_counts['paid']} из {current_counts['paywall']}) против {pct(ratio(previous_counts['paid'], previous_counts['paywall']))} на прошлой неделе; сквозная по v4.10 — {pct(ratio(current_counts['paid'], current_counts['first_question']))} против {pct(ratio(previous_counts['paid'], previous_counts['first_question']))}. Это сравнение неполного и полного периодов.",
    f"- Активация в первый час — {pct(ratio(current_trained, current_activation_base))} ({current_trained} из {current_activation_base}) против {pct(ratio(previous_trained, previous_activation_base))} ({previous_trained} из {previous_activation_base}); цель — 35%. Текущий период неполный.",
    f"- Причины отмен доступны только с 09.11: {survey_total} заполненных нетестовых ответа; выборка меньше 30, тренд ненадёжен.",
    "",
]

for section in ["Покупатели и воронка", "Продления и отказы банка", "Отмены", "Активация"]:
    lines.extend([
        f"## {section}",
        "",
        "| Метрика | Текущая неделя | Прошлая неделя | Изменение | Выборка | Источник и ограничения |",
        "|---|---:|---:|---:|---|---|",
    ])
    for metric in (item for item in metrics if item["section"] == section):
        name = str(metric["name"])
        unit = str(metric["unit"])
        current_text = md_value(metric["current"], unit)
        previous_text = md_value(metric["previous"], unit)
        source_note = f"{metric['source']}. {md_flags(metric)}".replace("|", "\\|")
        lines.append(
            f"| {name} | {current_text} | {previous_text} | {md_change(metric)} | {md_sample(metric)} | {source_note} |"
        )
    lines.append("")

lines.extend([
    "## Покупатели по дням",
    "",
    "Primer по дням: **нет данных** — нет свежего экспорта. Ниже только справочный PostHog `subscription_started`, уникальные люди после исключений.",
    "",
    "| День, МСК | PostHog subscription_started | Покрытие |",
    "|---|---:|---|",
])
for day_number in range((CURRENT_END - PREVIOUS_START).days + 1):
    day = PREVIOUS_START + timedelta(days=day_number)
    if day <= PREVIOUS_END:
        coverage_note = "полный день"
        value = str(daily_buyers[day])
    elif day < current_coverage_end.date():
        coverage_note = "полный день"
        value = str(daily_buyers[day])
    elif day == current_coverage_end.date():
        coverage_note = f"до {current_coverage_end.strftime('%H:%M')} МСК"
        value = str(daily_buyers[day])
    else:
        coverage_note = "вне выгрузки"
        value = NO_DATA
    lines.append(f"| {day.strftime('%d.%m.%Y')} | {value} | {coverage_note} |")

full_funnel = next(row for row in read_csv("funnel_totals.csv") if row["slice"] == "full_period" and row["project"] == "foxiq_ff")
historical_paywall = ratio(int(full_funnel["paid"]), int(full_funnel["paywall"]))
historical_through = ratio(int(full_funnel["paid"]), int(full_funnel["first_question"]))
historical_activation_trained = sum(trained for trained, _ in activation.values())
historical_activation_base = sum(base for _, base in activation.values())
activation_goal = 0.35

lines.extend([
    "",
    "## Почему Primer и PostHog различаются",
    "",
    f"Primer учитывает уникальных клиентов с первым settled-платежом $1 на IQ-воронках; последующие списания связываются по customerId. PostHog учитывает людей с серверным событием subscription_started. В старом окне это {primer_summary['trial_buyers_real']} против {coverage['buyers_kept']}: {primer_summary['early_trial_buyers_before_12oct_msk']} Primer-покупателя оплатили до 12.10, у части нет subscription_started, у части нет событий FoxIQ. Поэтому PostHog — справочный поведенческий источник, а не замена платежному Primer.",
    "",
    "## Исторические ориентиры — не результат этих недель",
    "",
    f"- Воронка 07.10–11.11 до 14:00 МСК: оплата с пейволла {pct(historical_paywall)} ({full_funnel['paid']} из {full_funnel['paywall']}), сквозная по v4.10 {pct(historical_through)} ({full_funnel['paid']} из {full_funnel['first_question']}).",
    f"- Активация 13.10–11.11: {pct(ratio(historical_activation_trained, historical_activation_base))} ({historical_activation_trained} из {historical_activation_base}); цель {pct(activation_goal)}.",
    f"- Продления по старой сводке до 11.11: {primer_summary['finished_renewed']} из {primer_summary['finished_trial_7d']}; отказ банка — {primer_summary['finished_declined']}, без попытки — {primer_summary['finished_no_attempt']}; предоплаченные карты — {primer_summary['prepaid_finished_renewed']} продлений из {primer_summary['prepaid_finished_trial']}. Эти значения не переносятся в недельные метрики.",
    "",
    "## Методика и допущения",
    "",
    "- Все границы — МСК. Для buyers.csv время purchased_at_utc скрипт переводит в МСК до разбивки по дням.",
    "- Воронка: funnel_start → funnel_screen_open со screen_index=1 → funnel_screen_open со screen_id строго paywall/Paywall → funnel_purchase_success. Расчёт по уникальным person_id, не по событиям. decline-экраны не считаются пейволлом. Сквозная по v4.10 — paid / первый вопрос; paid / первый экран показан отдельно.",
    "- Активация: game_started, test_started или lesson_completed в течение одного часа после subscription_started. first_run_started не считается началом тренировки.",
    "- buyers.csv — уже очищенная выгрузка: скрипт дополнительно исключает is_test=1 и строки с exclusion_reason. Почтовые фильтры, включая gox-media, yopmail и остальные тестовые аккаунты, применены на этапе выгрузки по playbook/posthog.md; исходных email в репозитории нет, независимо перепроверить их нельзя.",
    "- Новые тесты с обычных почт могут быть неотличимы от реальных пользователей; это ограничение исходной выгрузки.",
    "- Причины отмен: только outcome=cancelled, completed=true, пустой is_test. Сумма по причинам — люди с заполненным ответом, а не все отмены недели.",
    "- cancel_funnel_daily.csv не используется для числа отмен: в нём нет person_id и is_test, поэтому нельзя ни исключить тесты, ни deduplicate людей между днями.",
    "- Отмена банковским отказом не считается самостоятельной; для разделения нужны subscription_cancelled, subscription_expired и время попытки списания. Этих сырых событий в выгрузке нет.",
    "- Скрипт: scripts/foxiq-weekly.py. MD и CSV созданы из одной структуры результатов.",
    "",
    "## Что нужно для полного отчёта",
    "",
    "1. Свежий полный экспорт Primer за 02.11–15.11 по всему аккаунту; сырой файл с email и карточными данными в репозиторий не коммитить.",
    "2. Новая выгрузка PostHog до 15.11 23:59:59 МСК с теми же фильтрами и событиями первого часа.",
    "3. Сырые subscription_cancelled / subscription_expired / primer_payment либо агрегаты с person_id, timestamp, reason и is_test для недельных уникальных отмен, классификации и проверки списаний после отмены.",
    "",
])

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT_MD.relative_to(ROOT)}")
print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
print(f"PostHog subscription_started: current partial={current_buyers}, previous={previous_buyers}")
print(f"Activation: current={current_trained}/{current_activation_base}, previous={previous_trained}/{previous_activation_base}")
print(f"Cancellation survey responses={survey_total}; reasons={dict(survey_reasons)}")
