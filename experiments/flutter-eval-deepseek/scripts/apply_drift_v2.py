# -*- coding: utf-8 -*-
"""Дрейф v2 для lab_8: пагинация курсов (base-ловушка), фильтр новостей (forceRefresh),
read/watch-разделение настроек; старые члены помечены @Deprecated (совместимые шимы)."""
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
F = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixture")


def w(path, text):
    io.open(F + "\\" + path.replace("/", "\\"), "w", encoding="utf-8", newline="\n").write(text)


def patch(path, old, new):
    p = F + "\\" + path.replace("/", "\\")
    s = io.open(p, encoding="utf-8").read()
    assert old in s, "не найдено в %s: %s" % (path, old[:60])
    io.open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new, 1))


# 1) новые модели
w("lib/domain/model/currency_page.dart", """import 'package:mad_flutter_practicum/domain/model/currency_model.dart';

/// Параметры запроса курса валют (v2).
class CurrencyPageRequest {
  const CurrencyPageRequest({this.base = 'EUR', this.page = 0, this.pageSize = 20});

  final String base;
  final int page;
  final int pageSize;
}

/// Страница курса валют (v2).
class CurrencyPage {
  const CurrencyPage({required this.items, required this.page, required this.hasMore});

  final List<CurrencyModel> items;
  final int page;
  final bool hasMore;
}
""")
w("lib/domain/model/news_filter.dart", """/// Фильтр ленты новостей (v2).
class NewsFeedFilter {
  const NewsFeedFilter({this.source, this.limit = 30, this.forceRefresh = false});

  final String? source;
  final int limit;
  final bool forceRefresh;

  static const NewsFeedFilter all = NewsFeedFilter();
}
""")
patch("lib/domain/model/model.dart",
      "export 'currency_model.dart';",
      "export 'currency_model.dart';\nexport 'currency_page.dart';\nexport 'news_filter.dart';")

# 2) интерфейсы репозиториев
w("lib/domain/repository/currency_repository.dart", """import 'package:mad_flutter_practicum/domain/model/currency_model.dart';
import 'package:mad_flutter_practicum/domain/model/currency_page.dart';

abstract interface class CurrencyRepository {
  @Deprecated('v2: используйте fetchRates; будет удалено в v3')
  Future<List<CurrencyModel>> getCurrencyList();

  Future<CurrencyPage> fetchRates(CurrencyPageRequest request);

  Future<void> saveCurrencyList(List<CurrencyModel> value);
}
""")
w("lib/domain/repository/news_repository.dart", """import 'package:mad_flutter_practicum/domain/model/news_filter.dart';
import 'package:mad_flutter_practicum/domain/model/news_model.dart';

abstract interface class NewsRepository {
  @Deprecated('v2: используйте loadNewsFeed; будет удалено в v3')
  Future<List<NewsModel>> getNewsList();

  Future<List<NewsModel>> loadNewsFeed(NewsFeedFilter filter);

  Future<void> saveNewsList(List<NewsModel> value);
}
""")
patch("lib/domain/repository/settings_repository.dart",
      "  abstract final AppThemeMode themeMode;",
      "  @Deprecated('v2: используйте readThemeMode(); будет удалено в v3')\n  abstract final AppThemeMode themeMode;\n\n  AppThemeMode readThemeMode();")

