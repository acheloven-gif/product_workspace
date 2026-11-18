"""FoxIQ cohort comparison, buyers 02–08.11 vs 09–15.11, observed through 18.11 23:59 MSK.

Reads reports/data/foxiq-2026-11-18/cohort_aggregates.json and buyers.csv.
Writes the HTML report and the methodology note. Does not call PostHog.
"""

from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "reports" / "data" / "foxiq-2026-11-18" / "cohort_aggregates.json"
BUYERS = ROOT / "reports" / "data" / "foxiq-2026-11-16" / "buyers.csv"
OUT_HTML = ROOT / "reports" / "foxiq-cohort-compare-2026-11-09.html"
OUT_MD = ROOT / "reports" / "foxiq-cohort-compare-2026-11-09-metodika.md"

SMALL = "мало данных, тренд ненадёжен"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def pct(n: int, m: int) -> str:
    if m <= 0:
        return "нет данных"
    return f"{n / m * 100:.1f}".replace(".", ",") + "%"


def of(n: int, m: int) -> str:
    return f"{n} из {m} ({pct(n, m)})"


def pp(n1: int, m1: int, n0: int, m0: int, comparable: bool) -> str:
    if not comparable or m1 <= 0 or m0 <= 0:
        return "н/с"
    delta = (n1 / m1 - n0 / m0) * 100
    sign = "+" if delta > 0 else ""
    return sign + f"{delta:.1f}".replace(".", ",") + " п.п."


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def buyer_days() -> dict[str, int]:
    days: dict[str, int] = {}
    with BUYERS.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["is_test"] == "1" or row["exclusion_reason"].strip():
                continue
            day = row["purchased_at_msk"][:10]
            days[day] = days.get(day, 0) + 1
    return days


def check(data: dict) -> None:
    days = buyer_days()
    file_days = {day: n for day, n in data["daily_buyers"]}
    if days != file_days:
        raise SystemExit(f"buyers.csv days {days} != export {file_days}")
    prev = sum(n for day, n in file_days.items() if day <= "2026-11-08")
    curr = sum(n for day, n in file_days.items() if "2026-11-09" <= day <= "2026-11-15")
    if (prev, curr) != (58, 155):
        raise SystemExit(f"cohort size {prev}, {curr}")
    for key in ("previous", "current"):
        row = data["cohort"][key]
        n = data["weeks"][key]["n"]
        if n != (58 if key == "previous" else 155):
            raise SystemExit(key)
        buckets = (
            row["cancel_lt_1h"]
            + row["cancel_1h_6h"]
            + row["cancel_6h_24h"]
            + row["cancel_1d_3d"]
            + row["cancel_after_3d"]
        )
        if buckets != row["cancelled"]:
            raise SystemExit(f"{key} cancel buckets {buckets} != {row['cancelled']}")
        if row["cancel_1h"] != row["cancel_lt_1h"]:
            raise SystemExit(f"{key} first-hour cancel mismatch")
        if row["d1_ready"] != n or row["d2_ready"] != n or row["d3_ready"] != n:
            raise SystemExit(f"{key} window is not complete")
        side = data["first_session"][key]
        if side["cancelled"]["n"] + side["kept"]["n"] != n:
            raise SystemExit(f"{key} split")
        if side["cancelled"]["n"] != row["cancelled"]:
            raise SystemExit(f"{key} cancelled split")
        for field in ("train_1h", "game_1h", "test_1h", "lesson_1h"):
            total = side["cancelled"][field] + side["kept"][field]
            if total != row[field]:
                raise SystemExit(f"{key} {field} {total} != {row[field]}")
        starts = sum(item[2] for item in data["games_72h"][key])
        if starts != row["game_starts"]:
            raise SystemExit(f"{key} game starts {starts}")
        if row["train_days_3"] > row["train_days_2plus"] > row["any_train_day"]:
            raise SystemExit(f"{key} training days")
        if row["nothing_screens_1h"] > n - row["train_1h"]:
            raise SystemExit(f"{key} nothing screens")
    if data["variants"]["buyers_with_t1_or_t3"] != 0:
        raise SystemExit("T1/T3 appeared on buyers; split the cohorts before publishing")
    memory = data["sections_72h"]["current"]
    if memory["memory"] < max(memory["lessons"], memory["palaces"], memory["plan"]):
        raise SystemExit("memory union is smaller than a part")


def chip(show: bool) -> str:
    if not show:
        return ""
    return f'<div><span class="chip">{SMALL}</span></div>'


