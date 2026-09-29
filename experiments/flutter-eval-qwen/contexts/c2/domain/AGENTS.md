# lib/domain — контракты (v2)

1. Интерфейсы репозиториев v2: fetchRates(CurrencyPageRequest), loadNewsFeed(NewsFeedFilter),
   readThemeMode(). @Deprecated-члены будут удалены в v3 — новые интерфейсы через них
   не проектировать.
2. Модели CurrencyPageRequest/CurrencyPage/NewsFeedFilter — в lib/domain/model/.
