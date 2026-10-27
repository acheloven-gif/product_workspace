# FoxIQ: тексты писем для возврата пользователей (черновик)

2026-10-27. Черновики на английском по тезисам из `foxiq/emails.md` (логика согласована Катей).
Для реализации: [FoxIQ: письма для возврата пользователей — реализация](https://app.clickup.com/t/1249d35jzae) (Даня).
Письма A1–A3, B1–B4, C1–C3. C4 (повторения) — позже, после доработок под воронку memoryOS.

## Общее для всех писем

**Тон.** Дружелюбно, коротко, без давления и без обещаний роста IQ. Одна мысль, одна кнопка.

**Отправитель:** `FoxIQ <hello@foxiq.app>` (адрес отправителя уточнить: домен в Brevo уже работает). Ответы — на `support@foxiq.app`.

**Переменные**

| Переменная | Что подставляем | Если пусто |
|---|---|---|
| `{name}` | Имя пользователя | Обращение без имени: «Hi there,» |
| `{button_url}` | Ссылка со входом на нужный экран (+ `email_id`, `send_id`) | — |
| `{unsubscribe_url}` | Ссылка отписки Brevo | — |
| `{streak_days}` | Текущая серия, дней | — |
| `{days_away}` | Сколько дней без активности | — |
| `{next_lesson}` | Название следующего урока трека (например, «Hold the pattern») | «your next lesson» |
| `{next_category}` | Категория следующего урока (Memory, Logic…) | убрать фразу |
| `{active_days}` | Дней с активностью за неделю (1–7) | — |
| `{games_played}` | Игр сыграно за неделю | — |
| `{xp_week}` | XP за неделю | — |
| `{top_category}` | Категория с наибольшим числом игр за неделю | убрать строку |
| `{level_ups}` | Сколько уровней категорий выросло за неделю | убрать строку, если 0 |

**Футер (во всех письмах)**

> You're receiving this because you have a FoxIQ account.
> Questions? Just reply or write to support@foxiq.app.
> [Unsubscribe]({unsubscribe_url}) · FoxIQ, {company_address}

`{company_address}` — почтовый адрес юрлица в футере обязателен для рассылок в США (CAN-SPAM); подставить, когда будет юрлицо.

---

## A. Оплатил, в приложение не заходил

### A1 — через 1 час после оплаты

- **Subject:** Your FoxIQ results are ready
- **Preheader:** One tap to sign in — no password needed.
- **Body:**
  > Hi {name},
  >
  > Your FoxIQ account is set up and your results are waiting for you. Sign in with one tap — no password needed — and take a look.
- **Button:** See my results → экран результата

### A2 — через 1 день

- **Subject:** Your first 5-minute workout is waiting
- **Preheader:** Short games, one small step to start your streak.
- **Body:**
  > Hi {name},
  >
  > Your first daily workout is ready: a few short brain games, about 5 minutes. Finish it today and you'll have day one of your streak.
- **Button:** Start workout → тренировка дня

### A3 — через 3 дня

- **Subject:** Your FoxIQ access is ready whenever you are
- **Preheader:** Everything is saved — start in 5 minutes.
- **Body:**
  > Hi {name},
  >
  > Your access is active and everything is saved for you. Whenever you have 5 minutes, open FoxIQ and play today's workout — it's a good way to start.
- **Button:** Open FoxIQ → главная

Примечание: тема A3 изменена против таблицы («You haven't started yet — your plan is saved» → без упрёка «haven't started»).

---

## B. Заходил, потом пропал

### B1 — 2 дня без активности

- **Subject:** Today's workout is open
- **Preheader:** A fresh set of games, about 5 minutes.
- **Body:**
  > Hi {name},
  >
  > A new daily workout is ready for you — a fresh set of short games, about 5 minutes. Jump in whenever it suits you.
- **Button:** Start workout → тренировка дня

### B2 — 4 дня без активности

- **Subject:** Your next lesson is unlocked
- **Preheader:** Pick up right where you left off.
- **Body:**
  > Hi {name},
  >
  > Your next lesson, **{next_lesson}** in {next_category}, is open. Pick up right where you left off — it takes just a few minutes.
- **Button:** Continue → следующий урок трека

Примечание: тема «Your next level is unlocked» заменена на «lesson» — в треке это урок.

### B3 — 8 дней без активности

- **Subject:** {days_away} days off — pick up where you left off
- **Preheader:** Your progress and level are saved.
- **Body:**
  > Hi {name},
  >
  > Your progress, XP and level are all saved. Coming back takes about 5 minutes — one workout and you're back on track.
- **Button:** Continue → главная

### B4 — после паузы, ~15–16 дней

- **Subject:** We've saved your progress
- **Preheader:** We'll stop reminding you — it's all here when you're ready.
- **Body:**
  > Hi {name},
  >
  > We won't keep filling your inbox. Your progress is saved, and FoxIQ will be here whenever you want to come back.
- **Button:** Open FoxIQ → главная

---

## C. Активен

### C1 — серия под угрозой (21:00 UTC)

- **Subject:** Your {streak_days}-day streak ends tonight
- **Preheader:** One quick game is enough to keep it.
- **Body:**
  > Hi {name},
  >
  > You've trained {streak_days} days in a row. One quick game before midnight (UTC) keeps your streak going.
- **Button:** Save my streak → тренировка дня

### C2 — тренировка дня (первые 7 дней)

- **Subject:** Today's workout is ready
- **Preheader:** 5 short games, about 10 minutes.
- **Body:**
  > Hi {name},
  >
  > Your daily workout is ready: 5 short games across different skills, about 10 minutes in total.
- **Button:** Start workout → тренировка дня

### C3 — итог недели (воскресенье)

- **Subject:** Your week in FoxIQ
- **Preheader:** {active_days} days, {games_played} games, {xp_week} XP.
- **Body:**
  > Hi {name},
  >
  > Here's your week:
  > - **{active_days}** days trained
  > - **{games_played}** games played
  > - **{xp_week}** XP earned
  > - Current streak: **{streak_days}** days
  > - Most played: **{top_category}**
  > - Levels up this week: **{level_ups}**
  >
  > A new week starts tomorrow — your next workout is already waiting.
- **Button:** See my week → профиль

---

## Что не используем в текстах

- Обещания роста IQ, «станете умнее», проценты улучшений.
- Давление и чувство вины: «you haven't…», «don't give up», «last chance».
- Скидки и цены: письма с поводом — не про оплату; про списание пишут транзакционные письма.
