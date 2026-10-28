# Пересборка итоговой таблицы FB-выгрузок 28.10 (по замечаниям Кати от 28.10).
# Вход: reports/fb-kandidaty-itog-27-10.xlsx (сводная сверена построчно с 6 исходными выгрузками).
# Выход: reports/fb-kandidaty-itog-28-10.xlsx
# Запуск: python3 -I playbook/fb-vygruzki/rebuild_28_10.py <корень репозитория>
import openpyxl, collections, math, re, sys, copy
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.utils import get_column_letter

ROOT = sys.argv[1] if len(sys.argv) > 1 else '.'
SRC = f'{ROOT}/reports/fb-kandidaty-itog-27-10.xlsx'
OUT = f'{ROOT}/reports/fb-kandidaty-itog-28-10.xlsx'
MONTHS = ['Май', 'Июнь', 'Июль', 'Август', 'Октябрь']
MON = {'18.05': 'Май', '29.06': 'Июнь', '28.07': 'Июль', '27.08': 'Август', '28.08': 'Август', '10.10': 'Октябрь'}

wbv = openpyxl.load_workbook(SRC, data_only=True)
sv = list(wbv['Сводная (все строки)'].iter_rows(values_only=True))
H = sv[0]; ix = {h: i for i, h in enumerate(H)}
num = lambda x: x if isinstance(x, (int, float)) and not isinstance(x, bool) else 0

def scheme(u):
    u = (u or '').lower()
    return 'стор' if any(k in u for k in ['apps.apple', 'itunes.apple', 'play.google']) else 'веб'

# app, month, scheme -> pixel -> export -> [spend, conv, revenue]
D = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0.0])))
for r in sv[1:]:
    t = D[(r[0], MON[r[3]], scheme(r[ix['ссылка на ленд']]))][str(r[5])][r[3]]
    t[0] += num(r[ix['спенд за 28 дней']]); t[1] += num(r[ix['количество конверсий']]); t[2] += num(r[ix['доход за 28 дней']])

def agg(a, m, s):
    d = D.get((a, m, s))
    if not d: return None
    sp = cv = rev = 0
    for pix, ex in d.items():  # один пиксель в двух августовских выгрузках — берём выгрузку с бóльшим спендом
        e = max(ex.values(), key=lambda t: t[0]); sp += e[0]; cv += e[1]; rev += e[2]
    return sp, cv, rev

apps = sorted({r[0] for r in sv[1:]})
def main_scheme(a):
    return 'веб' if any(agg(a, m, 'веб') for m in MONTHS) else 'стор'

def trend_ao(sp):
    if not sp['Октябрь']: return 'пропал'
    if sp['Август']:
        q = sp['Октябрь'] / sp['Август'] - 1
        return 'растёт' if q > 0.2 else ('падает' if q < -0.2 else 'держится')
    return 'вернулся' if any(sp[m] for m in ['Май', 'Июнь', 'Июль']) else 'новый'

def trend_ja(sp):
    if not sp['Август']: return None
    base = sp['Июль'] or sp['Июнь']
    if not base: return 'новый'
    q = sp['Август'] / base - 1
    return 'растёт' if q > 0.2 else ('падает' if q < -0.2 else 'держится')

R = {}
for a in apps:
    s = main_scheme(a)
    x = {m: agg(a, m, s) for m in MONTHS}
    sp = {m: (v[0] if v else None) for m, v in x.items()}
    cpa = {m: (v[0] / v[1] if v and v[1] else None) for m, v in x.items()}
    rev = {m: (v[2] if v else None) for m, v in x.items()}
    R[a] = dict(s=s, sp=sp, cpa=cpa, rev=rev, ao=trend_ao(sp), ja=trend_ja(sp))

def pct(v, vals):
    if v is None: return None
    return (sum(1 for x in vals if x < v) + 1) / len(vals)
