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


# ---------- Шорт-лист и Под вопросом: простые таблицы в формате «Топ-кандидатов» ----------
from openpyxl.formula.translate import Translator
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill

WHY_Q = {
    'Mob (рецепты)': 'Рынок рецептов и планировщиков питания перенасыщен; ROAS в октябре 0,05.',
    'Cloaked': 'CPA высокий ($474, дорогая треть выгрузки 10.10).',
    'Aligned': 'CPA высокий ($180, дорогая треть выгрузки 10.10).',
    'Chillio': 'В выгрузке 10.10 есть (строки 22 и 186, Botan App Limited), но доход 0 (ROAS 0), CPA 51 467 и 4 455 — оплаты не отслеживаются, сравнить нельзя. Оплаты видны только в мае (ROAS 0,35, CPA 217).',
    'Guardio': 'CPA высокий ($210); в августовских выгрузках не было, вернулся в октябре.',
    'Mozart AI': 'Новый: есть только в выгрузке 10.10, тренда нет.',
    'HyperMusic AI (w2a.one)': 'Новый: есть только в выгрузке 10.10, тренда нет; ведёт в приложение.',
    'Trace': 'Доход почти нулевой (ROAS 0,06) — оплаты по пикселю видны плохо, CPA ненадёжен.',
    'Dear Melodies': 'Гео смешанное (tier-1 и не tier-1); ниша песен на заказ новая, спенд держится.',
    'Reverse Lookup': 'Доход почти нулевой (ROAS 0,01) — CPA ненадёжен; гео смешанное.',
    'Zurna (ИИ-фото)': 'Новый: есть только в выгрузке 10.10; CPA высокий ($192).',
}
TRENDS = 'растёт,держится,падает,новый,вернулся'

def copy_row_style(src, dst):
    if src.has_style:
        dst.font = copy.copy(src.font); dst.fill = copy.copy(src.fill); dst.border = copy.copy(src.border)
        dst.alignment = copy.copy(src.alignment); dst.number_format = src.number_format; dst.protection = copy.copy(src.protection)
FILL = {'растёт': 'C6EFCE', 'держится': 'FFEB9C', 'падает': 'FFC7CE', 'новый': 'DDEBF7', 'вернулся': 'DDEBF7'}

def src_row(a):
    for n in ['Топ-кандидаты', 'Находки (gems)']:
        w = wb[n]
        for r in range(4, w.max_row + 1):
            if w.cell(r, 2).value == a: return w, r
    raise KeyError(a)

def trend_rules(ws, col_letter, r1, r2):
    rng = f'{col_letter}{r1}:{col_letter}{r2}'
    for k, c in FILL.items():
        ws.conditional_formatting.add(rng, FormulaRule(formula=[f'{col_letter}{r1}="{k}"'], fill=PatternFill('solid', start_color=c, end_color=c)))
    dv = DataValidation(type='list', formula1=f'"{TRENDS}"', allow_blank=True); ws.add_data_validation(dv); dv.add(rng)

top = wb['Топ-кандидаты']
def build_table(title, order, intro, why_hdr, why):
    idx = wb.sheetnames.index(title); wb.remove(wb[title])
    ws = wb.create_sheet(title, idx)
    for k, d in top.column_dimensions.items(): ws.column_dimensions[k].width = d.width
    ws.sheet_view.showGridLines = top.sheet_view.showGridLines
    for r in (1, 2, 3):
        ws.row_dimensions[r].height = top.row_dimensions[r].height
        for c in range(1, top.max_column + 1):
            s = top.cell(r, c); t = ws.cell(r, c); t.value = s.value; copy_row_style(s, t)
    for m in top.merged_cells.ranges:
        if m.max_row <= 3: ws.merge_cells(str(m))
    ws.cell(1, 1).value = intro
    hdr = [ws.cell(3, c).value for c in range(1, top.max_column + 1)]
    wcol = hdr.index('Почему') + 1; ws.cell(3, wcol).value = why_hdr
    for i, a in enumerate(order):
        sw, sr = src_row(a); r = 4 + i
        ws.row_dimensions[r].height = sw.row_dimensions[sr].height
        for c in range(1, top.max_column + 1):
            s = sw.cell(sr, c); t = ws.cell(r, c); copy_row_style(top.cell(4, c), t)
            v = s.value
            if isinstance(v, str) and v.startswith('='):
                v = Translator(v, origin=s.coordinate).translate_formula(t.coordinate)
            t.value = v
            if s.hyperlink: t.hyperlink = copy.copy(s.hyperlink); t.hyperlink.ref = t.coordinate
        ws.cell(r, 1).value = i + 1
        if why: ws.cell(r, wcol).value = why[a]
        if a == 'Chillio': ws.cell(r, hdr.index('CPA окт') + 1).value = None
    r2 = 3 + len(order)
    for cf in top.conditional_formatting:
        for rng in cf.sqref.ranges:
            col = get_column_letter(rng.min_col)
            if col in ('D', 'E'): continue
            for rule in cf.rules: ws.conditional_formatting.add(f'{col}4:{col}{r2}', copy.copy(rule))
    trend_rules(ws, 'D', 4, r2); trend_rules(ws, 'E', 4, r2)
    ws.freeze_panes = top.freeze_panes

# в «Топ» и «Находках» в списке трендов тоже нужен «вернулся»
for n in ['Топ-кандидаты', 'Находки (gems)']:
    w = wb[n]
    for dv in w.data_validations.dataValidation:
        if dv.formula1 and 'новый' in dv.formula1: dv.formula1 = f'"{TRENDS}"'
    for cf in list(w.conditional_formatting):
        for rng in cf.sqref.ranges:
            col = get_column_letter(rng.min_col)
            if col in ('D', 'E'):
                c = FILL['вернулся']
                w.conditional_formatting.add(rng.coord, FormulaRule(formula=[f'{col}{rng.min_row}="вернулся"'], fill=PatternFill('solid', start_color=c, end_color=c)))

INTRO = ('Метрики — по самой свежей выгрузке 10.10 (web2web giants #9), спенд за 28 дней; тренд авг→окт — октябрь к августу; ранние выгрузки (май–август) — только для тренда. '
         'В список — только приложения, которые есть в выгрузке 10.10, с веб-воронкой и доходом > 0. Сортировка по скору: 30% спенд, 25% доля tier-1, 25% дешевизна CPA, 20% тренд.')
build_table('Шорт-лист', SHORT, 'Шорт-лист: кандидаты без оговорок. ' + INTRO, 'Почему', None)
build_table('Под вопросом', QUEST, 'Под вопросом: заметный спенд в выгрузке 10.10, но есть сомнения по нише, CPA или качеству данных. ' + INTRO, 'Почему под вопросом', WHY_Q)
wb.move_sheet('Шорт-лист', -wb.sheetnames.index('Шорт-лист'))
wb.move_sheet('Под вопросом', 1 - wb.sheetnames.index('Под вопросом'))
del wb['Методика (27.10)']

wb.save(OUT)
print('changes', len(changes))
for c in changes: print(c)
print('SHORT', SHORT); print('QUEST', QUEST)