def row(name: str, note: str, left: str, right: str, change: str, sample: str, small: bool) -> str:
    return (
        "<tr>"
        f"<td><div class=\"name\">{html.escape(name)}</div>{chip(small)}"
        f"<p class=\"note\">{html.escape(note)}</p></td>"
        f"<td class=\"num\">{html.escape(left)}</td>"
        f"<td class=\"num\">{html.escape(right)}</td>"
        f"<td class=\"num\">{html.escape(change)}</td>"
        f"<td class=\"sample\">{html.escape(sample)}</td>"
        "</tr>"
    )


def share_row(name: str, note: str, cur: int, prev: int, mcur: int, mprev: int, small: bool) -> str:
    return row(
        name,
        note,
        of(cur, mcur),
        of(prev, mprev),
        pp(cur, mcur, prev, mprev, not small),
        f"тек. n = {cur} из {mcur}; пред. n = {prev} из {mprev}",
        small,
    )


def build_html(data: dict) -> str:
    cur = data["cohort"]["current"]
    prev = data["cohort"]["previous"]
    nc, np_ = 155, 58
    nothing_c = nc - cur["train_1h"]
    nothing_p = np_ - prev["train_1h"]
    lines = [
        f"Тренировку в первый час начали {of(cur['train_1h'], nc)} против {of(prev['train_1h'], np_)}. Ничего не начали {of(nothing_c, nc)} и {of(nothing_p, np_)}.",
        f"В первый час отменили {of(cur['cancel_1h'], nc)} против {of(prev['cancel_1h'], np_)}. К 18.11 23:59 МСК отменили {of(cur['cancelled'], nc)} и {of(prev['cancelled'], np_)}.",
        f"На следующий календарный день зашли {of(cur['visit_d1'], nc)} и {of(prev['visit_d1'], np_)}. Окно 72 часов прошло у {of(cur['d3_ready'], nc)} и у {of(prev['d3_ready'], np_)}.",
        "T1 и T3 этим 213 покупателям не назначались, недели по варианту не делятся. Дыры в событиях 02–18.11 нет.",
        f"В новой когорте главную в первый час открыли {of(data['first_session']['current']['cancelled']['home_1h'], 85)} отменивших и {of(data['first_session']['current']['kept']['home_1h'], 70)} не отменивших.",
    ]
    head = "".join(f"<li>{html.escape(line)}</li>" for line in lines)

    def days_table() -> str:
        body = []
        for day, n in data["daily_buyers"]:
            klass = "prev" if day <= "2026-11-08" else "now"
            label = ".".join(reversed(day.split("-")))
            body.append(
                f"<tr class=\"{klass}\"><td>{label}</td><td class=\"num\">{n}</td><td class=\"num\">{n}</td></tr>"
            )
        return "".join(body)

    def events_table() -> str:
        body = []
        for day, events, people in data["daily_events"]:
            label = ".".join(reversed(day.split("-")))
            body.append(
                f"<tr><td>{label}</td><td class=\"num\">{events}</td><td class=\"num\">{people}</td></tr>"
            )
        return "".join(body)

    hour_rows = [
        share_row(
            "Тренировка: игра, тест или урок",
            "game_started, test_started или lesson_completed в первый час после покупки. Человек считается один раз.",
            cur["train_1h"], prev["train_1h"], nc, np_, False,
        ),
        share_row(
            "Начали игру",
            "Хотя бы один game_started в первый час.",
            cur["game_1h"], prev["game_1h"], nc, np_, False,
        ),
        share_row(
            "Начали тест",
            "Хотя бы один test_started в первый час.",
            cur["test_1h"], prev["test_1h"], nc, np_, False,
        ),
        share_row(
            "Завершили урок",
            "Хотя бы один lesson_completed в первый час. Старт урока отдельным событием не считается.",
            cur["lesson_1h"], prev["lesson_1h"], nc, np_, False,
        ),
        share_row(
            "Ничего из этого не начали",
            "В первый час не было ни game_started, ни test_started, ни lesson_completed. Это не то же самое, что «ушли за минуту».",
            nothing_c, nothing_p, nc, np_, False,
        ),
        share_row(
            "Не открыли и экран раздела",
            "К предыдущей строке добавлено: не было экрана /games, /tests, /lessons, /track или /palaces в первый час.",
            cur["nothing_screens_1h"], prev["nothing_screens_1h"], nc, np_, False,
        ),
        share_row(
            "Отменили в первый час",
            "subscription_cancelled, reason=user_initiated, раньше чем через 60 минут после покупки.",
            cur["cancel_1h"], prev["cancel_1h"], nc, np_, False,
        ),
    ]

    zero_days_c = nc - cur["any_train_day"]
    zero_days_p = np_ - prev["any_train_day"]
    one_day_c = cur["any_train_day"] - cur["train_days_2plus"]
    one_day_p = prev["any_train_day"] - prev["train_days_2plus"]
    two_day_c = cur["train_days_2plus"] - cur["train_days_3"]
    two_day_p = prev["train_days_2plus"] - prev["train_days_3"]
    day_rows = [
        share_row(
            "Заход на D1",
            "Следующий календарный день после дня покупки, МСК. Заход — событие приложения, кроме /auto-login, /auth, /magic-link-login и /onboarding. Окно 24 часа прошло у всех.",
            cur["visit_d1"], prev["visit_d1"], cur["d1_ready"], prev["d1_ready"], False,
        ),
        share_row(
            "Заход на D2",
            "Второй календарный день после дня покупки. Окно 48 часов прошло у всех.",
            cur["visit_d2"], prev["visit_d2"], cur["d2_ready"], prev["d2_ready"], False,
        ),
        share_row(
            "Заход на D3",
            "Третий календарный день после дня покупки. Окно 72 часа прошло у всех, поэтому «окно не прошло» никому не ставилось.",
            cur["visit_d3"], prev["visit_d3"], cur["d3_ready"], prev["d3_ready"], False,
        ),
        share_row(
            "0 дней с занятием за 72 часа",
            "Ни одного дня с game_started, test_started или lesson_completed в первые 72 часа.",
            zero_days_c, zero_days_p, nc, np_, False,
        ),
        share_row(
            "1 день с занятием",
            "Ровно один календарный день МСК с таким событием внутри 72 часов.",
            one_day_c, one_day_p, nc, np_, True,
        ),
        share_row(
            "2 дня с занятием",
            "Ровно два таких дня. Группа меньше 30.",
            two_day_c, two_day_p, nc, np_, True,
        ),
        share_row(
            "3 дня с занятием",
            "Три таких дня внутри 72 часов. Группа меньше 30.",
            cur["train_days_3"], prev["train_days_3"], nc, np_, True,
        ),
        share_row(
            "Играли хотя бы раз",
            "Люди с game_started в первые 72 часа. Число стартов — отдельная строка.",
            cur["people_games"], prev["people_games"], nc, np_, False,
        ),
        row(
            "Стартов игр",
            "Сумма game_started за 72 часа, не число людей. Один человек может начать много игр.",
            str(cur["game_starts"]),
            str(prev["game_starts"]),
            "н/с",
            f"тек. события = {cur['game_starts']}; пред. события = {prev['game_starts']}",
            False,
        ),
        share_row(
            "Начали тест хотя бы раз",
            "Люди с test_started в первые 72 часа.",
            cur["people_tests"], prev["people_tests"], nc, np_, False,
        ),
        row(
            "Стартов тестов",
            "Сумма test_started за 72 часа.",
            str(cur["test_starts"]),
            str(prev["test_starts"]),
            "н/с",
            f"тек. события = {cur['test_starts']}; пред. события = {prev['test_starts']}",
            True,
        ),
    ]

    section_order = [
        ("result", "Результат IQ, экран /iq-result"),
        ("home", "Главная, / или /home"),
        ("profile", "Профиль, /profile"),
        ("settings", "Настройки, /settings"),
        ("certificate", "Сертификат, экран /iq-certificate"),
        ("games", "Игры, экран /games"),
        ("track", "Трек уроков, /track"),
        ("explore", "Обзор, /explore"),
        ("tests", "Тесты, экран /tests"),
        ("memory", "Память: /lessons, /palaces или /plan, человек один раз"),
        ("lessons", "Уроки памяти, /lessons"),
        ("palaces", "Дворцы, /palaces"),
        ("plan", "План, /plan"),
    ]
    section_rows = []
    for key, title in section_order:
        small = key in {"lessons", "palaces", "plan"}
        section_rows.append(
            share_row(
                title,
                "Люди с $pageview или screen_view этого пути в первые 72 часа. Вход через /auto-login, /auth и /magic-link-login в разделы не входит.",
                data["sections_72h"]["current"][key],
                data["sections_72h"]["previous"][key],
                nc,
                np_,
                small,
            )
        )
    section_rows.append(
        share_row(
            "Имя на сертификате отправлено",
            "certificate_name_submitted в первые 72 часа. Это действие, не открытие экрана.",
            data["certificate_name_72h"]["current"],
            data["certificate_name_72h"]["previous"],
            nc,
            np_,
            False,
        )
    )
    mon_c = data["monetization"]["current"]
    mon_p = data["monetization"]["previous"]
    money_rows = [
        share_row(
            "Страница сердечек",
            "hearts_page_shown, placement=no_energy_lesson, в первые 72 часа. Покупкой не является.",
            mon_c["hearts_page"], mon_p["hearts_page"], nc, np_, True,
        ),
        share_row(
            "Покупка сердечек",
            "in_app_purchase_success с сердечками. Таких событий нет.",
            mon_c["hearts_purchase"], mon_p["hearts_purchase"], nc, np_, True,
        ),
        share_row(
            "Покупка монет",
            "Искались paywall_open_tokens и события с coin или token в имени. У покупателей их нет.",
            mon_c["coin_purchase"], mon_p["coin_purchase"], nc, np_, True,
        ),
        share_row(
            "Пейволл в приложении за 72 часа",
            "paywall_shown в первые 72 часа после покупки.",
            mon_c["paywall_72h"], mon_p["paywall_72h"], nc, np_, True,
        ),
        share_row(
            "Пейволл в приложении до 18.11 23:59",
            f"Одно событие в каждой когорте позже 72 часов. Текущая: placement={mon_c['paywall_placement']}. Прошлая: placement={mon_p['paywall_placement']}.",
            mon_c["paywall_to_cutoff"], mon_p["paywall_to_cutoff"], nc, np_, True,
        ),
        share_row(
            "Покупка месяца в приложении",
            "in_app_purchase_success, purchase_type=subscription, product_id=month, placement=home. Это не сердечки и не монеты.",
            mon_c["subscription_month_purchase"], mon_p["subscription_month_purchase"], nc, np_, True,
        ),
        share_row(
            "Brain Score",
            "У этих покупателей до 18.11 23:59 нет brain_score_shown, brain_profile_shown, brain_score_changed и brain_score_certificate_downloaded. События в проекте есть у других людей.",
            mon_c["brain_score"], mon_p["brain_score"], nc, np_, False,
        ),
    ]

    game_names = []
    seen = []
    for name, _, _ in data["games_72h"]["current"]:
        seen.append(name)
    for name, _, _ in data["games_72h"]["previous"]:
        if name not in seen:
            seen.append(name)
    cur_games = {name: (people, starts) for name, people, starts in data["games_72h"]["current"]}
    prev_games = {name: (people, starts) for name, people, starts in data["games_72h"]["previous"]}
    for name in seen:
        c_people, c_starts = cur_games.get(name, (0, 0))
        p_people, p_starts = prev_games.get(name, (0, 0))
        game_names.append(
            row(
                name,
                "game_started, свойство game, первые 72 часа. Человек может быть в нескольких строках.",
                f"{c_people} из {nc}, стартов {c_starts}",
                f"{p_people} из {np_}, стартов {p_starts}",
                "н/с",
                f"тек. n = {c_people} из {nc}; пред. n = {p_people} из {np_}",
                True,
            )
        )

    cancel_rows = [
        share_row(
            "Отменили к 18.11 23:59",
            "Хотя бы один subscription_cancelled с reason=user_initiated между покупкой и концом наблюдения. payment_failed сюда не входит.",
            cur["cancelled"], prev["cancelled"], nc, np_, False,
        ),
        share_row(
            "В первый час",
            "Меньше 60 минут от покупки до первой такой отмены.",
            cur["cancel_lt_1h"], prev["cancel_lt_1h"], nc, np_, False,
        ),
        share_row(
            "От 1 до 6 часов",
            "60–359 минут.",
            cur["cancel_1h_6h"], prev["cancel_1h_6h"], nc, np_, True,
        ),
        share_row(
            "От 6 до 24 часов",
            "360–1439 минут.",
            cur["cancel_6h_24h"], prev["cancel_6h_24h"], nc, np_, True,
        ),
        share_row(
            "От 1 до 3 суток",
            "1440–4319 минут.",
            cur["cancel_1d_3d"], prev["cancel_1d_3d"], nc, np_, True,
        ),
        share_row(
            "Позже 3 суток",
            "4320 минут и больше, но не позже 18.11 23:59 МСК.",
            cur["cancel_after_3d"], prev["cancel_after_3d"], nc, np_, False,
        ),
        share_row(
            "Отменили и ни разу не зашли в приложение",
            "До отмены и до конца окна не было события приложения вне /auto-login, /auth, /magic-link-login и /onboarding.",
            cur["cancel_no_app"], prev["cancel_no_app"], nc, np_, True,
        ),
    ]

    session_fields = [
        ("train_1h", "Тренировка в первый час"),
        ("game_1h", "Игра в первый час"),
        ("test_1h", "Тест в первый час"),
        ("lesson_1h", "Урок завершён в первый час"),
        ("result_1h", "Экран результата в первый час"),
        ("cert_1h", "Сертификат в первый час"),
        ("home_1h", "Главная в первый час"),
        ("left_minute", "Ушли за минуту"),
    ]
    session_rows = []
    for key, title in session_fields:
        cc = data["first_session"]["current"]["cancelled"]
        ck = data["first_session"]["current"]["kept"]
        pc = data["first_session"]["previous"]["cancelled"]
        pk = data["first_session"]["previous"]["kept"]
        note = "Отмена — user_initiated к 18.11 23:59. Первая сессия считается одинаково в обеих группах."
        if key == "left_minute":
            note = "Как в v4.23: от первого до последнего события приложения в первые 30 минут прошло меньше 60 секунд. Это не строка «ничего не начали»."
        session_rows.append(
            "<tr>"
            f"<td><div class=\"name\">{html.escape(title)}</div>"
            f"<p class=\"note\">{html.escape(note)}</p></td>"
            f"<td class=\"num\">{html.escape(of(cc[key], cc['n']))}</td>"
            f"<td class=\"num\">{html.escape(of(ck[key], ck['n']))}</td>"
            f"<td class=\"num\">{html.escape(of(pc[key], pc['n']))}</td>"
            f"<td class=\"num\">{html.escape(of(pk[key], pk['n']))}<div><span class=\"chip\">{SMALL}</span></div></td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FoxIQ — когорты 09–15.11 и 02–08.11</title>
<style>
:root {{
  --bg:#fff5ee; --card:#fffdfb; --ink:#3a2a26; --muted:#8b6f65; --line:#f4d9cb;
  --accent:#e48a6c; --chip:#fde3d6; --head:#fdebe1; --title:#7a3f2c;
  --good:#5f9c7a; --warn:#c9922f; --problem:#c9604f;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif; font-size:16px; line-height:1.5; }}
.wrap {{ max-width:900px; margin:0 auto; padding:32px 20px 72px; display:flex; flex-direction:column; gap:22px; }}
h1,h2 {{ margin:0; line-height:1.25; color:var(--title); }}
h1 {{ font-size:1.7rem; }}
h2 {{ font-size:1.2rem; }}
p,ul,ol {{ margin:0; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:18px 20px; box-shadow:0 8px 24px rgba(228,138,108,.12); }}
.card ol, .card ul {{ padding-left:1.2em; display:flex; flex-direction:column; gap:8px; }}
.meta {{ color:var(--muted); }}
.tbl {{ overflow-x:auto; border:1px solid var(--line); border-radius:16px; background:var(--card); }}
table {{ border-collapse:collapse; width:100%; }}
th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ background:var(--head); color:var(--title); font-size:.78rem; }}
tr:last-child td {{ border-bottom:none; }}
.num {{ font-variant-numeric:tabular-nums; }}
.name {{ font-weight:650; }}
.note {{ color:var(--muted); font-size:.84rem; margin-top:4px; }}
.sample {{ color:var(--muted); font-size:.84rem; }}
.chip {{ display:inline-flex; margin-top:6px; padding:2px 10px; border-radius:999px; background:var(--chip); color:var(--warn); font-size:.75rem; font-weight:650; }}
.legend {{ color:var(--muted); font-size:.9rem; }}
tr.prev td:first-child {{ color:var(--muted); }}
</style>
</head>
<body>
<main class="wrap">
<header>
<p class="meta">FoxIQ · поведение покупателей · наблюдение до 18.11.2026 23:59 МСК</p>
<h1>Когорта 09–15.11 против 02–08.11</h1>
<p class="meta">Покупатели триала: 155 и 58. Primer и PostHog сходятся по каждому дню. Поведение посчитано в PostHog.</p>
</header>
<section class="card">
<h2>Главное</h2>
<ol>{head}</ol>
</section>
<section class="card">
<h2>Проверено до расчётов</h2>
<ul>
<li>T1 и T3. Среди 213 покупателей нет ни одного события с t1_variant или t3_variant. Когорты по варианту не делятся. Первое t1_variant в проекте: 13.11.2026 11:20 UTC, почты тестового фильтра. Первое t3_variant: 17.11.2026 12:16 UTC, тоже тестовые почты. 18.11.2026 09:35 UTC один человек вне этих когорт получил t1=A, его почта не из тестового фильтра. Журнал 16.11: на живых T1 пока не запускаем. Журнал 18.11: Кориун написал, что T1 включён и новые тестовые аккаунты в него попадают.</li>
<li>Дыры. События foxiq и foxiq_ff есть в каждый день 02–18.11. Провала как 11.10 01:00 – 13.10 07:00 UTC нет. 02.11 тише остальных дней покупки, это не пустой день. 16–18.11 событий меньше: неделя покупок уже кончилась, тысячи событий остаются.</li>
<li>Список людей. reports/data/foxiq-2026-11-16/buyers.csv, без is_test и без exclusion_reason. По дням МСК Primer и PostHog: 4, 10, 5, 7, 16, 4, 12 и 20, 30, 27, 21, 19, 19, 19.</li>
</ul>
</section>
<section>
<h2>События по дням</h2>
<p class="meta">Все события foxiq и foxiq_ff, не только покупатели. Дата — МСК.</p>
<div class="tbl"><table>
<thead><tr><th>День</th><th>События</th><th>Люди</th></tr></thead>
<tbody>{events_table()}</tbody>
</table></div>
</section>
<section class="card">
<h2>Изменения продукта между неделями</h2>
<p>Возможные причины разницы. Выводов из списка нет.</p>
<ul>
<li>Кнопка отмены на каждом экране с 11.11. В разборе v4.6 эта кнопка не входила в вариант B.</li>
<li>Раздел памяти открыт всем с 11.11 14:06 UTC, 17:06 МСК: вкладки уроков и дворцов и навыки памяти в обзоре. Флага нет. В первые 72 часа прошлой когорты этот раздел мог попасть только покупателям после 08.11 17:06 МСК. Сколько таких людей, отдельно не посчитано. В измеренном окне раздел открыли 0 из 58.</li>
<li>Лимит ошибок и сердечки в уроках и дворцах: сообщение Дани 11.11. Игры для Premium без этого лимита.</li>
<li>Серия писем M с 12.11: M1–M3 вместо B1–B3 для тех, кто заходил до запуска памяти. B4 не отправлялась. В журнале 16.11, со слов Кориуна: с 13.11 отправлено 51 M1, 31 M2, 1 M3. Письма в этой выгрузке не считались.</li>
</ul>
</section>
<section>
<h2>Первый час</h2>
<p class="legend">Доли от всей когорты, 155 и 58. Пометка стоит там, где сравниваемая группа меньше 30. Красный цвет не используется: в легенде нет проблемной метрики.</p>
<div class="tbl"><table>
<thead><tr><th>Метрика</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(hour_rows)}</tbody>
</table></div>
</section>
<section>
<h2>Первые 3 дня</h2>
<p class="meta">D1, D2 и D3 — календарные дни МСК от дня покупки. Знаменатель — те, у кого окно уже прошло. Таких 155 из 155 и 58 из 58. Занятие — день с игрой, тестом или завершённым уроком.</p>
<div class="tbl"><table>
<thead><tr><th>Метрика</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(day_rows)}</tbody>
</table></div>
</section>
<section>
<h2>Что используют за 72 часа</h2>
<p class="meta">Одинаковая длина окна после покупки, не срок до 18.11. Иначе у когорты 02–08.11 было бы больше дней. Экраны входа в разделы не входят.</p>
<div class="tbl"><table>
<thead><tr><th>Раздел</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(section_rows)}</tbody>
</table></div>
</section>
<section>
<h2>Игры за 72 часа</h2>
<p class="meta">По каждой игре меньше 30 человек. {SMALL}. Игра fox-memory — это игра, не новый раздел памяти: в прошлой когорте её тоже запускали.</p>
<div class="tbl"><table>
<thead><tr><th>Игра</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(game_names)}</tbody>
</table></div>
</section>
<section>
<h2>Пейволл, сердечки, монеты, Brain Score</h2>
<div class="tbl"><table>
<thead><tr><th>Метрика</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(money_rows)}</tbody>
</table></div>
</section>
<section>
<h2>Когда отменяют</h2>
<p class="meta">Часы от покупки до первой отмены пользователя. Сумма корзин равна числу отменивших: 85 и 33.</p>
<div class="tbl"><table>
<thead><tr><th>Метрика</th><th>09–15.11</th><th>02–08.11</th><th>Разница</th><th>Выборка</th></tr></thead>
<tbody>{''.join(cancel_rows)}</tbody>
</table></div>
</section>
<section>
<h2>Первая сессия: отменили и не отменили</h2>
<p class="meta">Группа «не отменили» в неделе 02–08.11 — 25 человек. {SMALL}. В неделе 09–15.11 обе группы больше 30: отменили 85, не отменили 70.</p>
<div class="tbl"><table>
<thead><tr><th>В первый час</th><th>09–15, отменили</th><th>09–15, не отменили</th><th>02–08, отменили</th><th>02–08, не отменили</th></tr></thead>
<tbody>{''.join(session_rows)}</tbody>
</table></div>
</section>
<section class="card">
<h2>Гипотезы</h2>
<p>Это не факты отчёта. Проверки здесь нет.</p>
<ul>
<li>Кнопка отмены с 11.11 могла сдвинуть часть отмен в первый час. Внутри одной недели люди до кнопки и после кнопки не сравнивались.</li>
<li>Нулевая память у когорты 02–08.11 может быть границей окна: раздел открылся 11.11, а 72 часа большинства этих покупок к тому времени уже кончились.</li>
<li>Серия M с 12.11 могла изменить возврат. По письмам отдельного счёта нет.</li>
</ul>
</section>
<section>
<h2>Покупатели по дням</h2>
<p class="meta">Primer, первый успешный $1, и PostHog subscription_started. Числа совпали в каждый день, поэтому в таблице два одинаковых столбца.</p>
<div class="tbl"><table>
<thead><tr><th>День, МСК</th><th>Primer</th><th>PostHog</th></tr></thead>
<tbody>{days_table()}</tbody>
</table></div>
</section>
<section class="card">
<h2>Как считали</h2>
<p>Полные правила: reports/foxiq-cohort-compare-2026-11-09-metodika.md. Скрипт: scripts/foxiq-cohort-compare.py. ClickUp не менялся.</p>
</section>
</main>
</body>
</html>
"""


def build_md(data: dict) -> str:
    return """# Методика: когорты FoxIQ 09–15.11 и 02–08.11

