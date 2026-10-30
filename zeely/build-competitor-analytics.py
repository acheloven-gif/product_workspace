import base64, os, sys
S = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(S, 'img2')
OUT = sys.argv[1]

def img(name, cap, w=None):
    b = base64.b64encode(open(os.path.join(IMG, name + '.jpg'), 'rb').read()).decode()
    st = f' style="max-width:{w}px"' if w else ''
    return f'<figure><img src="data:image/jpeg;base64,{b}" alt="{cap}"{st}><figcaption>{cap}</figcaption></figure>'

def gallery(items):
    return '<div class="gallery">' + ''.join(img(n, c) for n, c in items) + '</div>'

def bar(label, a, b, total_a, total_b):
    pa = a / total_a * 100; pb = b / total_b * 100
    return (f'<tr><td>{label}</td>'
            f'<td><div class="bar"><span style="width:{pa:.0f}%"></span></div><span class="num">{a} · {pa:.0f}%</span></td>'
            f'<td><div class="bar b2"><span style="width:{pb:.0f}%"></span></div><span class="num">{b} · {pb:.0f}%</span></td></tr>')

def tag(kind):
    return {'d': '<span class="tag ok">Видно в данных</span>', 'p': '<span class="tag warn">Предположение</span>', 'n': '<span class="tag crit">Не знаем</span>'}[kind]

CSS = """
:root{--bg:#f5f7f8;--surface:#fff;--ink:#15202a;--muted:#56636f;--line:#dbe2e7;--soft:#eef3f5;--accent:#0d5f6f;--accent-soft:#e3f1f3;
--crit:#b42318;--crit-soft:#fdecea;--warn:#a15c07;--warn-soft:#fdf2e1;--ok:#0b7a4b;--ok-soft:#e5f5ec;--bar:#2a78d6;--bar2:#eb6834;
--f:"Golos Text","Segoe UI",Roboto,Arial,sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0e1418;--surface:#151d22;--ink:#e5ecef;--muted:#9aa8b2;--line:#29353d;--soft:#1b252b;
--accent:#5cc0d2;--accent-soft:#16323a;--crit:#ff8a7d;--crit-soft:#3a1d1a;--warn:#f3b45a;--warn-soft:#352a17;--ok:#56d39a;--ok-soft:#163126;--bar:#3987e5;--bar2:#d95926;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0e1418;--surface:#151d22;--ink:#e5ecef;--muted:#9aa8b2;--line:#29353d;--soft:#1b252b;--accent:#5cc0d2;--accent-soft:#16323a;
--crit:#ff8a7d;--crit-soft:#3a1d1a;--warn:#f3b45a;--warn-soft:#352a17;--ok:#56d39a;--ok-soft:#163126;--bar:#3987e5;--bar2:#d95926;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--f);font-size:16px;line-height:1.55}
.wrap{max-width:960px;margin:0 auto;padding:40px 16px 64px;display:flex;flex-direction:column;gap:44px}
h1{font-size:2rem;margin:0;line-height:1.2}h2{font-size:1.45rem;margin:0}h3{font-size:1.1rem;margin:8px 0 0}
p{margin:0;max-width:76ch}
.eyebrow{font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);font-weight:600}
.meta{color:var(--muted);font-size:.95rem}
section{display:flex;flex-direction:column;gap:14px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:18px 20px;display:flex;flex-direction:column;gap:10px}
.summary ol{margin:0;padding-left:22px;display:flex;flex-direction:column;gap:8px}
table{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:.92rem}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
.tw{overflow-x:auto}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;font-size:.86rem}
.muted{color:var(--muted)}.small{font-size:.86rem}
.tag{display:inline-block;font-size:.72rem;font-weight:600;border-radius:999px;padding:1px 8px;margin-left:4px;white-space:nowrap}
.tag.ok{background:var(--ok-soft);color:var(--ok)}.tag.warn{background:var(--warn-soft);color:var(--warn)}.tag.crit{background:var(--crit-soft);color:var(--crit)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
figure{margin:0;display:flex;flex-direction:column;gap:6px}
figure img{width:100%;border:1px solid var(--line);border-radius:8px;background:#fff}
figcaption{font-size:.8rem;color:var(--muted);line-height:1.35}
.wide figure img{max-width:100%}
.bar{display:inline-block;width:120px;height:8px;background:var(--soft);border-radius:4px;vertical-align:middle;margin-right:8px;overflow:hidden}
.bar span{display:block;height:100%;background:var(--bar)}.bar.b2 span{background:var(--bar2)}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:stretch}
.step{flex:1 1 150px;background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px;font-size:.9rem}
.step b{display:block;color:var(--accent);margin-bottom:4px}
blockquote{margin:0;padding:8px 14px;border-left:3px solid var(--line);color:var(--muted);font-size:.92rem}
ul{margin:0;padding-left:22px}li{margin:3px 0}
a{color:var(--accent)}
@media (max-width:600px){h1{font-size:1.6rem}.bar{width:60px}}
"""

H = []
a = H.append
a(f'<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
  f'<title>Zeely: разбор конкурента</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;600;700&family=JetBrains+Mono&display=swap"><style>{CSS}</style></head><body><main class="wrap">')

a('''<header style="display:flex;flex-direction:column;gap:10px">
<div class="eyebrow">Продуктовая и маркетинговая аналитика конкурента · Zeely-клон</div>
<h1>Zeely: что продают, как зарабатывают и как привлекают</h1>
<p class="meta">Zeely (Zeely, Inc.) — ИИ-маркетинг для малого бизнеса: из фото товара делает рекламные картинки и UGC-видео с ИИ-аватаром, помогает запустить рекламу в Meta и автопостинг в соцсети.
Срез — 29.10.2026. Источники: прохождение веб-воронки (22.10), 2 скринкаста Android-приложения (23–24.10), страницы App Store и Google Play, 500 отзывов App Store (US, 26.07–27.10.2026), 750 отзывов Google Play (US, 16.01–28.10.2026), Trustpilot (сводка и 40 последних отзывов, 29.10), выгрузки FB web2web giants #5–#9 (18.05–10.10.2026), Meta Ad Library (активные объявления на 29.10).
Внутренних данных конкурента (конверсии воронки, удержание, отмены) у нас нет — где вывод опирается на косвенные признаки, это помечено.</p>
</header>''')

