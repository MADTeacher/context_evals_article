import 'package:mad_flutter_practicum/domain/model/currency_model.dart';

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
