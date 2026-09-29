---
name: migration-v2
description: >-
  Work with the v2 repository APIs of this project: paginated currency rates
  (fetchRates/CurrencyPageRequest/CurrencyPage, base currency convention),
  news feed with freshness semantics (loadNewsFeed/NewsFeedFilter, cache-then-
  network), and settings read/watch split (readThemeMode after initAsyncData).
  Use when fixing bugs or adding features that touch currency, news, or
  settings code paths.
metadata:
  author: Stanislav [MADTeacher] Chernyshev
  version: "1.0-eval"
---

# Migration v2 (репозитории)

Проект мигрировал репозитории на v2. Старые члены (@Deprecated) запрещены
в новом коде. Прежде чем писать код — прочитай reference своей зоны:

- `references/currency.md` — пагинация курса валют (fetchRates, base-конвенция)
- `references/news.md` — лента новостей (loadNewsFeed, cache-then-network)
- `references/settings.md` — настройки (readThemeMode, init-guard, потоки)

Общий контракт миграции v2 — этот навык (текущий файл и references).
После правок — `flutter analyze` и целевые `flutter test`.
