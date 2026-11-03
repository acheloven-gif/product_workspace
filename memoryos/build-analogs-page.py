# Страница «Воронки аналогов memoryOS» (Artifact): плитки-цифры, короткая таблица, по 2–3 скрина на приложение; подробности — во всплывающих подсказках (data-tip).
#   python3 memoryos/build-analogs-page.py → memoryos/memoryos-analogs-page.html
# Скрины — references/memoryos/analogs/ и references/memoryos/funnel/. Стили — memoryos/analogs-page.css.
import base64, io, os, html
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(S, '..', 'references', 'memoryos')
OUT = os.path.join(S, 'memoryos-analogs-page.html')

def img(path, w=420):
    im = Image.open(os.path.join(R, path)).convert('RGB')
    if im.width > w: im = im.resize((w, int(im.height * w / im.width)))
    if im.height > w * 2.3: im = im.crop((0, 0, im.width, int(w * 2.3)))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=70)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def esc(s): return html.escape(s)

TEST, QUIZ = 'Сначала IQ-тест', 'Опрос о себе'
# q — сколько экранов-вопросов до e-mail (по прохождению 02–03.11.2026, США)
APPS = [
  dict(id='memoryos', name='memoryOS', type=QUIZ, q='19 вопросов + 3 вставки', mail='да, и имя',
       price='4 нед $15,19 → $49,99 · 12 нед $36,99 → $99,99 · 24 нед $59,99 → $119,99',
       ads='$347K веб + $163K стор, CPA $65, ROAS 0,40', walked='до пейволла',
       links=[('https://start.memoryos.com/new-h', 'start.memoryos.com/new-h')],
       about='Квиз про то, что забываете: имена, даты, пароли; страх возрастной памяти; Mind Palace «как у Шерлока». Затем «персональный план памяти», e-mail и пейволл с таймером.',
       screens=[('funnel/01-intro.jpg', 'Интро: «забываете имена и детали?»'), ('analogs/memoryos-now-11.jpg', 'Вопрос о деменции'), ('analogs/memoryos-paywall-1102-1.jpg', 'Пейволл: «сейчас → цель»')]),
  dict(id='cognitivegrowth', name='CognitiveGrowth', type=TEST, q='25 заданий, вопросов о себе нет', mail='нет',
       price='3 дня $0,99 → $12,99 в неделю', ads='$179K, CPA $42, ROAS 0,12', walked='до пейволла',
       links=[('https://quiz.cognitivegrowth.net/brain-iq/', 'quiz.cognitivegrowth.net/brain-iq'), ('https://quiz.cognitivegrowth.net/brain-iq-ja', 'brain-iq-ja (Япония)')],
       about='Сразу тест из 25 матриц-картинок, потом «считаем IQ» по 5 измерениям (в т.ч. Memory) и пейволл с закрытым результатом. В рекламе — деменция.',
       screens=[('analogs/cognitivegrowth-01.jpg', 'Задание-матрица'), ('analogs/cognitivegrowth-27.jpg', 'Расчёт по 5 измерениям'), ('analogs/cognitivegrowth-37.jpg', 'Пейволл: триал $0,99')]),
  dict(id='myiq', name='MyIQ', type=TEST, q='40 заданий (в т.ч. на память) + 3 вопроса о себе', mail='не дошли',
       price='не видели', ads='$5,48M — крупнейший в вертикали', walked='до расчёта (защита от ботов); у Наташи — «Assessment Incomplete»',
       links=[('https://myiq.com/start', 'myiq.com/start')],
       about='Тест на 40 заданий с таймером. Внутри — память: «запомните слово, спросим в конце», «запомните цифры, исчезнут через 2 с».',
       screens=[('analogs/myiq-00.jpg', 'Старт: 40 вопросов'), ('analogs/myiq-04.jpg', '«Запомните слово»'), ('analogs/myiq-10.jpg', '«Запомните цифры»')]),
  dict(id='intellio', name='Intellio', type=TEST, q='25 заданий + 2 вопроса о себе', mail='да',
       price='неделя $6,99 · 4 нед $19,99 → $39,99 · 12 нед $39,99 → $79,99', ads='$218K, CPA $127, ROAS 0,68', walked='до пейволла',
       links=[('https://intellio.club/start?cohort=intl_2&lang=en', 'intellio.club/start')],
       about='Тест «логика, паттерны, память» → расчёт IQ и плана → e-mail → пейволл, где отчёт виден частично и закрыт до оплаты.',
       screens=[('analogs/intellio-02.jpg', '«Тест: логика, паттерны, память»'), ('analogs/intellio-03.jpg', 'Задание'), ('analogs/intellio-paywall-1.jpg', 'Пейволл: отчёт закрыт')]),
  dict(id='selfery', name='Selfery', type=TEST, q='37 вопросов: ~31 задание (в т.ч. на память) + 6 о себе', mail='да, и имя',
       price='7 дней $4,99 · 1 мес $15,19 → $49,99/мес · 3 мес $25,99 → $69,99', ads='$62–72K (август), ROAS 1,40–1,44 — лучший в вертикали', walked='до пейволла',
       links=[('https://quiz.selferyapp.com/', 'quiz.selferyapp.com')],
       about='IQ-тест с таймером, внутри задания на память («запомните 8935 — какая 3-я цифра?»). Отчёт-тизер с навыками Logic, Memory, Speed, затем пейволл.',
       screens=[('analogs/selfery-18.jpg', '«Запомните 8935»'), ('analogs/selfery-53.jpg', 'Отчёт-тизер с Memory'), ('analogs/selfery-paywall-1.jpg', 'Пейволл')]),
  dict(id='testora', name='Testora', type=TEST, q='45 заданий', mail='не дошли',
       price='не видели', ads='$572K + $323K, CPA $65–69, ROAS 0,13–0,15', walked='18 заданий из 45',
       links=[('https://funnel.testora.space/start-1?cohort=testora_fl_iq_tp1', 'funnel.testora.space/start-1')],
       about='Длинный IQ-тест с таймером. С 04.2026 у компании (Extramile Ltd, она же MyGrowth) своё приложение в сторе.',
       screens=[('analogs/testora-00.jpg', 'Старт'), ('analogs/testora-06.jpg', 'Задание с таймером')]),
  dict(id='impulse', name='Impulse', type=QUIZ, q='18 вопросов + 2 во время загрузки', mail='да, и имя',
       price='4 нед $19,99 → $39,98 · 12 нед $39,99 → $79,98 · 24 нед $59,99 → $119,98', ads='в мае $1,5–1,8M (ROAS 1,05–1,22), в срезе 10.10 нет', walked='до пейволла',
       links=[('https://iq.mental-impulse.com/', 'iq.mental-impulse.com')],
       about='«1-minute quiz»: навыки (Memory первым), цели, шкалы согласия, минуты в день. Пока «собирается план» — всплывают вопросы «Да/Нет».',
       screens=[('analogs/impulse-04.jpg', 'Навыки: Memory первым'), ('analogs/impulse-24.jpg', 'Вопрос во время загрузки'), ('analogs/impulse-paywall-1.jpg', 'Пейволл')]),
  dict(id='nibble', name='Nibble', type=QUIZ, q='30 вопросов', mail='да, и имя',
       price='неделя $6,93 · 4 нед $15,19 → $38,95 · 12 нед $36,99 → $94,85', ads='в наших выгрузках нет', walked='до пейволла',
       links=[('https://nibble-app.com/funnels/general-en/quiz/general-en', 'nibble-app.com/funnels/general-en')],
       about='Микрообучение «вместо скроллинга». Навыки Memory и Focus, блок «сколько скроллите → до скольки сократить», экран «сейчас → цель».',
       screens=[('analogs/nibble-08.jpg', 'Навыки: Memory, Focus'), ('analogs/nibble-46.jpg', '«Сейчас → цель»'), ('analogs/nibble-paywall-1.jpg', 'Пейволл: промокод')]),
  dict(id='headway', name='Headway', type=QUIZ, q='~28 вопросов', mail='да',
       price='4 нед $19,99 → $39,98 · 12 нед $39,99 → $79,98 · 24 нед $59,99 → $119,98', ads='в наших выгрузках нет', walked='до пейволла',
       links=[('https://makeheadway.com/onboarding/start', 'makeheadway.com/onboarding/start')],
       about='Саммари книг. Опрос о целях и самооценке, проба книги, минуты в день, «план саморазвития», пейволл. Цены как у Impulse.',
       screens=[('analogs/headway-00.jpg', 'Старт: возраст сразу'), ('analogs/headway-06.jpg', 'Шкала самооценки'), ('analogs/headway-paywall-1.jpg', 'Пейволл')]),
  dict(id='inflow', name='Inflow', type=QUIZ + ' с результатом-шкалой', q='~36 вопросов + ~10 вставок', mail='да',
       price='пейволл не видели · App Store: $47,99/мес, $199,99/год', ads='в наших выгрузках нет', walked='до выбора направлений',
       links=[('https://www.getinflow.io/', 'getinflow.io'), ('https://www.join.getinflow.io/inflow-quiz/fuba-v2', 'join.getinflow.io/inflow-quiz')],
       about='Квиз про признаки СДВГ с маскотом-гидом. После e-mail — результат по шкале Low / Moderate / High / Very High и выбор направлений.',
       screens=[('analogs/inflow-12.jpg', 'Вопрос о прокрастинации'), ('analogs/inflow-63.jpg', 'Результат-шкала'), ('analogs/inflow-73.jpg', 'Выбор направлений')]),
  dict(id='mygrowth', name='MyGrowth', type=QUIZ + ' + вопросы-эрудиция', q='26 вопросов + 2 вставки', mail='да',
       price='не видели: поле e-mail не приняло ввод', ads='$522K (app.mygrowth.one), ROAS 0,72', walked='до e-mail',
       links=[('https://quiz.mygrowth.one/', 'quiz.mygrowth.one'), ('https://app.mygrowth.one/?cohort=anatomy-bau', 'app.mygrowth.one (основная в FB)')],
       about='Микрообучение. Вопросы о себе вперемешку с проверкой знаний («Кто такой Осирис?»), затем «курс под вас» с навыком Memory.',
       screens=[('analogs/mygrowth-13.jpg', 'Вопрос-эрудиция'), ('analogs/mygrowth-41.jpg', 'Курс: Memory среди навыков'), ('analogs/mygrowth-42.jpg', 'E-mail')]),
  dict(id='nofunnel', name='Elevate и Mindvalley', type='Без квиза', q='—', mail='—',
       price='Elevate ~$40/год в приложении; Mindvalley — членство', ads='в наших выгрузках нет', walked='лендинг',
       links=[('https://themindcompany.com/apps/elevate', 'Elevate'), ('https://www.mindvalley.com/superbrain', 'Mindvalley Superbrain')],
       about='Квиза нет: Elevate ведёт с лендинга в стор, Mindvalley продаёт курс Jim Kwik.',
       screens=[('analogs/elevate-landing.jpg', 'Elevate: лендинг'), ('analogs/mv-landing.jpg', 'Mindvalley: курс')]),
]