# 1 Коротко
a('''<section class="card summary"><h2>Коротко</h2><ol>
<li><b>Масштаб большой и стабильный.</b> Спенд FB на веб-воронку за 28 дней держится на уровне 2,4–3,2 млн USD с мая; на 10.10 — 3,22 млн USD, ROAS 28д 1,14, CPA 96 USD. Гео: США 71%, Великобритания 12%, Канада 6%. Активных объявлений в Ad Library на основной странице — ~1 800.''' + tag('d') + '''</li>
<li><b>Окупаемость — на продлениях.</b> За 28 дней доход почти равен спенду (ROAS 1,03–1,15), то есть первый платёж (19,95–49,95 USD) рекламу едва покрывает; прибыль даёт переход на 79,95 USD/мес и допродажи.''' + tag('p') + '''</li>
<li><b>Продают обещание «ИИ-сотрудник вместо агентства»</b>: «загрузи 1 фото — получи 100+ объявлений», «контент на 3 месяца в один клик», «1$ в день». Реклама идёт от лица основателей (страницы «Alina Bond», «Yaroslav Sam» — сооснователи Алина Бондаренко и Ярослав Самойлюк) и персонажей-«клиентов» (Olivia Bennett, Rachel Hayes и др.); скидка 70% почти в каждом объявлении.''' + tag('d') + '''</li>
<li><b>Главная жалоба — деньги, а не продукт.</b> Среди отзывов на 1–2★ почти половина (47%) про списания, отмену и возвраты: автопереход с 19,95–29,95 на 79,95 USD/мес, платный «Booster» ~40 USD сразу после оплаты, сложная отмена.''' + tag('d') + '''</li>
<li><b>Хвалят простоту и скорость</b> — это самая частая тема в 4–5★ (23%); дальше — качество картинок и видео (14%) и аватары. Ругают «ИИ-вид» роликов, сбои генерации, сложный интерфейс и отсутствие продаж после запуска рекламы.''' + tag('d') + '''</li>
<li><b>Рейтинги в сторах высокие (App Store 4,58; Google Play 4,32; Trustpilot 4,4), но собраны активно:</b> приложение просит оценку сразу после старта, Trustpilot-отзывы в основном «приглашённые». Доля 5★ в App Store выросла с 47% в августе до 77% в октябре.''' + tag('p') + '''</li>
<li><b>Что берём себе:</b> воронку с регистрацией до оплаты и именным промокодом, генерацию «фото → видео с аватаром» как главный сценарий, кредиты поверх подписки; но честнее с ценой продления и без навязанных допродаж — это главный источник их 1★ и возвратов.</li>
</ol></section>''')

# 2 Продукт
a('<section><h2>1. Продукт</h2>')
a('''<p>Целевой клиент — владелец малого бизнеса без маркетолога (товары, услуги, цифровые продукты; часто Shopify, Etsy, Amazon KDP). Обещание: «маркетинг за 15 минут в день». В приложении три слоя: <b>генерация</b> (картинки, видео с аватаром, трендовые ролики, говорящая голова), <b>продвижение</b> (запуск рекламы в Meta через свой или их партнёрский кабинет, автопостинг в Instagram и TikTok), <b>чат-помощник</b> по маркетингу.</p>''')
a('<h3>Путь клиента</h3><div class="flow">'
  '<div class="step"><b>Реклама</b>Отзыв «я сомневалась, но доверила рекламу ИИ», «прощай, агентство», «1 фото — 100+ объявлений», −70%</div>'
  '<div class="step"><b>Веб-квиз</b>~30 экранов: цель, роль, отрасль, каналы, бюджет; ветка «соцсети / реклама / оба»; отзывы и обещания между вопросами</div>'
  '<div class="step"><b>Регистрация</b>Почта и пароль до оплаты, имя, график «ваш рост»</div>'
  '<div class="step"><b>Пейволл</b>«up to 70% off», промокод с именем, таймер 10 мин, 3 тарифа</div>'
  '<div class="step"><b>Оплата</b>Solidgate: карта, Apple Pay, PayPal; дальше по отзывам — допродажа Booster</div>'
  '<div class="step"><b>Приложение</b>Вход по токену из воронки, чек-лист первых шагов, первая генерация</div></div>')
a('<h3>Веб-воронка (22.10.2026)</h3>')
a(gallery([('f_00-sellingstage', 'Первый вопрос: цель. На 29.10 варианты уже другие: «Get first sales / Drive more sales»'),
           ('f_09-acquisition', 'Развилка: соцсети, платная реклама или оба'),
           ('f_25-summary', 'Сводка профиля: «потенциал роста — High»'),
           ('f_31-prediction', 'Именной график роста без цифр'),
           ('f_33-tools', 'Что входит: агенты, аватары, интеграция с магазином')]))
a('<h3>Приложение (Android, записи 23–24.10.2026)</h3>')
a(gallery([('a1_01-t000.0', 'Старт: «Grow your brand with AI marketing»'),
           ('a1_16-t033.0', 'Онбординг: «вы сэкономите 4 200 USD» на дизайнере, монтажёре, маркетологе'),
           ('a2_r2_0.5', 'Home: чек-лист первых шагов 3/5, быстрые сценарии'),
           ('a2_r2_5.3', 'Assets: все работы, Brand DNA'),
           ('a2_r2_10.0', 'Image: трендовые концепты, библиотека реклам'),
           ('a2_r2_12.2', 'Video: видео с аватаром, вирусное видео, галереи'),
           ('a2_r2_27.0', 'Campaigns: автопостинг и платная реклама'),
           ('a2_r2_23.7', '«+»: Image, Video, Meta campaign, Social posting'),
           ('a2_r2_36.0', 'Ask AI: чат с выбором модели (Claude, Gemini, GPT)'),
           ('a2_r2_46.5', 'Профиль: баланс кредитов, подписка, промокоды'),
           ('a1_24-t057.5', 'Генерация, шаг 0: товар — до 8 фото, название, описание'),
           ('a1_30-t098.2', 'Выбор концепта ролика'),
           ('a1_34-t104.5', 'Аватары с фильтрами'),
           ('a1_37-t119.0', 'Генерация до 3 минут')]))
