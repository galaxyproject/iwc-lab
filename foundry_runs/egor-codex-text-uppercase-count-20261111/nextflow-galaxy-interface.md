# Nextflow to Galaxy interface

## Provenance

Основание: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md` и унаследованный `open-requirements.ledger.yml`. Сводка описывает локальный источник `file:source/`, workflow `text-uppercase-count`, ecosystem `nextflow`, source version `sha256:81abf32dc874c8aab7db43ae1a5a7b959a5cb57017b84abc908f3384bee7740d`. SHA256 прочитанной сводки: `1191ef9056dcc4e74e567e538cd3a820af09516b89fe639c4f22061eb44d4352`.

Источник содержит единственный безымянный workflow; `ANONYMOUS` и `text-uppercase-count` являются обозначениями сводки. Граф и параметры в сводке дополнены по исходнику после статического извлечения; ограничения и происхождение дополнений сохранены в `warnings[]`. Синтетические имена `output_1681429697` и `output_7601658389` не становятся публичными именами Galaxy.

## Scope and semantics

Сохраняются оба процесса и обе публикации: `UPPERCASE` преобразует один текстовый файл, затем `COUNT_LINES` получает именно его результат. Ни один процесс не удаляется и не заменяется заранее вычисленным файлом.

- `UPPERCASE`: сохранить действие `LC_ALL=C tr '[:lower:]' '[:upper:]'`. Преобразуются только строчные ASCII-буквы; не-ASCII-байты, пробелы, пустые строки, порядок строк и наличие либо отсутствие завершающего перевода строки сохраняются. Преобразование регистра Unicode не соответствует этому контракту.
- `COUNT_LINES`: сохранить действие `awk 'END { print "Количество строк: " NR }'`. Считаются записи с обычным разделителем строк AWK, включая пустые записи и последнюю непустую запись без завершающего перевода строки. Пустой файл дает `Количество строк: 0`. Выход содержит русскую подпись, десятичное число и завершающий перевод строки; подпись сохраняется в UTF-8. Простая замена на число символов перевода строки не обеспечивает этот контракт.

Выбор конкретных оберток, версий и портов инструментов выполняют последующие этапы. Этот документ определяет интерфейс и проверяемое поведение, а не конкретную схему gxformat2.

## Workflow inputs

| Field | Decision |
|---|---|
| Public id and effective label | `text_input` |
| Description | Исходный обычный текстовый файл. |
| `source_param` | `input` |
| `evidence` | `params[name=input]`; `workflow.channels[name=source]`: `construct=fromPath`, `from_param=input`, `source=Channel.fromPath(params.input, checkIfExists: true)`; `UPPERCASE.inputs[name=source_text]`. |
| `galaxy_input_type` | `data` |
| `galaxy_shape` | `File`: один dataset, без коллекции. |
| `format` | `txt` |
| `collection_type` | Не применяется. |
| `optional` | `false` |
| `default` | Не задается в Galaxy. |
| `requiredness_basis` | Без файла оба процесса не имеют входа. Исходное `required=false` отражает существующий локальный default, а не допустимость отсутствия данных. `required_runtime=false` не означает необязательность: этот флаг сводки относится к отдельному шаблону `.ifEmpty { error ... }`. |
| Source default | `${projectDir}/data/words.txt`: источник тестового примера, не путь на сервере Galaxy. |
| Fixture | Выбранный `test_candidates[id=pipeline-defaults].inputs[role=source_text]`: `data/words.txt`, `filetype=txt`, SHA1 `903bd24c965e537f3b4c3dea1298fb749691f740`. Относительный путь считается от `source/`; последующий этап переносит fixture в тестовый набор. |
| Confidence | Высокая для одиночной формы и обязательности; средняя для `txt`, основанная на `filetype`, назначении текста и командах, а не только суффиксе `.txt`. |
| Known losses | Локальный путь по умолчанию заменяется явным выбором dataset из истории Galaxy. Семантика обработки текста сохраняется. |

Параметр `input` не материализует samplesheet: `sample_sheets=[]`, нет `splitCsv`, парных файлов, метаданных образцов или повторяемого потока файлов. Не создавать скалярный путь, CSV-вход или коллекцию только из названия параметра.

## Workflow outputs

| Public id and effective label | Source evidence | Galaxy shape and format | Purpose |
|---|---|---|---|
| `uppercase_text` | `UPPERCASE.outputs[name=output_1681429697]`, `path 'uppercase.txt'`, `publish_dir=params.outdir, mode: 'copy'`; выбранный fixture output `role=uppercase`, `results/uppercase.txt`. | Один `File`, `format=txt`. Форма: высокая уверенность; формат: средняя. | Публичный результат преобразования и checkpoint перед подсчетом строк; этот же dataset передается в `COUNT_LINES`. |
| `line_count_summary` | `COUNT_LINES.outputs[name=output_7601658389]`, `path 'summary.txt'`, `publish_dir=params.outdir, mode: 'copy'`; выбранный fixture output `role=line_count`, `results/summary.txt`. | Один `File`, `format=txt`. Форма: высокая уверенность; формат: средняя. | Публичный итоговый текстовый отчет с точной подписью и числом записей `NR`. |

Файлы `uppercase.txt` и `summary.txt` сохраняются как исходные имена и смысл результатов. Galaxy управляет физическими путями и именами dataset в истории; имена инструментальных выходных портов должны быть подтверждены оберткой. Последующий шаблон задает реальные `outputSource`, не выводя имена портов из синтетических идентификаторов сводки.

## Labels and checkpoint outputs

Использовать одинаковые `id` и `label`: `text_input`, `uppercase_text`, `line_count_summary`. Русские пояснения хранить в `doc` или описаниях. Эти стабильные имена предназначены для `job:` и `outputs:` будущего теста; после импорта или конвертации проверить фактические имена интерфейса.

`uppercase_text` уже является публикуемым исходным результатом и достаточным checkpoint: сравнение только количества строк не обнаружит ошибку преобразования регистра. Дополнительных промежуточных публичных выходов не требуется. Будущий тест должен проверять содержимое обоих файлов относительно реального Nextflow-эталона выбранного fixture, включая UTF-8 подписи и переводы строк; проверка существования или ненулевого размера недостаточна. Сводка не содержит nf-test assertions или snapshot, поэтому эти проверки являются требованиями перевода, а не унаследованными проверками исходника.

## Excluded parameters and notice

Единое уведомление: из интерфейса Galaxy исключен параметр публикации `outdir`; результаты `uppercase.txt` и `summary.txt` выдаются как два именованных выхода в истории Galaxy.

| `source_param` | `class` | `effect` | `assessment` | Reason |
|---|---|---|---|---|
| `outdir` | `publish` | Определяет каталог двух `publishDir` с `mode: 'copy'`. | `safe` | В сводке не входит в скрипты, создание канала, условия или аргументы обработки. Galaxy управляет публикацией dataset; оба процесса и оба результата остаются. |

Основание исключения: packaged `nextflow-params-to-galaxy-inputs`, разделы `Control params` и `Warning and impact assessment`. Решение зафиксировано в `decisions[id=exclude-outdir-publication-control]`; исключенная поверхность учтена отдельно как `entries[id=drop-outdir-publication-interface]`, `kind=dropped`. Ее статус остается `open` по протоколу учета исключений до терминального этапа; это не вычислительный блокер и не отказ от результата обработки.

## Collections and reference data

Все входы и выходы одиночные. `collection_type`, идентификаторы элементов и операции над коллекциями не нужны. Справочные активы, индексы, data tables, `dbkey` и rebuild отсутствуют согласно `reference_assets=[]`, `reference_rebuilds=[]` и brief справочных данных. Унаследованная discovery `no-external-reference-assets` сохраняется без изменений.

## Confidence and known losses

Высокая уверенность: один исходный файл, два последовательных процесса, два публичных dataset, отсутствие ветвления, коллекций и справочных данных. Средняя уверенность для datatype `txt`: обработка является текстовой, однако у источника нет nf-schema или MIME-декларации. Не повышать специфичность до `tabular` только из возможного содержимого `.txt`.

У источника нет закрепленных версий `tr`, `awk`, контейнера или Conda. Не придумывать исходные версии. Конкретные версии целевых оберток и окружение будут подтверждены при реализации; точное поведение остается заданным выше. Без реального Galaxy-запуска и сравнения двух результатов соответствие перевода еще не подтверждено.

## Open obligations

Унаследованных открытых обязательств нет. Добавлено только осознанное исключение `drop-outdir-publication-interface` со статусом `open`, без `blocking=true`. Открытых вопросов о числе входов, форме коллекций, публичных результатах или справочных данных нет. Последующие этапы должны сохранить два процесса, подтвердить конкретные инструментальные порты и проверить оба результата; этим brief не объявляется успешный запуск Galaxy.

## Validation

Вход `summary-nextflow.json` проверен source-built CLI `packages/gxwf-foundry/dist/bin/foundry.js validate-summary-nextflow` с ожидаемым schema SHA256 `1b8872152de9be50634b3ec73cfd5963ae0ec19a95ccb99f6fe734f42656d80d`: `valid`, exit code 0. В `_verify.json` данного skill нет валидатора выходного Markdown; раздел `Validation` skill не объявляет других проверок.

## Feedback

no feedback: полный skill и примененные packaged references покрыли выбор формы, обязательности, имен, двух результатов и исключение параметра публикации. На этом этапе новых наблюдений об ошибках Foundry или связанных проектов не возникло.
