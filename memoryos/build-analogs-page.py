# Страница «Воронки аналогов memoryOS» (Artifact): сначала сводная таблица, потом по каждому приложению 2–3 скрина.
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

def links(a): return '<br>'.join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a>' for u, t in a['links'])
def chip(t): return f'<span class="chip {"test" if t.startswith("Сначала") else ("none" if t.startswith("Без") else "quiz")}">{esc(t)}</span>'

rows = ''.join(f'''<tr><td><a href="#{a['id']}"><b>{esc(a['name'])}</b></a></td><td>{chip(a['type'])}</td><td class="num">{esc(a['q'])}</td>
<td>{esc(a['mail'])}</td><td class="num">{esc(a['price'])}</td><td class="num">{esc(a['ads'])}</td><td class="lnk">{links(a)}</td><td>{esc(a['walked'])}</td></tr>''' for a in APPS)

def section(a):
    shots = ''.join(f'<button class="shot" type="button" data-cap="{esc(c)}"><img src="{img(p)}" alt="{esc(c)}" loading="lazy"><span>{esc(c)}</span></button>' for p, c in a['screens'])
    return f'''<section class="funnel" id="{a['id']}">
<div class="fhead"><h2>{esc(a['name'])}</h2>{chip(a['type'])}</div>
<p class="about">{esc(a['about'])}</p>
<p class="meta2"><b>Вопросов:</b> {esc(a['q'])} · <b>Цена:</b> {esc(a['price'])} · <span class="lnk">{links(a)}</span></p>
<div class="shots">{shots}</div></section>'''

CSS = open(os.path.join(S, 'analogs-page.css'), encoding='utf-8').read()
page = f'''<title>Воронки аналогов memoryOS</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header class="hero">
<p class="eyebrow">memoryOS-клон · разбор конкурентов · версия 2 · 03.11.2026</p>
<h1>Воронки аналогов memoryOS</h1>
<p class="lede">12 воронок, пройденных 02–03.11 с мобильного браузера из США, без оплаты (почту вводили, где её просят до пейволла). Нажмите на скрин, чтобы открыть крупно. Реклама — спенд за 28 дней из наших FB-выгрузок (срез 10.10, если не указано иное).</p>
</header>

<section class="card-sum">
<h2>Главное</h2>
<ul>
<li><b>Два типа воронок.</b> «Сначала IQ-тест» (CognitiveGrowth, MyIQ, Intellio, Selfery, Testora): 25–45 заданий с таймером → «считаем результат» → пейволл с закрытым отчётом. «Опрос о себе» (memoryOS, Impulse, Nibble, Headway, Inflow, MyGrowth): 18–36 вопросов о целях и болях → «персональный план» → e-mail → пейволл.</li>
<li><b>Самые большие деньги — у тестов:</b> MyIQ $5,5M за 28 дней, лучший ROAS — Selfery (1,4), у него задания на память внутри теста.</li>
<li><b>Цены в нише общие:</b> 4 недели $15,19–19,99 → продление ~$39–50. У Nibble первые платежи как у memoryOS, у Headway — как у Impulse.</li>
<li><b>В мнемонике крупный игрок один — memoryOS.</b> Для клона: база — копия квиза memoryOS; вариант B — мини-тест памяти → «индекс памяти» по шкале (как у Inflow) → закрытый отчёт (как у Intellio, Selfery).</li>
</ul>
</section>

<section>
<h2>Сводная таблица</h2>
<div class="tw"><table>
<thead><tr><th>Приложение</th><th>Тип воронки</th><th>Вопросов до e-mail</th><th>E-mail до пейволла</th><th>Цена: первый платёж → продление</th><th>Реклама FB, 28 дн.</th><th>Ссылка</th><th>Докуда прошли</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="foot">Если ссылка не открывается: у нас из США все 12 открылись 03.11. Часть воронок (Intellio, Selfery, MyGrowth, Testora) может не открываться из других стран или с блокировщиком рекламы — попробуйте через VPN США.</p>
</section>

{''.join(section(a) for a in APPS)}

<footer class="foot"><p>Источники: прохождение воронок 02–03.11.2026 (memoryOS — также 20–22.10), FB-выгрузки #5–#9 (18.05–10.10.2026), App Store. Полный отчёт с выводами — memoryos/memoryos-analogs-v2-2026-11-03.html в репозитории.</p></footer>
</main>
<dialog id="zoom" aria-label="Экран крупно"><form method="dialog"><button class="close" type="submit" aria-label="Закрыть">×</button></form><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>
const d=document.getElementById('zoom'),zi=document.getElementById('zoom-img'),zc=document.getElementById('zoom-cap');
document.querySelectorAll('.shot').forEach(b=>b.addEventListener('click',()=>{{zi.src=b.querySelector('img').src;zi.alt=b.dataset.cap;zc.textContent=b.dataset.cap;d.showModal();}}));
d.addEventListener('click',e=>{{if(e.target===d)d.close();}});
</script>'''
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, os.path.getsize(OUT))