a('''<div class="tw"><table><tr><th>Раздел</th><th>Что внутри</th><th>Платно</th></tr>
<tr><td>Home</td><td>Чек-лист: добавить товар → картинка → видео → опубликовать → запустить рекламу; быстрые сценарии; бренды</td><td>—</td></tr>
<tr><td>Image</td><td>Рекламная картинка из идеи, изменение размера, трендовые концепты, библиотека реклам (2 093 примера)</td><td>Кредиты</td></tr>
<tr><td>Video</td><td>Видео с ИИ-актёром, повтор трендового ролика (свой образец 3–30 с), говорящая голова 30 с, оживление картинки</td><td>Кредиты; картинка-основа — 25 кредитов</td></tr>
<tr><td>Campaigns</td><td>Автопостинг в Instagram/TikTok; реклама в Meta через свой кабинет или их партнёрский (одобрение ~24 ч, один счёт)</td><td>Комиссия до 12% от рекламного бюджета (страница цен) ''' + tag('d') + '''</td></tr>
<tr><td>Ask AI</td><td>Чат: исследование рынка, конкуренты, аудитория, тексты, разбор Instagram/TikTok; модели Claude / Gemini / GPT</td><td>Не знаем</td></tr>
</table></div>''')
a('</section>')

# 3 Монетизация
a('<section><h2>2. Монетизация</h2>')
a('<p>Модель — подписка с кредитами на генерацию и отдельные пакеты кредитов. На вебе — вводный период со скидкой, дальше полная цена; в сторах — неделя, месяц, год.</p>')
a('''<div class="tw"><table><tr><th>Веб-пейволл (22.10)</th><th>Первый период</th><th>Дальше</th><th>В день (по вводной цене)</th></tr>
<tr><td>2 недели</td><td class="num">19.95 USD</td><td class="num">39.95 USD</td><td class="num">1.43 USD</td></tr>
<tr><td>4 недели — «Most Popular», выбран</td><td class="num">29.95 USD</td><td class="num">79.95 USD / мес</td><td class="num">1.07 USD</td></tr>
<tr><td>8 недель</td><td class="num">49.95 USD</td><td class="num">159.95 USD</td><td class="num">0.89 USD</td></tr></table></div>''')
a('<p class="small muted">Заголовок «up to 70% off», «Your promo code is applied» с именем пользователя (mila_oct26), таймер 10 минут. Чекаут: «$29.95 today, and $79.95 every month thereafter», отмена в аккаунте или через support. Триала нет. Источник: прохождение воронки 22.10; на 29.10 первый вопрос воронки изменился, цены повторно не проверены.</p>')
a(gallery([('f_35-price-top', 'Веб-пейволл: 3 тарифа, промокод, таймер'), ('f_35-checkout', 'Чекаут: 29.95 сегодня, потом 79.95 в месяц'),
           ('a1_21-t050.6', 'Пейволл в приложении после онбординга (закрывается)'), ('a1_40-t178.3', 'Оплата в Google Play: недельный план')]))
a('''<div class="tw"><table><tr><th>Покупки в App Store (US, 29.10)</th><th>Цена</th></tr>
<tr><td>1-Week Plan / Weekly Plus Premium / 3D Trial Plan / Plus (Advanced AI Features)</td><td class="num">19.99 USD</td></tr>
<tr><td>1-Month Plan</td><td class="num">59.99 USD</td></tr><tr><td>2-Month Plan</td><td class="num">85.99 USD</td></tr>
<tr><td>3-Month Plan</td><td class="num">119.99 USD</td></tr><tr><td>1-Year Plan</td><td class="num">199.99 USD</td></tr>
<tr><td>100 Credits</td><td class="num">9.99 USD</td></tr></table></div>
<div class="tw"><table><tr><th>Страница цен на сайте (zeely.ai/price, 29.10)</th><th>Цена</th><th>Кредиты</th></tr><tr><td>Starter</td><td class="num">29.95 USD / мес (зачёркнуто 49.95)</td><td class="num">2 500</td></tr><tr><td>Plus</td><td class="num">49.95 USD / мес (зачёркнуто 89.95)</td><td class="num">5 000</td></tr><tr><td>Growth — «Most popular»</td><td class="num">79.95 USD / мес (зачёркнуто 149.95)</td><td class="num">10 000</td></tr></table></div><p class="small muted">Тарифы различаются только кредитами; набор функций одинаковый. Пробные (Intro) планы по умолчанию продлеваются в Growth за 79,95 USD (сторонние обзоры). Неиспользованные кредиты не переносятся на следующий месяц (ответ Zeely на Trustpilot). Google Play: покупки 4.99–199.99 USD за единицу. В Android-приложении (Казахстан) пейволл: неделя 9 990 ₸, месяц 31 990 ₸, год 103 990 ₸, по умолчанию год.</p>''')
a('<h3>Допродажи и удержание денег</h3><ul>'
  '<li><b>Booster / «удвоить контент»</b> — разовая допродажа ~40 USD сразу после оплаты; по отзывам выглядит как обязательный шаг, «нельзя пропустить». ' + tag('d') + ' (6 отзывов: «up charged me $40 for a booster», «$50 for 8 weeks plus $40 for double the content»)</li>'
  '<li><b>Пакеты и «Growth bundle»</b> при первом входе; пакет «$39» на выборе после пробного. ' + tag('d') + '</li>'
  '<li><b>Кредиты</b> — тратятся быстро на дорогих видеомоделях (упоминают Seedance), их повышали; 100 кредитов — 9.99 USD. ' + tag('d') + '</li>'
  '<li><b>Платная реклама через их кабинет</b> — комиссия до 12% от рекламного бюджета (страница zeely.ai/price, подтверждается отзывом). ' + tag('d') + '</li>'
  '<li><b>Удержание при отмене</b>: несколько экранов-уговоров перед отменой («had to hit cancel 3 or 4 times»). ' + tag('d') + '</li>'
  '<li>Точный состав и цены всех допродаж после оплаты не видели — без оплаты дальше чекаута не пройти. ' + tag('n') + '</li></ul>')