# Коротко для таблицы и карточек: вопросов, вход, продление, реклама (коротко), что берём
SHORT = {
 'memoryos':        ('19', '$15,19', '$49,99 / 4 нед', '$0,51M', 'Квиз целиком — основа клона'),
 'cognitivegrowth': ('25', '$0,99', '$12,99 / нед', '$0,18M', 'Закрытый результат на пейволле'),
 'myiq':            ('43', '—', '—', '$5,5M', 'Задания «запомни → вспомни» в тесте'),
 'intellio':        ('27', '$19,99', '$39,99 / 4 нед', '$0,22M', 'Отчёт виден частично, остальное — после оплаты'),
 'selfery':         ('37', '$15,19', '$49,99 / мес', '$0,07M', 'Тест с заданиями на память — лучший ROAS'),
 'testora':         ('45', '—', '—', '$0,90M', 'Только для сравнения'),
 'impulse':         ('20', '$19,99', '$39,98 / 4 нед', '$1,5–1,8M (май)', 'Вопросы во время загрузки плана'),
 'nibble':          ('30', '$15,19', '$38,95 / 4 нед', '—', 'Экран «сейчас → цель», блок про скроллинг'),
 'headway':         ('~28', '$19,99', '$39,98 / 4 нед', '—', 'Ориентир по ценам'),
 'inflow':          ('~36', '—', '$47,99 / мес', '—', 'Результат-шкала перед пейволлом'),
 'mygrowth':        ('26', '—', '—', '$0,52M', 'Только для сравнения'),
 'nofunnel':        ('—', '—', '~$40 / год', '—', 'Ежедневная тренировка в продукте'),
}

