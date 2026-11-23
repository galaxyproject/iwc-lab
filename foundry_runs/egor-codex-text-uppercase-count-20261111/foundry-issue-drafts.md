# Foundry issue drafts

Локальные черновики для galaxyproject/foundry. Ничего не опубликовано, ledger и lifecycle не изменены. Проверка текущего main относится к canonical Mold; совпадение его хеша не выдается за повторное выполнение CLI нового main. Итог: 13/13 этапов complete; реальные Galaxy tests 3/3 pass. Покрытие описано в foundry-run-review.md.

## Existing-issue comment draft: #763

Адрес: https://github.com/galaxyproject/foundry/issues/763

Дополнительный минимальный случай: у локального ad-hoc DSL2 нет nf-test, nextflow.config или profiles. Вызов foundry summarize-nextflow source --no-with-nextflow создал выбранный profile:test с effective_profiles=[test] и rationale explicit caller profile override, хотя профиль не передавался. В том же JSON profiles=[]. Повтор с --profile пустой строкой выбрал pipeline-defaults. Оба вызова и проверка сырой схемы завершились с кодом 0.

Свидетельство: <run>/logs/phase1-cli-summary.raw.json, <run>/logs/phase1-cli-no-profile.raw.json, <run>/logs/phase1-cli-raw-validation.log. Этот случай усиливает уже описанное в #763 исправление: отсутствие параметра не должно создавать несуществующий профиль. Полезна регрессия на источнике без профилей и nf-test.

Entry: summarize-nextflow-implicit-test-profile; severity=major. Locator: content/molds/summarize-nextflow/index.md. Наблюдаемый и текущий SHA256 Mold: d8e6759095994ad000fb8b78018da070761a5abfb8cf0a80c6c59b550a272501. Affected skill: summarize-nextflow; SHA256 SKILL.md: f243ace0e42b22e5be5b8c446e5732af976a071a6ae63d0af399a4a235597a85.

## New-issue draft: локальный источник наследует ложное git-происхождение родителя

summarize-nextflow для дерева source/ без собственного git-пина подхватил remote и HEAD родительского iwc-lab. Два обрабатываемых файла source/main.nf и source/data/words.txt не принадлежат указанному коммиту, но source.url стал https://github.com/galaxyproject/iwc-lab.git, source.version - b2638c02991f5b1521f1571f2a5aa2732660f681. Это связывает результаты с чужим исходным содержимым.

Воспроизведение: разместить локальные, не входящие в HEAD файлы Nextflow внутри другого git checkout и выполнить foundry summarize-nextflow source --profile пустой строкой --no-with-nextflow. Свидетельство данного запуска: <run>/logs/phase1-cli-no-profile.raw.json. Примененный локальный обход явно сохраняет file:source/ и содержательный хеш дерева в <run>/logs/phase1-source-provenance.json; это не объявлено git-коммитом.

Ожидаемое исправление: проверять принадлежность обрабатываемых файлов заявленному git-коммиту; при отсутствии собственного проверяемого пина указывать честное локальное происхождение или отсутствие версии. Не наследовать parent remote/HEAD без этой проверки. Поисковые совпадения #351 и #803 относятся соответственно к remote acquisition и provenance готового порта, а не к этой ошибке.

Entry: summarize-nextflow-nested-source-provenance; severity=major. Locator: content/molds/summarize-nextflow/index.md. Наблюдаемый и текущий SHA256 Mold: d8e6759095994ad000fb8b78018da070761a5abfb8cf0a80c6c59b550a272501. Affected skill: summarize-nextflow; SHA256 SKILL.md: f243ace0e42b22e5be5b8c446e5732af976a071a6ae63d0af399a4a235597a85.

## New-issue draft: неполный handoff для единственного безымянного DSL2 workflow

Источник содержит два процесса в main.nf, параметры input/outdir, source = Channel.fromPath(params.input, checkIfExists: true), upper = UPPERCASE(source) и COUNT_LINES(upper) в единственном безымянном workflow. Процессы CLI нашел, но выдал params=[], workflow.channels=[] и workflow.edges=[]. Обычный текст data/words.txt дополнительно получил роль samplesheet. Сырая сводка прошла схему с кодом 0.

Свидетельства: <run>/source/main.nf, <run>/logs/phase1-cli-no-profile.raw.json и <run>/logs/phase1-cli-raw-validation.log. В <run>/phase1-notes.md описано ручное дополнение графа и параметров перед передачей следующей фазе; исходный CLI JSON сохранен отдельно.

