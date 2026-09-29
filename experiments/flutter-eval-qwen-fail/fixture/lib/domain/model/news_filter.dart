/// Фильтр ленты новостей (v2).
class NewsFeedFilter {
  const NewsFeedFilter({this.source, this.limit = 30, this.forceRefresh = false});

  final String? source;
  final int limit;
  final bool forceRefresh;

  static const NewsFeedFilter all = NewsFeedFilter();
}
