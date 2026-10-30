# Сборка отчёта по Zeely: python3 zeely/build-report.py → zeely/zeely-competitor-analytics-2026-10-30.html
# Картинки и стили — zeely/img/ (вытащены из версии 29.10).
import base64, json, os
S = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(S, 'img')
CAP = json.load(open(os.path.join(IMG, 'captions.json'), encoding='utf-8'))
CSS = open(os.path.join(IMG, 'style.css'), encoding='utf-8').read()
OUT = os.path.join(S, 'zeely-competitor-analytics-2026-10-30.html')

def fig(i, cap=None):
    n = f'{i:02d}.jpg'
    b = base64.b64encode(open(os.path.join(IMG, n), 'rb').read()).decode()
    c = cap or CAP[n]
    return f'<figure><img src="data:image/jpeg;base64,{b}" alt="{c}"><figcaption>{c}</figcaption></figure>'

def gallery(ids): return '<div class="gallery">' + ''.join(fig(i) for i in ids) + '</div>'
def wide(ids): return '<div class="wide">' + ''.join(fig(i) for i in ids) + '</div>'
def tag(k): return {'d': '<span class="tag ok">Видно в данных</span>', 'p': '<span class="tag warn">Предположение</span>', 'n': '<span class="tag crit">Не знаем</span>'}[k]
D, P, N = tag('d'), tag('p'), tag('n')

def bars(rows, ta, tb):
    out = []
    for t, a, b in rows:
        pa, pb = a / ta * 100, b / tb * 100
        out.append(f'<tr><td>{t}</td><td><div class="bar"><span style="width:{pa:.0f}%"></span></div><span class="num">{a} · {pa:.0f}%</span></td>'
                   f'<td><div class="bar b2"><span style="width:{pb:.0f}%"></span></div><span class="num">{b} · {pb:.0f}%</span></td></tr>')
    return ''.join(out)

def src(t): return f'<p class="small muted">Источники: {t}</p>'

H = []; a = H.append
a('<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
  '<title>Zeely: разбор конкурента</title><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;600;700&family=JetBrains+Mono&display=swap">'
  f'<style>{CSS}</style></head><body><main class="wrap">')

a(f'''<header style="display:flex;flex-direction:column;gap:10px">
<div class="eyebrow">Продуктовая и маркетинговая аналитика конкурента · Zeely-клон</div>
<h1>Zeely: что продают, как зарабатывают и что из этого делаем мы</h1>
<p class="meta">Zeely (Zeely, Inc.) — ИИ-маркетинг для малого бизнеса: из фото товара делает рекламные картинки и видео с ИИ-аватаром, запускает рекламу в Meta и публикует посты в соцсети.
Срез — 29–30.10.2026. Источники: прохождение веб-воронки (22.10), 2 скринкаста Android-приложения (23–24.10), справка help.zeely.ai и zeely.ai/pricing (30.10), 1 250 отзывов App Store и Google Play + Trustpilot, выгрузки FB #5–#9 (18.05–10.10.2026), Meta Ad Library и spy-сервис (29.10), страницы цен конкурентов и документация Higgsfield API (30.10).
Внутренних данных конкурента (конверсии, удержание, отмены) у нас нет. Метки у выводов: {D} {P} {N}.</p>
</header>''')

# Коротко
a(f'''<section class="card summary"><h2>Коротко</h2><ol>
<li><b>Продукт — фабрика рекламных креативов:</b> фото товара + описание + ИИ-персонаж (из библиотеки или из своего селфи) → картинка или видео; концепты по нишам и трендовые ролики «повтори». Плюс запуск рекламы в Meta и автопостинг в Instagram и TikTok. {D}</li>
<li><b>Реклама клиента — через кабинет Zeely (от 25 USD в день, комиссия 12%, без паузы и правок) или через свой кабинет без комиссии.</b> Таргетинг — только гео, возраст, пол. {D}</li>
<li><b>Деньги — подписка + кредиты + апсейлы.</b> Вход 19,95–49,95 USD, дальше автоматически 79,95 USD/мес; тарифы на сайте отличаются только кредитами; сразу после оплаты — Booster ~40 USD. {D}</li>
<li><b>Масштаб большой:</b> FB-спенд на веб-воронку 2,4–3,2 млн USD за 28 дней, ROAS 1,03–1,15, CPA ~96 USD, США 71%. Окупаются на продлениях. {D} для цифр, {P} для вывода.</li>
<li><b>Главная жалоба — подписка, а не продукт:</b> 47% отзывов на 1–2★ — списания, отмена, возвраты. Хвалят простоту и скорость. {D}</li>
<li><b>Нам в v1:</b> генерация на Higgsfield API (оплата по факту), кредиты поверх подписки, постинг через готовый сервис-посредник; запуск рекламы — позже. Честная цена продления. {P}</li>
</ol></section>''')