def tip(t): return f' data-tip="{esc(t)}" tabindex="0"'

def typechip(t):
    if t.startswith('Сначала'): return '<span class="chip test">🧠 IQ-тест</span>'
    if t.startswith('Без'): return '<span class="chip none">без квиза</span>'
    return '<span class="chip quiz">📝 опрос</span>'

def row(a):
    q, entry, renew, ads, take = SHORT[a['id']]
    u = a['links'][0][0]
    return (f'<tr><td><a href="#{a["id"]}" class="nm">{esc(a["name"])}</a></td>'
            f'<td{tip(a["type"])}>{typechip(a["type"])}</td>'
            f'<td class="r num"{tip(a["q"])}>{esc(q)}</td>'
            f'<td class="r num"{tip(a["price"])}>{esc(entry)}</td>'
            f'<td class="num"{tip(a["price"])}>{esc(renew)}</td>'
            f'<td class="num"{tip(a["ads"] + " — спенд за 28 дней, FB-выгрузки")}>{esc(ads)}</td>'
            f'<td{tip("Прошли: " + a["walked"])}><a href="{esc(u)}" target="_blank" rel="noopener">открыть ↗</a></td></tr>')

def card(a):
    q, entry, renew, ads, take = SHORT[a['id']]
    shots = ''.join(f'<button class="shot" type="button" data-cap="{esc(c)}"><img src="{img(p)}" alt="{esc(c)}" loading="lazy"><span>{esc(c)}</span></button>' for p, c in a['screens'])
    lk = ' · '.join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)} ↗</a>' for u, t in a['links'])
    return (f'<section class="app" id="{a["id"]}"><div class="ah"><h3>{esc(a["name"])}</h3>{typechip(a["type"])}'
            f'<span class="pill"{tip(a["q"])}>❓ {esc(q)}</span><span class="pill"{tip(a["price"])}>💵 {esc(entry)}</span>'
            f'<span class="info"{tip(a["about"] + " Прошли: " + a["walked"] + ".")}>ⓘ подробнее</span></div>'
            f'<p class="take">👉 {esc(take)}</p><div class="shots">{shots}</div><p class="lk small">{lk}</p></section>')