Файл считает `scripts/foxiq-cohort-compare.py`. Отчёт: `reports/foxiq-cohort-compare-2026-11-09.html`. Выгрузка агрегатов: `reports/data/foxiq-2026-11-18/cohort_aggregates.json`. Почт и номеров карт в этих файлах нет.

## Кто вошёл

Покупатель — человек из `reports/data/foxiq-2026-11-16/buyers.csv` с пустым `exclusion_reason` и `is_test` не равным 1. Это первый `subscription_started` FoxIQ. Тестовый фильтр почты тот же, что в `playbook/posthog.md`, плюс исключения, уже записанные в этом файле.

Неделя — дата покупки по МСК. Прошлая: 02.11.2026 00:00 – 08.11.2026 23:59:59. Текущая: 09.11.2026 00:00 – 15.11.2026 23:59:59. В обеих 58 и 155 человек. По каждому дню Primer, первый успешный платёж $1, и PostHog дают одно число. Для поведения в приложении отдельной цифры Primer нет: заходы, игры и отмены взяты из PostHog. Где числа Primer и PostHog разные, отчёт показывает оба. Здесь они не разошлись.

Наблюдение событий: с момента покупки до 18.11.2026 23:59:59 МСК, то есть 18.11.2026 20:59:59 UTC.