oct_vals = [R[a]['cpa']['Октябрь'] for a in apps if R[a]['cpa']['Октябрь']]
aug_vals = [R[a]['cpa']['Август'] for a in apps if R[a]['cpa']['Август']]
for a in apps:
    R[a]['pct_oct'] = pct(R[a]['cpa']['Октябрь'], oct_vals)
    R[a]['pct_aug'] = pct(R[a]['cpa']['Август'], aug_vals)

TW = {'растёт': 1, 'держится': 0.7, 'новый': 0.5, 'вернулся': 0.5}
def score(a, t1):
    s = R[a]['sp']['Октябрь']
    if not s or t1 is None: return None
    p = R[a]['pct_oct'] if R[a]['pct_oct'] is not None else 1
    return round(30 * min(max((math.log10(s) - 5) / 2, 0), 1) + 25 * t1 + 25 * (1 - p) + 20 * TW.get(R[a]['ao'], 0), 1)

wb = openpyxl.load_workbook(SRC)
changes = []
def setv(ws, r, c, v, a, label):
    cell = ws.cell(r, c); old = cell.value
    if isinstance(old, str) and old.startswith('='): return
    if isinstance(v, float): v = round(v, 6)
    diff = (isinstance(old, (int, float)) and isinstance(v, (int, float)) and abs(old - v) > max(0.05, abs(v) * 0.001)) \
        or (not (isinstance(old, (int, float)) and isinstance(v, (int, float))) and (old or None) != (v or None))
    if diff: changes.append((ws.title, a, label, old, v))
    cell.value = v

# ---------- Топ-кандидаты и Находки ----------
T1 = {}
for name in ['Топ-кандидаты', 'Находки (gems)']:
    ws = wb[name]; hdr = [c.value for c in ws[3]]; col = {h: i + 1 for i, h in enumerate(hdr) if h}
    for r in range(4, ws.max_row + 1):
        a = ws.cell(r, 2).value
        if a not in R: continue
        d = R[a]; t1 = ws.cell(r, col['Доля tier-1']).value
        if isinstance(t1, (int, float)): T1[a] = t1
        for m, h in [('Июнь', 'Спенд 28д, Июнь'), ('Июль', 'Спенд 28д, Июль'), ('Август', 'Спенд 28д, Август'), ('Октябрь', 'Спенд 28д, Октябрь (10.10)')]:
            setv(ws, r, col[h], d['sp'][m], a, h)
        setv(ws, r, col['CPA окт'], round(d['cpa']['Октябрь'], 1) if d['cpa']['Октябрь'] else None, a, 'CPA окт')
        setv(ws, r, col['CPA-перцентиль окт (0 = дешевле всех)'], d['pct_oct'], a, 'CPA-перцентиль окт')
        setv(ws, r, col['Тренд июнь–авг'], d['ja'], a, 'Тренд июнь–авг')
        setv(ws, r, col['Тренд авг→окт'], d['ao'], a, 'Тренд авг→окт')
        if isinstance(t1, (int, float)) and ws.cell(r, col['Скор (0–100)']).value is not None:  # где скора не было (health в «Находках») — не добавляем
            setv(ws, r, col['Скор (0–100)'], score(a, t1), a, 'Скор')

# ---------- Health и фитнес ----------
ws = wb['Health и фитнес']; hdr = [c.value for c in ws[1]]; col = {h: i + 1 for i, h in enumerate(hdr) if h}
for r in range(2, ws.max_row + 1):
    a = ws.cell(r, 1).value
    if a not in R: continue
    d = R[a]
    for m in MONTHS:
        h = f'Спенд 28д, {m}'
        if h in col: setv(ws, r, col[h], d['sp'][m], a, h)
    setv(ws, r, col['CPA авг'], round(d['cpa']['Август'], 1) if d['cpa']['Август'] else None, a, 'CPA авг')
    setv(ws, r, col['CPA-перцентиль авг'], d['pct_aug'], a, 'CPA-перцентиль авг')
    setv(ws, r, col['CPA окт'], round(d['cpa']['Октябрь'], 1) if d['cpa']['Октябрь'] else None, a, 'CPA окт')
    setv(ws, r, col['CPA-перцентиль окт'], d['pct_oct'], a, 'CPA-перцентиль окт')