a('</section>')

# 4 Отзывы
a('<section><h2>3. Отзывы</h2>')
a('''<div class="tw"><table><tr><th>Площадка</th><th>Рейтинг</th><th>Оценок / отзывов</th><th>Распределение</th></tr>
<tr><td>App Store (US)</td><td class="num">4.58</td><td class="num">23 511</td><td>в выборке 500 отзывов: 5★ 66%, 4★ 7%, 3★ 3%, 2★ 3%, 1★ 21%</td></tr>
<tr><td>Google Play</td><td class="num">4.32</td><td class="num">9 312 / 1 193 · 100K+ установок</td><td>все оценки: 5★ 72%, 4★ 11%, 3★ 5%, 2★ 2%, 1★ 10%; в выборке 750 текстов: 1★ 42%, 5★ 41%</td></tr>
<tr><td>Trustpilot</td><td class="num">4.4</td><td class="num">4 516</td><td>5★ 65%, 4★ 16%, 3★ 5%, 2★ 2%, 1★ 12%; профиль «просит отзывы», отвечает на 100% негативных</td></tr></table></div>''')
a('<p class="small muted">Темы посчитаны по ключевым словам на выборке App Store (500 отзывов, 26.07–27.10) и Google Play (750, 16.01–28.10); один отзыв может попасть в несколько тем, счёт приблизительный. Trustpilot — 40 последних отзывов (все 3–5★), в счёт тем не входят.</p>')
a('<h3>На что жалуются (1–2★: App Store 121, Google Play 353)</h3><div class="tw"><table><tr><th>Тема</th><th>App Store</th><th>Google Play</th></tr>')
neg = [('Списания, отмена, возврат', 53, 171), ('Дорого / кредиты', 11, 39), ('Не работает / сбои генерации', 19, 32), ('Сложно пользоваться', 25, 25),
       ('Поддержка не помогла', 12, 23), ('Качество: «видно, что ИИ», голос, аватар', 14, 20), ('Реклама приложения обманывает', 13, 17),
       ('Нет продаж после рекламы', 10, 6), ('Навязчиво: просьба оценки, Booster', 5, 8)]
for t, x, y in neg: a(bar(t, x, y, 121, 353))
a('</table></div>')
a('<h3>Что хвалят (4–5★: App Store 364, Google Play 357)</h3><div class="tw"><table><tr><th>Тема</th><th>App Store</th><th>Google Play</th></tr>')
pos = [('Просто и быстро', 95, 68), ('Хорошие картинки и ролики', 58, 43), ('Аватары и видео', 54, 28), ('Пошли продажи / клиенты', 27, 23),
       ('Помогла поддержка', 25, 11), ('Заменяет маркетолога / дизайнера', 13, 4)]
for t, x, y in pos: a(bar(t, x, y, 364, 357))
a('</table></div><p class="small muted">106 из 357 положительных отзывов Google Play — короче 20 символов («good», «nice app»).</p>')
a('''<h3>Цитаты</h3>
<blockquote>«I signed up only for the $19.99 trial and specifically declined the $39 package… they moved me into a $79 membership» — App Store, 1★, 08.10</blockquote>
<blockquote>«Got scammed out of a 40$ booster add on I didn't want. They set their app up to make it look like you need to click on it to progress» — Google Play, 1★, 07.09</blockquote>
<blockquote>«The app won't even let me do anything until I give you a five star review» — App Store, 1★, 23.10</blockquote>
<blockquote>«I'm sick of seeing ads where it says a dollar a day… it's not a dollar a day» — Google Play, 1★, 11.10</blockquote>
<blockquote>«Makes great ads… campaign not so much. I spent $100 on a paid campaign and got zero leads» — App Store, 5★, 28.09</blockquote>
<blockquote>«Very easy to use… a few clicks, a few minutes of waiting, and it is done» — Trustpilot, 5★, 27.10</blockquote>''')
a('<p><b>Рейтинги собираются активно.</b> Доля 5★ в выборке App Store: август 47% (44 из 93), сентябрь 67% (143 из 214), октябрь 77% (131 из 170). Отзывы говорят о запросе оценки сразу после старта, до первой генерации. ' + tag('p') + ' — рост 5★ связан с запросом оценки, а не с улучшением продукта; причину по открытым данным не проверить.</p>')
a('</section>')

