# Промпт для отдельной сессии: серия drift-eval (прямой API DeepSeek)

Скопируй текст ниже в новую агентскую сессию в этой рабочей директории.

---

Ты продолжаешь эксперимент drift-eval (Flutter, API-drift) — ЧЕТВЁРТАЯ серия проекта
по статье «Управление контекстом в агентной программной инженерии» (INJOIT,
С. А. Чернышев). Используй навык **eval-series** — он описывает протокол; ниже —
конкретика этой серии. Цель серии: показать, что контекст после жизненного цикла
(C2) даёт реальный прирост успешности, когда он — единственный носитель актуального
знания (API проекта дрейфанул, внутренние знания модели устарели/отсутствуют).
Старт серии автором одобрен — после префлайта запускай сразу.

## Проект (C:\Users\MADTeacher\Documents\GitHub\flutter-drift-eval, git, чистый)

- fixture/ — полигон: lab_8 из Mad-Flutter-Practicum, приватная эволюция v2 (коммит
  ce8366f: пагинация fetchRates(CurrencyPageRequest) с ловушкой base 'EUR'/'USD',
  loadNewsFeed(NewsFeedFilter) с forceRefresh-семантикой кэш/сеть, readThemeMode()
  с init-guard; старые члены @Deprecated). fixture/ — отдельный git, НЕ трогать.
- protocol/methodology.md v1.0 (pre-registration, temperature 0,8) + раздел 9
  (дополнение до запуска: смена провайдера на прямой API DeepSeek — читать);
  protocol/scenarios/T1..T8.txt (группы: currency T1/T2, news T3/T4, settings
  T5/T6, mixed T7/T8); protocol/probe-result.md (зонд: deepseek lab_8 не знает).
- contexts/c1 (сырой AGENTS.md), contexts/c2 (K-структура + per-dir AGENTS.md +
  навык migration-v2 с references + V-хук guard_v2.py, блокирующий @Deprecated-члены).
- scripts/: make_workspace.sh, run_one.sh <T> <c0|c1|c2> <idx> (STREAM=<c> →
  results/stage_c*.csv), batch_drift.sh <c> (25 мин/вызов + circuit breaker:
  3 подряд rc≠0 → стоп), accept/T#.sh (через env WORKSPACE), merge_drift.py,
  analyze_drift.py, progress_drift.py, api_health.py.
- harness/madharness-mini/ — рабочая копия харнесса (клон main 671cb06 + патчи:
  extra_body/http_timeout в model.py, телеметрия model_usage и событие
  hook_blocked в model_loop.py). Исходные репозитории madharness-mini* не трогать.
- РЕЗУЛЬТАТЫ ПОЛНОСТЬЮ ВЫЧИЩЕНЫ (0/120, runs.csv пуст) — серия пишется с нуля,
  включая задачи T1/c0/1, T1/c2/1, T4/c2/1 (прошлые контрольные прогоны удалены).

## Модель и объём

deepseek-flash (DeepSeek-V4.1-Flash, прямой API https://api.deepseek.com,
thinking выключен через extra_body — уже в contexts/config.template.json),
temperature 0,8, max_turns 150, таймаут 1800 с, k=5. Серия: 8 задач × 3
конфигурации × 5 = 120 прогонов. Прогрев не нужен (зонд выполнен).

## Ключ API

Уже в C:\Users\MADTeacher\Documents\GitHub\madharness-mini-v1\games\.madharness-mini\config.json
(поле api_key; сам файл — gitignored; из скриптов читается только api_key).
КЛЮЧ НИГДЕ НЕ ПЕЧАТАТЬ И НЕ КОММИТИТЬ. Перед каждым коммитом:
grep -rl "sk-b8eb" . — пусто; если ключ попал в трассы/логи —
sed 's/sk-b8eb[A-Za-z0-9]*/***REDACTED***/g' по затронутым файлам ДО коммита.

## ЗАДАЧА 1. Провести серию

1. Пре-флайт: bash scripts/make_workspace.sh c0 (затем c1, c2) — workspaces
   перезапишутся с НОВОЙ конфигурацией (старые содержали OpenRouter). Проверь:
   в workspaces/c2/.madharness-mini/config.json — temperature 0,8, модель
   deepseek-flash, base_url api.deepseek.com; есть scripts/hooks/guard_v2.py и
   .madharness-mini/hooks.json; в workspaces/c1/.agents/skills — 8 навыков.
   Проверь, что установленный madharness-mini собран из harness/madharness-mini
   и содержит патчи: grep -c "model_usage\|extra_body" в site-packages
   .../madharness_mini/{model,model_loop}.py; если нет —
   uv tool install --force harness/madharness-mini.
   Финально: py scripts/api_health.py contexts/config.template.json <keyfile>.
