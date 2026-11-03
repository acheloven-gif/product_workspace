# Страница-галерея воронок аналогов memoryOS (для Artifact):
#   python3 memoryos/build-analogs-page.py → memoryos/memoryos-analogs-page.html
# Скрины — references/memoryos/analogs/ и references/memoryos/funnel/ (memoryOS, 20–22.10).
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

FUNNELS = [
  dict(id='memoryos', name='memoryOS', url='start.memoryos.com/new-h', scheme='Опрос о проблеме', role='Копируем — основа клона',
       spend='$347K веб + $163K стор за 28 дн. (10.10) · CPA $65 · ROAS 0,40 · США',
       price='4 нед $15,19 → $49,99 · 12 нед $36,99 → $99,99 · 24 нед $59,99 → $119,99',
       mail='e-mail и имя до пейволла', walked='02.11, до пейволла (с почтой Наташи)',
       screens=[('funnel/01-intro.jpg', 'Интро: «забываете имена и детали?»'), ('funnel/02-age.jpg', 'Возраст: «сравним с вашей группой»'),
                ('funnel/05-frustrations.jpg', 'Что забываете чаще всего'), ('analogs/memoryos-now-11.jpg', 'Страх деменции у себя и близких'),
                ('funnel/09-mind-palace-q.jpg', 'Mind Palace «как у Шерлока»'), ('analogs/memoryos-now-19.jpg', 'Подбадривание с цифрами'),
                ('funnel/10-daily-commitment.jpg', 'Минут в день'), ('funnel/11-plan-loading.jpg', 'Сборка плана + отзывы'),
                ('funnel/12-email.jpg', 'E-mail'), ('funnel/14-plan-ready.jpg', 'План готов: «+70% за 4 недели»'),
                ('analogs/memoryos-paywall-1102-1.jpg', 'Пейволл 02.11: таймер, «сейчас → цель»'), ('funnel/15-paywall-02.jpg', 'Пейволл: 3 пакета'), ('funnel/15-paywall-03.jpg', 'Пейволл: что входит')],
       take=['Под кнопкой новый текст: «отмена в один шаг в настройках, без звонка и письма; напомним перед каждым списанием» — взять себе.', 'Весь квиз — наша основа (свои тексты, без «чемпиона мира» и чужих цифр).', 'Вопрос о возрасте «сравним с вашей группой» — зацепка для индекса памяти.']),
  dict(id='cognitivegrowth', name='CognitiveGrowth', url='quiz.cognitivegrowth.net/brain-iq', scheme='Сначала тест', role='Берём механику для варианта B',
       spend='$179K за 28 дн. (10.10) · CPA $42 · ROAS 0,12 · США, GB, AU',
       price='$0,99 за 3 дня → $12,99 в неделю · «скидка 93%» с таймером 10:00',
       mail='e-mail не просят — сразу пейволл', walked='02.11',
       screens=[('analogs/cognitivegrowth-00.jpg', 'Старт: одна кнопка'), ('analogs/cognitivegrowth-01.jpg', 'Задание-матрица (25 штук)'),
                ('analogs/cognitivegrowth-26.jpg', 'Подтвердить ответы'), ('analogs/cognitivegrowth-27.jpg', 'Расчёт по 5 измерениям, в т.ч. Memory'),
                ('analogs/cognitivegrowth-37.jpg', 'Пейволл: результат закрыт'), ('analogs/cognitivegrowth-paywall-1.jpg', 'Условия, гарантия, бонусы'),
                ('analogs/cognitivegrowth-paywall-2.jpg', 'Рейтинг IQ знаменитостей')],
       take=['Тест в воронке → результат закрыт до оплаты.', 'Экран «считаем результат» по измерениям.', 'Не берём: рейтинг знаменитостей и «скидку 93%».']),
  dict(id='impulse', name='Impulse', url='iq.mental-impulse.com', scheme='Опрос о цели', role='Берём вопросы во время загрузки плана',
       spend='в мае $1,5–1,8M за 28 дн. (ROAS 1,05–1,22), в срезе 10.10 нет',
       price='4 нед $19,99 → $39,98 · 12 нед $39,99 → $79,98 · 24 нед $59,99 → $119,98 · «скидка 50%» с таймером 10:00',
       mail='e-mail, галочка согласия и имя до пейволла', walked='02.11, до пейволла (с почтой Наташи)',
       screens=[('analogs/impulse-00.jpg', 'Лендинг: «100M+ downloads»'), ('analogs/impulse-01.jpg', 'Пол на первом экране'),
                ('analogs/impulse-02.jpg', 'Возраст'), ('analogs/impulse-04.jpg', 'Навыки: Memory первым'), ('analogs/impulse-12.jpg', 'Шкала согласия'),
                ('analogs/impulse-22.jpg', '«Знали, что игры развивают?»'), ('analogs/impulse-23.jpg', 'Минут в день с уровнями'),
                ('analogs/impulse-24.jpg', 'Вопрос посреди загрузки плана'), ('analogs/impulse-mail-31.jpg', 'E-mail + согласие'), ('analogs/impulse-paywall-1.jpg', 'Пейволл: 3 пакета, 4 недели по умолчанию'), ('analogs/impulse-paywall-2.jpg', 'Пейволл: что входит, вопросы'), ('analogs/impulse-paywall-3.jpg', 'Пейволл: отзывы')],
       take=['Пейволл почти как у memoryOS: 3 пакета 4/12/24 недели с «-50%», но по умолчанию выбран самый короткий.', 'Всплывающие вопросы «Да/Нет» на экране сборки плана.', 'Подписи-уровни у цели «минут в день».']),
  dict(id='myiq', name='MyIQ', url='myiq.com/start', scheme='Сначала тест', role='Берём задания на память внутри теста',
       spend='$5,48M за 28 дн. (10.10) — крупнейший в вертикали; оплаты в пиксель не передаются',
       price='не видели: экран расчёта закрыт защитой от ботов',
       mail='—', walked='02.11',
       screens=[('analogs/myiq-00.jpg', 'Старт: 40 вопросов'), ('analogs/myiq-04.jpg', '«Запомните слово — спросим в конце»'),
                ('analogs/myiq-05.jpg', 'Задача с таймером'), ('analogs/myiq-10.jpg', '«Запомните цифры — исчезнут через 2 с»')],
       take=['3–5 заданий «запомни → вспомни через пару экранов» прямо в нашем квизе.']),
  dict(id='nibble', name='Nibble', url='nibble-app.com/funnels/general-en', scheme='Опрос о проблеме', role='Берём блок «скроллинг → фокус»',
       spend='в наших FB-выгрузках нет', price='неделя $6,93 → $38,95 · 4 нед $15,19 → $38,95 · 12 нед $36,99 → $94,85 · промокод «−61%», таймер',
       mail='имя и e-mail до пейволла', walked='03.11, до пейволла (с почтой Наташи)',
       links=[('https://nibble-app.com/funnels/general-en/quiz/general-en','nibble-app.com/funnels/general-en')],
       screens=[('analogs/nibble-01.jpg', 'Старт: «замените скроллинг»'), ('analogs/nibble-08.jpg', 'Навыки: Memory, Focus…'), ('analogs/nibble-25.jpg', 'Довольны ли концентрацией'),
                ('analogs/nibble-35.jpg', 'Сколько скроллите'), ('analogs/nibble-42.jpg', 'Загрузка + отзывы'), ('analogs/nibble-46.jpg', '«Сейчас → цель»: фокус и скроллинг'),
                ('analogs/nibble-paywall-1.jpg', 'Пейволл: промокод, 3 плана'), ('analogs/nibble-paywall-2.jpg', 'Пейволл: что внутри')],
       take=['Первые платежи как у memoryOS ($15,19 / $36,99) — одна ценовая сетка.', 'Вопросы «сколько скроллите → до скольки сократить» и «сейчас → цель» с двумя шкалами.', 'Промокод на пейволле вместо абстрактной скидки.']),
  dict(id='headway', name='Headway', url='makeheadway.com/onboarding', scheme='Опрос о проблеме', role='Сверяем цены',
       spend='в наших FB-выгрузках нет', price='4 нед $19,99 → $39,98 · 12 нед $39,99 → $79,98 · 24 нед $59,99 → $119,98 · «−50%», таймер',
       mail='e-mail до пейволла', walked='03.11, до пейволла (с почтой Наташи)',
       links=[('https://makeheadway.com/onboarding/start','makeheadway.com/onboarding/start')],
       screens=[('analogs/headway-00.jpg', 'Старт: возраст сразу'), ('analogs/headway-02.jpg', 'Сферы роста'), ('analogs/headway-06.jpg', 'Шкала самооценки'),
                ('analogs/headway-31.jpg', 'Минут в день'), ('analogs/headway-32.jpg', 'Сборка опыта'), ('analogs/headway-38.jpg', 'План готов'), ('analogs/headway-paywall-1.jpg', 'Пейволл')],
       take=['Цены один в один как у Impulse — ориентир для Димы.']),
  dict(id='inflow', name='Inflow', url='getinflow.io → join.getinflow.io/inflow-quiz', scheme='Опрос-тест', role='Берём шкалу-результат',
       spend='в наших FB-выгрузках нет', price='пейволл не видели · App Store: $47,99/мес, $199,99/год',
       mail='e-mail до результата', walked='03.11, до выбора направлений (с почтой Наташи)',
       links=[('https://www.getinflow.io/','getinflow.io'),('https://www.join.getinflow.io/inflow-quiz/fuba-v2','join.getinflow.io/inflow-quiz/fuba-v2')],
       screens=[('analogs/inflow-01.jpg', 'Старт: «правда о вашем СДВГ»'), ('analogs/inflow-11.jpg', 'Маскот Quinn'), ('analogs/inflow-12.jpg', 'Вопрос о прокрастинации'),
                ('analogs/inflow-35.jpg', 'Объясняющий вопрос'), ('analogs/inflow-47.jpg', '«У многих нет диагноза»'), ('analogs/inflow-59.jpg', 'E-mail'),
                ('analogs/inflow-63.jpg', 'Результат: шкала Low…Very High'), ('analogs/inflow-73.jpg', 'Выбор 3 направлений')],
       take=['Результат по шкале перед пейволлом → наш «индекс памяти».', 'Маскот-гид и вставки с поддержкой в квизе.']),
  dict(id='intellio', name='Intellio', url='intellio.club/start', scheme='Сначала тест', role='Берём закрытый отчёт',
       spend='$218K за 28 дн. (10.10) · CPA $127 · ROAS 0,68 · США, AU, GB', price='неделя $6,99 → $39,99 · 4 нед $19,99 → $39,99 · 12 нед $39,99 → $79,99 · «−50%», таймер',
       mail='e-mail до пейволла', walked='03.11, до пейволла (с почтой Наташи)',
       links=[('https://intellio.club/start?cohort=intl_2&lang=en','intellio.club/start')],
       screens=[('analogs/intellio-02.jpg', '«Тест: логика, паттерны, память»'), ('analogs/intellio-03.jpg', 'Задание'), ('analogs/intellio-31.jpg', 'Расчёт'),
                ('analogs/intellio-40.jpg', 'E-mail'), ('analogs/intellio-paywall-1.jpg', 'Пейволл: отчёт закрыт'), ('analogs/intellio-paywall-2.jpg', 'Пейволл: планы')],
       take=['Отчёт на пейволле с частью текста, остальное — после оплаты.']),
  dict(id='selfery', name='Selfery', url='quiz.selferyapp.com', scheme='Сначала тест', role='Берём задания на память в тесте',
       spend='$62–72K за 28 дн. (август) · CPA $69–73 · ROAS 1,40–1,44 · США', price='7 дней $4,99 → $49,99/мес · 1 мес $15,19 → $49,99/мес · 3 мес $25,99 → $69,99 · гарантия 30 дней',
       mail='e-mail и имя до пейволла', walked='03.11, до пейволла (с почтой Наташи)',
       links=[('https://quiz.selferyapp.com/','quiz.selferyapp.com')],
       screens=[('analogs/selfery-00.jpg', 'Старт'), ('analogs/selfery-18.jpg', '«Запомните 8935»'), ('analogs/selfery-19.jpg', '«Какая 3-я цифра?»'),
                ('analogs/selfery-41.jpg', '«Warning!»'), ('analogs/selfery-53.jpg', 'Отчёт-тизер: Logic, Memory, Speed'), ('analogs/selfery-paywall-1.jpg', 'Пейволл')],
       take=['Самый высокий ROAS в вертикали (1,4) — у теста с заданиями на память.', 'Отчёт-тизер в виде PDF с навыками, включая Memory.']),
  dict(id='mygrowth', name='MyGrowth', url='quiz.mygrowth.one', scheme='Опрос о проблеме', role='Только для сравнения',
       spend='$522K за 28 дн. (10.10, app.mygrowth.one) · ROAS 0,72 · CPA $77', price='не видели: поле e-mail не приняло ввод',
       mail='e-mail до пейволла', walked='03.11, до e-mail',
       links=[('https://quiz.mygrowth.one/','quiz.mygrowth.one'),('https://app.mygrowth.one/?cohort=anatomy-bau','app.mygrowth.one (основная в FB)')],
       screens=[('analogs/mygrowth-00.jpg', 'Старт'), ('analogs/mygrowth-13.jpg', 'Вопрос-эрудиция'), ('analogs/mygrowth-39.jpg', 'Сборка плана'),
                ('analogs/mygrowth-41.jpg', 'Курс: Memory среди навыков'), ('analogs/mygrowth-42.jpg', 'E-mail')],
       take=['Та же компания, что Testora (Extramile Ltd).']),
  dict(id='testora', name='Testora', url='funnel.testora.space', scheme='Сначала тест', role='Только для сравнения',
       spend='$572K + $323K за 28 дн. (10.10) · CPA $65–69 · ROAS 0,13–0,15', price='не видели: тест на 45 заданий, гонцу не хватило шагов',
       mail='—', walked='03.11, 18 заданий из 45',
       links=[('https://funnel.testora.space/start-1?cohort=testora_fl_iq_tp1','funnel.testora.space/start-1')],
       screens=[('analogs/testora-00.jpg', 'Старт'), ('analogs/testora-06.jpg', 'Задание с таймером')],
       take=['С 04.2026 ведёт в собственное приложение в сторе.']),
  dict(id='nofunnel', name='Elevate и Mindvalley', url='themindcompany.com · mindvalley.com/superbrain', scheme='Без квиза', role='Не копируем воронку',
       spend='в наших FB-выгрузках нет', price='Elevate ~$40/год в приложении; Mindvalley — членство',
       mail='—', walked='02.11',
       screens=[('analogs/elevate-landing.jpg', 'Elevate: лендинг → стор'), ('analogs/mv-landing.jpg', 'Mindvalley: курс Jim Kwik')],
       take=['В продукт: ежедневная тренировка и профиль сильных сторон (Elevate).']),
]