# 5 Маркетинг
a('<section><h2>4. Маркетинг</h2>')
a('<h3>Показатели из выгрузок FB (Meta, 28 дней до даты выгрузки)</h3><p class="small muted">Веб-воронку и рекламу «прямо в стор» не смешиваем: в сторе «конверсия» — установка. Источник: reports/fb-kandidaty-itog-28-10.xlsx, лист «Сводная», строки Zeely.</p>')
a('''<div class="tw"><table><tr><th>Выгрузка</th><th>Схема</th><th>Спенд 28д, USD</th><th>ROAS 28д</th><th>CPA, USD</th><th>Конверсий</th><th>Объявлений всего</th><th>Акк. (забанено)</th></tr>
<tr><td>#5 · 18.05</td><td>веб</td><td class="num">2 386 849</td><td class="num">1.15</td><td class="num">95</td><td class="num">25 823</td><td class="num">15 433</td><td class="num">8 (3)</td></tr>
<tr><td>#7.1 · 28.07</td><td>веб</td><td class="num">3 163 211</td><td class="num">1.03</td><td class="num">105</td><td class="num">27 357</td><td class="num">24 607</td><td class="num">8 (3)</td></tr>
<tr><td>#8 · 28.08</td><td>веб</td><td class="num">2 876 821</td><td class="num">1.10</td><td class="num">99</td><td class="num">29 395</td><td class="num">32 592</td><td class="num">8 (3)</td></tr>
<tr><td>#8 · 28.08, 2-я строка</td><td>веб</td><td class="num">290 498</td><td class="num">0.52</td><td class="num">4*</td><td class="num">69 873*</td><td class="num">4 519</td><td class="num">17 (3)</td></tr>
<tr><td>#9 · 10.10</td><td>веб</td><td class="num">3 222 426</td><td class="num">1.14</td><td class="num">96</td><td class="num">33 776</td><td class="num">35 705</td><td class="num">8 (3)</td></tr>
<tr><td>#5 · 18.05</td><td>стор</td><td class="num">158 407</td><td class="num">0.16</td><td class="num">14</td><td class="num">11 049</td><td class="num">2 651</td><td class="num">15 (3)</td></tr>
<tr><td>#6.1 · 29.06</td><td>стор</td><td class="num">138 902</td><td class="num">0.17</td><td class="num">11</td><td class="num">12 850</td><td class="num">5 014</td><td class="num">10 (3)</td></tr>
<tr><td>#7.1 · 28.07</td><td>стор</td><td class="num">143 012</td><td class="num">0</td><td class="num">137</td><td class="num">1 047</td><td class="num">2 457</td><td class="num">15 (3)</td></tr>
<tr><td>#9 · 10.10</td><td>стор</td><td class="num">96 326</td><td class="num">0.02</td><td class="num">6</td><td class="num">15 799</td><td class="num">3 426</td><td class="num">21 (4)</td></tr></table></div>
<p class="small muted">* Вторая веб-строка 28.08 с CPA 4 USD — аномалия выгрузки (другая цель оптимизации), в сравнение не берём. Гео веб-воронки на 10.10: США 71%, Великобритания 12%, Канада 6%, Украина 5%, Австралия 2% (tier-1 — 92%). Спенд веб-строки 10.10 за всё время с 06.04.2026 — 7,19 млн USD. Доход с одной конверсии — 107–119 USD.</p>''')
a('<p><b>Вывод по цифрам.</b> Веб-воронка — основной канал: 97% спенда; стор-схема мелкая и в минус по ROAS (0–0,17). CPA ~96–105 USD при доходе 107–119 USD на конверсию: за 28 дней почти в ноль, значит, модель держится на продлениях по 79,95 USD. ' + tag('d') + ' для цифр, ' + tag('p') + ' для вывода о продлениях.</p>')
a('''<h3>Топ-объявления из выгрузок</h3><div class="tw"><table><tr><th>Выгрузка</th><th>Текст</th><th>Спенд 28д</th><th>ROAS</th><th>CPA</th><th>CTR</th><th>Ленд</th></tr>
<tr><td>#9 · 10.10</td><td>«I was skeptical, but then I let AI take over my ad»</td><td class="num">57 897</td><td class="num">1.23</td><td class="num">89</td><td class="num">1.27%</td><td>/start?si=admaker-2</td></tr>
<tr><td>#5 · 18.05</td><td>«this is what happened to my business when i let a.i. employee run my ads on fb and ig… unlock 70% off now»</td><td class="num">64 167</td><td class="num">1.39</td><td class="num">79</td><td class="num">1.01%</td><td>/start/ai-admaker-2</td></tr>
<tr><td>#8 · 28.08</td><td>«get up to 70% off now! 🔥 boost your sales overnight»</td><td class="num">39 688</td><td class="num">1.30</td><td class="num">83</td><td class="num">1.11%</td><td>/start/ads-1</td></tr>
<tr><td>#7.1 · 28.07</td><td>— (видео)</td><td class="num">44 156</td><td class="num">1.65</td><td class="num">66</td><td class="num">1.07%</td><td>/start/adlaunch</td></tr>
<tr><td>#5 · 18.05, стор</td><td>«instantly generate ai ads — no cost to start! free for a limited time!»</td><td class="num">12 419</td><td class="num">0</td><td class="num">51</td><td class="num">2.90%</td><td>Google Play</td></tr></table></div>''')
a('''<h3>Meta Ad Library (активные объявления, все страны, 29.10)</h3><div class="tw"><table><tr><th>Страница (ID)</th><th>Имя сейчас</th><th>Активных</th><th>Главные углы</th></tr>
<tr><td>347877928399557 — основная «Zeely»</td><td>Alina Bond</td><td class="num">~1 800</td><td>«AI-automated content for just 1$/day», «свой ИИ-аватар», «3 месяца контента в один клик», «1 фото — 100+ объявлений», отзыв «I was skeptical…»</td></tr>
<tr><td>845344378655821</td><td>Olivia Bennett</td><td class="num">~370</td><td>«Say goodbye to marketing agencies — Zeely replaces them. Drop your link — and BOOM!», отзыв «I was skeptical…»</td></tr>
<tr><td>796787683518383 — «Zeely: AI Ads Maker»</td><td>Yaroslav Sam</td><td class="num">~85</td><td>«Tired of ads that don't perform? Upload 1 photo, get 100+ that do», «70% off»</td></tr>
<tr><td>776214692240497 — «Zeely: Grow Sales with AI»</td><td>Kate Nazary</td><td class="num">~66</td><td>отзыв «I was skeptical…», «прощай, агентство», новый угол для разработчиков приложений (28.10)</td></tr></table></div>
<p class="small muted">Страницы бренда переименованы в имена людей: «Alina Bond» и «Yaroslav Sam» — сооснователи (Алина Бондаренко, CCO; Ярослав Самойлюк, COO), Olivia Bennett, Rachel Hayes, Daniel Whitmore, Kate Nazary — персонажи-«владельцы бизнеса» (реальные ли это люди, не знаем). Нишевые креативы: продавцы Shopify («If you sell on Shopify don't skip this»), авторы книг Amazon KDP («347 продаж за неделю»), разработчики приложений. Подписи кнопок: «Unlock 70% OFF», «THE FINAL 70% OFF», «Reach your goal in 3 months with AI!». Спенд по отдельным объявлениям Ad Library не показывает.</p>''')
a('<div class="wide">' + img('ad_page_847877928399557_2'.replace('847', '347'), 'Основная страница (сейчас «Alina Bond»): отзыв-креатив, «1$/day», баннер для продавцов Shopify') +
  img('ad_page_845344378655821_2', 'Страница «Olivia Bennett»: «прощай, агентство», история автора книги') +
  img('ad_page_796787683518383', 'Страница «Zeely: AI Ads Maker»: «1 фото — 100+ объявлений»') + '</div>')