KPI = [('🔍', '12', 'воронок прошли', 'Пройдены 02–03.11.2026 с мобильного браузера из США, без оплаты. Почту вводили, где её просят до пейволла.'),
       ('🧠', '5', 'начинают с IQ-теста', 'CognitiveGrowth, MyIQ, Intellio, Selfery, Testora: 25–45 заданий с таймером → «считаем результат» → пейволл с закрытым отчётом.'),
       ('📝', '6', 'начинают с опроса', 'memoryOS, Impulse, Nibble, Headway, Inflow, MyGrowth: 19–36 вопросов о целях и болях → «персональный план» → e-mail → пейволл.'),
       ('💵', '$15–20', 'вход за 4 недели', 'Общая сетка ниши: 4 недели $15,19–19,99, продление ~$39–50. У Nibble первые платежи как у memoryOS, у Headway — как у Impulse.'),
       ('🏆', '1,4', 'лучший ROAS — Selfery', 'Selfery: IQ-тест с заданиями на память, ROAS 1,40–1,44 (FB, август). Самый большой спенд — MyIQ, $5,5M за 28 дней.')]
kpis = ''.join(f'<div class="kpi"{tip(t)}><span class="ki">{i}</span><span class="kv">{v}</span><span class="kl">{l}</span></div>' for i, v, l, t in KPI)