# 1 Продукт
a('<section><h2>1. Продукт и как он работает</h2>')
a('<p>Клиент — владелец малого бизнеса без маркетолога (товары, услуги; часто Shopify, Etsy, Amazon KDP). Обещание: «маркетинг за 15 минут в день». В приложении три слоя: <b>генерация</b> креативов, <b>продвижение</b> (реклама в Meta и автопостинг, раздел 2) и <b>ИИ-чат</b> по маркетингу.</p>')
a('''<h3>Путь клиента</h3><div class="flow">
<div class="step"><b>Реклама</b>«я сомневалась, но доверила рекламу ИИ», «прощай, агентство», −70%</div>
<div class="step"><b>Веб-квиз</b>~30 экранов: цель, отрасль, каналы, бюджет; ветка «соцсети / реклама / оба»</div>
<div class="step"><b>Регистрация</b>почта и пароль до оплаты, именной график «ваш рост»</div>
<div class="step"><b>Пейволл</b>«up to 70% off», именной промокод, таймер 10 мин</div>
<div class="step"><b>Оплата</b>карта, Apple Pay, PayPal; сразу апсейл Booster</div>
<div class="step"><b>Приложение</b>вход по токену из воронки, чек-лист первых шагов</div></div>''')
a('<h3>Веб-воронка (22.10)</h3>' + gallery([0, 1, 2, 3, 4]))
a('<h3>Приложение (Android, 23–24.10)</h3>' + gallery([5, 6, 7, 9, 10, 11, 13, 14]))
a(f'''<h3>Главный сценарий: товар → креатив</h3><div class="flow">
<div class="step"><b>1. Товар</b>до 8 фото, название, описание; «рыночный контекст» (ниша, аудитория, боли) — вручную или ИИ</div>
<div class="step"><b>2. Стартовая картинка</b>своё фото или генерация (Nano Banana, GPT Image)</div>
<div class="step"><b>3. Концепт</b>референс из галереи или свой образец</div>
<div class="step"><b>4. Персонаж</b>ИИ-аватар из библиотеки (фильтры: пол, возраст, стиль) или свой</div>
<div class="step"><b>5. Видео</b>Kling O3 Pro или Seedance 2.0; полный ролик, только хук или только тело; сценарий, голос, субтитры правятся</div></div>
{gallery([15, 16, 17, 18])}
<ul>
<li><b>Свой персонаж из селфи:</b> «even a selfie works» — фото анфас, без других людей; пол, возраст, стиль; готов меньше чем за минуту. {D}</li>
<li><b>Концепты по нишам</b> (не отдельные шаблоны): Fashion try-on — «одежда, обувь, ювелирка, аксессуары»; Service showcase — «салоны красоты, фитнес-тренеры»; Before &amp; after — «уход за кожей, фитнес»; ещё Street interview, Podcast, Hidden camera, ASMR, Testimonial, Offer и др. {D}</li>
<li><b>Тренды:</b> раздел Viral video — готовые трендовые ролики (Emotions, Glow-up, In motion), кнопка Recreate подставляет твой товар и аватар. {D}</li>
<li><b>Другие форматы:</b> говорящая голова 30 с, оживление картинки 5–10 с, пачка статичных объявлений (2–10 референсов), по умолчанию 9:16. {D}</li>
<li>Сколько аватаров в библиотеке и сколько своих можно на тарифе — в справке нет. {N}</li></ul>''')
a(src('скринкасты (references/zeely/app/), help.zeely.ai — 14349115, 13751532, 14471428, 15272345, 11007854, 12498965.'))
a('</section>')

