"""FoxIQ cohort comparison, buyers 02–08.11 vs 09–15.11.

Reads prepared aggregates and the repository's pseudonymized CSV exports.
Writes a chart-only HTML report and its methodology note. Does not call PostHog.
"""

from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports" / "data" / "foxiq-2026-11-18" / "cohort_aggregates.json"
EXPORT = ROOT / "reports" / "data" / "foxiq-2026-11-16"
BUYERS = EXPORT / "buyers.csv"
CANCELS = EXPORT / "cancel_events.csv"
OUT_HTML = ROOT / "reports" / "foxiq-cohort-compare-2026-11-09.html"
OUT_MD = ROOT / "reports" / "foxiq-cohort-compare-2026-11-09-metodika.md"

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def pct(n: int, m: int) -> str:
    if m <= 0:
        return "нет данных"
    return f"{n / m * 100:.1f}".replace(".", ",") + "%"


def of(n: int, m: int) -> str:
    return f"{n} из {m} ({pct(n, m)})"


def relative_change(n: int, m: int, previous_n: int, previous_m: int) -> float | None:
    if m <= 0 or previous_m <= 0 or previous_n == 0:
        return None
    return ((n / m) / (previous_n / previous_m) - 1) * 100


def trend(n: int, m: int, previous_n: int, previous_m: int, up: str = "выросли", down: str = "упали") -> str:
    change = relative_change(n, m, previous_n, previous_m)
    if change is None:
        return "нет базы для сравнения"
    if abs(change) < 0.05:
        return "не изменились"
    verb = up if change > 0 else down
    return f"{verb} на {abs(change):.1f}%".replace(".", ",")


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def read_buyers() -> list[dict[str, str]]:
    with BUYERS.open(encoding="utf-8", newline="") as handle:
        return [
            row for row in csv.DictReader(handle)
            if row["is_test"] != "1" and not row["exclusion_reason"].strip()
        ]


def buyer_days() -> dict[str, int]:
    days: dict[str, int] = {}
    for row in read_buyers():
        day = row["purchased_at_msk"][:10]
        days[day] = days.get(day, 0) + 1
    return days


def timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def first_cancels() -> dict[str, datetime]:
    result: dict[str, datetime] = {}
    with CANCELS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["event"] != "subscription_cancelled" or row["reason"] != "user_initiated":
                continue
            moment = timestamp(row["timestamp_utc"])
            person = row["person_id"]
            if person not in result or moment < result[person]:
                result[person] = moment
    return result


def button_split(data: dict) -> dict[str, dict[str, int]]:
    """Rebuild the 50/105 split without exposing person-level rows.

    The 09–10.11 subgroup has its full 72-hour cancel window inside the raw
    cancel export. The 11–15.11 subgroup is the checked current total minus it.
    """
    buyers = read_buyers()
    cancels = first_cancels()
    before_days = {"2026-11-09", "2026-11-10"}
    before_buyers = [row for row in buyers if row["purchased_at_msk"][:10] in before_days]
    before = {"n": len(before_buyers), "cancel_1h": 0, "cancel_72h": 0, "train_1h": 0}
    latest_required = datetime.min.replace(tzinfo=timezone.utc)
    for row in before_buyers:
        purchased = timestamp(row["purchased_at_utc"])
        latest_required = max(latest_required, purchased + timedelta(hours=72))
        cancelled = cancels.get(row["person_id"])
        if cancelled is not None:
            seconds = (cancelled - purchased).total_seconds()
            before["cancel_1h"] += int(0 <= seconds < 3600)
            before["cancel_72h"] += int(0 <= seconds < 72 * 3600)
        before["train_1h"] += int(any(
            row[field] == "1" for field in ("game_started", "test_started", "lesson_completed")
        ))
    export_end = max(cancels.values())
    if export_end < latest_required:
        raise SystemExit("cancel export does not cover the full 09–10.11 72-hour window")
    current = data["cohort"]["current"]
    current_72h = sum(current[key] for key in (
        "cancel_lt_1h", "cancel_1h_6h", "cancel_6h_24h", "cancel_1d_3d"
    ))
    after = {
        "n": data["weeks"]["current"]["n"] - before["n"],
        "cancel_1h": current["cancel_1h"] - before["cancel_1h"],
        "cancel_72h": current_72h - before["cancel_72h"],
        "train_1h": current["train_1h"] - before["train_1h"],
    }
    if (before["n"], after["n"]) != (50, 105):
        raise SystemExit(f"button split sizes {before['n']}, {after['n']}")
    for key, total in (("cancel_1h", 63), ("cancel_72h", 77), ("train_1h", 22)):
        if before[key] + after[key] != total or min(before[key], after[key]) < 0:
            raise SystemExit(f"button split {key} does not reconcile")
    return {"before": before, "after": after}


