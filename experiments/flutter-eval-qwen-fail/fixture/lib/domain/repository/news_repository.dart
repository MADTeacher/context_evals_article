import 'package:mad_flutter_practicum/domain/model/news_filter.dart';
import 'package:mad_flutter_practicum/domain/model/news_model.dart';

abstract interface class NewsRepository {
  @Deprecated('v2: используйте loadNewsFeed; будет удалено в v3')
  Future<List<NewsModel>> getNewsList();

  Future<List<NewsModel>> loadNewsFeed(NewsFeedFilter filter);

  Future<void> saveNewsList(List<NewsModel> value);
}