# 2 Реклама и постинг для клиента
a('<section><h2>2. Реклама и постинг для клиента</h2>')
a(f'''<h3>Платная реклама в Meta</h3><div class="tw"><table><tr><th></th><th>Через кабинет Zeely</th><th>Через свой кабинет Meta</th></tr>
<tr><td>Чей кабинет</td><td>Zeely («Zeely's Meta partner account»), в объявлении — данные бизнеса клиента</td><td>Клиента: подключает Meta, выбирает кабинет и страницу</td></tr>
<tr><td>Настройки</td><td colspan="2">Аудитория от ИИ или своя: <b>гео, возраст, пол</b> (интересов и lookalike нет); цели Traffic / Leads (в своём ещё Sales); только креативы, сделанные в Zeely</td></tr>
<tr><td>Бюджет</td><td><b>от 25 USD в день</b> × число дней, оплата сразу в чекауте Zeely</td><td>минимум Meta, платит клиент напрямую</td></tr>
<tr><td>Модерация</td><td>команда Zeely 1–12 ч (до 24 ч) + Meta; отклонили — деньги вернут</td><td>только Meta</td></tr>
<tr><td>Пауза и правки</td><td><b>нельзя</b>; остановить — через поддержку, возврат остатка не гарантирован</td><td>в кабинете Meta</td></tr>
<tr><td>Комиссия</td><td><b>12% от бюджета</b>, с Booster — 6%</td><td>нет</td></tr></table></div>
<ul><li><b>Как берут комиссию,</b> в справке не написано: «весь бюджет уходит в Meta», оплата одним платежом в чекауте. Значит, 12% сверху бюджета и сразу (за 50 USD бюджета ~56 USD); отслеживать нечего — кабинет их. {P}</li>
<li>Кабинет Zeely снимает с клиента верификацию и баны, но клиент не управляет кампанией — отсюда отзывы «потратил 100 USD — 0 продаж». {P}</li></ul>''')
a(src('help.zeely.ai — 11008054, 17174229, 9874321, 12531014 (service fee, 17.07.2026), 16974620; zeely.ai/pricing.'))
a(f'''<h3>Постинг в соцсети (бесплатно, без комиссии)</h3><div class="flow">
<div class="step"><b>1. Подключить</b>один раз: Instagram — логин и пароль Instagram; TikTok — вход и доступ, аккаунт публичный</div>
<div class="step"><b>2. Выбрать</b>готовые креативы и площадку: Instagram (пост, Reels, Stories), TikTok (фото, видео, карусель, до 20 в кампании)</div>
<div class="step"><b>3. Расписание</b>Zeely сам раскладывает по календарю; совет — до 7 постов в день</div>
<div class="step"><b>4. Проверить</b>дата, подпись, теги; «Rewrite» — ИИ перепишет текст</div>
<div class="step"><b>5. Launch</b>Zeely публикует сам ±30 мин; ошибка — статус «Failed» с причиной</div></div>
<ul><li><b>Можно и вручную:</b> «Download» и «Share» (системное «Поделиться») у каждого креатива. {D}</li>
<li>Через что публикуют, не сказано; вход логином Instagram похож на официальный API Instagram, а он постит только в бизнес- и авторские аккаунты. {P} (по документации Meta)</li></ul>''')
a(src('help.zeely.ai — 12572798, 14301492, 14179183, 12683284, 11003948, 11570124.'))
a('</section>')