def check(data: dict) -> None:
    days = buyer_days()
    file_days = {day: n for day, n in data["daily_buyers"]}
    if days != file_days:
        raise SystemExit(f"buyers.csv days {days} != export {file_days}")
    if (sum(n for day, n in file_days.items() if day <= "2026-11-08"),
            sum(n for day, n in file_days.items() if "2026-11-09" <= day <= "2026-11-15")) != (58, 155):
        raise SystemExit("cohort sizes are not 58 and 155")
    for key in ("previous", "current"):
        row = data["cohort"][key]
        n = data["weeks"][key]["n"]
        if n != (58 if key == "previous" else 155):
            raise SystemExit(key)
        within_72h = sum(row[field] for field in (
            "cancel_lt_1h", "cancel_1h_6h", "cancel_6h_24h", "cancel_1d_3d"
        ))
        all_cancels = within_72h + row["cancel_after_3d"]
        expected_72h = 15 if key == "previous" else 77
        expected_all = 33 if key == "previous" else 85
        if (within_72h, all_cancels) != (expected_72h, expected_all):
            raise SystemExit(f"{key} cancel buckets {(within_72h, all_cancels)}")
        if all_cancels != row["cancelled"] or row["cancel_1h"] != row["cancel_lt_1h"]:
            raise SystemExit(f"{key} cancel mismatch")
        if row["d1_ready"] != n or row["d2_ready"] != n or row["d3_ready"] != n:
            raise SystemExit(f"{key} window is not complete")
        side = data["first_session"][key]
        if side["cancelled"]["n"] + side["kept"]["n"] != n:
            raise SystemExit(f"{key} split")
        if side["cancelled"]["n"] != row["cancelled"]:
            raise SystemExit(f"{key} cancelled split")
        for field in ("train_1h", "game_1h", "test_1h", "lesson_1h"):
            if side["cancelled"][field] + side["kept"][field] != row[field]:
                raise SystemExit(f"{key} {field}")
        if sum(item[2] for item in data["games_72h"][key]) != row["game_starts"]:
            raise SystemExit(f"{key} game starts")
        if row["train_days_3"] > row["train_days_2plus"] > row["any_train_day"]:
            raise SystemExit(f"{key} training days")
    if data["variants"]["buyers_with_t1_or_t3"] != 0:
        raise SystemExit("T1/T3 appeared on buyers")
    memory = data["sections_72h"]["current"]
    if memory["memory"] < max(memory["lessons"], memory["palaces"], memory["plan"]):
        raise SystemExit("memory union is smaller than a part")
    split = button_split(data)
    if split["before"]["n"] + split["after"]["n"] != 155:
        raise SystemExit("button split total")


def fill_class(period: str, small: bool = False) -> str:
    return f"fill {period}" + (" hatched" if small else "")


def pair_bars(rows: list[tuple], period_labels: tuple[str, str] = ("09–15.11", "02–08.11")) -> str:
    """Rows: label, current n/m, previous n/m, current small, previous small."""
    output = []
    current_label, previous_label = period_labels
    for label, cur, prev, small_c, small_p in rows:
        nc, mc = cur
        np_, mp = prev
        note = '<span class="small-note">мало данных</span>' if small_c or small_p else ""
        output.append(f"""
<div class="h-row">
  <div class="h-label">{html.escape(label)}{note}</div>
  <div class="h-bars">
    <div class="bar-line">
      <span class="bar-period">{current_label}</span>
      <div class="track"><span class="{fill_class('current', small_c)}" style="width:{nc / mc * 100 if mc else 0:.3f}%"></span></div>
      <span class="bar-value">{html.escape(of(nc, mc))}</span>
    </div>
    <div class="bar-line">
      <span class="bar-period">{previous_label}</span>
      <div class="track"><span class="{fill_class('previous', small_p)}" style="width:{np_ / mp * 100 if mp else 0:.3f}%"></span></div>
      <span class="bar-value">{html.escape(of(np_, mp))}</span>
    </div>
  </div>
</div>""")
    return "".join(output)


def daily_chart(data: dict) -> str:
    maximum = max(n for _, n in data["daily_buyers"])
    days = []
    for day, n in data["daily_buyers"]:
        period = "previous" if day <= "2026-11-08" else "current"
        height = max(2, round(n / maximum * 146, 2))
        days.append(f"""
<div class="day" aria-label="{day}: {n} покупателей">
  <span class="day-value">{n}</span>
  <div class="day-track"><span class="day-fill {period}" style="height:{height}px"></span></div>
  <span class="day-label">{day[-2:]}</span>
</div>""")
    return f"""
<div class="days">{''.join(days)}</div>
<div class="week-labels"><span>02–08.11 · 58</span><span>09–15.11 · 155</span></div>
<p class="caption">Primer и PostHog сходятся</p>"""


