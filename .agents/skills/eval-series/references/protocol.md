# Протокол eval-серии: детали и команды

Проверено на сериях mad-skills-eval v2.0/v3.0, swe-skills-eval, drift-eval.
Пути примеров — flutter-drift-eval; в других сериях адаптировать имена задач/конфигов.

## 1. Харнесс

Копия в `<repo>/harness/madharness-mini` (клон main
https://github.com/MADTeacher/madharness-mini), `harness/` в .gitignore,
установка `uv tool install --force <repo>/harness/madharness-mini`.

Патч в копии (madharness_mini/model.py, chat()): после сборки payload добавить
```python
# Проброс доп. параметров тела запроса из конфига (например,
# "extra_body": {"thinking": {"type": "disabled"}} для прямого API DeepSeek).
payload.update(self.cfg.data.get("extra_body") or {})
```
и таймаут чтения:
```python
with urllib.request.urlopen(
    req, timeout=int(self.cfg.data.get("http_timeout") or 120)
) as resp:
```
Зачем: madharness-mini шлёт только model/messages/temperature/tools с жёстким
таймаутом 120 с — длинные ответы и thinking-режим роняют прогон с
`TimeoutError: read operation timed out`. Прямой API DeepSeek (deepseek-flash)
по умолчанию включает thinking — отключать явно `"extra_body": {"thinking":
{"type": "disabled"}}`, если серия идёт в нон-тинкинг-режиме (проверять по
объёмам completion-токенов контрольных прогонов).

## 2. run_one.sh / STREAM / circuit breaker (схема)

- run_one.sh <T> <c> <idx>: свежая копия fixture → workspaces/run/T__c__idx →
  инжект конфига из шаблона (ключ из keyfile) → контекст по c0/c1/c2 →
  `timeout 1800 madharness-mini run "<сценарий>"` → копия трассы → приёмка
  `WORKSPACE=... bash scripts/accept/T#.sh` → строка CSV.
- STREAM=<c> перенаправляет строку в results/stage_c.csv (параллельные потоки
  пишут в разные файлы).
- В конце run_one.sh: `[ "$RC" -ne 0 ] && exit 1; exit 0` — код возврата нужен
  circuit breaker'у.
- batch_drift.sh:/todo по отсутствующим комбинациям (читает runs.csv + stage_*),
  бюджет 1500 с на вызов; после каждого прогона:
  ```bash
  if bash run_one.sh "$T" "$C" "$I"; then FAILS=0
  else FAILS=$((FAILS+1)); [ "$FAILS" -ge 3 ] && { echo "batch $C: 3 подряд rc!=0 — стоп"; exit 3; }
  fi
  ```

## 3. Запуск потоков (внешний цикл с health-гейтом)

```bash
while :; do
  until py scripts/api_health.py contexts/config.template.json <keyfile>; do sleep 300; done
  STREAM=c0 bash scripts/batch_drift.sh c0 2>&1 | tee -a results/logs/batch_c0.log
  tail -n 1 results/logs/batch_c0.log | grep -q "всё сделано" && break
done
echo "STREAM-C0-FINISHED"
```
run_in_background=true для каждого из трёх потоков. Health-гейт проверяет API
перед КАЖДЫМ вызовом батча (~25 мин), circuit breaker ограничивает чурн внутри
батча: при сбое сети/API максимум 3 фан-строки на поток, а не десятки.

## 4. Полная остановка (по требованию или при инциденте)

TaskStop/background-kill НЕ убивает дерево процессов: batch_drift.sh, run_one.sh,
madharness-mini переживают остановку обёртки и продолжают писать строки.

```powershell
Get-CimInstance Win32_Process -Filter "Name='bash.exe'" |
  Where-Object { $_.CommandLine -match 'batch_drift|run_one\.sh' }   # не matcher'ь свой шелл!
```
Порядок: (1) родители (обёртки, batch_drift) с `taskkill //PID <pid> //F //T`,
(2) осиротевшие madharness-mini по PID. Родители раньше детей — иначе run_one
успеет записать строку с rc≠0. После остановки: проверить, что
`Get-CimInstance ... -Filter "Name='madharness-mini.exe'"` пуст, и вычистить
фан-строки (rc≠0) из stage-файлов csv-модулем (заодно удалить их трассы/логи,
чтобы не путались с перезапусками).

## 5. Инцидент-протокол (обрывы сети/API во время серии)

Признаки: пачка rc=1 с трассами 1–2 КБ (краш на первом вызове), либо большие
трассы с обрывом без session_end; в логах TimeoutError / SSL EOF / WinError 10054.
Действия: потоки сами стоят в health-гейте; после восстановления — проверить
прогресс, фан-строки чистятся в фазе флэков. Волны обрывов в одном интервале у
всех потоков одновременно = проблема маршрута/провайдера, а не конфигураций.

## 6. Схема CSV (15 колонок, без заголовка)

T, C, I, rc, accept, archv, navv, dur, turns(всегда 0 — не заполняется, считать
из трасс), tin, tout, tin+tout, blocked, skills(";"-join), status(в кавычках,
многострочный). Читать ТОЛЬКО csv-модулем с newline="".

## 7. Анализ трасс (строгий парсинг)

```python
events = [json.loads(l) for l in open(trace, encoding="utf-8") if l.strip()]
```
- активация навыка: `e["event"] == "skill_activated"`, имя на верхнем уровне:
  `e.get("skill") or e.get("name")`; НЕ искать имя в data/локации grep'ом.
- блокировки V-хуков: только `e["event"] == "hook_blocked"`, считать события.
- ходы: `max(e.get("turn") or 0)` по `model_usage`; токены: сумма prompt_tokens /
  completion_tokens по `model_usage`.
- контакт с доком/навыком: вхождение ключевого слова в tool_observation.

ДИ Вильсона (z=1,959964):
```python
d = 1 + z*z/n; c = (p + z*z/(2*n))/d
h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
```
При k=5 пороговых утверждений (p ≥ 0,9) не делать — только p̂ и интервалы.

## 8. Триаж неудач

Каждая неудача (accept≠0 или rc≠0 после перезапусков) разбирается по логу
`results/logs/T__C__I.out` и трассе: что агент реально делал, доходил ли до
верификации (запускал ли flutter test/analyze фактически — частая имитация),
использовал ли устаревший/несуществующий API (stale-knowledge), не флейк ли
среды. Классы: (1) дефект контекста, (2) ограничение модели-среды (вкл.
stale-knowledge), (3) флейк. Доля (1) = q_C; (2)+(3) — потолок модели-среды.

## 9. Известные ловушки окружения

- Bash tool: таймаут максимум 600 000 мс; длинные ожидания — циклы sleep 570.
- `py` (Windows launcher) печатает «Could not find platform independent
  libraries <prefix>» — безвредно, отфильтровывать.
- Сценарии/логи UTF-8: в Git Bash tail/grep могут показывать кириллицу
  кракозябрами — читать файлы инструментом Read или через python.
- TaskStop не убивает дерево процессов (см. п. 4).

## 10. Контрольные вопросы перед запуском серии

1. temperature/модель/base_url в config.template.json соответствуют
   methodology.md? Изменения методики — только коммитом с причиной.
2. Зонд знаний выполнен (модель НЕ знает дрейфованное API)?
3. Приёмки зелёные на контрольных прогонах (по одной на конфигурацию)?
4. Workspaces пересобраны после ЛЮБОГО изменения шаблона/контекстов?
5. Ключ нигде не напечатан; `grep -rl "<префикс ключа>" .` пуст?