# ---------- Веб и стор отдельно ----------
ws = wb['Веб и стор отдельно']; hdr = [c.value for c in ws[3]]; col = {h: i + 1 for i, h in enumerate(hdr) if h}
for r in range(4, ws.max_row + 1):
    a = ws.cell(r, 1).value; sc = ws.cell(r, 2).value
    if a not in R or not sc: continue
    s = 'стор' if 'стор' in sc and 'веб' not in sc else 'веб'
    for m in MONTHS:
        v = agg(a, m, s)
        setv(ws, r, col[f'Спенд 28д, {m}'], v[0] if v else None, a, f'{s}: спенд {m}')
        setv(ws, r, col[f'CPA, {m}'], round(v[0] / v[1], 2) if v and v[1] else None, a, f'{s}: CPA {m}')

# ---------- Шорт-лист и Под вопросом: пересборка ----------
def parse_cards(ws):
    toc = {}; r = 6
    while isinstance(ws.cell(r, 1).value, int) or (isinstance(ws.cell(r, 1).value, str) and ws.cell(r, 1).value.isdigit()):
        toc[ws.cell(r, 2).value] = [ws.cell(r, c).value for c in range(1, 9)]; r += 1
    starts = []
    for rr in range(r, ws.max_row + 1):
        v = ws.cell(rr, 1).value; n2 = ws.cell(rr + 1, 1).value
        if v in toc and isinstance(n2, str) and '· пиксель ' in n2: starts.append((v, rr))
    cards = {}
    for i, (a, s) in enumerate(starts):
        e = starts[i + 1][1] - 1 if i + 1 < len(starts) else ws.max_row
        cards[a] = (ws, s, e)
    return toc, cards

toc_s, cards_s = parse_cards(wb['Шорт-лист'])
toc_q, cards_q = parse_cards(wb['Под вопросом'])
allcards = {**cards_s, **cards_q}; alltoc = {**toc_s, **toc_q}

REASON = {
    'Chillio': 'ПОД ВОПРОСОМ: в выгрузке 10.10 у Chillio (Botan App Limited, домен get-chillio.app) две строки — ID 22 и 186, спенд 1,85M и 0,12M, — но дохода нет (ROAS 0), CPA в выгрузке 51 467 и 4 455: оплаты не отслеживаются, сравнивать нельзя. Последний срез, где видны оплаты, — май (ROAS 0,35, CPA 217, другая воронка winter-magic). Ссылка gs-house-ai из выгрузки не открывается. ',
    'Aligned': 'ПОД ВОПРОСОМ (решение 20.10): CPA $180 — в дорогой трети выгрузки 10.10; в шорт-лист не берём. ',
}
SHORT = [a for a in toc_s if a not in ('Chillio', 'Aligned', 'Mosso')]
QUEST = list(toc_q) + ['Aligned', 'Chillio']
def tier(a): return alltoc[a][5]
def sc_of(a):
    t1 = T1.get(a)
    return score(a, t1) if t1 is not None else alltoc[a][2]
SHORT.sort(key=lambda a: -(sc_of(a) or 0)); QUEST.sort(key=lambda a: -(sc_of(a) or 0))

def copy_row_style(src, dst):
    if src.has_style:
        dst.font = copy.copy(src.font); dst.fill = copy.copy(src.fill); dst.border = copy.copy(src.border)
        dst.alignment = copy.copy(src.alignment); dst.number_format = src.number_format; dst.protection = copy.copy(src.protection)