2. Запусти ТРИ фоновых батча параллельно (run_in_background), каждый со СВОИМ
   staging-CSV и health-гейтом (см. навык eval-series, п. 3 протокола):
   внешний цикл потока = until api_health → STREAM=cX batch_drift.sh cX, пока
   не «всё сделано».
3. Мониторинг: проверки каждые ~10 мин (sleep ≤570 с, таймаут Bash ≤600 000 мс),
   короткая сводка прогресса (py scripts/progress_drift.py results) каждые
   ~40 минут. Батч печатает «batch cX: всё сделано» либо «time budget reached»
   либо сообщение circuit breaker'а — по завершению перезапускай тот же батч
   (гейт сам подождёт лежащий API). Ориентир: 120 прогонов × 7–15 мин / 3 потока.
4. Флэки: rc≠0 И accept≠0 — перезапуск через STREAM=<c> run_one.sh; rc≠0 ПРИ
   accept=0 — ТОЖЕ перезапуск (сессия оборвана средой, приёмка прошла на
   осиротевшем workspace — цензурированный образец недействителен); при
   сомнительной приёмке — 3 замера, вердикт по большинству. Финал: 120
   уникальных комбинаций, 0 строк с rc≠0.
5. Если сеть/API начнёт ронять прогоны волнами — не выдумывай данные: потоки
   стоят в гейте, фан-строки чистятся, серия продолжается; при систематическом
   падении приёмки >50 % одного инстанса — СТОП и сообщение автору.

## ЗАДАЧА 2. Слияние и анализ

1. Слей stage_c*.csv в results/runs.csv ТОЛЬКО через csv-модуль python
   (py scripts/merge_drift.py results — keep-last по (T, config, idx),
   валидация полей и матрицы).
2. Анализ: py scripts/analyze_drift.py → results/analysis/final-report-drift.md:
   - p̂ с 95 % ДИ Вильсона по каждой задаче (T1..T8 × C0/C1/C2), по сумме и
     группам (currency/news/settings/mixed) + контрасты C2−C0, C2−C1, C1−C0;
   - активация навыков: строго по событиям skill_activated (имя на верхнем
     уровне события), hook_blocked — строго по событиям hook_blocked
     (текстовый grep завышает на порядки); ходы — из трасс (max turn по
     model_usage; в CSV колонка turns не заполняется);
   - средние токены/ходы/длительность по конфигурациям;
   - триаж КАЖДОЙ неудачи по логу results/logs/T__C__I.out и трассе: класс
     (1) дефект контекста / (2) ограничение модели-среды (подкласс
     stale-knowledge — применил несуществующий или @Deprecated API) / (3) флейк.
     Доля (1) = q_C. Классы вноси в results/analysis/triage.csv
     (T,C,I,class,subclass,note) и перегенерируй отчёт.
3. Главный вопрос: подтверждается ли прирост C2 относительно C0 и C1 именно на
   задачах с конвенциями v2 (T1/T2 base:'USD', T4 cache-then-network, T5/T6
   init-guard)? Сравни с тремя прошлыми сериями (отчёты в results/analysis/
   mad-skills-eval: final-report-v3.md, comparison-report.md; swe-skills-eval:
   final-report-swe.md), где пользы не было из-за эффекта потолка: v2.0
   (deepseek, lab_8 v1!) C0=0,91; v3.0 (qwen) C1>C2>C0; swe C0=C1=1,00.
4. Коммит результатов (по правилам ключей выше; в коммит входят merge/analyze
   скрипты, отчёт, трассы, логи, methodology-файлы; harness/ в .gitignore).

## СТОП-условия (остановись и сообщи, не выдумывай данные)

Модель недоступна или массово падает приёмка (>50 % одного инстанса);
расхождение матрицы после слияния, не чинящееся перезапусками.

## Финальный ответ

Таблица p̂ по задачам и итог; триаж всех неудач; активация навыков и V-хуки;
токены/время по конфигурациям; ответ на главный вопрос (есть ли у ЖЦ-контекста
реальная польза в этом дизайне и где именно).