## Что проверено до долей

T1 и T3. За 01.11 21:00 UTC – 18.11 20:59 UTC ни один из 213 покупателей не получил `t1_variant` или `t3_variant`. Когорты по варианту не делились. Первое `t1_variant` в проекте — 13.11.2026 11:20 UTC на почтах тестового фильтра. Первое `t3_variant` — 17.11.2026 12:16 UTC, тоже тестовые почты. 18.11.2026 09:35 UTC один человек вне этих когорт получил t1=A. Журнал 16.11 фиксирует решение не запускать T1 на живых. Журнал 18.11 фиксирует слова Кориуна, что T1 включён для новых тестовых аккаунтов.

Дыры. Число событий `foxiq` и `foxiq_ff` посчитано по дням МСК с 02.11 по 18.11. Пустого дня нет. Образец дыры остаётся прежним: 11.10 01:00 – 13.10 07:00 UTC. 02.11 тише других дней покупки. 16–18.11 ниже, потому что неделя покупок кончилась.

Окно 72 часов. Для каждого покупателя проверено, что покупка плюс 24, 48 и 72 часа не позже 18.11.2026 20:59:59 UTC. Условие выполнено у 155 из 155 и у 58 из 58. Строка «окно не прошло» в отчёте не используется и в ноль не переводится. Если бы у человека окно не прошло, он вышел бы из знаменателя D1, D2 или D3.