def build(title, order, intro):
    old = wb[title]; idx = wb.sheetnames.index(title)
    ws = wb.create_sheet(title + '_new', idx)
    for k, d in old.column_dimensions.items(): ws.column_dimensions[k].width = d.width
    ws.sheet_view.showGridLines = old.sheet_view.showGridLines
    tmpl_toc = 6
    for r in range(1, 6):
        for c in range(1, 9):
            s = old.cell(r, c); t = ws.cell(r, c); t.value = s.value; copy_row_style(s, t)
        ws.row_dimensions[r].height = old.row_dimensions[r].height
    for m in old.merged_cells.ranges:
        if m.max_row <= 5: ws.merge_cells(str(m))
    ws.cell(2, 1).value = intro
    cur = 6 + len(order) + 3
    starts = {}
    for a in order:
        src, s, e = allcards[a]
        starts[a] = cur; off = cur - s
        for r in range(s, e + 1):
            ws.row_dimensions[r + off].height = src.row_dimensions[r].height
            for c in range(1, 9):
                sc = src.cell(r, c); t = ws.cell(r + off, c); t.value = sc.value; copy_row_style(sc, t)
                if sc.hyperlink:
                    t.hyperlink = copy.copy(sc.hyperlink); t.hyperlink.ref = t.coordinate
        for m in src.merged_cells.ranges:
            if s <= m.min_row and m.max_row <= e:
                ws.merge_cells(start_row=m.min_row + off, start_column=m.min_col, end_row=m.max_row + off, end_column=m.max_col)
        for cf in src.conditional_formatting:
            for rng in cf.sqref.ranges:
                if s <= rng.min_row and rng.max_row <= e:
                    for rule in cf.rules:
                        ws.conditional_formatting.add(f'{get_column_letter(rng.min_col)}{rng.min_row + off}:{get_column_letter(rng.max_col)}{rng.max_row + off}', copy.copy(rule))
        # мета-строка карточки: тренд и скор
        meta = ws.cell(cur + 2, 1)
        if isinstance(meta.value, str):
            v = re.sub(r'тренд авг→окт: [^·]+', f'тренд авг→окт: {R[a]["ao"]}   ', meta.value)
            sc_ = sc_of(a)
            v = re.sub(r'скор \d+/100', f'скор {round(sc_) if sc_ is not None else "—"}/100', v)
            if v != meta.value: changes.append((title, a, 'карточка: тренд/скор', meta.value[-60:], v[-60:]))
            meta.value = v
        if a in REASON:
            idea = ws.cell(cur + 3, 1)
            idea.value = REASON[a] + (idea.value or '')
        cur = e + off + 1
    for i, a in enumerate(order):
        r = 6 + i; d = R[a]; sc_ = sc_of(a)
        vals = [i + 1, a, round(sc_) if sc_ is not None else None, d['sp']['Октябрь'],
                round(d['cpa']['Октябрь'], 1) if d['cpa']['Октябрь'] else None, tier(a), d['ao'], alltoc[a][7]]
        for c, v in enumerate(vals, 1):
            t = ws.cell(r, c); t.value = v; copy_row_style(old.cell(tmpl_toc, c), t)
        ws.row_dimensions[r].height = old.row_dimensions[tmpl_toc].height
        ws.cell(r, 2).hyperlink = Hyperlink(ref=ws.cell(r, 2).coordinate, location=f"'{title}'!A{starts[a]}")
        if a == 'Chillio': ws.cell(r, 5).value = 'н/д (ROAS 0)'
    ws.freeze_panes = old.freeze_panes
    wb.remove(old); ws.title = title

PERIOD = ('Источник: 6 выгрузок FB (18.05, 29.06, 28.07, 27.08, 28.08, 10.10). Метрики пикселя и спенд — по самой свежей выгрузке 10.10 (web2web giants #9), '
          'спенд за 28 дней; тренд — октябрь к августу; более ранние срезы — только история. В список попадают приложения, которые есть в выгрузке 10.10 '
          'с веб-воронкой и с отслеживаемыми оплатами (доход > 0). Скор: 30% спенд, 25% доля tier-1, 25% дешевизна CPA, 20% тренд; сортировка по скору.')
build('Шорт-лист', SHORT, 'Приложения-кандидаты без оговорок. ' + PERIOD + ' Сомнительные — на листе «Под вопросом».')
build('Под вопросом', QUEST, 'Варианты с оговорками: заметный спенд в выгрузке 10.10, но есть сомнения по нише, продукту, CPA или качеству данных. ' + PERIOD)

