"""HTML-отчёт по пересчёту FB-кандидатов в оформлении «Воронки аналогов memoryOS».

Данные и решения — те же, что в fb-pereschet-2026-11-09.xlsx; идеи, креативы и скрины лендингов —
из fb-shortlist-28-10.html (первая выборка 28.10). Подсказок по наведению нет: всё видно сразу.
"""
import html
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl

from build_pereschet import EXCLUDED_REASON, NOTES, SRC, load, num

sys.stdout.reconfigure(encoding="utf-8")
REPORTS = Path(__file__).resolve().parents[2] / "reports"
OUT = REPORTS / "fb-pereschet-2026-11-09.html"
SHORTLIST = REPORTS / "fb-shortlist-28-10.html"
CR_SCEN = (0.01, 0.02, 0.025)
COPY_K = 0.85
ROAS_MIN = 0.75  # ≈ верхняя четверть ROAS веб-воронок выгрузки 10.10 (0,76)
ORDER = ["Продолжать", "Проверить", "Низкий приоритет", "Отклонить"]
GCLS = {"Продолжать": "go", "Проверить": "chk", "Низкий приоритет": "low", "Отклонить": "no"}

IDEAS = [
    dict(apps=["Intch"], title="Intch → карьерный помощник",
         text="Брать не агрегатор вакансий, а подготовку к работе: генератор и улучшатель резюме + симулятор "
              "собеседований с ИИ + тренинг прохождения собеседований. Сейчас Intch — поиск удалённой и part-time работы.",
         src="выборка 28.10, дополнено 09.11"),
    dict(apps=["Skilario"], title="Skilario + агрегатор ИИ-инструментов",
         text="Объединить с нашим приложением-агрегатором ИИ-инструментов: в одной подписке доступ к сервисам "
              "и обучение по ним.", src="выборка 28.10"),
    dict(apps=["TheRealIntro", "Honey (ИИ-девушка)"], title="Флирт + ИИ-компаньон: TheRealIntro + Honey",
         text="Объединить обучение флирту (TheRealIntro) с ИИ-компаньоном (Honey): отработка уроков флирта "
              "в диалоге + генерация фанфиков.", src="выборка 28.10", cai=True),
    dict(apps=["Mozart AI", "Dear Melodies", "Zurna (ИИ-фото)", "HyperMusic AI (w2a.one)"],
         title="Генераторы песен и клипов → подписка для ИИ-артистов",
         text="Подписка для тех, кто делает свои ИИ-музыкальные группы и ИИ-артистов. По четырём приложениям "
              "медианный CPA $46,4 против $79 по всей выгрузке 10.10.", src="выборка 28.10"),
    dict(apps=["Chillio"], title="Chillio + блокер экранного времени",
         text="Объединить ИИ-планировщик домашних дел с блокером экранного времени. В пересчёт не попал: "
              "доход по пикселю 0, продукт на паузе с 06.11.", src="выборка 28.10"),
]
IDEA_BY_APP = {a: i for i in IDEAS for a in i["apps"]}


def e(s):
    return html.escape(str(s)) if s is not None else "—"


def money(v, d=0):
    if v is None:
        return "—"
    return "$" + f"{v:,.{d}f}".replace(",", " ").replace(".", ",")


def mln(v):
    return "—" if v is None else "$" + f"{v / 1e6:.2f}".replace(".", ",") + "M"


def pct(v, d=1):
    return "—" if v is None else f"{v * 100:.{d}f}".replace(".", ",") + "%"


def x(v):
    return "—" if v is None else f"{v:.2f}".replace(".", ",")


def group(decision):
    return next((g for g in ORDER if decision.startswith(g)), "Проверить")