## Определения

Первый час. От `subscription_started` до плюс 60 минут.

Тренировка. `game_started`, `test_started` или `lesson_completed`. Так же в `reports/foxiq-product-journeys-2026-11-11-v4.23.html`. `first_run_started` тренировкой не считается.

«Ничего не начали». В первый час нет ни одного из трёх событий тренировки. Человек мог видеть результат и главную.

«Не открыли и экран раздела». К этому добавлено отсутствие `$pageview` и `screen_view` на `/games`, `/tests`, `/lessons`, `/track`, `/palaces`.

«Ушли за минуту». Отдельно. Как в v4.23: в первые 30 минут есть события приложения, и от первого до последнего меньше 60 секунд. Это не замена строке «ничего не начали».

Отмена. `subscription_cancelled` с `reason=user_initiated`. Берётся первое такое событие. `subscription_expired` с `payment_failed` в отмены пользователя не входит. Пара в ту же секунду в эту выборку не попала бы как пользовательская отмена, потому что причина другая.

Заход в приложение. `$pageview`, `screen_view` или `app_opened`, проект foxiq, библиотека web, путь не из `/auto-login`, `/auth`, `/magic-link-login`, `/onboarding`.

D1, D2, D3. Календарный день МСК: дата покупки плюс 1, 2 или 3. Это не скользящие 24 часа. Знаменатель — люди, у которых соответствующее окно уже прошло.