# 3) реализации
w("lib/data/repository_impl/currency_repository_impl.dart", """import 'package:mad_flutter_practicum/domain/datasource/db_datasource.dart';
import 'package:mad_flutter_practicum/domain/datasource/rest_datasource.dart';
import 'package:mad_flutter_practicum/domain/model/currency_model.dart';
import 'package:mad_flutter_practicum/domain/model/currency_page.dart';
import 'package:mad_flutter_practicum/domain/repository/currency_repository.dart';

class CurrencyRepositoryImpl implements CurrencyRepository {
  const CurrencyRepositoryImpl(this._restDatasource, this._dbDatasource);

  final RestDatasource _restDatasource;
  final DbDatasource _dbDatasource;

  @override
  @Deprecated('v2: используйте fetchRates; будет удалено в v3')
  Future<List<CurrencyModel>> getCurrencyList() => _restDatasource.getCurrencyList();

  @override
  Future<CurrencyPage> fetchRates(CurrencyPageRequest request) async {
    final List<CurrencyModel> all = await _restDatasource.getCurrencyList();
    final int start = request.page * request.pageSize;
    if (start >= all.length) {
      return CurrencyPage(items: const [], page: request.page, hasMore: false);
    }
    final int end = (start + request.pageSize).clamp(0, all.length);
    return CurrencyPage(items: all.sublist(start, end), page: request.page, hasMore: end < all.length);
  }

  @override
  Future<void> saveCurrencyList(List<CurrencyModel> value) => _dbDatasource.saveCurrencyList(value);
}
""")
w("lib/data/repository_impl/news_repository_impl.dart", """import 'package:mad_flutter_practicum/domain/datasource/db_datasource.dart';
import 'package:mad_flutter_practicum/domain/datasource/rest_datasource.dart';
import 'package:mad_flutter_practicum/domain/model/news_filter.dart';
import 'package:mad_flutter_practicum/domain/model/news_model.dart';
import 'package:mad_flutter_practicum/domain/repository/news_repository.dart';

class NewsRepositoryImpl implements NewsRepository {
  const NewsRepositoryImpl(this._restDatasource, this._dbDatasource);

  final RestDatasource _restDatasource;
  final DbDatasource _dbDatasource;

  @override
  @Deprecated('v2: используйте loadNewsFeed; будет удалено в v3')
  Future<List<NewsModel>> getNewsList() => _restDatasource.getNewsList();

  @override
  Future<List<NewsModel>> loadNewsFeed(NewsFeedFilter filter) async {
    if (filter.forceRefresh) {
      final List<NewsModel> fresh = await _restDatasource.getNewsList();
      await _dbDatasource.saveNewsList(fresh);
      return fresh;
    }
    return _dbDatasource.getNewsList();
  }

  @override
  Future<void> saveNewsList(List<NewsModel> value) => _dbDatasource.saveNewsList(value);
}
""")
patch("lib/data/repository_impl/settings_repository_impl.dart",
      "  @override\n  AppThemeMode get themeMode => _datasource.themeMode;",
      "  @override\n  @Deprecated('v2: используйте readThemeMode(); будет удалено в v3')\n  AppThemeMode get themeMode => readThemeMode();\n\n  @override\n  AppThemeMode readThemeMode() => _datasource.themeMode;")

# 4) миграция приложения на v2
patch("lib/app/currency_list/currency_list_page.dart",
      "_currencyListFuture = currencyRepository.getCurrencyList().then((List<CurrencyModel> value) {",
      "_currencyListFuture = currencyRepository.fetchRates(const CurrencyPageRequest(base: 'USD')).then((CurrencyPage page) {\n      final List<CurrencyModel> value = page.items;")
patch("lib/app/currency_list/currency_list_page.dart",
      "      currencyRepository.saveCurrencyList(value);",
      "      currencyRepository.saveCurrencyList(value);")
patch("lib/app/news_list/news_list_page.dart",
      "_newsListFuture = newsRepository.getNewsList().then((List<NewsModel> value) {\n      newsRepository.saveNewsList(value);",
      "_newsListFuture = newsRepository.loadNewsFeed(const NewsFeedFilter(forceRefresh: true)).then((List<NewsModel> value) {")
patch("lib/app/profile/profile_page.dart",
      "ValueNotifier(_settingsRepository.themeMode)",
      "ValueNotifier(_settingsRepository.readThemeMode())")

# 5) тесты: стабы виджет-тестов
patch("test/widget/home_container_test.dart",
      "when(mockCurrencyRepository.getCurrencyList()).thenAnswer((_) async => []);",
      "when(mockCurrencyRepository.fetchRates(any)).thenAnswer((_) async => const CurrencyPage(items: [], page: 0, hasMore: false));")
patch("test/widget/home_container_test.dart",
      "when(mockNewsRepository.getNewsList()).thenAnswer((_) async => []);",
      "when(mockNewsRepository.loadNewsFeed(any)).thenAnswer((_) async => []);")