def media():
    """Креатив и скрин лендинга по каждому приложению из первой выборки."""
    s = open(SHORTLIST, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<article class="card"[^>]*>(.*?)</article>', s, re.S):
        body = m.group(1)
        name = re.search(r"<h3>(.*?)</h3>", body).group(1)
        imgs = {}
        for im in re.finditer(r'<img class="k-(crea|shot)" src="([^"]+)" alt="([^"]*)"', body):
            imgs[im.group(1)] = im.group(2)
        out[html.unescape(name)] = imgs
    return out


def find_media(app, med):
    if app in med:
        return med[app]
    head = app.split(" (")[0]
    return next((v for k, v in med.items() if k.split(" (")[0] == head), {})


def calc(d):
    spend, cpa, roas = num(d["спенд за 28 дней"]), num(d["CPA за 28 дней"]), num(d["ROAS за 28 дней"])
    clicks, cpc = num(d["переходы по ссылке"]), num(d["CPC"])
    conv = spend / cpa
    rpc = spend * roas / conv
    cr = conv / clicks
    bad = roas < 0.1 or rpc < 5
    cost = {s: cpc / s for s in CR_SCEN}
    cost_k, cost_k85 = cpc / cr, cpc / (cr * COPY_K)
    cov_k85 = rpc / cost_k85
    if bad:
        payback = "Не знаем — доход не виден"
    elif cov_k85 >= 1:
        payback = "1-й месяц"
    elif cov_k85 >= 0.5:
        payback = "2–3 мес., если держатся продления"
    else:
        payback = "за 3 мес. маловероятно"
    d["ссылка на ленд"] = str(d["ссылка на ленд"]).replace("://zealy.ai/", "://zeely.ai/")
    return dict(d=d, spend=spend, cpa=cpa, roas=roas, clicks=clicks, cpc=cpc, conv=conv, rpc=rpc, cr=cr, bad=bad,
                cost=cost, cost_k=cost_k, cost_k85=cost_k85, cov={s: rpc / c for s, c in cost.items()},
                cov_k=rpc / cost_k, cov_k85=cov_k85, payback=payback)


def rows():
    apps, funnels = load()
    out, excl = [], []
    for d in funnels:
        app = d["Приложение (группа)"]
        if (app, str(d["ID строки"])) in EXCLUDED_REASON:
            excl.append((d, EXCLUDED_REASON[(app, str(d["ID строки"]))]))
            continue
        if app == "TheRealIntro":
            apps[app]["geo"] = "нет в выгрузке; квиз и объявление на немецком (quizlang=de)"
        n = NOTES[app]
        out.append(dict(calc(d), app=app, a=apps[app], note=n, group=group(n["decision"])))
    out.sort(key=lambda r: (ORDER.index(r["group"]), -r["cov_k85"] if not r["bad"] else 9))
    return out, excl, set(apps)


def about_index():
    """«Про что приложение» со всех листов таблицы 28.10."""
    wb = openpyxl.load_workbook(SRC, read_only=True)
    res = {}
    for ws in wb.worksheets:
        rs = list(ws.iter_rows(values_only=True))
        hi = next((i for i, r in enumerate(rs[:5]) if r and "Приложение" in r and "Про что приложение" in r), None)
        if hi is None:
            continue
        hdr = rs[hi]
        for r in rs[hi + 1:]:
            d = dict(zip(hdr, r))
            if d.get("Приложение") and d.get("Про что приложение"):
                res.setdefault(str(d["Приложение"]).split(" (")[0].split(" / ")[0], d["Про что приложение"])
    return res


EXPORTS = [("web2web giants #5", "18.05"), ("web2web giants #6.1", "29.06"), ("web2web giants #7.1", "28.07"),
           ("web2web new #1", "27.08"), ("web2web giants #8", "28.08"), ("web2web giants #9", "10.10")]
STORE = re.compile(r"apps\.apple\.com|play\.google\.com|w2a\.one|onelink|app\.link", re.I)


def path_key(u):
    u = re.sub(r"^https?://", "", str(u or ""))
    base = u.split("?")[0].rstrip("/")
    variant = re.findall(r"(?:landing_uu?id|cohort|flow|quizlang)=([^&]+)", u)
    return (base + (" · " + " · ".join(variant) if variant else "")) or "—"


def history():
    """Все строки бренда во всех выгрузках: динамика спенда и список воронок."""
    wb = openpyxl.load_workbook(SRC, read_only=True)
    rs = list(wb["Сводная (все строки)"].iter_rows(values_only=True))
    hdr = rs[0]
    h = defaultdict(list)
    for r in rs[1:]:
        d = dict(zip(hdr, r))
        h[d["Приложение (группа)"]].append(d)
    return h


def brand_info(app, hist):
    rows_ = hist.get(app, [])
    web = [d for d in rows_ if not STORE.search(str(d["ссылка на ленд"]))]
    store = len(rows_) - len(web)
    by_exp = []
    for name, date in EXPORTS:
        part = [d for d in web if d["Выгрузка"] == name]
        if part:
            sp = sum(num(d["спенд за 28 дней"]) or 0 for d in part)
            rev = sum((num(d["спенд за 28 дней"]) or 0) * (num(d["ROAS за 28 дней"]) or 0) for d in part)
            by_exp.append((date, sp, rev / sp if sp else None, len(part)))
    funnels = {}
    for d in web:
        k = path_key(d["ссылка на ленд"])
        f = funnels.setdefault(k, dict(first=d["дата запуска рекламы"], seen=[], max=0))
        f["seen"].append(d["Дата выгрузки"])
        f["max"] = max(f["max"], num(d["спенд за 28 дней"]) or 0)
        if d["дата запуска рекламы"] and (not f["first"] or d["дата запуска рекламы"] < f["first"]):
            f["first"] = d["дата запуска рекламы"]
    last = [d for d in web if d["Выгрузка"] == "web2web giants #9"]
    sp28 = sum(num(d["спенд за 28 дней"]) or 0 for d in last)
    sp7 = sum(num(d["спенд за 7 дней"]) or 0 for d in last)
    ads = sum(num(d["кол-во объявлений всего"]) or 0 for d in last)
    ads100 = sum(num(d["объявления со спендом ≥ 100$"]) or 0 for d in last)
    accel = sp7 * 4 / sp28 if sp28 else None
    if len(by_exp) == 1:
        trend = "новый: только в выгрузке 10.10"
    else:
        ch = by_exp[-1][1] / by_exp[-2][1] - 1
        trend = ("растёт" if ch > 0.2 else "падает" if ch < -0.2 else "держится") + \
                f" ({'+' if ch >= 0 else ''}{ch * 100:.0f}% к {by_exp[-2][0]})"
    spy = last[0] if last else {}
    return dict(by_exp=by_exp, funnels=funnels, store=store, accel=accel, ads=ads, ads100=ads100, trend=trend,
                tyver=spy.get("ссылка на tyver"), adheart=spy.get("ссылка на adheart"),
                domain=".".join(path_key(spy.get("ссылка на ленд")).split(" ")[0].split("/")[0].split(".")[-2:]))


def brand_block(b):
    dyn = " → ".join(f"{dt}: {mln(sp)}" + (f" (ROAS {x(ro)})" if ro else "") for dt, sp, ro, _ in b["by_exp"])
    acc = "—" if b["accel"] is None else f"{x(b['accel'])} " + (
        "— разгоняется" if b["accel"] > 1.15 else "— тормозит" if b["accel"] < 0.85 else "— ровно")
    fl = "".join(f"<li><span class='url'>{e(k[:70])}</span> · запуск {e(f['first'].strftime('%d.%m.%Y') if hasattr(f['first'], 'strftime') else f['first'])}"
                 f" · в выгрузках: {e(', '.join(dict.fromkeys(f['seen'])))} · макс. спенд 28д {mln(f['max'])}</li>"
                 for k, f in sorted(b["funnels"].items(), key=lambda kv: -kv[1]["max"])[:6])
    more = len(b["funnels"]) - 6
    spy = " · ".join(f'<a href="{e(href(u))}" target="_blank" rel="noopener">{lbl} ↗</a>'
                     for lbl, u in (("tyver", b["tyver"]), ("adheart", b["adheart"]),
                                    ("Similarweb", f"https://www.similarweb.com/website/{b['domain']}/")) if u)
    return f"""<dl class="facts">
<div><dt>Спенд 28 дн. по выгрузкам</dt><dd>{dyn}</dd></div>
<div><dt>Тренд · ускорение (спенд 7 дн. × 4 ÷ 28 дн.)</dt><dd>{e(b['trend'])} · {acc}</dd></div>
<div><dt>Объявлений на 10.10 (всего · со спендом ≥ $100)</dt><dd>{int(b['ads'])} · {int(b['ads100'])}</dd></div>
<div><dt>Spy-сервисы</dt><dd>{spy}{' · стор-строк бренда: ' + str(b['store']) if b['store'] else ''}</dd></div>
</dl>
<div class="lim"><b>Воронки бренда в выгрузках: {len(b['funnels'])}</b><ul>{fl}{f'<li>и ещё {more}</li>' if more > 0 else ''}</ul></div>"""


def candidates(selected):
    """Вся выгрузка 10.10: веб-воронки с видимым доходом, CPA ≤ медианы и ROAS ≥ ROAS_MIN."""
    wb = openpyxl.load_workbook(SRC, read_only=True)
    rs = list(wb["Сводная (все строки)"].iter_rows(values_only=True))
    hdr = rs[0]
    web, total = [], 0
    for r in rs[1:]:
        d = dict(zip(hdr, r))
        if d["Выгрузка"] != "web2web giants #9":
            continue
        total += 1
        app = d["Приложение (группа)"]
        if (d["куда ведёт реклама (схема)"] != "веб" or app.startswith("(") or STORE.search(str(d["ссылка на ленд"]))
                or not all(num(d[k]) for k in ("спенд за 28 дней", "CPA за 28 дней", "ROAS за 28 дней",
                                               "переходы по ссылке", "CPC"))):
            continue
        c = calc(d)
        if not c["bad"]:
            web.append(dict(c, app=app, health=d["Блок"] == "health и фитнес", sel=app in selected,
                            cat=d["комментарий"] or d["категория"], geo=geo_short(d["спенд топ-стран"]),
                            owner=d["родительский аккаунт"], ad=d["текст объявления"],
                            crea=d["креатив из топ-объявления"], shot=d["скриншот ленда"]))
    cpas = sorted(w["cpa"] for w in web)
    med = cpas[len(cpas) // 2]
    passed = [w for w in web if w["cpa"] <= med and w["roas"] >= ROAS_MIN and not w["health"]]
    border = sorted({w["app"] for w in web if w["cpa"] > med and w["roas"] >= 1 and not w["health"]}
                    - {w["app"] for w in passed})
    passed.sort(key=lambda w: w["cpa"])
    return total, len(web), med, passed, border


def geo_short(g):
    if not g:
        return "нет в выгрузке"
    pairs = re.findall(r'"?([A-Z]{2})"?\s*[:\-]\s*(\d+)', str(g))
    if not pairs:
        return str(g)
    tot = sum(int(v) for _, v in pairs)
    return ", ".join(f"{k} {int(v) * 100 // tot}%" for k, v in sorted(pairs, key=lambda p: -int(p[1]))[:3])


CSS = """
:root{--bg:#eef1f6;--surface:#fff;--ink:#141a2b;--muted:#5a6378;--line:#d6dbe6;--accent:#2f4fd8;--accent-soft:#e3e8fb;
--gold:#a0640a;--gold-soft:#fbf0dc;--go:#1f7a4d;--go-soft:#e2f3ea;--no:#b42318;--no-soft:#fbe7e5;--low:#5a6378;--low-soft:#eceef3;
--display:"Unbounded","Onest",system-ui,sans-serif;--body:"Onest",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root{--bg:#0f1320;--surface:#171c2c;--ink:#e7eaf3;--muted:#9aa3b8;--line:#2a3148;
--accent:#8ea2ff;--accent-soft:#222c52;--gold:#f0b85c;--gold-soft:#3a2d16;--go:#6fd3a0;--go-soft:#173326;--no:#ff8f86;--no-soft:#3a1c1a;
--low:#9aa3b8;--low-soft:#222838;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.55}
.wrap{max-width:1180px;margin:0 auto;padding:40px 16px 64px;display:flex;flex-direction:column;gap:52px}
h1,h2{font-family:var(--display);text-wrap:balance;margin:0;line-height:1.15}
h1{font-size:clamp(1.6rem,4vw,2.5rem);font-weight:700;max-width:24ch}
h2{font-size:1.35rem;font-weight:500}
p{margin:0}
section{display:flex;flex-direction:column;gap:14px}
.eyebrow{font-size:.75rem;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);font-weight:600}
.hero{display:flex;flex-direction:column;gap:18px}
.lede{color:var(--muted);max-width:75ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:2px;min-width:0}
.kpi .ki{font-size:1.2rem}.kpi .kv{font-family:var(--display);font-size:1.6rem;font-weight:700;color:var(--accent);line-height:1.1}
.kpi .kl{font-size:.84rem;color:var(--muted);line-height:1.3}
.sum{background:var(--accent-soft);border-radius:10px;padding:16px 20px;gap:8px}
.sum h2{font-size:1.1rem}.sum ol{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:6px}
.ideas{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.idea{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--gold);border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:6px;min-width:0}
.idea b{font-family:var(--display);font-weight:500}
.idea .src{font-size:.78rem;color:var(--muted)}
.cai{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:.84rem;margin-top:4px}
.cai div{background:var(--gold-soft);border-radius:8px;padding:8px 10px}
.cai b{font-family:var(--body);font-weight:600;display:block}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;background:var(--surface);font-size:.88rem}
table.fit{table-layout:fixed;font-size:.84rem}
table.fit th,table.fit td{overflow-wrap:anywhere}
table.fit .desc{color:var(--muted);font-size:.8rem;line-height:1.35}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--accent-soft);font-weight:600;font-size:.78rem}
td.r,th.r{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
td a{color:var(--accent)}
.nm{font-weight:600;color:var(--ink);text-decoration:none}.nm:hover{color:var(--accent)}
tr.bad td.r{color:var(--muted)}
.chip{font-size:.75rem;font-weight:600;border-radius:999px;padding:2px 10px;white-space:nowrap;display:inline-block}
.c-go{background:var(--go-soft);color:var(--go)}.c-chk{background:var(--gold-soft);color:var(--gold)}
.c-low{background:var(--low-soft);color:var(--low)}.c-no{background:var(--no-soft);color:var(--no)}
.c-idea{background:var(--gold-soft);color:var(--gold)}.c-lbl{background:var(--bg);color:var(--muted);border:1px solid var(--line)}
.pill{font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:1px 10px;background:var(--surface);white-space:nowrap}
.nav{display:flex;flex-wrap:wrap;gap:8px}
.nav a{font-size:.85rem;color:var(--accent);text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:3px 11px;background:var(--surface)}
.nav a:hover{background:var(--accent-soft)}
.ghead{display:flex;align-items:baseline;gap:10px;margin-top:8px}
.app{display:flex;flex-direction:column;gap:10px;padding-top:20px;border-top:1px solid var(--line);scroll-margin-top:16px}
.ah{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px}
.ah h3{font-family:var(--display);font-weight:500;font-size:1.2rem;margin:0 6px 0 0}
.about{max-width:80ch}
.ibox{background:var(--gold-soft);border-radius:8px;padding:8px 12px;font-size:.93rem;max-width:90ch}
.take{font-size:.95rem;max-width:90ch}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:start}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1px;margin:0;background:var(--line);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.facts div{background:var(--surface);padding:9px 13px;min-width:0}
.facts dt{font-size:.7rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);font-weight:600}
.facts dd{margin:2px 0 0;font-size:.92rem;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.facts dd a{color:var(--accent)}
table.sc{font-size:.84rem;min-width:0}
.shots{display:flex;gap:10px}
.shot{flex:0 0 150px;display:flex;flex-direction:column;gap:4px;background:none;border:0;padding:0;text-align:left;cursor:zoom-in;color:inherit;font:inherit}
.shot img{width:150px;aspect-ratio:9/16;object-fit:cover;object-position:top;border:1px solid var(--line);border-radius:12px;background:var(--surface)}
.shot span{font-size:.78rem;color:var(--muted)}
.shot:hover img{border-color:var(--accent)}
.meta2{font-size:.8rem;color:var(--muted)}
.url{font-family:var(--mono);font-size:.8rem;overflow-wrap:anywhere}
.lim b{font-weight:600;font-size:.92rem}
.ok{color:var(--go);font-weight:600}.todo{color:var(--gold);font-weight:600}
.foot{font-size:.82rem;color:var(--muted);max-width:90ch}
.lim{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 18px}
.lim ul{margin:0;padding-left:20px;display:flex;flex-direction:column;gap:5px;font-size:.92rem}
dialog{border:0;border-radius:14px;padding:16px;background:var(--surface);color:var(--ink);max-width:min(460px,92vw);max-height:92vh}
dialog::backdrop{background:rgb(10 12 20 / .7)}
dialog img{display:block;width:100%;max-height:80vh;object-fit:contain;border-radius:10px}
dialog p{font-size:.88rem;color:var(--muted);margin-top:8px}
.close{position:absolute;top:6px;right:10px;background:var(--surface);color:var(--ink);border:1px solid var(--line);border-radius:999px;width:32px;height:32px;font-size:1.1rem;cursor:pointer}
dialog form{margin:0}
@media(max-width:760px){.grid2{grid-template-columns:1fr}.cai{grid-template-columns:1fr}}
"""


def chip(g):
    return f'<span class="chip c-{GCLS[g]}">{e(g)}</span>'


def slug(app):
    return re.sub(r"[^a-z0-9]+", "-", app.lower()).strip("-") or "app"


def idea_card(i, shown):
    cai = ""
    if i.get("cai"):
        cai = ('<div class="cai"><div><b>Пользователи в месяц</b>28 млн — пик 2024 · ~20 млн — 2025</div>'
               '<div><b>Выручка за год</b>$32M — 2024 · $30–50M — оценка 2025</div></div>'
               '<p class="src">Ориентир — Character.AI, подписка c.ai+ $9,99/мес. Оценки Sacra и Axis Intelligence, '
               'официальной отчётности нет.</p>')
    links = " · ".join(f'<a href="#{slug(a)}">{e(a.split(" (")[0])}</a>' if a in shown
                       else f'{e(a.split(" (")[0])} (исключено)' for a in i["apps"])
    return (f'<div class="idea"><b>💡 {e(i["title"])}</b><p>{e(i["text"])}</p>{cai}'
            f'<p class="src">Приложения: {links} · источник: {e(i["src"])}</p></div>')


def scen_table(fs):
    multi = len(fs) > 1
    head = "".join(f'<th class="r" colspan="2">{"Воронка " + str(k + 1) if multi else "Наша цена / покрытие"}</th>'
                   for k in range(len(fs)))
    sub = "".join('<th class="r">цена события</th><th class="r">покрытие</th>' for _ in fs)
    lines = [("CR 1%", lambda r: r["cost"][0.01], lambda r: r["cov"][0.01]),
             ("CR 2%", lambda r: r["cost"][0.02], lambda r: r["cov"][0.02]),
             ("CR 2,5%", lambda r: r["cost"][0.025], lambda r: r["cov"][0.025]),
             ("CR конкурента", lambda r: r["cost_k"], lambda r: r["cov_k"]),
             ("CR конкурента × 0,85", lambda r: r["cost_k85"], lambda r: r["cov_k85"])]
    body = "".join(
        f"<tr><td>{lbl}</td>" + "".join(f'<td class="r">{money(c(r), 1)}</td><td class="r">{x(v(r))}</td>' for r in fs)
        + "</tr>" for lbl, c, v in lines)
    return (f'<div class="tw"><table class="sc"><thead><tr><th>Сценарий</th>{head}</tr>'
            f'<tr><th></th>{sub}</tr></thead><tbody>{body}</tbody></table></div>')


def app_section(app, fs, med):
    r0 = fs[0]
    a, n = r0["a"], r0["note"]
    tr = f'{mln(num(a["jul"]))} → {mln(num(a["aug"]))} → {mln(num(a["oct"]))}'
    pills = (f'<span class="pill">💸 {mln(sum(r["spend"] for r in fs))} за 28 дн.</span>'
             + "".join(f'<span class="pill">CPA {money(r["cpa"])} · ROAS {x(r["roas"])}</span>' for r in fs))
    idea = IDEA_BY_APP.get(app)
    ibox = f'<p class="ibox">💡 <b>Идея:</b> {e(idea["text"])}</p>' if idea else ""
    funnels = "<br>".join(f'<a href="{e(r["d"]["ссылка на ленд"])}" target="_blank" rel="noopener">'
                          f'{e(re.sub(r"^https?://", "", r["d"]["ссылка на ленд"])[:60])} ↗</a>' for r in fs)
    pay = "; ".join(e(r["payback"]) for r in fs)
    facts = [("Гео", e(a["geo"]) + (f" · tier-1 {pct(num(a['tier1']), 0)}" if num(a["tier1"]) is not None else "")),
             ("Спенд 28 дн.: июль → авг → окт", tr),
             ("CPC · CR переход → событие", "; ".join(f'{money(r["cpc"], 2)} · {pct(r["cr"], 2)}' for r in fs)),
             ("Доход с конверсии", "; ".join(money(r["rpc"], 1) for r in fs)),
             ("Событие CPA", e(n["event"])),
             ("Окупаемость (CR конкурента × 0,85)", f"<b>{pay}</b>"),
             ("Воронка" + ("и" if len(fs) > 1 else ""), funnels)]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)
    calc = ('<p class="meta2">Сценарии не считаем: доход по пикселю не отражает оплаты.</p>'
            if all(r["bad"] for r in fs) else scen_table([r for r in fs if not r["bad"]]))
    im = find_media(app, med)
    shots = "".join(f'<button class="shot" type="button" data-cap="{lbl}: {e(app)}"><img src="{im[k]}" '
                    f'alt="{lbl}: {e(app)}" loading="lazy"><span>{lbl}</span></button>'
                    for k, lbl in (("crea", "Креатив"), ("shot", "Лендинг")) if k in im)
    rows_id = ", ".join(str(r["d"]["ID строки"]) for r in fs)
    return f"""<section class="app" id="{slug(app)}">
<div class="ah"><h3>{e(app)}</h3>{chip(r0['group'])}{'<span class="chip c-idea">💡 идея</span>' if idea else ''}
<span class="chip c-lbl">{e(n['label'])}</span>{pills}</div>
<p class="about">{e(a['about'])}</p>{ibox}
<div class="grid2"><div style="display:flex;flex-direction:column;gap:10px;min-width:0">
<dl class="facts">{dl}</dl>{calc}
<p class="take">👉 <b>{e(n['decision'])}.</b> {e(n['why'])}</p></div>
<div class="shots">{shots}</div></div>
<p class="meta2">Блок 28.10: {e(a['block'])} · строки выгрузки 10.10: {e(rows_id)}</p>
</section>"""


BLURB = {
    "Educly": "Обучение ИИ с нуля: 28 дней по 15 минут с телефона.",
    "KitUp": "Микрообучение и саморазвитие каждый день. Аудитория — Турция и Украина.",
    "Famio": "Семейный GPS-трекер: где сейчас близкие, на карте.",
    "BetterMe": "Отношения: квиз про стиль привязанности.",
    "Muses Academy": "Отношения: «стань той, кого он потерял и хочет вернуть».",
    "Zenfy": "Заработок: удалённая работа вместо графика 9–5.",
    "ProMuse": "Обучение ИИ: 28-дневная программа с сертификатом.",
    "fnlfx (беттинг)": "ИИ-прогнозы на спорт для ставок.",
    "AI Corso": "Обучение ИИ с сертификатом.",
    "MusesAcred": "Отношения: «стань женщиной, которую он не может оставить».",
    "Education4Kids": "Детское образование.",
    "TheRealIntro": "Обучение знакомствам и флирту для мужчин.",
    "Kodree": "Курсы ИИ, анализа данных и дизайна, сертификат по Claude.",
}


def blurb(c):
    land = str(c["d"]["ссылка на ленд"])
    if c["app"] == "Finestro":
        if "quiz24" in land:
            return "Личные финансы: «приложение изменило, как я веду деньги»."
        return "Заработок на ИИ: «построй будущее с ИИ»."
    return BLURB.get(c["app"], str(c["cat"]))


def pay_short(p):
    if str(p).startswith("1-й"):
        return "1-й месяц"
    if str(p).startswith("2"):
        return "2–3 мес."
    if "маловероятно" in str(p):
        return "позже 3 мес."
    return "не знаем"


def sentence(s, n=150):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    cut = re.split(r"(?<=[.!])\s", s, maxsplit=1)[0]
    if len(cut) > n:
        cut = cut[:n].rsplit(" ", 1)[0] + "…"
    return cut or "—"


def href(u):
    u = str(u or "")
    return u if u.startswith("http") else "https://" + u


def event_guess(r):
    if r["rpc"] < 15:
        return f"Не ясно: доход с конверсии {money(r['rpc'], 1)} — похоже на триал или первую дешёвую оплату"
    return f"Оплата (доход с конверсии {money(r['rpc'], 0)}) — предположение"


def cand_section(app, fs, about, hist):
    r0 = fs[0]
    b = brand_info(app, hist)
    chips = (('<span class="chip c-low">health и фитнес</span>' if r0["health"] else "")
             + ('<span class="chip c-go">есть в выборке 28.10</span>' if r0["sel"] else "")
             + ('<span class="chip c-idea">💡 идея</span>' if app in IDEA_BY_APP else ""))
    pills = (f'<span class="pill">💸 {mln(sum(r["spend"] for r in fs))} за 28 дн.</span>'
             + "".join(f'<span class="pill">CPA {money(r["cpa"])} · ROAS {x(r["roas"])}</span>' for r in fs))
    txt = about.get(app.split(" (")[0])
    if not txt:
        ad = str(r0["ad"] or "")
        txt = f"{r0['cat']}. Текст объявления: «{ad[:140]}»" if ad and "{{" not in ad else str(r0["cat"])
    idea = IDEA_BY_APP.get(app)
    ibox = f'<p class="ibox">💡 <b>Идея:</b> {e(idea["text"])}</p>' if idea else ""
    funnels = "<br>".join(f'<a href="{e(href(r["d"]["ссылка на ленд"]))}" target="_blank" rel="noopener">'
                          f'{e(re.sub(r"^https?://", "", r["d"]["ссылка на ленд"])[:60])} ↗</a>' for r in fs)
    media_l = " · ".join(f'<a href="{e(href(r[k]))}" target="_blank" rel="noopener">{lbl}{" " + str(i + 1) if len(fs) > 1 else ""} ↗</a>'
                         for i, r in enumerate(fs) for k, lbl in (("crea", "креатив"), ("shot", "лендинг")) if r[k])
    facts = [("Компания · категория", f"{e(r0['owner'])} · {e(r0['cat'])}"),
             ("Гео (доли спенда)", "; ".join(e(r["geo"]) for r in fs)),
             ("CPC · CR переход → событие", "; ".join(f'{money(r["cpc"], 2)} · {pct(r["cr"], 2)}' for r in fs)),
             ("Событие CPA", "; ".join(e(event_guess(r)) for r in fs)),
             ("Окупаемость (CR конкурента × 0,85)", "<b>" + "; ".join(e(r["payback"]) for r in fs) + "</b>"),
             ("Воронка" + ("и" if len(fs) > 1 else ""), funnels),
             ("Креатив и лендинг (Drive)", media_l or "—")]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)
    return f"""<section class="app" id="c-{slug(app)}">
<div class="ah"><h3>{e(app)}</h3>{chips}{pills}</div>
<p class="about">{e(txt)}</p>{ibox}
<dl class="facts">{dl}</dl>{scen_table(fs)}
<p class="eyebrow">Ресерч бренда по выгрузкам 18.05–10.10</p>{brand_block(b)}
<p class="meta2">Строки выгрузки 10.10: {e(", ".join(str(r["d"]["ID строки"]) for r in fs))} · метка: Видно в данных (CPA, ROAS), событие — предположение</p>
</section>"""