День с занятием. Календарный день МСК внутри 72 часов, в который был `game_started`, `test_started` или `lesson_completed`.

Использование. Экраны и игры считаются за первые 72 часа после покупки, чтобы у обеих недель была одна длина окна. Срок до 18.11 длиннее у тех, кто купил раньше, поэтому он не взят основной метрикой. Пейволл дополнительно показан до 18.11, потому что за 72 часа он был нулевым, а два события лежат позже.

Память. Пути `/lessons`, `/palaces`, `/plan`. Человек в строке «память» один, даже если открыл несколько путей. Игра `fox-memory` в эту строку не входит: она запускалась и в неделе 02–08.11.

Сертификат. Экран `/iq-certificate` и отдельно событие `certificate_name_submitted`.

Brain Score. Искались `brain_profile_shown`, `brain_score_shown`, `brain_score_changed`, `brain_score_certificate_downloaded`, `improve_score_shown`. У покупателей этих недель их 0. В проекте за то же окно такие события есть у других людей, поэтому это не пустое имя события. `iq_result_shown` — экран результата IQ, не Brain Score.

Сердечки и монеты. `hearts_page_shown`, `in_app_purchase_success`, `in_app_purchase_click`, `paywall_open_tokens`. Единственный `in_app_purchase_success` у этих покупателей: `purchase_type=subscription`, `product_id=month`. Сердечек и монет в нём нет.