# 3 Монетизация
a('<section><h2>3. Монетизация</h2>')
a('<p>Подписка с кредитами на генерацию + докупка кредитов + апсейлы + комиссия с рекламы. На вебе — вводный период со скидкой, потом полная цена; в сторах — неделя, месяц, год.</p>')
a('''<div class="tw"><table><tr><th>Где</th><th>Тариф</th><th>Цена, USD</th><th>Что дальше / что входит</th></tr>
<tr><td rowspan="3">Веб-пейволл (22.10)</td><td>2 недели</td><td class="num">19.95</td><td>потом 39.95</td></tr>
<tr><td>4 недели («Most Popular»)</td><td class="num">29.95</td><td>потом 79.95 / мес</td></tr>
<tr><td>8 недель</td><td class="num">49.95</td><td>потом 159.95</td></tr>
<tr><td rowspan="3">Сайт zeely.ai/pricing</td><td>Starter</td><td class="num">29.95 / мес</td><td>2 500 кредитов</td></tr>
<tr><td>Plus</td><td class="num">49.95 / мес</td><td>5 000 кредитов</td></tr>
<tr><td>Growth</td><td class="num">79.95 / мес</td><td>10 000 кредитов</td></tr>
<tr><td rowspan="2">App Store (US)</td><td>неделя / месяц / год</td><td class="num">19.99 / 59.99 / 199.99</td><td>есть «Plus (Advanced AI Features)» за 19.99</td></tr>
<tr><td>100 кредитов</td><td class="num">9.99</td><td>разовая покупка</td></tr></table></div>''')
a(gallery([19, 20, 21, 22]))
a(f'''<ul>
<li><b>Тарифы на сайте отличаются только кредитами</b> — функции одинаковые, «Avatar customization» во всех. Тезис «в Pro — доп. персонажи» открытыми источниками Zeely не подтверждается (так устроено у MakeUGC: свои аватары 0 / 1 / 3 по тарифам). Что даёт «Plus» в приложении — {N}, проверить можно только покупкой.</li>
<li><b>Кредиты быстро кончаются:</b> видео Kling O3 Pro — 45 кредитов за секунду, Seedance 2.0 — 60 (справка Zeely, {D}). Ролик 17 с — 765 кредитов: на Growth это ~13 роликов в месяц, на Starter ~3 (наш расчёт по этим ставкам).</li>
<li><b>Апсейлы сразу после оплаты</b> (видим по отзывам, сами экраны не видели — без оплаты дальше чекаута не пройти), {D}:
<ul><li><b>Booster («удвоить контент»)</b> — ~40 USD; выглядит как обязательный шаг («up charged me $40 for a booster»); с ним комиссия за рекламу 6% вместо 12%.</li>
<li><b>Пакеты и «Growth bundle»</b> — при первом входе; после пробного — пакет за 39 USD.</li></ul></li>
<li><b>Комиссия 12%</b> с рекламы через их кабинет (раздел 2). {D}</li>
<li><b>Удержание при отмене:</b> несколько экранов-уговоров («had to hit cancel 3 or 4 times»). {D}</li></ul>''')
a(src('прохождение воронки 22.10 (на 29.10 воронка изменилась, цены повторно не проверены), zeely.ai/pricing, App Store (29.10), help.zeely.ai — 13545627, 16627057, отзывы.'))
a('</section>')

# 4 Отзывы
a('<section><h2>4. Отзывы</h2>')
a('''<div class="tw"><table><tr><th>Площадка</th><th>Рейтинг</th><th>Оценок</th><th>1★ / 5★</th></tr>
<tr><td>App Store (US)</td><td class="num">4.58</td><td class="num">23 511</td><td>в выборке 500: 21% / 66%</td></tr>
<tr><td>Google Play</td><td class="num">4.32</td><td class="num">9 312</td><td>все оценки: 10% / 72%</td></tr>
<tr><td>Trustpilot</td><td class="num">4.4</td><td class="num">4 516</td><td>12% / 65%; отзывы в основном «приглашённые»</td></tr></table></div>''')
a('<h3>На что жалуются (1–2★: App Store 121, Google Play 353)</h3><div class="tw"><table><tr><th>Тема</th><th>App Store</th><th>Google Play</th></tr>' +
  bars([('Списания, отмена, возврат', 53, 171), ('Сложно пользоваться', 25, 25), ('Не работает / сбои генерации', 19, 32), ('Дорого / кредиты', 11, 39),
        ('Качество: «видно, что ИИ», голос', 14, 20), ('Поддержка не помогла', 12, 23), ('Реклама приложения обманывает', 13, 17), ('Нет продаж после рекламы', 10, 6)], 121, 353) + '</table></div>')
