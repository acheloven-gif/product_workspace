# Красивая HTML-страница шорт-листа (карточки с креативами и скриншотами) — версия 28.10.
# Берёт карточки из reports/fb-shortlist.html (20.10), состав, порядок и цифры — из reports/fb-kandidaty-itog-28-10.xlsx.
# Выход: reports/fb-shortlist-28-10.html. Без JS — открывается из вложения ClickUp.
import re, sys, openpyxl

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
old = open(f'{ROOT}/reports/fb-shortlist.html', encoding='utf-8').read()
wb = openpyxl.load_workbook(f'{ROOT}/reports/fb-kandidaty-itog-28-10.xlsx', data_only=True)

def rows(name):
    ws = wb[name]; hdr = [c.value for c in ws[3]]
    return {ws.cell(r, 2).value: dict(zip(hdr, [ws.cell(r, c).value for c in range(1, len(hdr) + 1)]))
            for r in range(4, ws.max_row + 1) if ws.cell(r, 2).value}
D = {**rows('Шорт-лист'), **rows('Под вопросом')}

# --- карточки и блоки групп из старой страницы
cards = {}
for m in re.finditer(r'<article class="card" id="\w+">\s*<header><h3>([^<]+)</h3>', old):
    e = old.find('</article>', m.start()) + len('</article>')
    cards[m.group(1).replace('&amp;', '&')] = old[m.start():e]
groups = {}
for m in re.finditer(r'<div class="group"', old):
    e = old.find('<article', m.start()); g = old[m.start():e]
    key = 'flirt' if 'ФЛИРТ' in g else ('songs' if 'ГЕНЕРАТОРЫ' in g else 'lookup')
    groups[key] = g
groups['songs'] = groups['songs'].replace('46,5 $', '46,4 $')

PILL = {'растёт': 'up', 'держится': 'hold', 'новый': 'new', 'вернулся': 'new', 'падает': 'down'}
def money(v): return f'{v:,.0f}'.replace(',', ' ') + ' $'
def cpa_s(a):
    v = D[a].get('CPA окт')
    return f'{v:.0f} $' if isinstance(v, (int, float)) else 'н/д — оплат нет'

FIX = {  # устаревшие формулировки в карточках
    'Zeely': [('Zealy, Inc. · zealy.ai', 'Zeely, Inc. · zeely.ai')],
    'memoryOS': [('Самый низкий CPA в выгрузке 10.10.', 'CPA веб-воронки 65 $ — в нижней трети выгрузки 10.10; спенд веб-воронки к августу +41%.')],
    'Chillio': [('CPA в выгрузке аномальный (пиксель фиксирует очень мало конверсий) — по нему не сравнивать.',
                 'ПОД ВОПРОСОМ: в выгрузке 10.10 есть (строки 22 и 186, Botan App Limited), но доход 0 и ROAS 0 — оплаты не отслеживаются, CPA сравнивать нельзя. Оплаты видны только в мае (ROAS 0,35, CPA 217 $).')],
    'Aligned': [('CPA дорогой.', 'ПОД ВОПРОСОМ: CPA высокий — 180 $, дорогая треть выгрузки 10.10.')],
    'Guardio': [('CPA высокий.', 'CPA высокий (210 $). В августовских выгрузках не было — вернулся в октябре.')],
}

def card(a, cid):
    h = cards[a]; d = D[a]
    h = re.sub(r'id="\w+"', f'id="{cid}"', h, count=1)
    h = re.sub(r'name="m-\w+"', f'name="m-{cid}"', h)
    h = re.sub(r'id="\w+-(crea|shot)"', lambda m: f'id="{cid}-{m.group(1)}"', h)
    h = re.sub(r'for="\w+-(crea|shot)"', lambda m: f'for="{cid}-{m.group(1)}"', h)
    sc = d['Скор (0–100)']; t = d['Тренд авг→окт']
    k0 = h.find('<div class="kpis">'); k1 = h.find('</div>', k0)
    kp = h[k0:k1]
    kp = re.sub(r'Скор \d+/100', f'Скор {sc:.0f}/100', kp)
    kp = re.sub(r'<span class="pill (up|hold|new|down)">[^<]*</span>', f'<span class="pill {PILL[t]}">{t}</span>', kp, count=1)
    kp = re.sub(r'Спенд 28д, окт: [^<]+', f'Спенд 28д, окт: {money(d["Спенд 28д, Октябрь (10.10)"])}', kp)
    h = h[:k0] + kp + h[k1:]
    for o, n in FIX.get(a, []):
        assert o in h, (a, o); h = h.replace(o, n)
    return h