a("""<h3>Как подают продукт на сайте</h3><div class="card">
<p><b>Позиционирование сменилось.</b> В 2023 Zeely подавался как «приложение для роста продаж» (Zeely: AI Sales Growth App); сейчас — «AI marketing platform» и «агентная ИИ-платформа для создания, запуска и масштабирования рекламы». Главный экран zeely.ai: «Create, launch and scale winning ads with AI» — «Manage your full performance marketing cycle with AI strategies shaped by top marketing experts».</p>
<ul><li><b>Обещание масштаба и простоты:</b> «Loved by 2M+ Zeely users», «Zeely helps small sellers run ads like big brands», «expertise behind million-dollar budgets», «save hours on campaign setup».</li>
<li><b>Витрина ИИ-моделей:</b> «One plan. 30+ AI models» — на сайте названы Claude, Gemini, GPT, Seedance, Kling, Veo, Grok Imagine, Nano Banana, ElevenLabs, Wan. Продают доступ к «лучшим моделям» в одном месте.</li>
<li><b>Цикл целиком:</b> видео (UGC, аватары, «AI twin»), картинки пачками, запуск рекламы в Meta с аналитикой креативов и «Competitor spy» (живые объявления 10 000+ брендов), органика по трендам, ИИ-агент (в т.ч. в Slack).</li>
<li><b>Ниши на сайте:</b> Shopify, Etsy, Amazon, WooCommerce, дропшиппинг; бьюти, одежда, фитнес, животные, рестораны, недвижимость, аренда, техника; SEO-страницы под каждую («Instagram ad creator», «TikTok ad creator», «LinkedIn ad generator», «AI employee»).</li>
<li><b>Доверие:</b> «Meta Business Partner», Forbes, TechCrunch, Sifted в воронке; в приложении — 4.6★ и «2 000 000+ businesses».</li></ul>
<p class="small muted">Источник: zeely.ai и zeely.ai/price (29.10.2026), блог zeely.ai, AIN (2023). Счётчик «2M+ users» — заявление компании.</p></div>""")
a("""<h3>Через какую рекламу продают</h3><ul>
<li><b>Meta (Facebook, Instagram, Messenger, Threads, WhatsApp) — основной канал.</b> Веб-воронка — 97% спенда в выгрузке 10.10; ~1 800 активных объявлений только на основной странице, ещё ~520 на трёх других. """ + tag('d') + """</li>
<li><b>Реклама «прямо в стор»</b> — небольшая (96–158 тыс. USD за 28 дней), с бесплатным входом: «no cost to start», «free for a limited time». """ + tag('d') + """</li>
<li><b>TikTok, Google, YouTube</b> — в открытых источниках следов платной рекламы не нашли; TikTok упоминается только как площадка для клиентов. """ + tag('n') + """</li>
<li><b>Инфлюенсеры</b> — открыта вакансия Influencer Marketing Manager (tier-1 рынки), публичной партнёрской программы нет. """ + tag('p') + """ — канал строят.</li>
<li><b>SEO и контент</b> — блог с десятками статей: обзоры «Is Zeely worth it?», «Is Zeely a scam?», «Is Zeely reliable?», сравнения «Zeely vs Creatify», «Creatify alternatives», гайды по нишевой рекламе. Перехватывают поисковые запросы о себе и о конкурентах. """ + tag('d') + """</li></ul>""")
a("""<h3>Креативы: о чём реклама (выборка 109 объявлений из Ad Library, 4 страницы, 29.10)</h3><div class="tw"><table><tr><th>Угол</th><th>Объявлений</th><th>Как звучит</th></tr>
<tr><td>Прощай, агентство</td><td class="num">31</td><td>«Say goodbye to marketing agencies 🚫 Zeely replaces them ✅ It creates and publishes high-converting ads and organic content for you. Drop your link — and BOOM!»</td></tr>
<tr><td>Отзыв «я сомневалась»</td><td class="num">30</td><td>«I was skeptical, but then I let AI take over my ads on FB & IG… Before: Wasting money, now reaching new customers & boosting sales like crazy! 🚀» — самый долгий: в ротации с 18.09, топ по спенду в выгрузках</td></tr>
<tr><td>1 фото — 100+ объявлений</td><td class="num">25</td><td>«Tired of ads that don't perform? Upload 1 photo, get 100+ that do 🔥»</td></tr>
<tr><td>ИИ-маркетолог 24/7, контент на месяцы</td><td class="num">9</td><td>«AI Creators create high-performing videos… Create months of content in just a few clicks. Your AI Marketing Agent, available 24/7»</td></tr>
<tr><td>Цена «1$ в день», свой аватар</td><td class="num">5</td><td>«AI-automated content for your business for just 1$/day! Create your own AI Avatar… 3 months of content in one click»</td></tr>
<tr><td>Скидка, продажи «за ночь»</td><td class="num">2</td><td>«Get up to 70% off now! 🔥 Boost your sales overnight!»</td></tr>
<tr><td>Для разработчиков приложений (новый, 28.10)</td><td class="num">2</td><td>«Building an app is only half the work — getting users is the real challenge… launches your campaign in 2 clicks!»</td></tr>
<tr><td>Без текста</td><td class="num">5</td><td>только видео или картинка</td></tr></table></div>
<p class="small muted">Подписи под объявлением: «I create top-selling ads with AI» (40), «Unlock 70% OFF» / «GET 70% OFF» / «THE FINAL 70% OFF» (44), «Get 100+ scroll-stopping ads» (23), «Reach your goal in 3 months with AI!» (10). Выборка — первые карточки на каждой странице, не весь массив; доли — ориентир. Форматы: вертикальные UGC-видео «владельца бизнеса», текстовые картинки-«исповеди» («If you sell on Shopify, don't skip this», «I almost told my family I was deleting my book from Amazon KDP… 347 sales this week», «Stop trying to be an influencer»). Частая ротация: большинство активных объявлений запущены 4–28.10.</p>""")
a("""<h3>Свежие креативы из spy-сервиса (скрин Наташи, 29.10)</h3><div class="tw"><table><tr><th>Креатив</th><th>Страница</th><th>Подпись</th><th>В ротации</th><th>Показатели сервиса</th></tr>
<tr><td>Вебинар для команд: «How many BFCM statics can your designer ship? Fewer than 50 a day?», «Black Friday webinar for teams spending $50k+ a month»</td><td>Zeely***g Agent</td><td>«Scale Ads From Black Friday to Christmas»</td><td class="num">8 дней</td><td class="num">Creative Score 10K / 9.2K, показы 36K, Popularity 64</td></tr>
<tr><td>Оффер «Unlimited Seedance 2.5» — безлимит на видеомодель, «Stop wasting credits on AI generations», экран с тарифом «7 days unlimited»</td><td>Zeely***siness</td><td>«Get Unlimited Seedance 2.5 👈»</td><td class="num">2–3 дня</td><td class="num">Creative Score 1.4K–2.8K, показы 4.4–4.7K</td></tr>
<tr><td>Заметка-«скриншот» в стиле Apple Notes: «I don't mean to alarm you, but… we're looking for Amazon KDP authors to test Zeely AI. Tap to try»</td><td>Al***ond (Alina Bond)</td><td>«I learned how to create top-selling ads with AI»</td><td class="num">1 день</td><td class="num">Creative Score 1.4K, показы 4.4K</td></tr>
<tr><td>Нативные фото с текстом: «I'm a solo tattoo artist» на футболке, текст на осеннем листе</td><td>Al***ond</td><td>«I learned how to create top-selling ads with AI»</td><td class="num">1 день</td><td class="num">Creative Score 1.4K</td></tr></table></div>
<ul><li><b>Все объявления — W2A</b> (реклама → веб-воронка → приложение), площадка Facebook. """ + tag('d') + """</li>
<li><b>Идут вверх по рынку:</b> отдельная страница-«агент» продаёт вебинар к Чёрной пятнице командам с рекламным бюджетом от 50 тыс. USD в месяц — это B2B-сегмент, а не владелец маленького бизнеса. У этого креатива самые высокие показатели на скрине. """ + tag('d') + """ для креатива, """ + tag('p') + """ — что это отдельное направление продаж.</li>
<li><b>Отвечают на жалобы офферами:</b> кредиты на дорогих видеомоделях — частая претензия в отзывах (упоминают Seedance), и теперь продают «безлимит на Seedance 2.5» отдельным предложением. """ + tag('p') + """</li>
<li><b>Ниши через «приглашение на тест»:</b> авторы Amazon KDP, тату-мастера — текст выглядит как личная заметка, а не реклама; новые креативы живут 1–3 дня — тестируют много и быстро.</li></ul>
"""); a("""<h3>Серия «текст на футболке и на предметах»</h3>
<p>Самый массовый новый формат: реклама написана на спине футболки, на стикере на ноутбуке, на стене, на листе — выглядит как живое фото, а не баннер. Тексты — шаблон под профессию: «I'M A SOLO MAKEUP ARTIST», «I'M A SOLO PET SHOP OWNER», «I'm a solo tattoo artist» → «Give Zeely 1 photo and get 100+ Reels in 10 minutes to keep your business visible and reach more customers. Tap below to try Zeely». У футболки «Your business needs content. You don't need a career as a content creator…» — лучшие показатели на скрине: 4 дня в ротации, Creative Score 4.4K, 16K показов. """ + tag('d') + """</p>
<p>Одна идея — десятки ниш: меняется только профессия на футболке. Скорее всего, сами креативы делают своим же инструментом — это и демонстрация продукта. """ + tag('p') + """ Рядом — вебинар «One concept — 200–300 top creatives. The AI Creative Factory behind Zeely's…» (29.10, для креативных и перформанс-команд).</p>
""" + "<div class=\"wide\">" + img('spy_tshirts', 'Spy-сервис, 29.10: футболки «I\'m a solo…», стикер «Stop trying to be a content creator», заметка для авторов KDP, вебинар для команд (скрин Наташи)') + "</div>" + """"""); a("""<p class="small muted">Источник: 2 скриншота spy-сервиса от Наташи, 29.10.2026 (16 объявлений); названия страниц в сервисе частично скрыты. Метрики Creative Score и Popularity — внутренние показатели сервиса, не спенд.</p>""")
a("""<h3>Что о них пишут в интернете</h3><div class="tw"><table><tr><th>Тема</th><th>Что известно</th><th>Источник</th></tr>
<tr><td>Компания</td><td>Украинский стартап, основан в 2021–2022; сооснователи Дмитрий Самойлюк (CEO), Ярослав Самойлюк (COO), Алина Бондаренко (CCO); до этого — диджитал-агентство. 170–200+ сотрудников. Forbes Украина — топ-25 самых быстрорастущих стартапов (2024).</td><td>AIN, Vestbee, Dealroom, PitchBook</td></tr>
<tr><td>Инвестиции</td><td>Победа в The Pitch by Deel & J.P. Morgan (Париж) — 1 млн USD от Deel; форма SEC D от 14.09.2026 — 8,84 млн USD от 24 инвесторов (агрегатор называет это Series A, инвесторы не раскрыты). Всего по PitchBook — 10,2 млн USD.</td><td>Vestbee, Dealroom, FundUp, RuntimeWire, PitchBook</td></tr>
<tr><td>Обзоры</td><td>Независимые обзоры сходятся: «быстро и просто для новичка, для быстрой рекламы товара, но не полноценный маркетинг»; тексты шаблонные; ограничены готовыми сценариями. Главный минус — биллинг: дешёвый вход, автопродление на 79,95 USD.</td><td>reloop.so, gethookd.ai, vidmuse.ai, fluxnote.io, aboutchromebooks.com</td></tr>
<tr><td>«Scam»</td><td>Обвинения в мошенничестве — из-за списаний и отмены, а не продукта. Zeely сам пишет SEO-статьи «Is Zeely a scam?», «Is Zeely reliable?», признаёт жалобы на биллинг и отмену. На Reddit отдельных тредов не нашли.</td><td>zeely.ai/blog, TalkAndroid, Techbullion, Trustpilot</td></tr>
<tr><td>Конкуренты о Zeely</td><td>Сравнения пишут конкуренты (Creatify, Novoads, Stork, AdCreate): Zeely — инструмент «запустить кампанию в Meta», Creatify и Arcads — сильнее в генерации видео с аватарами, AdCreative.ai — в статичных баннерах.</td><td>novoads.ai, stork.ai, superscale.ai, alici.ai</td></tr>
<tr><td>Площадки отзывов</td><td>Trustpilot — главный источник репутации (4,4, 4 516 отзывов, профиль платный, «приглашает» отзывы); на G2 — 0 отзывов; на Capterra профиля нет.</td><td>Trustpilot, G2</td></tr></table></div>
<p class="small muted">Многие «обзоры» — от самой Zeely или аффилиатов и конкурентов; факты о деньгах и сотрудниках — из вторичных источников, первичный только Form D.</p>""")
a('''<h3>Связка «креатив → воронка → пейволл → приложение»</h3><ul>
<li><b>Креатив</b> обещает результат от лица «такого же владельца бизнеса» и скидку 70%. В части креативов — «1$ в день», хотя вводная цена 0,89–1,43 USD в день, а с продления — около 2,7 USD в день — это прямая жалоба в отзывах.</li>
<li><b>Воронка</b> продолжает обещание: ветка под цель (соцсети или реклама), отзывы и экраны «экономия 15 часов в неделю» между вопросами, сводка «потенциал — High». Под каждый угол — свой ленд (/ai-admaker-2, /adlaunch, /ads-1).</li>
<li><b>Пейволл</b> повторяет «70% off» из рекламы, добавляет именной промокод и таймер — креатив и пейволл говорят одно и то же.</li>
<li><b>Приложение</b> открывается сразу с аккаунтом из воронки; первый экран — чек-лист «создать картинку → видео → опубликовать → запустить рекламу», т.е. продукт ведёт к тому, что обещали в рекламе. Разрыв — в цене после первого периода и в допродажах сразу после оплаты.</li></ul>''')
a('</section>')

