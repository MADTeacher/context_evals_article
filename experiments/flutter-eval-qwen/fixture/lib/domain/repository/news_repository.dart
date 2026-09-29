import 'package:mad_flutter_practicum/domain/model/news_filter.dart';
import 'package:mad_flutter_practicum/domain/model/news_model.dart';

abstract interface class NewsRepository {
  @Deprecated('This member is deprecated and will be removed in a future version')
  Future<List<NewsModel>> getNewsList();

  Future<List<NewsModel>> loadNewsFeed(NewsFeedFilter filter);

  Future<void> saveNewsList(List<NewsModel> value);
}
