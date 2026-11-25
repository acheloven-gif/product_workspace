# Robella: ресёрч воронок конкурентов и идеи новых воронок

Задача: [Robella: ресёрч воронок — идеи новых воронок](https://app.clickup.com/t/1249d35truy) (поставила Катя, срок 30.11).
Дата: 25.11.2026. Исполнитель: Наталья (через Claude).

## Коротко

- Нашли 6 конкурентов с веб-воронками в нише «стилист / гардероб / цветотип», 5 прошли до пейвола: Dressly, Mosso, K-Styler, Inspoy (Stylix), Myswatches. Essembl ведёт с лендинга в App Store, квиза нет.
- **Первый экран.** У 3 из 5 квиз-воронок (Dressly, Mosso, K-Styler) первый экран выглядит одинаково: обещание, рейтинг и число пользователей, а под ними сразу кнопки выбора возраста. Отдельного экрана загрузки или вступления нет, первый клик уже отвечает на вопрос. У Robella два первых экрана — загрузка (intro) и вопрос про возраст, на них уходят 83%. Подробнее в «Выводах для Robella».
- **Нарратив.** Два варианта:
  - цвет → фигура → образ жизни → «план стиля на 4–8 недель» (Mosso, K-Styler);
  - боль онлайн-покупок (возвраты, «сюрпризы» в заказе) → посадка → цвет → капсула с ссылками на покупки (Dressly).
  Внутри квиза везде прогресс-бары: «Phase 1 Completed», «77% match → 89%», промежуточные экраны-обещания.
- **Оффер.** У Mosso, K-Styler и Dressly — план на 4/8/12/16/24 недели. Первый период со скидкой 66–70% через промокод в URL, скретч-карта или «скидка Чёрной пятницы» и таймер 10–15 минут. Затем продление по полной цене: $49.99–99.99 за период. У Inspoy — триал $1 на 3 дня, затем $39.99/мес (так же устроен US-оффер Robella). Myswatches — разовая покупка $29.99/$39.99 и физическая карта цветов.
- **Масштаб рекламы.** Больше всего свежей рекламы у Inspoy: 21 из 27 объявлений в выборке запущены в ноябре. Mosso рекламируется с июня по ноябрь на EN/ES/PT. Рекламу Dressly в Meta Ad Library по ключевым словам найти не удалось.

## Как собирали

- Реклама: Meta Ad Library, активные объявления, поиск по ключевым словам (ai stylist, color analysis, capsule wardrobe, color palette quiz, style quiz app и др.) и по названиям конкурентов, 25.11.2026. Из объявлений брали ссылки на воронки, тексты и даты запуска. Tyver API не пустил (Not authenticated), поэтому выгрузку Tyver не делали.
- Воронки: прошли каждую сами в браузере (мобильный профиль iPhone, язык EN), выбирали «женщина, 35–44». Почта тестовая (yopmail). Оплату не делали, фото не загружали: везде был шаг «пропустить».
- Ограничения:
  - по одному проходу на воронку; цены могут зависеть от гео, времени и промо — сейчас идёт Чёрная пятница;
  - IP-гео прохода не контролировали;
  - число результатов в Ad Library — по ключевому слову, в него попадают посторонние объявления: это ориентир, а не точное число объявлений бренда;
  - гео показов не смотрели, видны только языки объявлений.

## Конкуренты

### 1. Dressly — капсульный гардероб через «боль онлайн-покупок»

- Воронка: https://quiz.dressly.world/en/new-general-smart-plan-hp-4w-2 (ссылка «Take 1-minute quiz» со страницы входа account.dressly.world).
- Реклама: активных объявлений Dressly в Ad Library по запросам «Dressly» и «dressly.world» не нашли. Сторонний разбор web2wave («198 000 объявлений, 87,6% ведут на quiz.dressly.world») прочитать не удалось: сайт закрыт сетью, цифры видны только в выдаче поиска — **Не знаем**, актуальны ли.
- Первые экраны:
  1. «4.4 out of 5 · 1 000 000+ users · **Dress effortlessly** · Simplify your wardrobe with a personalized plan that finds perfect outfits for you · Pass the quiz to personalize your subscription» + кнопки **Age: 18–34 / 35–44 / 45–54 / 55+**.
  2. «1 000 000+ people use Dressly to shop smarter · “Your best outfit isn’t new — it’s just finally worn right”» + «featured in» (логотипы СМИ).
  3. «How satisfied are you with your wardrobe?»
  4. «Where does most of your shopping happen?»
  5. «How often do you update your wardrobe?» → «How much do you trust online shopping?» → экран «Shop online with certainty».
- Нарратив — 5 блоков, всего около 30 экранов до почты:
  - «Shopping Experience»: сюрпризы в заказах, вещи разваливаются после двух стирок, возвраты;
  - «Look & Fit»: тип фигуры;
  - «Color»: глаза, кожа, волосы;
  - «Personal Style»: поводы, стиль, «nothing to wear»;
  - «Final Steps»: главная цель.
  Между блоками — экраны-обещания: «No more 'return' headaches», «Colors that make you glow», «Stop blending in». Затем «Your Personalized Wardrobe Upgrade Plan… by January 2027», загрузка с отзывами, почта, имя, скретч-карта «70%».
- Пейвол: промокод в URL, таймер 10 минут.

  | План | Сейчас | Потом | В день |
  |---|---|---|---|
  | 4 недели (MOST POPULAR) | $15.19 | $49.99 каждые 4 недели | $0.54 |
  | 12 недель | $36.99 | $99.99 каждые 12 недель | $0.44 |
  | 24 недели | $59.99 | $119.99 каждые 24 недели | $0.36 |

  Что внутри плана: капсула из 10 вещей, 30+ образов, виртуальная примерка («See it on you first»), список покупок со ссылками. Юрлицо: Solwita Corp (Лас-Вегас).

### 2. Mosso — «AI-стилист, который тебя понимает», капсула и цвет

- Воронки из рекламы:
  - https://mosso.ai/mid/v3-4w/quiz (перенаправляет на `/en/mid/transform-my-style-bmc/quiz`);
  - `/mid/8wupfreebupd2v1-pp/quiz`;
  - `/mid/8wupfreeblgl-amz/quiz`;
  - `/es/mid/armario-capsula/quiz`;
  - `/pt/mid/8wupfreebupd2v1-v4sub1skipleg/quiz`.
- Реклама: объявления идут от страниц-«персон» (Emma Quince, Grace Collins, Rose Hunter, Olivia Reyes, Vanessa Carvalho) в стиле UGC. Тексты:
  - «✨ Meet your AI stylist who actually gets you. Mosso learns your style, your lifestyle, and what makes you feel amazing…»;
  - «Meet the AI stylist that turns your closet into the ultimate capsule wardrobe».
  Языки EN/ES/PT. Даты запуска в выборке — июнь–ноябрь 2026, из них 6 объявлений запущены в ноябре и 5 в октябре.
- Первые экраны:
  1. «Learn which colors and shapes flatter you most» (загрузка квиза) → «**Confidence and style at every stage** · To unlock your personalized subscription plan, select your age group» + **18–29 / 30–39 / 40–49 / 50+**.
  2. «120,000+ women found their signature style with Mosso · 4.8/5 out of 1743 reviews».
  3. «What are your main goals?» (фигура / цвета / собраться за 5 минут / не покупать лишнего).
  4. «Imagine getting dressed in under 5 minutes · We've analyzed 2 million data points…».
  5. Глаза → волосы → тон кожи → подтон → «33% · Phase 1 Completed · Your best colors are set».
- Нарратив — 3 фазы с прогрессом:
  - цвета;
  - фигура и посадка: рост, вес, что подчеркнуть, проблемы, слайдер «какую долю вещей носите»;
  - образ жизни и бюджет: город и климат, день, где покупаете, бюджет, свайп-карточки «Would you wear this?».
  Дальше идут вопросы во время загрузки («Do you ever feel like certain outfits make you look older than you are?»), предложение сделать фото лица (можно пропустить), почта, скретч-карта «Black Friday 70%».
- Пейвол: «Your 28-Day Plan is Ready in MOSSO App», цветотип показан, промокод в URL, таймер 14 минут.

  | План | Сейчас | Цена без скидки |
  |---|---|---|
  | 4 недели | $19.99 | $59.99 |
  | 8 недель (MOST POPULAR) | $29.99 | $99.99 |
  | 16 недель | $49.99 | $149.99 |

  Продление по полной цене: для 8-недельного плана — $99.99 каждые 8 недель. Подарок: e-book «The Ultimate Capsule Guide».

### 3. K-Styler — «корейский метод: измерено, а не угадано»

- Воронка: https://quiz.mykstyler.com/quizv1-sgo, конструктор web2wave. Пейвол: `/paywall/plan-offer-v1-sgo`.
- Реклама: страница «Soojin Yoon 윤수진 — Korean Personal Style Expert». Текст:
  > «Tired of buying clothes that looked amazing on the hanger — and terrible on you? … Two quick scans — body and face — measure your skeletal frame and personal coloring… No quiz. No opinion. Measured. … the same Korean image-consulting method behind a $500/hr Seoul practice — from your phone.»

  Запуски в выборке — июль–ноябрь 2026, больше всего в сентябре. По запросу «K-Styler» в Ad Library около 820 результатов, но в выборке есть посторонние объявления.
- Первые экраны:
  1. «4.6 out of 5 · 114k users · 3-MINUTE QUIZ · **The Korean styling method · Built for your body** · Select your age to discover the colors and shapes that flatter you» + **Age: 18–34 / 35–44 / 45–54 / 55+**.
  2. «114,000+ women use K-Styler to dress for the body and coloring they actually have · “You were never hard to dress. You were just never measured.”».
  3. «How does getting dressed usually make you feel?» (Confident / Unsure / Tired / Overwhelmed).
  4. «What’s your main goal?».
  5. «Which styles do you like?» → «Imagine getting dressed in under 5 minutes».
- Нарратив: вопросы почти дословно совпадают с Mosso, но порядок другой — сначала чувства и цели, потом поведение, сложности, фигура и цвет. Между ними экраны с позиционированием:
  - «It was never you»;
  - «Measured, not guessed»;
  - «Why not just ask ChatGPT?»;
  - «Western color systems mistype women of color… The Korean method was built to read every undertone».
  Дальше: «How fast do you want results? 4/8/16 weeks» → график плана «by January 2027» → загрузка с отзывами → почта.
- Пейвол: промокод «70%» и таймер 10 минут. 4-недельный план: $14.99 вместо $49.99 ($0.54 в день), затем $49.99 каждые 4 недели. Подарок: e-book, гарантия возврата 28 дней. Блок «Meet the founder» (Soojin Yoon, AICI, Сеул). Юрлицо: Zenith Labs Limited.

### 4. Inspoy (Stylix) — заход через примерку стрижки, квиз про стиль

- Воронка: https://sub.stylix.app/quiz-pp?mode=hairstyle&creative_topic=hairstyle
- Реклама: несколько страниц — «Stylist: Palette Finder», «Stylist: Outfit Maker with Olivia Carter», «Style Better Daily», «Inspoy Hair Studio». Хук в рекламе — примерка стрижки по фото:
  - «Thinking about a new haircut? See yourself with different hairstyles before making a change. Upload a photo…»;
  - «See Your Next Haircut Before the Salon».

  Языки EN/PT/JA/AR. В выборке по запросу «Inspoy» 27 объявлений, 21 из них запущено в ноябре, 6 — в октябре. Всего в Ad Library около 310–340 результатов.
- Первые экраны:
  1. «**Look and feel your best in clothes that flatter you** · 100 000+ women changed their lives with Inspoy · Light Summer · Best colors · Start».
  2. «Know which colors and styles work for you · Answer a few questions…».
  3. «How old are you?» (6 вариантов).
  4. «With Inspoy, I hope to…» (выбрать топ-3).
  5. «Imagine a closet where every piece sparks joy».
- Нарратив: 17 вопросов — стиль, гардероб, рост и вес, фигура, что подчеркнуть, что скорректировать, климат, образ жизни, бренды, бюджет, эстетика. По ходу растёт «совпадение» гида со стилем: «51% matches» → «77% match unlocked» → «89% done — let's unlock your color power». Затем скан лица (можно пропустить) и анализ с лентой «112 people unlocked… in the last hour». Итог — «Personal summary, 97% match»: цветотип и фигура показаны, палитра и образы закрыты («Unlock»). Потом почта.
- Пейвол: промокод AUTUMN_2026. Варианты триала:
  - 3 дня за $1 (RECOMMENDED);
  - 1 неделя за $5.49;
  - 4 недели за $9.99.

  После 3-дневного триала — $39.99 в месяц. Функции: цветотип, цифровой гардероб, виртуальная примерка, подборка покупок, чат с AI-стилистом. Гарантия возврата 14 дней. Юрлицо: Digital Solutions LLC (Аврора, Колорадо).

### 5. Myswatches — короткий квиз и разовая покупка карты цветов

- Воронка: https://myswatchesquiz.netlify.app/
- Реклама: страница Myswatches, 23 объявления в выборке, запуски в октябре и ноябре. Текст:
  > «For 20 YEARS I bought clothes that looked good in store, but never suited me. Turns out I was wearing the wrong colors my entire life… Unlock 50+ of your Power Colors… Join 10,000+ women… Take our quiz».
- Первые экраны:
  1. «BLACK FRIDAY WEEK DEAL · **Find out exactly which colors were made for you** · 4.9/5 · Trusted by 20,000+ women» + три входа: «Find My Colors + get cards» / «Just Get Cards» / «I know my season».
  2. Цвет глаз (1/8).
  3. Цвет волос.
  4. Тон кожи.
  5. Металл украшений → подтон → возраст → фото (можно пропустить).
- Нарратив: 8 вопросов. Потом «проверка ответов», анимация «подбора сезона» и результат с отзывами «до / после». Таблица: консультация вживую $200–600 против $39.99.
- Оффер: **разовая покупка, не подписка**.
  - Basic — $29.99: результат за 48 часов, 20 цветов;
  - Premium — $39.99: результат за 24 часа, 50+ оттенков, цвета-антиподы, физическая карта, книга образов, бонусы Чёрной пятницы.

  Проверку делает человек (так заявлено). Гарантия возврата 30 дней.

### 6. Essembl — гардероб из своих вещей (лендинг → App Store)

- Ссылка из рекламы: https://try.essembl.com/
- Реклама: страница Valentinessembl, около 240 результатов в Ad Library, запуски июль–октябрь 2026. Аудитория в основном мужская (#menswear). Тексты:
  - «Turn your wardrobe into outfits», «No more “I have nothing to wear”»;
  - «snap the piece and Essembl tells you if it actually works with what you already own».
- Первый экран: «SOUND FAMILIAR? **200 clothes. Nothing to wear.** · 4.5 from 4.6K App Store ratings · 2.4M users», демо «Scan → Wardrobe → Outfit», кнопка «Show me what to wear» (в App Store) или «continue on the web» (вход через Apple / Google / Email). Квиза и веб-пейвола нет, поэтому на вебе цены не видны.

## Сводка офферов

| Конкурент | Вход | Длина до почты | Оффер на пейволе | Продление |
|---|---|---|---|---|
| Dressly | возраст на 1-м экране | ~30 экранов | 4 нед. $15.19 / 12 нед. $36.99 / 24 нед. $59.99 | $49.99 / $99.99 / $119.99 за период |
| Mosso | возраст на 1-м экране | ~30 экранов | 4 нед. $19.99 / **8 нед. $29.99** / 16 нед. $49.99 | $59.99 / $99.99 / $149.99 за период |
| K-Styler | возраст на 1-м экране | ~32 экрана | 4 нед. $14.99 | $49.99 / 4 нед. |
| Inspoy | лендинг + Start, возраст на 3-м | ~25 экранов | триал 3 дня $1 / 1 нед. $5.49 / 4 нед. $9.99 | $39.99 / мес |
| Myswatches | лендинг + 3 входа | 8 вопросов | разово $29.99 / $39.99 | нет |
| Robella (US, для сравнения) | загрузка (intro) → возраст | ~30 экранов | триал $1 | $39.90 / мес |

Robella — по разбору от 20.11 и карточке Robella (воронка США отдана в трафик 11.11).

## Выводы для Robella

- **Видно в данных.** У трёх конкурентов, у которых больше всего свежей рекламы в нише, первый экран совмещает обещание, социальное доказательство и вопрос про возраст. Пользователь начинает квиз первым же нажатием. У Robella перед возрастом стоит отдельный экран загрузки (intro), а на первых двух экранах теряется 83% (у FoxIQ и Azora — 40–45%).
- **Предположение.** Если убрать отдельный экран intro и вынести вопрос про возраст на первый экран вместе с обещанием и рейтингом, просадка на входе уменьшится. Это не сокращение квиза: вопросы остаются, меняется только первый экран. Просадка на этом шаге значительная, поэтому правка подходит под исключение из правила «квиз не сокращаем». Решение — за Катей и Димой.
- **Не знаем.** Какие из этих воронок окупаются. Конверсий и расходов конкурентов в открытых данных нет.

## Идеи новых воронок для Robella

Все идеи — гипотезы для обсуждения с Катей и Димой. Цены и воронки выбирают Дима и Никита.

1. **«Твой сезон цвета за 2 минуты»** (цвет первым, как Mosso / K-Styler / Myswatches)
   - Заход: реклама «Носила не те цвета 20 лет» / «Find the colors that make you glow».
   - Первые экраны:
     1. обещание + рейтинг + возраст кнопками;
     2. социальное доказательство;
     3. глаза → волосы → кожа → подтон с картинками;
     4. промежуточный результат «Your best colors are set — 33%»;
     5. дальше фигура и стиль.
   - Оффер: цветотип в итоге показан, палитра и образы закрыты, план на 4 недели.

2. **«Капсула из того, что уже есть в шкафу»** (как Dressly / Mosso / Essembl)
   - Заход: «200 вещей — и нечего надеть», «носишь 20% гардероба».
   - Первые экраны:
     1. обещание + возраст;
     2. «Какую долю вещей вы носите?» (слайдер);
     3. «Как часто нечего надеть?»;
     4. сложности с гардеробом;
     5. экран-обещание «Get dressed in 5 minutes».
   - Оффер: «28-дневный капсульный план» + e-book в подарок, ссылки на покупки.

3. **«Покупай онлайн без возвратов»** (нарратив Dressly)
   - Заход: «Заказала — не подошло — возврат? Узнай свою посадку и цвета до покупки».
   - Первые экраны:
     1. обещание + возраст;
     2. где покупаете;
     3. как часто «сюрпризы» в заказе;
     4. возвраты;
     5. экран «No more return headaches».
   - Оффер: план + проверка вещи перед покупкой — у Robella есть примерка, это совпадает с обещанием.

4. **«Примерь образ / стрижку по одному фото»** (заход Inspoy)
   - Заход: визуальная примерка в рекламе («See it on you before you buy / before the salon»).
   - Первые экраны:
     1. лендинг с примером «до / после» + Start;
     2. «Что хотите узнать?» (выбрать топ-3);
     3. возраст;
     4. дальше квиз с растущим «% совпадения».
   - Оффер: триал $1 на 3 дня — у Robella такая же схема, меняется только заход.
   - Что важно: заход работает, только если примерка в приложении Robella показывает хороший результат. Нужна продуктовая проверка.

5. **«Измерено, а не угадано»** (позиционирование K-Styler)
   - Заход: эксперт или метод («цвет и фигура по скану, а не по мнению», «почему не спросить ChatGPT»).
   - Первые экраны:
     1. обещание + возраст;
     2. «You were never hard to dress. You were just never measured»;
     3. как вы себя чувствуете, когда одеваетесь;
     4. главная цель;
     5. экран против «советов наугад».
   - Оффер: план на 4 недели со скидкой по промокоду и гарантией возврата.
   - Нужно лицо или эксперт для рекламы. Метод нельзя приписывать реальной практике, которой нет.

## Пройти руками (не открылось из среды Claude)

- Воронку Robella https://f.robella.app/ai-stylist браузер в среде Claude не открыл (ошибка соединения). Сравнение первых экранов — по разбору от 20.11.
- Essembl: веб-вход через аккаунт и цены в App Store (https://try.essembl.com/ → App Store).
- Разбор Dressly от web2wave: https://www.web2wave.com/post/dresslys-meta-ad-strategy-198-000-ads-27-creatives