JS = """
const d=document.getElementById('zoom'),zi=document.getElementById('zoom-img'),zc=document.getElementById('zoom-cap');
document.querySelectorAll('.shot').forEach(b=>b.addEventListener('click',()=>{zi.src=b.querySelector('img').src;zi.alt=b.dataset.cap;zc.textContent=b.dataset.cap;d.showModal();}));
d.addEventListener('click',e=>{if(e.target===d)d.close();});
(function(){
  const tip=document.createElement('div');tip.id='tip';tip.setAttribute('role','tooltip');tip.hidden=true;document.body.appendChild(tip);
  let cur=null;
  function place(x,y){const w=tip.offsetWidth,h=tip.offsetHeight,vw=innerWidth,vh=innerHeight;let nx=Math.min(x+14,vw-w-8),ny=y+16;if(ny+h>vh-8)ny=y-h-12;tip.style.left=Math.max(8,nx)+'px';tip.style.top=Math.max(8,ny)+'px';}
  function show(el,x,y){cur=el;tip.textContent=el.dataset.tip;tip.hidden=false;place(x,y);}
  function hide(){cur=null;tip.hidden=true;}
  document.addEventListener('mouseover',e=>{const el=e.target.closest('[data-tip]');if(el)show(el,e.clientX,e.clientY);else if(cur)hide();});
  document.addEventListener('mousemove',e=>{if(cur)place(e.clientX,e.clientY);});
  document.addEventListener('focusin',e=>{const el=e.target.closest('[data-tip]');if(el){const r=el.getBoundingClientRect();show(el,r.left,r.bottom);}});
  document.addEventListener('focusout',hide);
  document.addEventListener('click',e=>{const el=e.target.closest('[data-tip]');if(el&&!e.target.closest('a,button')){if(cur===el)hide();else{const r=el.getBoundingClientRect();show(el,r.left,r.bottom);}}else if(!el)hide();});
  addEventListener('scroll',hide,{passive:true});
})();
"""

CSS = open(os.path.join(S, 'analogs-page.css'), encoding='utf-8').read()
rows = ''.join(row(a) for a in APPS)
cards = ''.join(card(a) for a in APPS)
page = f'''<title>Воронки аналогов memoryOS</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header class="hero">
<p class="eyebrow">memoryOS-клон · конкуренты · 03.11.2026</p>
<h1>🧠 Воронки аналогов memoryOS</h1>
<p class="lede">Наведите на цифру или ячейку — появятся подробности. Нажмите на скрин — откроется крупно.</p>
<div class="kpis">{kpis}</div>
</header>
<section class="sum">
<h2>Что берём в клон</h2>
<ol>
<li><b>База</b> — квиз memoryOS как есть.</li>
<li><b>Вариант B</b> — мини-тест памяти → «индекс памяти» по шкале → закрытый отчёт на пейволле.</li>
<li><b>Цена</b> — по сетке ниши: $15–20 за 4 недели.</li>
</ol>
</section>
<section>
<h2>Все воронки</h2>
<div class="tw"><table class="lite">
<thead><tr><th>Приложение</th><th>Тип</th><th class="r">Вопросов</th><th class="r">Вход</th><th>Продление</th><th>Реклама, 28 дн.</th><th>Воронка</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="foot">Не открывается Intellio, Selfery, MyGrowth или Testora — попробуйте через VPN США без блокировщика рекламы.</p>
</section>
<section class="apps">
<h2>Скрины по каждому</h2>
{cards}
</section>
<footer class="foot"><p>Источники: прохождение воронок 02–03.11.2026, FB-выгрузки 18.05–10.10.2026, App Store. Полный отчёт — memoryos/memoryos-analogs-v2-2026-11-03.html.</p></footer>
</main>
<dialog id="zoom" aria-label="Экран крупно"><form method="dialog"><button class="close" type="submit" aria-label="Закрыть">×</button></form><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>{JS}</script>'''
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, os.path.getsize(OUT))

# отдельный файл с полной HTML-обёрткой (для вложения и пересылки)
full = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">' + page.replace('</style>', '</style></head><body>', 1) + '</body></html>'
open(os.path.join(S, 'memoryos-analogs-funnels-2026-11-03.html'), 'w', encoding='utf-8').write(full)