def cancel_stacks(data: dict) -> str:
    labels = [
        ("cancel_lt_1h", "Первый час"),
        ("cancel_1h_6h", "1–6 ч"),
        ("cancel_6h_24h", "6–24 ч"),
        ("cancel_1d_3d", "1–3 суток"),
    ]
    stacks = []
    details = []
    for period, title in (("current", "09–15.11"), ("previous", "02–08.11")):
        row = data["cohort"][period]
        total = sum(row[key] for key, _ in labels)
        cohort_n = data["weeks"][period]["n"]
        segments = []
        for index, (key, label) in enumerate(labels):
            n = row[key]
            text = f"{n} из {total}" if index == 0 else ""
            segments.append(
                f'<span class="seg seg-{index}" style="width:{n / total * 100:.4f}%">{text}</span>'
            )
        stacks.append(f"""
<div class="stack-row">
  <div class="stack-title">{title}<span>{of(total, cohort_n)}</span></div>
  <div class="stack">{''.join(segments)}</div>
</div>""")
    for index, (_, label) in enumerate(labels):
        cur = data["cohort"]["current"][labels[index][0]]
        prev = data["cohort"]["previous"][labels[index][0]]
        details.append(f"""
<div class="stack-detail"><span class="detail-name"><i class="seg-dot seg-{index}"></i>{label}</span>
<span>09–15: <b>{of(cur, 77)}</b></span><span>02–08: <b>{of(prev, 15)}</b></span></div>""")
    return f"{''.join(stacks)}<div class=\"stack-details\">{''.join(details)}</div>"


def session_chart(data: dict) -> str:
    groups = [
        ("09–15 · отменили", data["first_session"]["current"]["cancelled"]),
        ("09–15 · не отменили", data["first_session"]["current"]["kept"]),
        ("02–08 · отменили", data["first_session"]["previous"]["cancelled"]),
        ("02–08 · не отменили", data["first_session"]["previous"]["kept"]),
    ]
    metrics = [("home_1h", "Главная"), ("cert_1h", "Сертификат"), ("train_1h", "Тренировка")]
    panels = []
    for key, title in metrics:
        bars = []
        for index, (label, group) in enumerate(groups):
            n, m = group[key], group["n"]
            period = "current" if index < 2 else "previous"
            small = m < 30
            bars.append(f"""
<div class="session-bar">
  <span class="session-value">{n} из {m}<small>{pct(n, m)}</small></span>
  <div class="session-track"><span class="{fill_class(period, small)}" style="height:{n / m * 100:.3f}%"></span></div>
  <span class="session-label">{label}{' · мало данных' if small else ''}</span>
</div>""")
        panels.append(f'<div class="session-panel"><h3>{title}</h3><div class="session-bars">{"".join(bars)}</div></div>')
    return f'<div class="session-grid">{"".join(panels)}</div><p class="caption">Главная вероятно путь к кнопке отмены, причину не утверждаем</p>'


