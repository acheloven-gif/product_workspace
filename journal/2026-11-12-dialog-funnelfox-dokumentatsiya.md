# 2026-11-12

## Диалог с Brain: FunnelFox по документации

- Наталья сказала, что Катя просила разобраться самой, а не пересказывать созвон. Попросила объяснить FunnelFox по открытой документации.
- Источники: [обзор FunnelFox Payments](https://funnelfox.com/docs/billing), [quickstart](https://funnelfox.com/docs/billing/quickstart), [оркестрация](https://funnelfox.com/docs/billing/payments-orchestration), [ретраи и каскад](https://funnelfox.com/docs/billing/payments-retries), [3DS](https://funnelfox.com/docs/billing/payments-3ds), [FunnelFox Pay](https://funnelfox.com/docs/billing/pay).
- Главное из документации: FunnelFox Payments хранит состояние подписки независимо от платёжки; умеет роутинг по гео, сегментам и балансировку; каскад на запасную платёжку и автоповторы при неудачном списании; Adaptive 3DS; в панели есть раздел Operations (сбои вебхуков, диспуты, чарджбэки). Документация прямо упоминает, что платежи идут через Primer.
