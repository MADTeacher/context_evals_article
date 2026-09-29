# reference: news (лента новостей, v2)

Карта кода: интерфейс `lib/domain/repository/news_repository.dart` (loadNewsFeed +
@Deprecated getNewsList); реализация `lib/data/repository_impl/news_repository_impl.dart`;
фильтр — `lib/domain/model/news_filter.dart`; экран — `lib/app/news_list/news_list_page.dart`.

## Конвенции v2

1. `forceRefresh: true` — сеть + запись в кэш (БД). `forceRefresh: false` /
   `NewsFeedFilter.all` — ТОЛЬКО кэш (БД), сеть не дергается.
2. Паттерн экрана — cache-then-network: при открытии показать кэш
   (`loadNewsFeed(const NewsFeedFilter.all)`) и параллельно запустить
   фоновую загрузку (`loadNewsFeed(const NewsFeedFilter(forceRefresh: true))`),
   по приходу ответа обновить список.
3. Действие пользователя «Обновить» — всегда `forceRefresh: true`.
4. `NewsFeedFilter(source: ...)` фильтрует по источнику, `limit` ограничивает выборку.

Типовые ошибки: один вызов с default-фильтром (кэш) вместо сети; потеря
записи в кэш при forceRefresh; замена списка вместо фонового обновления.