def toc(order, pre):
    tr = []
    for i, a in enumerate(order, 1):
        d = D[a]; t = d['Тренд авг→окт']
        grp = 'Флирт + ИИ-компаньон' if a in ('TheRealIntro', 'Honey (ИИ-девушка)') else (
              'Генераторы песен и клипов' if a in ('Mozart AI', 'HyperMusic AI (w2a.one)', 'Dear Melodies', 'Zurna (ИИ-фото)') else (
              'Пробив по номеру' if a in ('Trace', 'Reverse Lookup') else ''))
        tr.append(f'<tr><td>{i}</td><td><a href="#{pre}{i}">{a}</a></td><td>{d["Скор (0–100)"]:.0f}</td><td>{money(d["Спенд 28д, Октябрь (10.10)"])}</td>'
                  f'<td>{cpa_s(a)}</td><td>{d["Тир гео"]}</td><td><span class="pill {PILL[t]}">{t}</span></td><td class="muted">{grp}</td></tr>')
    return ('<div class="tw toc"><table><thead><tr><th>#</th><th>Приложение</th><th>Скор</th><th>Спенд 28д, окт</th><th>CPA окт</th>'
            '<th>Тир гео</th><th>Тренд</th><th>Группа</th></tr></thead><tbody>' + ''.join(tr) + '</tbody></table></div>')

# порядок: по скору, группы — вместе (как в xlsx, но связки рядом)
SHORT = ['Skilario', 'Intch', 'Zeely', 'memoryOS', 'Kidology', 'Prayers Academy', ('flirt', ['TheRealIntro', 'Honey (ИИ-девушка)'])]
QUEST = ['Mob (рецепты)', 'Cloaked', 'Aligned', 'Chillio', 'Guardio',
         ('songs', ['Mozart AI', 'HyperMusic AI (w2a.one)', 'Dear Melodies', 'Zurna (ИИ-фото)']), ('lookup', ['Trace', 'Reverse Lookup'])]
def flat(o): return [x for it in o for x in (it[1] if isinstance(it, tuple) else [it])]
assert sorted(flat(SHORT)) == sorted(rows('Шорт-лист')) and sorted(flat(QUEST)) == sorted(rows('Под вопросом'))

def section(sid, order, lead):
    out = [f'<section class="tab" id="{sid}"><p class="lead">{lead}</p>', toc(flat(order), sid)]
    i = 0
    for it in order:
        if isinstance(it, tuple):
            out.append(groups[it[0]])
            for a in it[1]: i += 1; out.append(card(a, f'{sid}{i}'))
        else:
            i += 1; out.append(card(it, f'{sid}{i}'))
    return '\n'.join(out) + '</section>'

head = old[:old.find('<div class="wrap">')]
css_extra = '<style>.upd{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:12px 16px;max-width:95ch}.upd b{display:block;margin-bottom:4px}.upd ul{margin:0;padding-left:18px;color:var(--fg)}</style>'
S, Q = flat(SHORT), flat(QUEST)
page = head + css_extra + f'''<div class="wrap">
<input type="radio" class="tr" name="tab" id="t-short" checked><input type="radio" class="tr" name="tab" id="t-quest">
<header class="top"><p class="eyebrow">FB-выгрузки web2web · обновлено 28.10</p><h1>Шорт-лист приложений</h1>
<p class="meth">Метрики — выгрузка 10.10 (web2web giants #9), спенд за 28 дней. Тренд — август → октябрь; ранние выгрузки (май–август) — только для тренда. В списки — только приложения из выгрузки 10.10.</p>
<div class="upd"><b>Что изменилось 28.10</b><ul>
<li>Сводная сверена построчно со всеми 6 выгрузками — цифры перенесены верно; исправлены расчёты поверх: тренды, август у части приложений, скоры, порядок.</li>
<li>Шорт-лист — только приложения с веб-воронкой и оплатами в выгрузке 10.10: {len(S)}. Убраны Mosso, Aligned и Chillio (Aligned и Chillio — в «Под вопросом»).</li>
<li>У Chillio в выгрузке 10.10 оплат нет (ROAS 0) — CPA сравнивать нельзя; оплаты видны только в мае.</li>
</ul></div>
<nav class="tabs"><label for="t-short">Шорт-лист <b>{len(S)}</b></label><label for="t-quest">Под вопросом <b>{len(Q)}</b></label></nav></header>
{section('short', SHORT, 'По скору: спенд, доля tier-1, дешевизна CPA, тренд. Связки идей — рядом.')}
{section('quest', QUEST, 'Заметный спенд в выгрузке 10.10, но есть сомнения по нише, CPA или качеству данных.')}
<footer class="muted">Источник: выгрузки web2web giants #5, #6.1, #7.1, #8, #9 и web2web new #1. Ориентир по Character.AI — оценки Sacra и Axis Intelligence.</footer>
</div>
</body></html>
'''
if '</body>' not in old: page = page.replace('</body></html>\n', '')
open(f'{ROOT}/reports/fb-shortlist-28-10.html', 'w', encoding='utf-8').write(page)
print('ok', len(S), len(Q), len(page))
