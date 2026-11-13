# Foundry run review

Запуск `egor-codex-text-uppercase-count-20261111` завершен: `complete`, 13/13 этапов `done`, каждый этап имеет `feedback_checked=true`. Runtime: `pass`, три теста Planemo, шесть Galaxy tool jobs `ok` с exit code 0, ошибок и пропусков нет. Шесть реальных скачиваний совпали с Nextflow по байтам и SHA-256; три загруженных входа также совпали с fixtures. Тип и состояние каждого выхода отдельно подтверждены метаданными настоящей базы Galaxy.

Источник: пользовательский учебный Nextflow DSL2 с двумя текстовыми процессами. Три исходных исполнения Nextflow прошли реально; ожидаемые выходы не получены из Galaxy. Сохранены 2/2 процесса и 2/2 публикуемых результата. Единственное исключение интерфейса - каталог публикации `params.outdir`, явно учтенный как `surrendered` в `workflow-limitations.md`. Вычислительных блокеров не осталось.

## Покрытие

| Этап | Результат и свидетельство |
| --- | --- |
| 1 summarize-nextflow | Сырой CLI JSON сохранен; ложный профиль и git-происхождение исправлены явно, граф дополнен по исходнику; итог проходит схему. |
| 2 reference-data | Внешних справочных данных нет; решение и ledger сохранены. |
| 3 interface | Один текстовый вход, два стабильных публичных выхода; outdir учтен отдельно. |
| 4 data-flow | Сохранена последовательность UPPERCASE -> COUNT_LINES и публичный промежуточный результат. |
| 5 IWC comparison | Проверен корпус из 120 workflow при pin `deafc4876f2c778aaf075e48bd8e95f3604ccc92`; подходящего предметного exemplar нет. Биологический пример не подставлялся. |
| 6 template | Draft и схема валидны; исходный template сохранен в `checkpoints/`. |
| 7 implementation | Две итерации. Strict-state gates: 1/1 и 2/2, нулевые fail/skip; финальный oracle `draft=false`; extraction не удаляет шаги или выходы. |
| 8 test-data-resolution | Выбран `nextflow-to-test-data`, реальный исходный fixture; schema guard и refs проходят. |
| 9 test plan | Исходных nf-test assertions нет; provenance указан честно как intent / fixture-derived, добавлены два граничных случая с реальным Nextflow-эталоном. |
| 10 tests | Три companion tests, точные сравнения обоих выходов и SHA-256; static schema/labels gate проходит. Runtime gate выполнен этапом 12 по тому же неизмененному файлу. |
| 11 terminal validation | Строгая структура, состояния двух инструментов и обе связи проходят. |
| 12 runtime | Настоящий Planemo-managed Galaxy; 3/3 теста прошли. JSON, HTML, XML, журнал, IDs и фактические выходы сохранены. |
| 13 debug | Первая ошибка окружения отделена от результата workflow; вторая попытка проходит. Типы HDA подтверждены отдельной выборкой `mode=ro`. |

Непроверенных этапов нет. Все authoring-решения делались агентом по cast SKILL.md, исполнительные команды действительно запускались. Это не заявление о переводе без вмешательств: сырая сводка требовала исправлений. Foundry pin `df991d0d789b0a29618cbcdbe7eb6d9508f1f062`; подробная идентичность pipeline и сборки в `foundry-run.yml`. Точный ID модели, токены и стоимость средой не раскрыты.

## Воспроизведение и обходы

CLI-поиск Tool Shed завершился ошибкой сети/таймаутом. Версии и changeset обоих известных кандидатов получены действительными CLI-вызовами отдельно; рекомендации помечены `weak` и раскрывают override. Это не объявлено успешным поиском или отсутствием оберток. Sed cache provenance `orphan` также сохранен явно; фактическая установка обоих инструментов из Tool Shed подтверждена runtime.

Локальная проверка staging показала, что File с `path` теряет индивидуальное `to_posix_lines:false`; поэтому маленькие UTF-8 входы переданы через `contents`. Payload-проверка использовала локальную заглушку и не считается запуском Galaxy. Самостоятельное исполнение Galaxy и фактические входные байты подтверждены последующим настоящим тестом.

Первая реальная попытка остановлена при загрузке из-за слишком длинного TMPDIR для AF_UNIX на macOS. Она имеет `not-run`, архив журнала и кода завершения, без структурированного тестового отчета. Изменен только TMPDIR; вторая попытка успешно исполнила все тесты. Эта ошибка нашей конфигурации не представлена как дефект upstream.

## Триаж пяти feedback entries

| Entry | Disposition | Обоснование |
| --- | --- | --- |
| summarize-nextflow-implicit-test-profile | comment-draft | Точный открытый дубликат: https://github.com/galaxyproject/foundry/issues/763 . Подготовлено дополнительное минимальное свидетельство. |
| summarize-nextflow-nested-source-provenance | issue-draft | Неотслеживаемые исходники наследуют git pin родителя. #351 и #803 связаны с другой областью; точный дубликат не найден ограниченными поисками. |
| summarize-nextflow-anonymous-dsl2-handoff | issue-draft | Неполный schema-valid граф единственного безымянного workflow. #666 связан с выбором именованного графа; закрытая #111 с поиском процессов. |
| nextflow-test-plan-assumes-nf-test-evidence | issue-draft | Безусловное требование исходных nf-test assertions не покрывает выбранный pipeline-defaults. #679 и #793 исправляют другие части контракта. |
| galaxy-stager-ignores-file-newline-override | issue-draft | Related project: galaxy-tool-util staging, Planemo caller. Корень проверен по фактическому payload и исходному коду; хеш Foundry для related project не придуман. |

Текущий main проверен для canonical Mold: оба content hashes совпадают с cast. Совпадение документа не выдается за повторное исполнение CLI нового main. Первые три entries указывают Mold как контракт; ожидаемая программная коррекция относится также к resolver/CLI. Отдельные исправления не объединены только из-за общего locator.

Ledger содержит все пять исходных entries и их provenance; ничего не удалено или переименовано. Triage evidence: `logs/feedback-triage.json`; проверка related project не требует вымышленного Foundry hash. Локальные пути заменены в публикуемых копиях, учетные данные и базы не включены. Исходные диагностические копии остаются вне репозитория; преобразования раскрыты в `redactions.json`.

Подготовлены один комментарий к существующей задаче и четыре предложения новых задач в `foundry-issue-drafts.md`. Отдельные GitHub issues/comments не публиковались. Все черновики направлены в `galaxyproject/foundry`, включая related-project наблюдение.

Reporting feedback pass: `no feedback`. Полные ограничения результата находятся в `workflow-limitations.md`; успешное исполнение этого учебного примера не доказывает корректность больших nf-core conversions.