def build_html(data: dict) -> str:
    cur = data["cohort"]["current"]
    prev = data["cohort"]["previous"]
    nc, np_ = data["weeks"]["current"]["n"], data["weeks"]["previous"]["n"]
    split = button_split(data)

    hour_rows = [
        ("Тренировка", (cur["train_1h"], nc), (prev["train_1h"], np_), False, False),
        ("Игра", (cur["game_1h"], nc), (prev["game_1h"], np_), False, False),
        ("Тест", (cur["test_1h"], nc), (prev["test_1h"], np_), False, False),
        ("Урок", (cur["lesson_1h"], nc), (prev["lesson_1h"], np_), False, False),
        ("Ничего не начали", (nc - cur["train_1h"], nc), (np_ - prev["train_1h"], np_), False, False),
        ("Отменили в первый час", (cur["cancel_1h"], nc), (prev["cancel_1h"], np_), False, False),
    ]
    day_rows = [
        ("Заход D1", (cur["visit_d1"], nc), (prev["visit_d1"], np_), False, False),
        ("Заход D2", (cur["visit_d2"], nc), (prev["visit_d2"], np_), False, False),
        ("Заход D3", (cur["visit_d3"], nc), (prev["visit_d3"], np_), False, False),
        ("0 дней с занятием", (nc - cur["any_train_day"], nc), (np_ - prev["any_train_day"], np_), False, False),
        ("1 день с занятием", (cur["any_train_day"] - cur["train_days_2plus"], nc), (prev["any_train_day"] - prev["train_days_2plus"], np_), False, False),
        ("2 дня с занятием", (cur["train_days_2plus"] - cur["train_days_3"], nc), (prev["train_days_2plus"] - prev["train_days_3"], np_), False, False),
        ("3 дня с занятием", (cur["train_days_3"], nc), (prev["train_days_3"], np_), False, False),
    ]
    section_order = [
        ("result", "Результат IQ"), ("home", "Главная"), ("profile", "Профиль"),
        ("settings", "Настройки"), ("certificate", "Сертификат"), ("games", "Игры"),
        ("track", "Трек"), ("explore", "Обзор"), ("tests", "Тесты"), ("memory", "Память"),
    ]
    section_rows = []
    for key, label in section_order:
        c = data["sections_72h"]["current"][key]
        p = data["sections_72h"]["previous"][key]
        section_rows.append((label, (c, nc), (p, np_), c < 30, p < 30))

    current_games = {name: people for name, people, _ in data["games_72h"]["current"]}
    previous_games = {name: people for name, people, _ in data["games_72h"]["previous"]}
    game_order = [name for name, _, _ in data["games_72h"]["current"]]
    game_order += [name for name, _, _ in data["games_72h"]["previous"] if name not in current_games]
    game_rows = []
    for name in game_order:
        c, p = current_games.get(name, 0), previous_games.get(name, 0)
        game_rows.append((name, (c, nc), (p, np_), c < 30, p < 30))

    before, after = split["before"], split["after"]
    button_rows = [
        ("Отмена в первый час", (after["cancel_1h"], after["n"]), (before["cancel_1h"], before["n"]), after["n"] < 30, before["n"] < 30),
        ("Отмена за 72 часа", (after["cancel_72h"], after["n"]), (before["cancel_72h"], before["n"]), after["n"] < 30, before["n"] < 30),
        ("Тренировка в первый час", (after["train_1h"], after["n"]), (before["train_1h"], before["n"]), after["n"] < 30, before["n"] < 30),
    ]

    result_current = data['sections_72h']['current']['result']
    result_previous = data['sections_72h']['previous']['result']
    memory_current = data['sections_72h']['current']['memory']
    positive_points = [
        f"Доля увидевших результат IQ <b>{trend(result_current, nc, result_previous, np_, 'выросла', 'упала')}</b>: <b>{of(result_current, nc)}</b> против <b>{of(result_previous, np_)}</b>.",
        f"Возвраты D2 <b>{trend(cur['visit_d2'], nc, prev['visit_d2'], np_)}</b>: <b>{of(cur['visit_d2'], nc)}</b> против <b>{of(prev['visit_d2'], np_)}</b>; D3 — с <b>{of(prev['visit_d3'], np_)}</b> до <b>{of(cur['visit_d3'], nc)}</b> (при нулевой базе рост в % не считаем).",
        f"Доля занимавшихся в 2+ дня <b>{trend(cur['train_days_2plus'], nc, prev['train_days_2plus'], np_, 'выросла', 'упала')}</b>: <b>{of(cur['train_days_2plus'], nc)}</b> против <b>{of(prev['train_days_2plus'], np_)}</b>.",
        f"Новый раздел памяти открыли <b>{of(memory_current, nc)}</b> за 72 часа; в прошлой когорте он был закрыт, поэтому рост в % не сравниваем.",
    ]
    main_points = [
        f"Отмены в первый час <b class=\"negative\">{trend(cur['cancel_1h'], nc, prev['cancel_1h'], np_)}</b>: <b>{of(cur['cancel_1h'], nc)}</b> против <b>{of(prev['cancel_1h'], np_)}</b>.",
        f"Отмены за 72 часа <b class=\"negative\">{trend(77, nc, 15, np_)}</b>: <b>77 из 155 (49,7%)</b> против <b>15 из 58 (25,9%)</b>.",
        f"<span class=\"positive-label\">Положительные моменты:</span> результат IQ <b>{trend(result_current, nc, result_previous, np_, 'вырос', 'упал')}</b>; D2 <b>{trend(cur['visit_d2'], nc, prev['visit_d2'], np_)}</b>; занятия в 2+ дня <b>{trend(cur['train_days_2plus'], nc, prev['train_days_2plus'], np_)}</b>; D3 — с 0 до <b>{pct(cur['visit_d3'], nc)}</b>; память — <b>{pct(memory_current, nc)}</b>.",
    ]

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>FoxIQ — когорты 09–15.11 и 02–08.11</title>
<style>
:root {{
  --bg:#fff5ee; --card:#fffdfb; --ink:#3a2a26; --muted:#8b6f65; --line:#f4d9cb;
  --accent:#e48a6c; --previous:#e7b39d; --chip:#fde3d6; --head:#fdebe1; --title:#7a3f2c;
  --good:#5f9c7a; --warn:#c9922f; --problem:#c9604f;
}}
* {{ box-sizing:border-box; }}
html {{ overflow-x:hidden; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; font-size:16px; line-height:1.45; -webkit-font-smoothing:antialiased; }}
.wrap {{ width:min(900px,100%); margin:0 auto; padding:32px 20px 64px; display:flex; flex-direction:column; gap:18px; }}
header {{ padding:8px 2px 12px; border-bottom:1px solid var(--line); }}
h1,h2,h3,p,ul {{ margin:0; }}
h1 {{ max-width:720px; color:var(--title); font-size:clamp(1.65rem,4vw,2.35rem); line-height:1.12; letter-spacing:-.035em; font-weight:720; }}
h2 {{ color:var(--title); font-size:1.08rem; line-height:1.25; letter-spacing:-.01em; }}
h3 {{ color:var(--title); font-size:.92rem; text-align:center; }}
.meta {{ margin-top:10px; color:var(--muted); font-size:.92rem; }}
.legend {{ display:flex; flex-wrap:wrap; gap:8px 18px; margin-top:16px; color:var(--muted); font-size:.79rem; }}
.legend span {{ display:inline-flex; align-items:center; gap:7px; }}
.swatch {{ width:20px; height:8px; border-radius:3px; background:var(--accent); }}
.swatch.previous {{ background:var(--previous); }}
.swatch.hatch {{ background:repeating-linear-gradient(135deg,var(--accent) 0 3px,var(--head) 3px 5px); border:1px solid var(--accent); }}
.card {{ min-width:0; background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; box-shadow:0 8px 24px rgba(228,138,108,.09); }}
.card-head {{ display:flex; align-items:baseline; gap:12px; margin-bottom:18px; }}
.index {{ color:var(--accent); font-size:.72rem; font-weight:750; letter-spacing:.12em; }}
.main-points {{ padding-left:1.25em; display:grid; gap:7px; }}
.main-points li::marker {{ color:var(--accent); }}
.positive-label {{ color:var(--good); font-weight:700; }}
.negative {{ color:var(--problem); }}
.positive-list li::marker {{ color:var(--good); }}
.caption {{ margin-top:14px; color:var(--muted); font-size:.83rem; }}
.h-row {{ display:grid; grid-template-columns:minmax(130px,180px) minmax(0,1fr); gap:14px; padding:10px 0; border-bottom:1px solid var(--line); }}
.h-row:last-child {{ border-bottom:0; padding-bottom:0; }}
.h-row:first-child {{ padding-top:0; }}
.h-label {{ min-width:0; font-size:.88rem; font-weight:620; overflow-wrap:anywhere; }}
.small-note {{ display:block; width:max-content; margin-top:3px; color:var(--warn); font-size:.7rem; font-weight:600; }}
.h-bars {{ min-width:0; display:grid; gap:5px; }}
.bar-line {{ min-width:0; display:grid; grid-template-columns:64px minmax(36px,1fr) minmax(124px,148px); gap:10px; align-items:center; }}
.bar-period {{ color:var(--title); font-size:.72rem; font-weight:700; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.track {{ height:15px; min-width:0; overflow:hidden; border-radius:4px; background:var(--head); }}
.fill {{ display:block; min-width:0; height:100%; border-radius:4px; background:var(--accent); }}
.fill.previous {{ background:var(--previous); }}
.fill.hatched {{ background:repeating-linear-gradient(135deg,var(--accent) 0 5px,var(--head) 5px 8px); border:1px solid var(--accent); }}
.fill.previous.hatched {{ background:repeating-linear-gradient(135deg,var(--previous) 0 5px,var(--head) 5px 8px); border-color:var(--previous); }}
.bar-value {{ color:var(--ink); font-size:.76rem; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.days {{ height:196px; display:grid; grid-template-columns:repeat(14,minmax(0,1fr)); gap:5px; align-items:end; }}
.day {{ min-width:0; display:grid; grid-template-rows:20px 150px 20px; gap:3px; text-align:center; }}
.day-value {{ font-size:.75rem; font-weight:700; font-variant-numeric:tabular-nums; }}
.day-track {{ height:150px; display:flex; align-items:flex-end; justify-content:center; border-bottom:1px solid var(--line); }}
.day-fill {{ display:block; width:100%; max-width:34px; min-height:2px; border-radius:4px 4px 0 0; background:var(--accent); }}
.day-fill.previous {{ background:var(--previous); }}
.day-label {{ color:var(--muted); font-size:.7rem; }}
.week-labels {{ display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:5px; color:var(--muted); font-size:.74rem; text-align:center; }}
.stack-row {{ display:grid; grid-template-columns:120px minmax(0,1fr); gap:14px; align-items:center; margin-bottom:12px; }}
.stack-title {{ font-size:.83rem; font-weight:700; }}
.stack-title span {{ display:block; margin-top:3px; color:var(--muted); font-size:.72rem; font-weight:500; }}
.stack {{ height:42px; display:flex; overflow:hidden; border-radius:7px; background:var(--head); }}
.seg {{ min-width:0; display:flex; align-items:center; justify-content:center; overflow:hidden; color:var(--ink); font-size:.74rem; font-weight:700; white-space:nowrap; border-right:2px solid var(--card); }}
.seg:last-child {{ border-right:0; }}
.seg-0 {{ background:var(--accent); }}
.seg-1 {{ background:#edb39c; }}
.seg-2 {{ background:#f2c9b7; }}
.seg-3 {{ background:#f8dfd2; }}
.stack-details {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px 20px; margin-top:18px; padding-top:14px; border-top:1px solid var(--line); }}
.stack-detail {{ display:grid; gap:2px; color:var(--muted); font-size:.72rem; }}
.stack-detail b {{ color:var(--ink); font-weight:650; }}
.detail-name {{ display:flex; align-items:center; gap:6px; color:var(--ink); font-weight:650; }}
.seg-dot {{ width:9px; height:9px; flex:0 0 auto; border-radius:2px; }}
.split-legend {{ display:flex; gap:14px; margin:-6px 0 14px; color:var(--muted); font-size:.76rem; }}
.session-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:16px; }}
.session-panel {{ min-width:0; padding:12px 8px; background:var(--bg); border-radius:12px; }}
.session-panel h3 {{ margin-bottom:12px; }}
.session-bars {{ height:226px; display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:5px; }}
.session-bar {{ min-width:0; display:grid; grid-template-rows:38px 142px 42px; gap:2px; text-align:center; }}
.session-value {{ font-size:.66rem; font-weight:700; font-variant-numeric:tabular-nums; }}
.session-value small {{ display:block; color:var(--muted); font-size:.62rem; font-weight:500; }}
.session-track {{ height:142px; display:flex; align-items:flex-end; justify-content:center; border-bottom:1px solid var(--line); }}
.session-track .fill {{ width:72%; height:0; min-height:2px; border-radius:4px 4px 0 0; }}
.session-label {{ color:var(--muted); font-size:.58rem; line-height:1.2; overflow-wrap:anywhere; }}
.compact-list {{ padding-left:1.15em; display:grid; gap:7px; font-size:.9rem; }}
.hypotheses li {{ padding-left:2px; }}
.hypotheses span {{ display:block; color:var(--warn); font-size:.72rem; }}
.method {{ color:var(--muted); font-size:.82rem; text-align:center; }}
.method a {{ color:var(--title); text-underline-offset:3px; }}
@media (max-width:640px) {{
  .wrap {{ padding:22px 12px 44px; gap:14px; }}
  .card {{ padding:16px 13px; }}
  .h-row {{ grid-template-columns:1fr; gap:7px; padding:11px 0; }}
  .h-label {{ font-size:.84rem; }}
  .small-note {{ display:inline; margin-left:6px; }}
  .bar-line {{ grid-template-columns:58px minmax(24px,1fr) 124px; gap:7px; }}
  .bar-period {{ font-size:.67rem; }}
  .bar-value {{ font-size:.69rem; }}
  .days {{ gap:3px; }}
  .day-value {{ font-size:.68rem; }}
  .stack-row {{ grid-template-columns:92px minmax(0,1fr); gap:9px; }}
  .stack {{ height:38px; }}
  .stack-title {{ font-size:.75rem; }}
  .stack-title span {{ font-size:.65rem; }}
  .stack-details {{ grid-template-columns:1fr; gap:10px; }}
  .session-grid {{ grid-template-columns:1fr; }}
  .session-bars {{ height:215px; }}
  .session-bar {{ grid-template-rows:38px 132px 40px; }}
  .session-track {{ height:132px; }}
  .session-value {{ font-size:.72rem; }}
  .session-label {{ font-size:.63rem; }}
}}
</style>
</head>
<body>
<main class="wrap">
<header>
  <h1>FoxIQ: когорта 09–15.11 против 02–08.11</h1>
  <p class="meta">Покупатели триала: 09–15.11 — 155; 02–08.11 — 58.</p>
  <div class="legend"><span><i class="swatch"></i>09–15.11</span><span><i class="swatch previous"></i>02–08.11</span><span><i class="swatch hatch"></i>мало данных</span></div>
</header>
<section class="card">
  <h2>Главное</h2>
  <ul class="main-points"><li>{main_points[0]}</li><li>{main_points[1]}</li><li>{main_points[2]}</li></ul>
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">01</span><h2>Покупатели по дням</h2></div>
  {daily_chart(data)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">02</span><h2>Первый час</h2></div>
  {pair_bars(hour_rows)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">03</span><h2>Отмены по времени от покупки · до 72 часов</h2></div>
  {cancel_stacks(data)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">04</span><h2>Заходы и дни с занятием · 72 часа</h2></div>
  {pair_bars(day_rows)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">05</span><h2>Что используют за 72 часа</h2></div>
  {pair_bars(section_rows)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">06</span><h2>Игры за 72 часа · люди</h2></div>
  {pair_bars(game_rows)}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">07</span><h2>До и после кнопки отмены с 11.11</h2></div>
  <div class="split-legend"><span><i class="swatch"></i>11–15.11: 105</span><span><i class="swatch previous"></i>09–10.11: 50</span></div>
  {pair_bars(button_rows, ("11–15.11", "09–10.11"))}
</section>
<section class="card chart-card">
  <div class="card-head"><span class="index">08</span><h2>Первая сессия · первый час</h2></div>
  {session_chart(data)}
</section>
<section class="card">
  <h2>Изменения продукта между неделями</h2>
  <ul class="compact-list">
    <li>Кнопка отмены на каждом экране — с 11.11.</li>
    <li>Раздел памяти открыт всем — с 11.11.</li>
    <li>Лимит ошибок и сердечки в уроках и дворцах.</li>
    <li>Серия писем M — с 12.11.</li>
  </ul>
</section>
<section class="card">
  <h2>Гипотезы</h2>
  <ul class="compact-list hypotheses">
    <li>Кнопка отмены могла сдвинуть часть отмен в первый час.<span>гипотеза, не подтверждена данными</span></li>
    <li>Серия M могла изменить возвраты.<span>проверяется</span></li>
  </ul>
</section>
<section class="card">
  <h2>Положительные моменты · без учёта роста трафика</h2>
  <ul class="compact-list positive-list">{''.join(f'<li>{point}</li>' for point in positive_points)}</ul>
  <p class="caption">Возвраты и регулярные занятия выше, но их абсолютные доли остаются низкими.</p>
</section>
<p class="method"><a href="foxiq-cohort-compare-2026-11-09-metodika.md">Методика, определения метрик и проверки до расчётов</a></p>
</main>
</body>
</html>
"""


def build_md(data: dict) -> str:
    split = button_split(data)
    before, after = split["before"], split["after"]
    return f"""# Методика: когорты FoxIQ 09–15.11 и 02–08.11

Файл считает `scripts/foxiq-cohort-compare.py`. Отчёт: `reports/foxiq-cohort-compare-2026-11-09.html`. Выгрузка агрегатов: `reports/data/foxiq-2026-11-18/cohort_aggregates.json`. Почт и номеров карт в этих файлах нет.

## Кто вошёл

Покупатель — человек из `reports/data/foxiq-2026-11-16/buyers.csv` с пустым `exclusion_reason` и `is_test` не равным 1. Это первый `subscription_started` FoxIQ. Тестовый фильтр почты тот же, что в `playbook/posthog.md`, плюс исключения, уже записанные в этом файле.

Неделя — дата покупки по МСК. Прошлая: 02.11.2026 00:00 – 08.11.2026 23:59:59. Текущая: 09.11.2026 00:00 – 15.11.2026 23:59:59. В обеих 58 и 155 человек. По каждому дню Primer, первый успешный платёж $1, и PostHog дают одно число. Для поведения в приложении отдельной цифры Primer нет: заходы, игры и отмены взяты из PostHog.

Наблюдение событий: с момента покупки до 18.11.2026 23:59:59 МСК, то есть 18.11.2026 20:59:59 UTC.

## Что проверено до долей

T1 и T3. За 01.11 21:00 UTC – 18.11 20:59 UTC ни один из 213 покупателей не получил `t1_variant` или `t3_variant`. Когорты по варианту не делились. Первое `t1_variant` в проекте — 13.11.2026 11:20 UTC на почтах тестового фильтра. Первое `t3_variant` — 17.11.2026 12:16 UTC, тоже тестовые почты. 18.11.2026 09:35 UTC один человек вне этих когорт получил t1=A. Журнал 16.11 фиксирует решение не запускать T1 на живых. Журнал 18.11 фиксирует слова Корюна, что T1 включён для новых тестовых аккаунтов.

Дыры. Число событий `foxiq` и `foxiq_ff` посчитано по дням МСК с 02.11 по 18.11. Пустого дня нет. Образец дыры остаётся прежним: 11.10 01:00 – 13.10 07:00 UTC. 02.11 тише других дней покупки. 16–18.11 ниже, потому что неделя покупок кончилась.

Окно 72 часов. Для каждого покупателя проверено, что покупка плюс 24, 48 и 72 часа не позже 18.11.2026 20:59:59 UTC. Условие выполнено у 155 из 155 и у 58 из 58. Строка «окно не прошло» в отчёте не используется и в ноль не переводится.

Суммы. Дневные покупки в `buyers.csv` совпадают с агрегатом: 58 и 155. Отмены за 72 часа по четырём корзинам: 77 и 15. Полное число отмен до конца наблюдения: 85 и 33; в график 100%-полос входят только одинаковые 72-часовые окна, поэтому их знаменатели — 77 и 15, а не 85 и 33.

## Определения

Первый час. От `subscription_started` до плюс 60 минут.

Тренировка. `game_started`, `test_started` или `lesson_completed`. `first_run_started` тренировкой не считается.

«Ничего не начали». В первый час нет ни одного из трёх событий тренировки. Человек мог видеть результат и главную.

Отмена. `subscription_cancelled` с `reason=user_initiated`. Берётся первое такое событие. `subscription_expired` с `payment_failed` в отмены пользователя не входит.

Время отмены. Первая корзина — меньше 60 минут; вторая — 60–359 минут; третья — 360–1439 минут; четвёртая — 1440–4319 минут. Составные полосы показывают доли внутри отмен за первые 72 часа. Отмены позже 72 часов в этот график не входят.

Заход в приложение. `$pageview`, `screen_view` или `app_opened`, проект foxiq, библиотека web, путь не из `/auto-login`, `/auth`, `/magic-link-login`, `/onboarding`.

D1, D2, D3. Календарный день МСК: дата покупки плюс 1, 2 или 3. Это не скользящие 24 часа. Знаменатель — люди, у которых соответствующее окно уже прошло.

День с занятием. Календарный день МСК внутри 72 часов, в который был `game_started`, `test_started` или `lesson_completed`.

Использование. Экраны и игры считаются за первые 72 часа после покупки, чтобы у обеих недель была одна длина окна. Экраны входа в разделы не входят. Человек может быть в нескольких играх и разделах.

Память. Пути `/lessons`, `/palaces`, `/plan`. Человек в строке «память» один, даже если открыл несколько путей. Игра `fox-memory` в эту строку не входит: она запускалась и в неделе 02–08.11.

Сертификат. Экран `/iq-certificate`.

Малая выборка. В разделах и играх штриховка и пометка «мало данных» ставятся, если действие совершили меньше 30 человек. В первой сессии ориентир — размер сравниваемой группы: группа «02–08, не отменили» включает 25 человек и заштрихована.

## До и после кнопки отмены

Текущая когорта разделена по дате покупки: 09–10.11 — {before['n']} человек, 11–15.11 — {after['n']} человек.

Тренировка в первый час считается по полям `game_started`, `test_started`, `lesson_completed` в `buyers.csv`; эти поля описывают именно час после покупки. Получено {before['train_1h']} и {after['train_1h']}, в сумме 22.

Для 09–10.11 отмены в первый час и за 72 часа посчитаны по первому `subscription_cancelled` с `reason=user_initiated` в `cancel_events.csv`: {before['cancel_1h']} и {before['cancel_72h']}. Полное 72-часовое окно этой подгруппы находится внутри выгрузки. Для 11–15.11 значения получены вычитанием из сверенного итога текущей когорты: {after['cancel_1h']} и {after['cancel_72h']}. Суммы подгрупп: 63 в первый час и 77 за 72 часа.

## Чего скрипт не делает

Не ходит в PostHog заново. Не читает файл Primer с почтами и картами. Не выводит персональные строки. Не меняет ClickUp. Не делит когорту по T1, потому что у покупателей варианта нет.
"""


def main() -> None:
    data = load()
    check(data)
    html_text = build_html(data)
    md_text = build_md(data)
    if EMAIL.search(html_text) or EMAIL.search(md_text):
        raise SystemExit("output contains an email address")
    for forbidden in ("<script", "<table", "События по дням", "Проверено до расчётов", "Кориун", ":hover", "onmouseover"):
        if forbidden.lower() in html_text.lower():
            raise SystemExit(f"forbidden HTML content: {forbidden}")
    if html_text.count('class="card chart-card"') != 8:
        raise SystemExit("expected eight chart cards")
    OUT_HTML.write_text(html_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"wrote {OUT_HTML.name} and {OUT_MD.name}")


if __name__ == "__main__":
    main()