def main():
    rs, excl, selected = rows()
    med = media()
    by_app = {}
    for r in rs:
        by_app.setdefault(r["app"], []).append(r)
    counts = {g: sum(1 for fs in by_app.values() if fs[0]["group"] == g) for g in ORDER}
    best = sorted([r for r in rs if not r["bad"]], key=lambda r: -r["cov_k85"])[:4]
    best_txt = ", ".join(f"{r['app']} ({x(r['cov_k85'])})" for r in best)
    total, n_web, cpa_med, cands, border = candidates(selected)
    about = about_index()
    hist = history()
    binfo = {c["app"]: brand_info(c["app"], hist) for c in cands}
    c_by_app = {}
    for c in cands:
        c_by_app.setdefault(c["app"], []).append(c)
    c_main = [a for a, fs in c_by_app.items() if not fs[0]["health"]]
    c_health = [a for a, fs in c_by_app.items() if fs[0]["health"]]
    c_pay = [a for a in c_main if max(r["cov_k85"] for r in c_by_app[a]) >= 1]

    trs = "".join(f"""<tr class="{'bad' if r['bad'] else ''}"><td><a href="#{slug(r['app'])}" class="nm">{e(r['app'])}</a>
{'<span class="chip c-idea">💡</span>' if r['app'] in IDEA_BY_APP else ''}</td>
<td class="desc">{e(sentence(r['a']['about']))}</td><td>{chip(r['group'])}</td>
<td>{e(r['a']['geo'])}</td><td class="r">{money(r['cpa'])}</td><td class="r">{x(r['roas'])}</td>
<td class="r"><b>{x(r['cov_k85'])}</b></td><td>{e(pay_short(r['payback']))}</td></tr>""" for r in rs)

    sections = ""
    for g in ORDER:
        part = [(app, fs) for app, fs in by_app.items() if fs[0]["group"] == g]
        if part:
            sections += f'<div class="ghead"><h2>{e(g)}</h2>{chip(g)}<span class="meta2">{len(part)} прил.</span></div>'
            sections += "".join(app_section(app, fs, med) for app, fs in part)
    nav = "".join(f'<a href="#{slug(app)}">{e(app.split(" (")[0])}</a>' for app in by_app)

    c_trs = "".join(f"""<tr><td><a href="#c-{slug(c['app'])}" class="nm">{e(c['app'])}</a>
{'<span class="chip c-go">28.10</span>' if c['sel'] else ''}</td>
<td class="desc">{e(blurb(c))}</td><td>{e(c['geo'])}</td>
<td class="r"><b>{money(c['cpa'])}</b></td><td class="r"><b>{x(c['roas'])}</b></td>
<td class="r"><b>{x(c['cov_k85'])}</b></td><td>{e(pay_short(c['payback']))}</td>
<td>{e(binfo[c['app']]['trend'].split(' (')[0].split(':')[0])}</td></tr>""" for c in cands)
    c_sections = "".join(cand_section(a, c_by_app[a], about, hist) for a in c_main)
    c_nav = "".join(f'<a href="#c-{slug(a)}">{e(a.split(" (")[0])}</a>' for a in c_by_app)
    ex_rows = "".join(f"<tr><td><b>{e(d['Приложение (группа)'])}</b></td><td class='r'>{e(d['ID строки'])}</td>"
                      f"<td class='r'>{mln(num(d['спенд за 28 дней']))}</td><td class='r'>{money(num(d['CPA за 28 дней']))}</td>"
                      f"<td class='r'>{x(num(d['ROAS за 28 дней']))}</td><td>{e(why)}</td></tr>" for d, why in excl)
    pay_txt = ", ".join(c_pay)

    doc = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Пересчёт FB-кандидатов — 09.11.2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>{CSS}</style></head><body><main class="wrap">