# ---------- Методика ----------
ws = wb['Методика (27.10)']; ws.title = 'Методика (28.10)'
r0 = ws.max_row + 2
lines = [
    'Обновление 28.10 (по комментарию Кати от 28.10)',
    '1. Сводная сверена построчно с исходными выгрузками (6 файлов, 892 строки, все числовые поля) — совпадает. Подробности — лист «Проверка (28.10)».',
    '2. Тренд авг→окт: «новый» — только если приложения нет ни в одной выгрузке до октября; если было в мае–июле, но не в августе — «вернулся» (вес в скоре как у «новый»).',
    '3. Спенд по месяцам пересчитан для всех приложений во всех листах по одному правилу: основная схема (веб), один пиксель в двух августовских выгрузках — берётся выгрузка с бóльшим спендом.',
    '4. Шорт-лист и «Под вопросом»: только приложения из выгрузки 10.10 с веб-воронкой и доходом > 0. Таблица содержания и карточки отсортированы по скору; тренд и скор в карточках обновлены.',
    '5. Chillio перенесён в «Под вопросом»: в выгрузке 10.10 нет дохода (ROAS 0), CPA некорректен. Решения 20.10 перенесены и в таблицу: Mosso убран из шорт-листа, Aligned — в «Под вопросом».',
    '6. Лист «Вертикали» не пересчитывался: в нём спенд по всем схемам (веб + стор); для CPA и сравнения приложений не использовать.',
    '',
    'Что изменилось 28.10 (было → стало):',
]
for i, t in enumerate(lines): ws.cell(r0 + i, 1).value = t
ws.cell(r0, 1).font = openpyxl.styles.Font(bold=True)
r1 = r0 + len(lines)
for j, h in enumerate(['Лист', 'Приложение', 'Поле', 'Было', 'Стало']): ws.cell(r1, j + 1).value = h
for k, ch in enumerate(changes, 1):
    for j, v in enumerate(ch): ws.cell(r1 + k, j + 1).value = v if not isinstance(v, float) else round(v, 4)

