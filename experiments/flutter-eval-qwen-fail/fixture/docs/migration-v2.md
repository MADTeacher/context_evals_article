# Migration Guide: Mad Flutter Practicum v2

Дата релиза: 2026-09-22. Обратно несовместимые изменения API репозиториев.
Старые члены помечены @Deprecated и будут удалены в v3.

## 1. CurrencyRepository — пагинация курса валют

- **Удалён прямой список**. `getCurrencyList()` → **`fetchRates(CurrencyPageRequest request)`**,
  возвращает `CurrencyPage { items, page, hasMore }`.
- **ВАЖНО (проектная конвенция): во всех экранах запрос строится с `base: 'USD'`.**
  Значение по умолчанию в `CurrencyPageRequest` — 'EUR' — оставлено для совместимости
  с интеграционным шлюзом, но в приложении НЕ используется.
- Пагинация: `page` нумеруется с 0, `pageSize` по умолчанию 20; признак конца —
  `hasMore == false`.
- `saveCurrencyList` сохраняет элементы текущей страницы (без изменений).

## 2. NewsRepository — фильтр ленты и семантика свежести

- `getNewsList()` → **`loadNewsFeed(NewsFeedFilter filter)`**.
- `NewsFeedFilter { source?, limit = 30, forceRefresh = false }`; `NewsFeedFilter.all` —
  лента целиком.
- **Семантика свежести (проектная конвенция)**:
  - `forceRefresh: true` — принудительный запрос в сеть, результат записывается в кэш (БД);
  - `forceRefresh: false` (в т.ч. `NewsFeedFilter.all`) — **только кэш (БД)**, сеть не вызывается.
- **Паттерн экрана новостей — cache-then-network**: при открытии вкладки показываем кэш
  (`forceRefresh: false`) и параллельно обновляем в фоне (`forceRefresh: true`);
  любое действие пользователя «Обновить» — всегда `forceRefresh: true`.

## 3. SettingsRepository — разделение read/watch

- Геттер `themeMode` → **метод `readThemeMode()`**.
- **ВАЖНО (проектная конвенция): `readThemeMode()` вызывать только после
  `initAsyncData()`** (он выполняется на Splash). До инициализации значение
  не определено — обращение до Splash считается дефектом.
- Поток `themeModeStream` — без изменений; подписки продолжают работать.

## 4. Общие требования

- Новый код не должен ссылаться на @Deprecated члены: `flutter analyze` обязан быть
  без замечаний.
- Пользовательские изменения сопровождаются фрагментом `changelog/<номер>.bugfix.rst`.
