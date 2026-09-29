import 'package:mad_flutter_practicum/domain/model/app_theme_mode.dart';

abstract interface class SettingsRepository {
  Future<void> initAsyncData();

  abstract final Stream<bool> isAuthStream;

  abstract final bool isAuth;

  abstract final Stream<AppThemeMode> themeModeStream;

  @Deprecated('v2: используйте readThemeMode(); будет удалено в v3')
  abstract final AppThemeMode themeMode;

  AppThemeMode readThemeMode();

  void setThemeMode(AppThemeMode mode);

  Future<String?> getToken();

  Future<void> setToken(String? token);
}