# 5 Дополнение 30.10
a(open(os.path.join(S, 'section-2026-10-30.html'), encoding='utf-8').read())

# 6 Что берём
a('''<section class="card"><h2>Что берём себе</h2><ol>
<li><b>Отзыв-креатив от лица владельца бизнеса</b> («я сомневалась, но доверила рекламу ИИ») и угол «вместо агентства» — их самые долгоживущие и дешёвые по CPA объявления (CPA 66–89 USD против 96 в среднем).</li>
<li><b>Нишевые креативы и ленды</b> под Shopify, авторов книг, услуги — отдельные входы в одну воронку.</li>
<li><b>Формат «текст на футболке / стикере» с шаблоном «I'm a solo &lt;профессия&gt;»</b> — дешёвый в производстве, выглядит нативно, масштабируется на десятки ниш; делать нашим же генератором.</li>
<li><b>Сезонные и B2B-креативы</b> (Чёрная пятница, вебинар для команд с бюджетом) и офферы-ответы на боль клиентов (безлимит на дорогую модель) — проверить у себя после запуска.</li>
<li><b>Реклама от лица основателя и «клиента»</b>, частая ротация (новые объявления каждую неделю) и 3–4 повторяющихся угла вместо одного.</li>
<li><b>SEO-страницы под нишевые запросы и «X vs Y»</b> — дешёвый второй канал; заранее подготовить страницу «Is &lt;наш продукт&gt; legit?» с честными условиями продления.</li>
<li><b>Воронку с регистрацией до оплаты</b>, именным промокодом и таймером; аккаунт сразу готов в приложении.</li>
<li><b>Главный сценарий «фото товара → видео с ИИ-аватаром»</b> и чек-лист первых шагов на главной — это то, за что их хвалят («просто и быстро»).</li>
<li><b>Кредиты поверх подписки и пакеты кредитов</b> (у них 100 кредитов — 9,99 USD) — второй источник дохода и прогрев платёжек.</li>
<li><b>Не копируем:</b> скрытый переход на 79,95 USD/мес, «обязательный» Booster, запрос 5★ до первого результата, «1$ в день» в рекламе — это почти половина их 1–2★ и источник возвратов и чарджбеков. Цену продления показываем явно на пейволле и в письме перед списанием.</li>
<li><b>Проверить у себя:</b> качество видео («видно, что ИИ», неправильное произношение) и сбои генерации — вторая по частоте группа жалоб; запуск рекламы в Meta не обещаем, пока не уверены в результате — «0 продаж после 100 USD» стабильно бьёт по рейтингу.</li>
</ol></section>''')

a('''<section><h2>Ограничения данных и источники</h2><ul class="small">
<li>Нет внутренних данных конкурента: конверсия воронки, доля продлений, отмены, LTV — не знаем. ROAS и CPA — из выгрузок FB (28 дней), по ним нельзя судить о продлениях.</li>
<li>Отзывы: App Store — RSS, 500 последних (US), Google Play — 750 последних (US, en), Trustpilot — сводка и 40 последних. Темы — по ключевым словам, приблизительно.</li>
<li>Воронка пройдена 22.10.2026 (мобильный вид, en-US); на 29.10 первый вопрос изменился, цены повторно не проверялись. Допродажи после оплаты видны только из отзывов.</li>
<li>Ad Library — активные объявления на 29.10, все страны; число объявлений — по счётчику страницы, спенд по объявлениям не раскрывается.</li>
<li>Материалы: скринкасты и скриншоты — references/zeely/; выгрузки — reports/fb-kandidaty-itog-28-10.xlsx.</li></ul></section>''')

a('</main></body></html>')
open(OUT, 'w').write('\n'.join(H))
print(OUT, os.path.getsize(OUT))