<header class="hero">
<p class="eyebrow">FB-выгрузки · пересчёт по требованиям Димы · 09.11.2026</p>
<h1>📊 Пересчёт FB-кандидатов (web2web)</h1>
<p class="lede">Выгрузка web2web giants #9 от 10.10.2026, метрики за 28 дней. Отбор по всей выгрузке: низкий CPA и хороший ROAS, спенд не учитывается. Ниже — выборка 28.10 с идеями.</p>
<div class="kpis">
<div class="kpi"><span class="ki">🔍</span><span class="kv">{n_web}</span><span class="kl">веб-воронок с видимым доходом из {total} строк выгрузки</span></div>
<div class="kpi"><span class="ki">🎯</span><span class="kv">{len(c_by_app)}</span><span class="kl">приложений: CPA ≤ {money(cpa_med)} и ROAS ≥ 0,75, без health ({len(cands)} воронок)</span></div>
<div class="kpi"><span class="ki">⏱️</span><span class="kv">{len(c_pay)}</span><span class="kl">окупаются в 1-й месяц при CR конкурента × 0,85</span></div>
<div class="kpi"><span class="ki">💡</span><span class="kv">{len(IDEAS)}</span><span class="kl">идей по объединению приложений (выборка 28.10)</span></div>
</div></header>
<section class="sum"><h2>Главное</h2><ol>
<li>Правило отбора: CPA не дороже медианы по веб-воронкам выгрузки ({money(cpa_med)}) и ROAS 28 дней от 0,75 (верхняя четверть). Спенд не учитывается, health и фитнес исключены. Прошли {len(c_main)} приложений.</li>
<li>В первый месяц при конверсии на 15% хуже конкурента окупаются: {e(pay_txt)}. Покрытие при CR конкурента × 0,85 равно 0,85 × ROAS, поэтому окупаемость в первый месяц требует ROAS от 1,18.</li>
<li>Динамика по выгрузкам (замена охватам, пока нет spy-данных): растут — {e(", ".join(a for a in c_by_app if binfo[a]["trend"].startswith("растёт")))}; разгоняются за последние 7 дней — {e(", ".join(a for a in c_by_app if (binfo[a]["accel"] or 0) > 1.15))}; новые — {e(", ".join(a for a in c_by_app if binfo[a]["trend"].startswith("новый")))}; падают — {e(", ".join(a for a in c_by_app if binfo[a]["trend"].startswith("падает")))}.</li>
<li>CPA выше медианы, но ROAS ≥ 1 — в отбор не попали: {e(", ".join(border))}.</li>
<li>Из выборки 28.10 правило проходит только TheRealIntro (одна воронка). Zeely — ROAS 1,14, но CPA $96 выше медианы. У остальных ROAS 0,2–0,5.</li>
<li>Событие CPA везде — предположение по доходу с конверсии; подтверждается только проходом воронки до пейволла. Ниши и воронки новых кандидатов не оценивали.</li>
</ol></section>
<section><h2>Методика ресерча: что сделано</h2>
<div class="tw"><table><thead><tr><th>Шаг методики</th><th>Статус</th><th>Как в отчёте</th></tr></thead><tbody>
<tr><td>Сортировка по CPA за 28 дней</td><td class="ok">сделано</td><td>Таблица кандидатов отсортирована по CPA; отсев — CPA ≤ {money(cpa_med)} и ROAS ≥ 0,75.</td></tr>
<tr><td>Воронка web2web, а не переход в стор</td><td class="ok">сделано по ссылке</td><td>Исключены строки со схемой «стор» и ссылками на App Store, Google Play, w2a.one, onelink. Вручную воронки не открывали.</td></tr>
<tr><td>Окупаемость в первый месяц, максимум за 3</td><td class="ok">сделано</td><td>Покрытие = доход с конверсии ÷ наша цена события; ≥ 1 — первый месяц, 0,5–1 — 2–3 месяца.</td></tr>
<tr><td>Конверсия = конверсии ÷ переходы, при копировании −15%</td><td class="ok">сделано</td><td>Сценарии CR 1%, 2%, 2,5%, CR конкурента и CR конкурента × 0,85 в каждой карточке.</td></tr>
<tr><td>Все воронки бренда, сортировка по охватам, скорость набора</td><td class="todo">частично</td><td>Охватов в выгрузке нет. Вместо них по выгрузкам 18.05–10.10: все воронки бренда, динамика спенда, ускорение за 7 дней и число объявлений. Ссылки на tyver и adheart — в карточках; охваты смотреть там.</td></tr>
<tr><td>Forplay, Sensor Tower, оптика, Similarweb</td><td class="todo">вручную</td><td>Доступа из отчёта нет. Ссылка на Similarweb по домену — в карточках; Forplay и Sensor Tower — поиск по названию бренда.</td></tr>
<tr><td>Столбец заблокированных аккаунтов почти не учитывать</td><td class="ok">учтено</td><td>В отборе и решениях не используется.</td></tr>
<tr><td>Запускать сразу несколько воронок с разными пейволами и нарративами</td><td class="todo">к тесту</td><td>В карточках — список воронок бренда (до 6) как варианты для теста. Пейволы и нарративы — после прохода воронок.</td></tr>
</tbody></table></div></section>
<section id="cands"><h2>Кандидаты по CPA и ROAS — вся выгрузка 10.10</h2>
<p class="meta2">Одна строка — одна воронка, без health и фитнеса. Сортировка по CPA. Покрытие при CR конкурента × 0,85: 1,0 — окупается в первый месяц. CPC, доход с конверсии и все сценарии цены — в карточке.</p>
<div class="tw"><table class="fit"><colgroup><col style="width:13%"><col style="width:27%"><col style="width:14%"><col style="width:8%"><col style="width:8%"><col style="width:9%"><col style="width:12%"><col style="width:9%"></colgroup>
<thead><tr><th>Приложение</th><th>Про что</th><th>Гео</th><th class="r">CPA</th><th class="r">ROAS</th>
<th class="r">Покрытие</th><th>Окупаемость</th><th>Тренд</th></tr></thead><tbody>{c_trs}</tbody></table></div>
<nav class="nav">{c_nav}</nav>{c_sections}</section>
<section><h2>Выборка 28.10: идеи по приложениям</h2><div class="ideas">{''.join(idea_card(i, by_app) for i in IDEAS)}</div></section>
<section><h2>Выборка 28.10: все воронки</h2>
<p class="meta2">Покрытие при CR конкурента × 0,85: 1,0 — окупается в первый месяц. Серым в цифрах — строки, где доход по пикселю не виден. 💡 — есть идея. Спенд, CPC и сценарии цены — в карточке.</p>
<div class="tw"><table class="fit"><colgroup><col style="width:12%"><col style="width:28%"><col style="width:14%"><col style="width:16%"><col style="width:8%"><col style="width:7%"><col style="width:8%"><col style="width:7%"></colgroup>
<thead><tr><th>Приложение</th><th>Про что</th><th>Решение</th><th>Гео</th><th class="r">CPA</th><th class="r">ROAS</th>
<th class="r">Покрытие</th><th>Окупаемость</th></tr></thead><tbody>{trs}</tbody></table></div></section>
<section><h2>Выборка 28.10: по каждому приложению</h2><nav class="nav">{nav}</nav>{sections}</section>
<section><h2>Выборка 28.10: исключено из расчёта</h2>
<div class="tw"><table><thead><tr><th>Приложение</th><th class="r">Строка</th><th class="r">Спенд 28д</th><th class="r">CPA</th><th class="r">ROAS</th><th>Причина</th></tr></thead><tbody>{ex_rows}</tbody></table></div></section>
<section><h2>Как считали и ограничения</h2><div class="lim"><ul>
<li>Срез — выгрузка web2web giants #9 от 10.10.2026, все метрики за 28 дней. Одна строка — одна воронка.</li>
<li>Отбор кандидатов по всей выгрузке: веб-воронки с видимым доходом (ROAS ≥ 0,1 и доход с конверсии ≥ $5), CPA не дороже медианы ({money(cpa_med)}) и ROAS ≥ 0,75; health и фитнес исключены (медиана CPA посчитана по всем веб-воронкам, включая health). Спенд не учитывается (минимальный в выгрузке — около $0,09M за 28 дней). Пороги — выбор для первого среза, их можно сдвинуть.</li>
<li>Web2web отобраны по ссылке из выгрузки; ссылки на App Store, w2a.one и строки без дохода исключены. Воронки и оплату вручную не проходили.</li>
<li>Сценарии CR: 1%, 2%, 2,5% (из созвона), CR конкурента = конверсии ÷ переходы, и CR конкурента × 0,85 — поправка на копирование, ориентир из созвона, не проверенное правило.</li>
<li>Окупаемость: покрытие ≥ 1 — 1-й месяц; 0,5–1 — 2–3 месяца, если держатся продления; &lt; 0,5 — за 3 месяца маловероятно. Продлений по выгрузке не видно.</li>
<li>Фактического числа конверсий в выгрузке нет: это формула (прибыль ÷ прибыль с конверсии), доход — спенд × ROAS. Конверсии = спенд ÷ CPA; CPA и ROAS округлены, точность ±1–2% (для ROAS ≤ 0,06 — до ±20%).</li>
<li>Доход с конверсии за 28 дней включает продления прошлых когорт и не учитывает возвраты — это приближение дохода первого месяца.</li>
<li>CPC — средний по строке, по странам не разбит. Гео — доли спенда по странам из выгрузки.</li>
<li>Идеи, креативы и скрины лендингов — из первой выборки 28.10; идея по Intch дополнена 09.11.</li>
</ul></div></section>
<footer class="foot"><p>Источники: reports/fb-kandidaty-itog-28-10.xlsx (листы «Шорт-лист», «Под вопросом», «Сводная (все строки)»), fb-shortlist-28-10.html. Книга с формулами: fb-pereschet-2026-11-09.xlsx. Ориентир по Character.AI — оценки Sacra и Axis Intelligence.</p></footer>
</main>
<dialog id="zoom" aria-label="Скрин крупно"><form method="dialog"><button class="close" type="submit" aria-label="Закрыть">×</button></form><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>
const d=document.getElementById('zoom'),zi=document.getElementById('zoom-img'),zc=document.getElementById('zoom-cap');
document.querySelectorAll('.shot').forEach(b=>b.addEventListener('click',()=>{{zi.src=b.querySelector('img').src;zc.textContent=b.dataset.cap;d.showModal();}}));
d.addEventListener('click',ev=>{{if(ev.target===d)d.close();}});
</script></body></html>"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    miss = [a for a in by_app if not find_media(a, med)]
    print("saved", OUT, len(doc), "chars;", counts, "| no media:", miss)
    print("cpa median", cpa_med, "| main:", c_main, "| health:", c_health, "| pay:", c_pay, "| border:", border)


if __name__ == "__main__":
    main()