a('<h3>Что хвалят (4–5★: App Store 364, Google Play 357)</h3><div class="tw"><table><tr><th>Тема</th><th>App Store</th><th>Google Play</th></tr>' +
  bars([('Просто и быстро', 95, 68), ('Хорошие картинки и ролики', 58, 43), ('Аватары и видео', 54, 28), ('Пошли продажи / клиенты', 27, 23)], 364, 357) + '</table></div>')
a('''<blockquote>«I signed up only for the $19.99 trial and specifically declined the $39 package… they moved me into a $79 membership» — App Store, 1★, 08.10</blockquote>
<blockquote>«I'm sick of seeing ads where it says a dollar a day… it's not a dollar a day» — Google Play, 1★, 11.10</blockquote>
<blockquote>«Makes great ads… campaign not so much. I spent $100 on a paid campaign and got zero leads» — App Store, 5★, 28.09</blockquote>
<blockquote>«Very easy to use… a few clicks, a few minutes of waiting, and it is done» — Trustpilot, 5★, 27.10</blockquote>''')
a(f'<p><b>Рейтинг накручивают просьбой об оценке</b> сразу после старта: доля 5★ в App Store выросла с 47% (август) до 77% (октябрь). {D} для цифр, {P} для причины.</p>')
a(src('App Store — 500 последних (US, 26.07–27.10), Google Play — 750 последних (US, 16.01–28.10), Trustpilot — сводка. Темы — по ключевым словам, один отзыв может быть в нескольких темах.'))
a('</section>')

# 5 Конкуренты
a('<section><h2>5. Конкуренты</h2>')
a(f'<p>Генерировать рекламу с ИИ-аватарами умеют многие. Zeely выделяется <b>полным циклом</b>: креатив → запуск рекламы → постинг на одной подписке. Чистые генераторы (Arcads, MakeUGC, HeyGen) сильнее в видео, но рекламу не запускают; ближе всех — Creatify (есть запуск рекламы) и Pippit (есть постинг). {D} для функций и цен, {P} для «кто сильнее».</p>')
a('''<div class="tw"><table><tr><th>Сервис</th><th>Что делает</th><th>Запуск рекламы</th><th>Постинг</th><th>Отличие от Zeely</th></tr>
<tr><td><b>Zeely</b></td><td>фото товара → картинки и видео с аватаром</td><td>да, Meta</td><td>да</td><td>—</td></tr>
<tr><td>Creatify</td><td>ссылка на товар → видеореклама с аватаром</td><td>да</td><td>не проверяли</td><td>ближайший, дешевле, есть API</td></tr>
<tr><td>Arcads</td><td>UGC-видео, 1 000+ ИИ-актёров, свой аватар</td><td>не заявлено</td><td>не заявлено</td><td>самые реалистичные актёры, дороже всех</td></tr>
<tr><td>MakeUGC</td><td>сценарий → ИИ-актёр, «товар в руках»</td><td>не заявлено</td><td>не заявлено</td><td>свои аватары — только на старших тарифах</td></tr>
<tr><td>TopView</td><td>ссылка → видео, аватары</td><td>не заявлено</td><td>не заявлено</td><td>чистый генератор</td></tr>
<tr><td>HeyGen</td><td>говорящие аватары, перевод</td><td>нет</td><td>нет</td><td>общий видеоинструмент</td></tr>
<tr><td>Pippit (CapCut)</td><td>ссылка на товар → видео, аватары</td><td>не заявлено</td><td>да, + TikTok Shop</td><td>ближе всех по постингу</td></tr>
<tr><td>AdCreative.ai</td><td>статичные баннеры</td><td>не заявлено</td><td>не заявлено</td><td>только статика</td></tr></table></div>''')
a(f'''<p><b>Цены</b> <span class="small muted">(USD в месяц; «за год» — в месяц при оплате за год)</span></p>
<div class="tw"><table><tr><th>Сервис</th><th>Тариф</th><th>Помесячно</th><th>За год</th><th>Что входит</th><th>Бесплатно</th></tr>
<tr><td rowspan="2"><b>Zeely</b></td><td>вводный (веб)</td><td colspan="2">19.95–49.95 за 2–8 недель, потом 79.95/мес</td><td>как Growth</td><td rowspan="2">нет</td></tr>
<tr><td>Starter / Plus / Growth</td><td class="num">29.95 / 49.95 / 79.95</td><td>—</td><td>2 500 / 5 000 / 10 000 кредитов</td></tr>
<tr><td rowspan="2">Creatify</td><td>Standard</td><td class="num">15</td><td class="num">10</td><td>55 кредитов (~7 видео по 5 с)</td><td rowspan="2">10 кредитов, водяной знак</td></tr>
<tr><td>Pro</td><td class="num">55</td><td class="num">38</td><td>280 кредитов</td></tr>
<tr><td rowspan="3">MakeUGC</td><td>Starter</td><td>не указано</td><td class="num">29</td><td>500 кредитов, своих аватаров нет</td><td rowspan="3">пробный за 1 USD</td></tr>
<tr><td>Growth</td><td>не указано</td><td class="num">39</td><td>1 000 кредитов, 1 свой аватар</td></tr>
<tr><td>Pro</td><td>не указано</td><td class="num">79</td><td>2 000+ кредитов, 3 своих аватара</td></tr>
<tr><td>TopView</td><td>Plus</td><td>не указано</td><td class="num">36</td><td>100 кредитов</td><td>не указано</td></tr>
<tr><td rowspan="2">HeyGen</td><td>Creator</td><td class="num">29</td><td class="num">24</td><td>600 кредитов</td><td rowspan="2">3 видео/мес, водяной знак</td></tr>
<tr><td>Pro</td><td class="num">49</td><td>не указано</td><td>1 000 кредитов</td></tr>
<tr><td>Arcads</td><td>—</td><td colspan="3">на сайте цен нет; по обзорам ~110 за ~10 видео {P}</td><td>пробный есть</td></tr>
<tr><td>AdCreative.ai</td><td>—</td><td colspan="3">страница цен не открылась; по обзорам ~39 {P}</td><td>—</td></tr>
<tr><td>Pippit</td><td>—</td><td colspan="3">цифры на странице неоднозначны — не берём</td><td>да</td></tr></table></div>''')
a(src('страницы цен creatify.ai, makeugc.ai, topview.ai, heygen.com, pippit.ai, главная arcads.ai (30.10); Arcads и AdCreative — сторонние обзоры. Creatify: «помесячно / за год» — наше прочтение зачёркнутой и текущей цены.'))
a('</section>')

