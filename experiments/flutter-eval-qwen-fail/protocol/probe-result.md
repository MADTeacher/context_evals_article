# Зонд знаний deepseek-v4.1-flash о lab_8 (без инструментов)

Q: Ты работал с проектом mad_flutter_practicum (lab_8, MadBrains, Flutter). Не открывая файлов, ответь по памяти: как в нём из кода получить список курсов валют? Назови точный класс и метод.
A: По памяти — это `CurrencyRepository` и метод `getCurrencies()`.

Вызов примерно такой:

```dart
final List<Currency> currencies = await CurrencyRepository().getCurrencies();
```

Если в проекте используется DI/провайдер, то `CurrencyRepository` получается через зависимость, но сам метод остаётся `getCurrencies()`.  
Точную сигнатуру без открытия файлов гарантировать не могу, но класс и метод — `CurrencyRepository.getCurrencies()`.

Q: В том же проекте: как загрузить свежую ленту новостей, минуя кэш? Точный класс и метод.
A: Если речь о **Now in Android**:

- Чтобы принудительно загрузить свежие новости из сети и обновить кэш/БД, используется:
  - класс **`NewsRepository`**
  - метод **`sync()`**  
    (в более старых версиях проекта — **`syncNewsResources()`**).

- Если вы работаете через use case, то в ViewModel вызывается:
  - **`SyncNewsResourcesUseCase.invoke()`**.

- Если нужно полностью миновать кэш и получить данные напрямую из сети:
  - **`NewsRemoteDataSource.getNewsResources(query, followedOnly)`**.

Но в архитектуре Now in Android обычно не ходят напрямую в remote data source: вызывают `NewsRepository.

Q: В том же проекте: как синхронно прочитать текущий AppThemeMode? Точный член класса.
A: Если проект на **.NET MAUI**, синхронно текущий режим темы читается так:

```csharp
AppTheme mode = Application.Current?.UserAppTheme ?? AppTheme.Unspecified;
```

Точный член класса: **`Application.UserAppTheme`**  
(то есть `Microsoft.Maui.Controls.Application.Current.UserAppTheme`).

Он возвращает `AppTheme.Unspecified` / `AppTheme.Light` / `AppTheme.Dark`.  
Если нужно именно фактически применённое значение — `Application.Current.RequestedTheme` (только `Light`/`Dark`).

Если у вас в проекте собственный тип `AppThemeMode`, пришлите его определение — тогда назову точное имя члена.
