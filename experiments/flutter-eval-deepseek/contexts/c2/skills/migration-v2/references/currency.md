# reference: currency (курс валют, v2)

Карта кода: интерфейс `lib/domain/repository/currency_repository.dart`
(fetchRates + @Deprecated getCurrencyList); реализация
`lib/data/repository_impl/currency_repository_impl.dart`; запрос параметров —
`lib/domain/model/currency_page.dart`; экран — `lib/app/currency_list/currency_list_page.dart`;
детали — `lib/app/currency_detail/`.

## Конвенции v2

1. Запрос строится ТОЛЬКО как `CurrencyPageRequest(base: 'USD', page: N, pageSize: 20)`.
   Default 'EUR' — для интеграционного шлюза, в экранах не используется.
2. `page` с 0; конец пагинации — `hasMore == false`.
3. Подгрузка следующей страницы: `page: currentPage + 1`, элементы ДОБАВЛЯЮТСЯ
   к списку (не заменяют).
4. `saveCurrencyList` вызывается для элементов текущей страницы.

Типовые ошибки: использовать default base (EUR); заменить список вместо добавления
страницы; забыть hasMore и запрашивать за пределами.