# 6 Маркетинг
a('<section><h2>6. Как Zeely привлекает клиентов</h2>')
a('''<div class="tw"><table><tr><th>Выгрузка FB</th><th>Схема</th><th>Спенд 28д, USD</th><th>ROAS</th><th>CPA, USD</th></tr>
<tr><td>#5 · 18.05</td><td>веб</td><td class="num">2 386 849</td><td class="num">1.15</td><td class="num">95</td></tr>
<tr><td>#7.1 · 28.07</td><td>веб</td><td class="num">3 163 211</td><td class="num">1.03</td><td class="num">105</td></tr>
<tr><td>#8 · 28.08</td><td>веб</td><td class="num">2 876 821</td><td class="num">1.10</td><td class="num">99</td></tr>
<tr><td>#9 · 10.10</td><td>веб</td><td class="num">3 222 426</td><td class="num">1.14</td><td class="num">96</td></tr>
<tr><td>#5–#9</td><td>стор</td><td class="num">96 326 – 158 407</td><td class="num">0 – 0.17</td><td>не сравниваем*</td></tr></table></div>''')
a(f'''<ul>
<li><b>Веб-воронка — 97% спенда.</b> Гео на 10.10: США 71%, Великобритания 12%, Канада 6%. CPA ~96–105 USD при доходе 107–119 USD на конверсию за 28 дней — почти в ноль, прибыль даёт продление по 79,95 USD. {D} для цифр, {P} для вывода.</li>
<li><b>* Реклама «прямо в стор»</b> — объявления в Facebook и Instagram, которые ведут сразу на установку в App Store / Google Play, без веб-воронки: скачал бесплатно, пейволл уже внутри. Это ~3% бюджета, ROAS 0–0,17 — не окупается; «конверсия» там — установка, поэтому CPA с вебом не сравниваем. Тексты: «no cost to start», «free for a limited time». {D}</li>
<li><b>TikTok, Google, YouTube</b> — следов платной рекламы не нашли. {N} <b>SEO</b> — блог «Is Zeely a scam?», «Zeely vs Creatify» перехватывает поиск о себе и конкурентах. {D}</li></ul>''')
a('''<h3>О чём реклама (109 объявлений Ad Library, 29.10)</h3><div class="tw"><table><tr><th>Угол</th><th>Объявл.</th><th>Как звучит</th></tr>
<tr><td>Прощай, агентство</td><td class="num">31</td><td>«Say goodbye to marketing agencies — Zeely replaces them. Drop your link — and BOOM!»</td></tr>
<tr><td>Отзыв «я сомневалась»</td><td class="num">30</td><td>«I was skeptical, but then I let AI take over my ads…» — в ротации с 18.09, топ по спенду (CPA 89)</td></tr>
<tr><td>1 фото — 100+ объявлений</td><td class="num">25</td><td>«Upload 1 photo, get 100+ that do»</td></tr>
<tr><td>ИИ-маркетолог 24/7</td><td class="num">9</td><td>«Create months of content in just a few clicks»</td></tr>
<tr><td>«1$ в день», свой аватар</td><td class="num">5</td><td>«AI-automated content for just 1$/day! Create your own AI Avatar»</td></tr></table></div>''')
a(f'''<ul>
<li><b>Реклама от лица людей:</b> страницы бренда переименованы в «Alina Bond» и «Yaroslav Sam» (сооснователи) и персонажей-«клиентов» (Olivia Bennett, Kate Nazary); скидка 70% почти везде; новые объявления каждую неделю. {D}</li>
<li><b>Свежие форматы (spy-сервис, 29.10):</b> текст на футболке «I'm a solo &lt;профессия&gt;» → «Give Zeely 1 photo and get 100+ Reels» — одна идея на десятки ниш; заметка «ищем авторов Amazon KDP для теста»; оффер «Unlimited Seedance 2.5» как ответ на жалобы про кредиты; вебинар к Чёрной пятнице для команд с бюджетом от 50 тыс. USD — выход в B2B. {D} для креативов, {P} для B2B.</li>
<li><b>Связка:</b> креатив и пейволл говорят одно («70% off»), под каждый угол — свой ленд; разрыв — «1$ в день» в рекламе против ~2,7 USD в день после продления. {D}</li>
<li><b>Компания:</b> украинский стартап (2021–2022), 170–200+ сотрудников; Form D от 14.09.2026 — 8,84 млн USD, всего ~10,2 млн USD (PitchBook). {D}</li></ul>''')
a(wide([23, 26]))
a(src('выгрузки FB — reports/fb-kandidaty-itog-28-10.xlsx; Meta Ad Library (29.10); 2 скрина spy-сервиса от Наташи (29.10); zeely.ai, блог; AIN, Vestbee, PitchBook, SEC Form D.'))
a('</section>')