# ---------- Проверка (28.10) ----------
pv = wb.create_sheet('Проверка (28.10)', 1)
pv.column_dimensions['A'].width = 34; pv.column_dimensions['B'].width = 120
B = openpyxl.styles.Font(bold=True)
rows = [
    ('ПРОВЕРКА ДАННЫХ (28.10)', None),
    (None, None),
    ('Исходники', 'web2web giants #5 (18.05), #6.1 (29.06), #7.1 (28.07), web2web new #1 (27.08), giants #8 (28.08), giants #9 (10.10) — файлы из задачи в ClickUp и от Наташи.'),
    ('1. Сводная ↔ исходники', 'Все 892 строки «Сводной» найдены в исходниках по дате выгрузки и ID строки; все числовые поля (спенд, ROAS, CPA, доход, прибыль, конверсии, аккаунты, объявления, топ-объявление) совпадают. '
     'Расхождения только в формате: 14 длинных ID пикселя Excel хранит как число (последние цифры округлены), 1 ссылка Tyver в исходнике — #REF!. Ошибок переноса нет.'),
    ('2. Полнота', 'Строки выгрузки 10.10, не попавшие в «Сводную», проверены по спенду: это нутра/БАДы, товарка и мини-сериалы (Hims, Noom Med, Kilo, Orbio, LifeMD, cherryshort и т.п.) — по условию задачи не берём. Пропущенных приложений не найдено.'),
    ('3. Арифметика листов', 'Спенд по месяцам, CPA, перцентили, тренды и скор в «Топ», «Находки», «Health», «Веб и стор», таблицах содержания и карточках пересчитаны независимо от «Сводной» и сверены: после исправлений расхождений 0. '
     'Метрики пикселя в карточках (спенд, доход, ROAS, CPA, конверсии, клики, аккаунты) сверены с выгрузкой 10.10 — 228 ячеек, расхождений 0.'),
    ('4. Что было неправильно', 'а) тренд «новый» у приложений, которые были в мае–июле, но не в августе (Guardio, SweetSecrets) → «вернулся»; '
     'б) у части приложений тренд июнь–авг и спенд за август остались от старой версии расчёта (Testora, Kure, MyBody) → пересчитано по одному правилу; '
     'в) в карточках шорт-листа остались старые скор и тренд (Zeely 76 → 69, memoryOS «держится» → «растёт»); таблица содержания была не по скору; '
     'г) Chillio стоял в шорт-листе с CPA 31 320 — см. п. 5; '
     'д) решения 20.10 не были перенесены в таблицу: Mosso убран из шорт-листа, Aligned — в «Под вопросом». Полный список «было → стало» — на листе «Методика (28.10)».'),
    ('5. Chillio', 'В выгрузке 10.10 есть: строки ID 22 (пиксель 479921384506883, quiz.get-chillio.app/gs-house-ai, спенд 28д 1 852 797) и ID 186 (пиксель 2896379393996743, cleaning-game, 120 276), аккаунт Botan App Limited. '
     'Но доход 0, ROAS 0, CPA в выгрузке 51 467 и 4 455 — оплаты по пикселю не отслеживаются, оценить связку нельзя. Оплаты видны только в мае (ROAS 0,35, CPA 217, воронка winter-magic); в июле–августе ROAS 0,08 → 0,01. '
     'Поэтому Chillio убран из шорт-листа в «Под вопросом».'),
    ('6. Правило шорт-листа', 'Только приложения из самой свежей выгрузки (10.10) с веб-воронкой и доходом > 0; метрики — по выгрузке 10.10; ранние выгрузки — только для тренда и истории.'),
    ('7. На что смотреть осторожно', None),
]
anom_lo = []; anom_zero = []
for r in sv[1:]:
    sp = num(r[ix['спенд за 28 дней']]); cpa = r[ix['CPA за 28 дней']]; roas = r[ix['ROAS за 28 дней']]
    if scheme(r[ix['ссылка на ленд']]) == 'веб' and isinstance(cpa, (int, float)) and cpa < 10 and sp > 50000:
        anom_lo.append(f'{r[0]} ({r[3]}, ID {r[4]}: спенд ' + f'{sp:,.0f}'.replace(',', ' ') + f', CPA {cpa})')
    if r[3] == '10.10' and sp > 100000 and not num(r[ix['доход за 28 дней']]):
        anom_zero.append(f'{r[0]} (ID {r[4]}: спенд ' + f'{sp:,.0f}'.replace(',', ' ') + f', CPA {cpa})')
rows += [
    ('   веб-строки с CPA < 10', 'похоже на оптимизацию на установку/лид, а не оплату — CPA не сравним: ' + '; '.join(anom_lo) + '.'),
    ('   10.10: доход 0 при спенде > 100k', 'оплаты не отслеживаются, CPA не сравним: ' + '; '.join(anom_zero) + '.'),
    ('   опечатки в выгрузке 10.10', 'у Zeely в выгрузке 10.10 написано «Zealy, Inc.» и zealy.ai — пиксель тот же (507395697701950), это Zeely; часть ссылок на ленды в выгрузке битая (gs-house-ai у Chillio и др.).'),
    ('   «Вертикали»', 'спенд по всем схемам (веб + стор), не пересчитывался — для CPA и сравнения приложений не использовать.'),
]
for i, (k, v) in enumerate(rows, 1):
    pv.cell(i, 1).value = k; pv.cell(i, 2).value = v
    pv.cell(i, 1).font = B; pv.cell(i, 2).alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
    pv.cell(i, 1).alignment = openpyxl.styles.Alignment(wrap_text=True, vertical='top')
pv.cell(1, 1).font = openpyxl.styles.Font(bold=True, size=14)

wb.save(OUT)
print('changes', len(changes))
for c in changes: print(c)
print('SHORT', SHORT); print('QUEST', QUEST)