Пейволл. `paywall_shown` после покупки. За 72 часа: 0 и 0. До 18.11: 1 и 1, placement `paywall` и `app_entry`.

Малая выборка. Пометка «мало данных, тренд ненадёжен» стоит, если знаменатель группы меньше 30, и на строках, где само действие есть меньше чем у 30 человек и сравниваются эти люди, а не доля когорты 58 и 155. Доля от 155 и от 58 пометки не получает. В колонке «не отменили» недели 02–08.11 знаменатель 25, тренд по ней не считается.

Изменения продукта выписаны отдельным блоком. Рядом нет вывода, что они объясняют разницу. Гипотезы стоят внизу HTML и здесь не повторяются как факты.

## Чего скрипт не делает

Не ходит в PostHog заново. Не читает файл Primer с почтами и картами. Не меняет ClickUp. Не делит когорту по T1, потому что у покупателей варианта нет.
"""


def main() -> None:
    data = load()
    check(data)
    html_text = build_html(data)
    md_text = build_md(data)
    if EMAIL.search(html_text) or "@" in html_text:
        raise SystemExit("html contains an address or @")
    if EMAIL.search(md_text):
        raise SystemExit("methodology contains an address")
    OUT_HTML.write_text(html_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    print(f"wrote {OUT_HTML.name} and {OUT_MD.name}")


if __name__ == "__main__":
    main()