def esc(s): return html.escape(s)

LINKS = {'memoryos': [('https://start.memoryos.com/new-h', 'start.memoryos.com/new-h')], 'cognitivegrowth': [('https://quiz.cognitivegrowth.net/brain-iq/', 'quiz.cognitivegrowth.net/brain-iq'), ('https://quiz.cognitivegrowth.net/brain-iq-ja', '…/brain-iq-ja (Япония)')], 'impulse': [('https://iq.mental-impulse.com/', 'iq.mental-impulse.com'), ('https://archetype.mental-impulse.com/', 'archetype.mental-impulse.com')], 'myiq': [('https://myiq.com/start', 'myiq.com/start')], 'nofunnel': [('https://themindcompany.com/apps/elevate', 'Elevate'), ('https://www.mindvalley.com/superbrain', 'Mindvalley Superbrain')]}
def links_html(f):
    ls = f.get('links') or LINKS.get(f['id'], [])
    return ' · '.join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(t)}</a>' for u, t in ls) if ls else esc(f['url'])

def section(f):
    shots = ''.join(f'<button class="shot" type="button" data-cap="{esc(c)}"><img src="{img(p)}" alt="{esc(c)}" loading="lazy"><span>{esc(c)}</span></button>' for p, c in f['screens'])
    take = ''.join(f'<li>{esc(t)}</li>' for t in f['take'])
    return f'''<section class="funnel" id="{f['id']}">
<div class="fhead"><div class="ftitle"><h2>{esc(f['name'])}</h2><span class="url">{links_html(f)}</span></div>
<div class="chips"><span class="chip scheme">{esc(f['scheme'])}</span><span class="chip role">{esc(f['role'])}</span></div></div>
<dl class="facts"><div><dt>Реклама FB</dt><dd>{esc(f['spend'])}</dd></div><div><dt>Цена</dt><dd>{esc(f['price'])}</dd></div>
<div><dt>Почта</dt><dd>{esc(f['mail'])}</dd></div><div><dt>Пройдено</dt><dd>{esc(f['walked'])}</dd></div></dl>
<div class="strip" tabindex="0" aria-label="Экраны воронки {esc(f['name'])}">{shots}</div>
<div class="take"><b>Что берём</b><ul>{take}</ul></div></section>'''

