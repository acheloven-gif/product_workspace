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
  dict(id='nofunnel', name='Elevate и Mindvalley', url='themindcompany.com · mindvalley.com/superbrain', scheme='Без квиза', role='Не копируем воронку',
       spend='в наших FB-выгрузках нет', price='Elevate ~$40/год в приложении; Mindvalley — членство',
       mail='—', walked='02.11',
       screens=[('analogs/elevate-landing.jpg', 'Elevate: лендинг → стор'), ('analogs/mv-landing.jpg', 'Mindvalley: курс Jim Kwik')],
       take=['В продукт: ежедневная тренировка и профиль сильных сторон (Elevate).']),
]

def esc(s): return html.escape(s)

def section(f):
    shots = ''.join(f'<button class="shot" type="button" data-cap="{esc(c)}"><img src="{img(p)}" alt="{esc(c)}" loading="lazy"><span>{esc(c)}</span></button>' for p, c in f['screens'])
    take = ''.join(f'<li>{esc(t)}</li>' for t in f['take'])
    return f'''<section class="funnel" id="{f['id']}">
<div class="fhead"><div class="ftitle"><h2>{esc(f['name'])}</h2><span class="url">{esc(f['url'])}</span></div>
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
<p class="lede">Экраны пяти воронок, пройденных 02.11 с мобильного браузера в США: до пейволла, без оплаты (в memoryOS и Impulse — с почтой pn@gox-media.com). Нажмите на экран, чтобы открыть его крупно. Цифры рекламы — из наших FB-выгрузок (срез 10.10.2026).</p>
<div class="schemes">
<div class="scheme-card"><b>Опрос о проблеме</b><span>memoryOS, Impulse</span><p>25–30 вопросов о целях и болях → «персональный план» → e-mail → пейволл.</p></div>
<div class="scheme-card"><b>Сначала тест</b><span>CognitiveGrowth, MyIQ</span><p>25–40 заданий с таймером → «считаем результат» → пейволл с закрытым результатом, триал $0,99. Так работают лидеры по спенду.</p></div>
</div>
<nav class="nav" aria-label="Конкуренты">{nav}</nav>
</header>
{''.join(section(f) for f in FUNNELS)}
<footer class="foot"><p>Источники: прохождение воронок 02.11.2026 и 20–22.10.2026 (memoryOS), FB-выгрузки #5–#9 (18.05–10.10.2026), лендинги Impulse и Elevate. Внутренних данных конкурентов нет. Полный отчёт с выводами — memoryos/memoryos-analogs-2026-11-02.html в репозитории.</p></footer>
</main>
<dialog id="zoom" aria-label="Экран крупно"><form method="dialog"><button class="close" type="submit" aria-label="Закрыть">×</button></form><img id="zoom-img" alt=""><p id="zoom-cap"></p></dialog>
<script>
const d=document.getElementById('zoom'),zi=document.getElementById('zoom-img'),zc=document.getElementById('zoom-cap');
document.querySelectorAll('.shot').forEach(b=>b.addEventListener('click',()=>{{zi.src=b.querySelector('img').src;zi.alt=b.dataset.cap;zc.textContent=b.dataset.cap;d.showModal();}}));
d.addEventListener('click',e=>{{if(e.target===d)d.close();}});
</script>'''
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, os.path.getsize(OUT))