# 7 Что делаем мы
a('<section><h2>7. Что делаем мы</h2>')
a('<p>Сейчас у Zeely-клона есть только лендинг (вариант D, принят 28.10), Коля делает приложение и спрашивал про Higgsfield API.</p>')
a(f'''<h3>Движок генерации — Higgsfield API</h3><ul>
<li><b>Подходит и для тестов, и как основа:</b> 50+ моделей (Kling, Seedance, Wan, свои Soul и Marketing Studio Image), оплата по факту в USD, пополнение от 5 USD, деньги только за успешные генерации. {D}</li>
<li><b>Цены:</b> Kling 2.5 — 0.042 USD/с, Kling 3.0 — 0.112 USD/с, Seedance 2.5 — 0.074 USD/с, картинка — 0.003–0.006 USD. Zeely берёт с клиента за Kling ~0.36 USD/с (45 кредитов по цене Growth) — себестоимость у нас примерно в 3 раза ниже. {D} для ставок, {P} для сравнения (версии моделей разные).</li>
<li><b>Технически:</b> SDK Python и Node, асинхронные задачи с вебхуками, 20 параллельных запросов на старте; результат хранится от 7 дней — сразу копировать к себе; свой персонаж — Soul ID. {D}</li>
<li><b>Проверить до запуска:</b> можно ли перепродавать генерации внутри своего продукта и правила для фото реальных людей — в прочитанном не сказано, нужны Terms of Use. {N}</li></ul>''')
a(src('higgsfield.ai/blog/higgsfield-api (16.09.2026), help-центр Higgsfield, docs.higgsfield.ai (30.10).'))
a('@@POSTING@@')
a(f'''<h3>Что из Zeely делаем и когда</h3><div class="tw"><table><tr><th>Функция</th><th>Когда</th><th>Как</th></tr>
<tr><td>Фото товара + описание → картинки пачкой</td><td>v1</td><td>Higgsfield API; промпт из «рыночного контекста»</td></tr>
<tr><td>Видео с аватаром из библиотеки</td><td>v1</td><td>заранее сгенерированные персонажи + Kling / Seedance</td></tr>
<tr><td>Свой персонаж из селфи</td><td>v1, если позволят Terms</td><td>Soul ID в Higgsfield</td></tr>
<tr><td>Трендовые ролики «повтори»</td><td>v1</td><td>своя подборка референсов + перенос движения</td></tr>
<tr><td>Скачать и «Поделиться»</td><td>v1</td><td>~1 день, без интеграций {P}</td></tr>
<tr><td>Постинг в Instagram и TikTok по расписанию</td><td>v1</td><td>через сервис-посредник (см. выше), 1–2 дня {P}</td></tr>
<tr><td>Запуск рекламы через свой кабинет + комиссия</td><td>после первого трафика</td><td>нужны статус партнёра Meta, свой кабинет, модерация, деньги клиента — зона Кати и Димы; в «≤1 дня» не укладывается {P}</td></tr></table></div>''')
a('''<h3>Что берём и чего не повторяем</h3><ul>
<li><b>Берём в продукт:</b> главный сценарий «фото товара → видео с аватаром» и чек-лист первых шагов (за это хвалят); концепты по нишам и тренды; кредиты поверх подписки и пакеты кредитов.</li>
<li><b>Берём в воронку и рекламу:</b> регистрацию до оплаты, именной промокод и таймер; отзыв-креатив от лица владельца бизнеса и угол «вместо агентства» (CPA 66–89 USD против 96 в среднем); нишевые креативы и формат «текст на футболке», сделанные нашим же генератором; SEO-страницы «X vs Y».</li>
<li><b>Не повторяем:</b> скрытый переход на 79,95 USD, «обязательный» Booster, просьбу о 5★ до первого результата, «1$ в день» в рекламе — это почти половина их 1–2★, возвраты и чарджбеки. Цену продления показываем на пейволле и в письме перед списанием.</li>
<li><b>Проверить у себя:</b> качество видео («видно, что ИИ») и сбои генерации — вторая по частоте жалоба.</li></ul>''')
a('</section>')

a('''<section><h2>Ограничения данных</h2><ul class="small">
<li>Нет внутренних данных Zeely: конверсия воронки, продления, отмены, LTV — не знаем. ROAS и CPA — из выгрузок FB за 28 дней.</li>
<li>Воронка пройдена 22.10.2026 (мобильный вид, en-US); апсейлы после оплаты видны только по отзывам.</li>
<li>Справка Zeely, цены конкурентов и Higgsfield прочитаны 30.10.2026 и могут меняться.</li>
<li>Материалы: references/zeely/ (скринкасты, скриншоты), reports/fb-kandidaty-itog-28-10.xlsx.</li></ul></section>''')
a('</main></body></html>')

html = '\n'.join(H)
html = html.replace('@@POSTING@@', open(os.path.join(S, 'posting-block.html'), encoding='utf-8').read())
open(OUT, 'w', encoding='utf-8').write(html)
print(OUT, os.path.getsize(OUT))
