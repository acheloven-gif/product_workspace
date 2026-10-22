# Zeely — разбор конкурента

Задача: [Zeely: разобрать воронку и приложение конкурента, решить, берём ли нишу](https://app.clickup.com/t/1249d35j0t1).
Статус разбора: пройдена воронка (22.10.2026). Приложение, реклама, оценка копии и риски — следующим шагом.

## Ссылки

- Воронка: https://zeely.ai/start/ai-admaker-2/
- App Store: https://apps.apple.com/us/app/zeely-ai-marketing-platform/id1586861768
- Google Play: https://play.google.com/store/apps/details?id=app.zeely.android

## 1. Воронка (web, до пейволла)

Прохождение 22.10.2026: мобильный вид (iPhone), локаль en-US, тестовая почта.
Материалы — `references/zeely/funnel/`:
- `path-ads-and-social/` — скриншоты всех шагов, ветка «реклама + соцсети» (самая длинная);
- `path-paid-ads-only/` — экраны, которые отличаются в ветке «только реклама»;
- `screencast-ads-and-social.webm`, `screencast-paid-ads-only.webm` — скринкасты обеих веток.

### Общая схема

~30 экранов: квиз (~17 вопросов) → вставки с обещаниями и отзывами → сводка профиля → «загрузка» →
регистрация (email + пароль) → имя → график роста → что входит → сравнение «без / с Zeely» → пейволл → чекаут.
Регистрация с паролем стоит **до** оплаты: аккаунт создаётся в воронке, после оплаты человек сразу входит в продукт
(в URL пейволла есть `funnelLoginToken`).

Ветвление — по ответу на вопрос «Where do you want to promote your business?»:
- Social media → блок про соцсети;
- Paid ads → блок про рекламу;
- Both → оба блока (самая длинная ветка).
Первый вопрос («Start advertising» / «Level up my ads») на путь не влияет.

### Экраны по порядку (ветка Both)

| # | Экран | Содержание |
|---|---|---|
| 1 | Цель | What's your goal? — Start advertising / Level up my ads |
| 2 | Роль | Small business owner, Company decision-maker, Side hustler / solopreneur, Content creator, In-house marketer, Marketing agency, Freelancer / consultant, Other |
| 3 | Размер компании | Just me … More than 100 employees |
| 4 | Что продвигаем | Products / Digital products / Services / Mix |
| 5 | Где представлен бизнес (мультивыбор) | Shopify, Instagram or Facebook, My own website, Etsy, TikTok, Amazon, eBay, Other, Skip |
| 6 | Отзыв | «Helps me consistently promote my products» |
| 7 | Отрасль | ~80 вариантов + поле своего ответа |
| 8 | Каналы (мультивыбор) | Instagram/Facebook, TikTok, Google, YouTube, LinkedIn, Other, Let Zeely AI decide |
| 9 | Опыт продвижения | No experience … Expert |
| 10 | Как продвигать (развилка) | Social media / Paid ads / Both / No plan yet — Zeely AI can decide |
| 11 | Обещание | Both: «helps businesses grow faster — creates both social posts and ads»; Paid ads: «creates your ads and guides you through campaign setup — step by step» |
| 12 | Запускали рекламу? | Yes / Not yet *(ветка ads)* |
| 13 | Главная сложность рекламы | Knowing where to start, Understanding why my ads don't work, Creating ad visuals and copy, Setting up Ads Manager, Finding the time, Other *(ветка ads)* |
| 14 | Бюджет на маркетинг в месяц | $0 … More than $50,000 |
| 15 | Утверждение | «My budget's tight, so I need ads that actually work» (шкала согласия) *(ветка ads)* |
| 16 | Отзыв | «The ease of launching campaigns is real» *(ветка ads)* |
| 17 | Цель в соцсетях (мультивыбор) | Get noticed, Save time, Post consistently, Never run out of ideas, Keep up with trends, Understand what's working *(ветка social)* |
| 18 | Обещание | «Go viral on socials and grow your business» *(ветка social)* |
| 19 | Отзыв | «Got my book promoted on social media» *(ветка social)* |
| 20 | Часы на соцсети в день | <1 … 5+ *(ветка social)* |
| 21 | Утверждение | «Running socials feels like a full-time job on top of my real one» *(ветка social)* |
| 22 | Активность под постами | Low … Haven't posted yet *(ветка social)* |
| 23 | Обещание | «Use AI to run your socials and grow your business organically» *(ветка social)* |
| 24 | Опыт с визуальным контентом | never … as part of my job |
| 25 | Обещание | «Create launch-ready social posts» |
| 26 | Время на маркетинг в неделю | <5 … 15+ часов |
| 27 | Утверждение | «I don't have the budget to hire marketers or freelancers» |
| 28 | Обещание | «Just 15 minutes a day… Save 15+ hours a week» |
| 29 | Сводка профиля | Business Growth Potential: High; отрасль, канал, бюджет, опыт; «AI adoption could boost profitability by up to 45%» |
| 30 | Загрузка | «Setting up your business profile & toolkit» |
| 31 | Регистрация | email → подтверждение email → пароль (≥8 символов); ссылки на Terms, Privacy, Arbitration agreement, Permitted Use Policy |
| 32 | Имя | What is your name? |
| 33 | График роста | «{Имя}, this is your growth trajectory» — кривая «You are here → Your goal», без цифр |
| 34 | Отзыв | «It's an easy way to compete with giants» |
| 35 | Что входит | Online Ads Agent, Social Media AI Agent, AI-Generated Ads (статика и видео), Hyper-Realistic AI Avatars, Store Integration; + Analytics, AI features |
| 36 | Сравнение | без Zeely / с Zeely |
| 37 | Пейволл | см. ниже |
| 38 | Чекаут | см. ниже |

Замечание: в сводке бюджет показан как $0 даже после выбора «Up to $500» — сводка, скорее всего, частично шаблонная
(Предположение, проверено на одном прохождении).

### Пейволл и цены

- Заголовок «Get your subscription with up to 70% off», «Your promo code is applied!» — промокод с именем пользователя
  (`mila_oct26`), таймер 10 минут.
- Тарифы (первый период → потом):

| План | Первый период | Потом |
|---|---|---|
| 2-Week Plan | $19.95 за 2 недели | $39.95 |
| 4-Week Plan (Most Popular, по умолчанию) | $29.95 за 4 недели | $79.95 каждый месяц |
| 8-Week Plan | $49.95 за 8 недель | $159.95 |

- Ниже: список функций, отзыв, FAQ (что создаёт, подходит ли для услуг, нужен ли опыт, как войти, легко ли отменить).
- Чекаут: Solidgate (платёжная форма), Apple Pay, PayPal, карта. Текст: «$29.95 today, and $79.95 every month thereafter until you cancel»;
  отмена в аккаунте или через support@zeely.app.
- Триала нет: сразу платный вводный период.
- Апсейлы после оплаты не видны: дальше пейволла без оплаты не пройти.

### Что воронка продаёт

- Аудитория — владелец малого бизнеса без опыта и без бюджета на маркетолога («can't afford to retain an agency»).
- Обещание — «маркетинг за 15 минут в день»: ИИ делает посты и рекламу (видео, аватары) и помогает запустить кампании.
- Основная механика квиза — персонализация (отрасль, каналы, бюджет), но реальная «персональная» выдача в воронке
  ограничивается сводкой и графиком без цифр.

## 2. Приложение

_Следующий шаг._

## 3. Сложность копии

_Следующий шаг._

## 4. Реклама конкурента

_Следующий шаг._

## 5. Риски

_Следующий шаг._

## Вывод

_После разделов 2–5._
