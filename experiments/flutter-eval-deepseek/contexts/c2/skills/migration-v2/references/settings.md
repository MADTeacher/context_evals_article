# reference: settings (настройки, v2)

Карта кода: интерфейс `lib/domain/repository/settings_repository.dart`;
реализация `lib/data/repository_impl/settings_repository_impl.dart`; экран —
`lib/app/profile/profile_page.dart` (+ theme_mode_selector_bs.dart); splash —
`lib/app/splash_page.dart` (вызывает initAsyncData).

## Конвенции v2

1. `readThemeMode()` — синхронное чтение текущего режима. Вызывать ТОЛЬКО после
   `initAsyncData()` (splash): до инициализации значение не определено.
2. Подписка на изменения — `themeModeStream` (broadcast): экраны обновляются
   автоматически при setThemeMode.
3. `setThemeMode(mode)` сохраняет в preference-датасорс и публикует в поток.
4. `isAuth`/`isAuthStream`/`getToken`/`setToken` — без изменений в v2.

Типовые ошибки: вызвать readThemeMode до initAsyncData; читать геттер
( deprecated) вместо метода; не подписаться на поток и показывать устаревшее
значение после переключения.
