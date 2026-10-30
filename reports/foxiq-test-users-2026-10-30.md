# FoxIQ: список тестовых пользователей (PostHog), 30.10.2026

Задача: [Получить полный список исключённых тестовых пользователей и проверить, что они действительно исключены](https://app.clickup.com/t/1249d35ky7q).
Источник — PostHog, `project` = `foxiq` и `foxiq_ff`, события с 01.10.2026 по 30.10.2026 (UTC). Отбор — фильтр тестовых адресов из `playbook/posthog.md`.

**Итого: 598 тестовых адресов, 30 основных аккаунтов.** Полный список по адресам — `reports/foxiq-test-users-2026-10-30.csv`.

Правила отбора: адрес с `+`; домены `gox-media.com`, `yandex.ru`, `example.com`, `mailinator.com`; `test` в адресе; адреса сотрудников (k.k.tarasova, nikitos.gura, dariaivanova, eevakenn, nedvedyea, kkk@gmail.com, myskillhouse2020@gmail.com).

| Основной аккаунт | Адресов (вариантов) | Событий | project | Первое | Последнее |
|---|---|---|---|---|---|
| nedvedyea@gmail.com | 392 | 3254 | foxiq, foxiq_ff | 2026-10-01 | 2026-10-28 |
| eevakenn@gmail.com | 107 | 544 | foxiq, foxiq_ff | 2026-10-01 | 2026-10-27 |
| k.k.tarasova0404@gmail.com | 39 | 415 | foxiq, foxiq_ff | 2026-10-01 | 2026-10-27 |
| dariaivanova8245@gmail.com | 14 | 113 | foxiq, foxiq_ff | 2026-10-02 | 2026-10-28 |
| nikitos.gura99@gmail.com | 14 | 51 | foxiq | 2026-10-01 | 2026-10-10 |
| hdw@gox-media.com | 4 | 317 | foxiq, foxiq_ff | 2026-10-01 | 2026-10-27 |
| themaximusversus@gmail.com | 4 | 221 | foxiq, foxiq_ff | 2026-10-27 | 2026-10-27 |
| neevedyea@gmail.com | 2 | 7 | foxiq | 2026-10-01 | 2026-10-08 |
| test@example.com | 1 | 66 | foxiq, foxiq_ff | 2026-10-28 | 2026-10-28 |
| qa-preview-pastlife-en@example.com | 1 | 1 | foxiq | 2026-10-09 | 2026-10-09 |
| qa-preview-palm-pt@example.com | 1 | 1 | foxiq | 2026-10-09 | 2026-10-09 |
| qa-preview-soulmate-es@example.com | 1 | 1 | foxiq | 2026-10-09 | 2026-10-09 |
| qa-preview-palm-multi@example.com | 1 | 1 | foxiq | 2026-10-09 | 2026-10-09 |
| dariaivanovadaria@yandex.ru | 1 | 104 | foxiq, foxiq_ff | 2026-10-01 | 2026-10-28 |
| krippsi@yandex.ru | 1 | 2 | foxiq | 2026-10-01 | 2026-10-01 |
| j.d@gox-media.com | 1 | 2 | foxiq | 2026-10-06 | 2026-10-06 |
| funnel.review.m4817@mailinator.com | 1 | 142 | foxiq, foxiq_ff | 2026-10-20 | 2026-10-20 |
| funnel.review.f2963@mailinator.com | 1 | 7 | foxiq, foxiq_ff | 2026-10-20 | 2026-10-20 |
| gshtest@gmail.com | 1 | 2 | foxiq | 2026-10-10 | 2026-10-10 |
| nedvedyea@gmsil.com | 1 | 8 | foxiq | 2026-10-09 | 2026-10-09 |
| nedvedyea@gmaio.com | 1 | 3 | foxiq | 2026-10-02 | 2026-10-02 |
| nedvedyed@gmail.com | 1 | 3 | foxiq | 2026-10-06 | 2026-10-06 |
| nedvedyea-@gmail.com | 1 | 3 | foxiq | 2026-10-02 | 2026-10-02 |
| k.k.tarasova0404@gmai.com | 1 | 2 | foxiq | 2026-10-05 | 2026-10-05 |
| k.k.tarasova0403@gmail.com | 1 | 2 | foxiq | 2026-10-06 | 2026-10-06 |
| funnel-test@azora-astro.com | 1 | 1 | foxiq | 2026-10-01 | 2026-10-01 |
| medvedyea@gmail.com | 1 | 1 | foxiq | 2026-10-09 | 2026-10-09 |
| kkk@gmail.com | 1 | 10 | foxiq | 2026-10-01 | 2026-10-10 |
| myskillhouse2020@gmail.com | 1 | 4 | foxiq | 2026-10-05 | 2026-10-09 |
| nedvedyea4543hh@gmail.com | 1 | 2 | foxiq | 2026-10-09 | 2026-10-09 |

Проверка: адресов, похожих на тестовые (опечатки в адресах сотрудников, qa, review, demo и т.п.), которые фильтр пропускает, за этот период не найдено.
Не попадают в список: анонимные пользователи без почты; проходы воронки с метками-пустышками (`utm_campaign` = `88888888` / `{campaignid}`, 3 человека за октябрь) — они исключаются отдельным условием; 1 покупатель под вопросом (Армения, 28.10) — ждёт подтверждения команды.