Ожидаемое исправление: согласовать поддержку ad-hoc DSL2 между Mold, схемой и CLI. Для единственного безымянного workflow извлекать прямые вызовы, канал и параметры из main.nf либо явно завершать как неподдерживаемый случай. Не называть txt таблицей образцов без свидетельства таблицы. #666, пункт 1, близок по потере графа, но описывает выбор между именованными nf-core workflow. Закрытая #111 касается обнаружения процессов и корня, которое в этом примере уже работает; это отдельный случай.

Entry: summarize-nextflow-anonymous-dsl2-handoff; severity=major. Locator: content/molds/summarize-nextflow/index.md. Наблюдаемый и текущий SHA256 Mold: d8e6759095994ad000fb8b78018da070761a5abfb8cf0a80c6c59b550a272501. Affected skill: summarize-nextflow; SHA256 SKILL.md: f243ace0e42b22e5be5b8c446e5732af976a071a6ae63d0af399a4a235597a85.

## New-issue draft: test-plan Mold требует nf-test evidence для pipeline-defaults без assertions

Выбранный summarize-nextflow кандидат pipeline-defaults имеет assert_workflow_success=null, snapshot=null и prose_assertions=[]. В source нет nf-test. Реальные запуски Nextflow дают наблюденные ожидаемые файлы, но это новые измерения запуска, а не исходный набор assertions. При этом nextflow-test-to-galaxy-test-plan безусловно требует source.derived_from=test-evidence, ссылаясь на наличие реальных nf-test evidence.

Ожидаемое исправление: ветвить происхождение по фактическим исходным assertions. Для данного случая разрешить source.derived_from=intent, отдельно отмечать измеренные значения как fixture-derived и явно фиксировать no-upstream-expected-outputs. Не требовать вымышленного nf-test.

Свидетельства: <run>/summary-nextflow.json, <run>/galaxy-test-plan.yml и реальные исходные результаты, указанные в плане. Закрытая #679 исправляла assertion-level evidence/family; она не закрывает оставшееся безусловное source-level требование. #793 касается выбора кандидата и полей snapshot, а не fallback без исходных assertions.

Entry: nextflow-test-plan-assumes-nf-test-evidence; severity=minor. Locator: content/molds/nextflow-test-to-galaxy-test-plan/index.md. Наблюдаемый и текущий SHA256 Mold: fa769216f621ef25470c9fb907df1278635c0a1e022b647b9462ff7b92469291. Affected skill: nextflow-test-to-galaxy-test-plan; SHA256 SKILL.md: 663497fa43dbb593048924127d6c4e28dd3bd73f73df7a1cb9f66f1145520c4b.

## New-issue draft: File newline override теряется в Galaxy staging

Suspected upstream: galaxy-tool-util 26.1.2, FileUploadTarget/fetch staging; caller Planemo 0.75.48. Каноническая upstream identity: https://github.com/galaxyproject/galaxy. Черновик предназначен для galaxyproject/foundry, чтобы контекст запуска остался вместе с разбором.

Workflow-test schema принимает to_posix_lines:false у File. Проверка установленного Planemo stage_in и galaxy.tool_util.client.staging.upload_func_fetch показала, что для FileUploadTarget fetch payload использует глобальное True вместо свойства конкретного File. В предварительном payload получено to_posix_lines:true. FileLiteralTarget с contents явно передает false. Это свидетельство кода и payload до исполнения, а не утверждение о неудачном Galaxy job.

Ожидаемое исправление upstream: уважать явное значение конкретного File, используя глобальный флаг только как default. Временно Foundry может документировать contents для маленьких UTF-8 fixtures, когда важны точные байты и отсутствие последнего LF. Обход этого запуска сохраняет реальные contents исходников и manifest SHA256; инструменты и эталоны из-за него не изменены.

Entry: galaxy-stager-ignores-file-newline-override; severity=minor. Affected skill: implement-galaxy-workflow-test. Свидетельства: <run>/galaxy-workflow.gxwf-tests.yml, <run>/test-data/manifest.json и logs/runtime-staging-preflight.json. У related-project нет Foundry subject hash; он не придуман. По ограниченным поискам Foundry по to_posix_lines и newline/Planemo дубликат не найден.