patch("test/widget/home_container_test.dart",
      "when(mockSettingsRepository.themeMode).thenAnswer((_) => AppThemeMode.system);",
      "when(mockSettingsRepository.readThemeMode()).thenReturn(AppThemeMode.system);")
patch("test/widget/currency_list_page_test.dart",
      "when(mockCurrencyRepository.getCurrencyList()).thenAnswer((_) async => currencyItems);",
      "when(mockCurrencyRepository.fetchRates(any)).thenAnswer((_) async => CurrencyPage(items: currencyItems, page: 0, hasMore: false));")
patch("test/widget/news_list_page_test.dart",
      "when(mockNewsRepository.getNewsList()).thenAnswer((_) async => newsItems);",
      "when(mockNewsRepository.loadNewsFeed(any)).thenAnswer((_) async => newsItems);")

# 6) тест репозитория: новые контракты v2
patch("test/unit/repository_test.dart",
      "import 'package:mad_flutter_practicum/domain/domain.dart';",
      "import 'package:mad_flutter_practicum/domain/domain.dart';\nimport 'package:mad_flutter_practicum/domain/model/currency_page.dart';\nimport 'package:mad_flutter_practicum/domain/model/news_filter.dart';")
patch("test/unit/repository_test.dart",
      """      verify(mockRestDatasource.getCurrencyList()).called(1);
    });""",
      """      verify(mockRestDatasource.getCurrencyList()).called(1);
    });

    test('fetchRates returns requested page and hasMore flag', () async {
      final all = [
        for (int i = 0; i < 3; i++)
          CurrencyModel(id: '$i', nominal: 1, name: 'Валюта $i', symbol: 'C$i', value: i + 1.0, previousValue: i),
      ];
      when(mockRestDatasource.getCurrencyList()).thenAnswer((_) async => all);

      final page0 = await repository.fetchRates(const CurrencyPageRequest(base: 'USD', page: 0, pageSize: 2));

      expect(page0.items.map((c) => c.id), ['0', '1']);
      expect(page0.hasMore, isTrue);
    });

    test('fetchRates returns empty page beyond the end', () async {
      when(mockRestDatasource.getCurrencyList()).thenAnswer((_) async => const []);

      final page = await repository.fetchRates(const CurrencyPageRequest(base: 'USD', page: 5, pageSize: 20));

      expect(page.items, isEmpty);
      expect(page.hasMore, isFalse);
    });""")
patch("test/unit/repository_test.dart",
      """      verify(mockRestDatasource.getNewsList()).called(1);
    });""",
      """      verify(mockRestDatasource.getNewsList()).called(1);
    });

    test('loadNewsFeed with forceRefresh reads from network and caches', () async {
      final newsList = [
        NewsModel(title: 'Свежая новость', link: 'https://example.com/fresh', date: DateTime.now()),
      ];
      when(mockRestDatasource.getNewsList()).thenAnswer((_) async => newsList);

      final result = await repository.loadNewsFeed(const NewsFeedFilter(forceRefresh: true));

      expect(result, newsList);
      verify(mockRestDatasource.getNewsList()).called(1);
      verify(mockDbDatasource.saveNewsList(newsList)).called(1);
      verifyNever(mockDbDatasource.getNewsList());
    });

    test('loadNewsFeed without forceRefresh reads only from cache', () async {
      final cached = [
        NewsModel(title: 'Из кэша', link: 'https://example.com/cached', date: DateTime.now()),
      ];
      when(mockDbDatasource.getNewsList()).thenAnswer((_) async => cached);

      final result = await repository.loadNewsFeed(const NewsFeedFilter.all);

      expect(result, cached);
      verify(mockDbDatasource.getNewsList()).called(1);
      verifyNever(mockRestDatasource.getNewsList());
    });""")
patch("test/unit/repository_test.dart",
      "import 'package:mockito/mockito.dart';",
      "import 'package:mockito/mockito.dart';\n\nimport '../mocks/datasource.mocks.dart' show MockDbDatasource;")

print("дрейф v2 внесён в fixture")
