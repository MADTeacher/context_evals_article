import 'package:mad_flutter_practicum/domain/model/currency_model.dart';
import 'package:mad_flutter_practicum/domain/model/currency_page.dart';

abstract interface class CurrencyRepository {
  @Deprecated('This member is deprecated and will be removed in a future version')
  Future<List<CurrencyModel>> getCurrencyList();

  Future<CurrencyPage> fetchRates(CurrencyPageRequest request);

  Future<void> saveCurrencyList(List<CurrencyModel> value);
}
