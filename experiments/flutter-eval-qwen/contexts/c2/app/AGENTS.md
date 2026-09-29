# lib/app — экраны (v2)

Правила корневого AGENTS.md действуют здесь полностью. Дополнительно:

1. Запросы данных — только через репозитории v2: fetchRates(base: 'USD'),
   loadNewsFeed(NewsFeedFilter) с семантикой свежести (кэш vs forceRefresh).
2. Режим темы — readThemeMode() после Splash; подписка на изменения — themeModeStream.
3. Экраны-фutures не должны использовать @Deprecated-члены (контракт — навык migration-v2).
