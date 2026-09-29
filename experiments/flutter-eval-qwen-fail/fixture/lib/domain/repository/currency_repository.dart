import 'package:mad_flutter_practicum/domain/model/currency_model.dart';
import 'package:mad_flutter_practicum/domain/model/currency_page.dart';

abstract interface class CurrencyRepository {
  @Deprecated('v2: используйте fetchRates; будет удалено в v3')
  Future<List<CurrencyModel>> getCurrencyList();

  Future<CurrencyPage> fetchRates(CurrencyPageRequest request);

  Future<void> saveCurrencyList(List<CurrencyModel> value);
}