nav = ''.join(f'<a href="#{f["id"]}">{esc(f["name"])}</a>' for f in FUNNELS)
CSS = open(os.path.join(S, 'analogs-page.css'), encoding='utf-8').read()
page = f'''<title>Воронки аналогов memoryOS</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Onest:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>{CSS}</style>
<main class="wrap">
<header class="hero">
<p class="eyebrow">memoryOS-клон · разбор конкурентов · срез 02.11.2026</p>
<h1>Как аналоги memoryOS ведут человека от рекламы до оплаты</h1>
<p class="lede">Версия 2 от 03.11: экраны 12 воронок, пройденных 02–03.11 с мобильного браузера в США, без оплаты (почту вводили там, где её просят до пейволла). Нажмите на экран, чтобы открыть его крупно. Цифры рекламы — из наших FB-выгрузок (срез 10.10.2026).</p>
<div class="schemes">
<div class="scheme-card"><b>Опрос о проблеме</b><span>memoryOS, Impulse, Nibble, Headway, Inflow, MyGrowth</span><p>25–30 вопросов о целях и болях → «персональный план» → e-mail → пейволл.</p></div>
<div class="scheme-card"><b>Сначала тест</b><span>CognitiveGrowth, MyIQ, Intellio, Selfery, Testora</span><p>25–40 заданий с таймером → «считаем результат» → пейволл с закрытым результатом, триал $0,99. Так работают лидеры по спенду.</p></div>
</div>
<div class="scheme-card news"><b>Что нового в версии 2</b><ul>
<li>Общая ценовая сетка ниши: 4 недели $15,19–19,99 → ~$39–50. У Nibble первые платежи как у memoryOS, у Headway цены как у Impulse.</li>
<li>Тестовые воронки (Intellio, Selfery, Inflow, CognitiveGrowth) показывают «результат» и закрывают его до оплаты. Selfery с заданиями на память — самый высокий ROAS вертикали (1,4).</li>
<li>В мнемонике масштабный игрок по-прежнему один — memoryOS. Быстрее всех в 2026 растут «прокачай IQ» (IQ Evolve) и концентрация (Focustown).</li>
</ul></div>
<nav class="nav" aria-label="Конкуренты">{nav}</nav>
</header>
{''.join(section(f) for f in FUNNELS)}
<footer class="foot"><p>Источники: прохождение воронок 02–03.11.2026 и 20–22.10.2026 (memoryOS), FB-выгрузки #5–#9 (18.05–10.10.2026), лендинги Impulse и Elevate. Внутренних данных конкурентов нет. Полный отчёт с выводами — memoryos/memoryos-analogs-v2-2026-11-03.html в репозитории (версия 1 — memoryos-analogs-2026-11-02.html).</p></footer>
</main>
<dialog id="zoom" aria-label="Экран крупно"><form method="dialog"><button class="close" type="submit" aria-label="Закрыть">×</button></form><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>
const d=document.getElementById('zoom'),zi=document.getElementById('zoom-img'),zc=document.getElementById('zoom-cap');
document.querySelectorAll('.shot').forEach(b=>b.addEventListener('click',()=>{{zi.src=b.querySelector('img').src;zi.alt=b.dataset.cap;zc.textContent=b.dataset.cap;d.showModal();}}));
d.addEventListener('click',e=>{{if(e.target===d)d.close();}});
</script>'''
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, os.path.getsize(OUT))
