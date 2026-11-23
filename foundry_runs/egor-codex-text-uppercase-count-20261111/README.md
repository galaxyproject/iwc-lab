# Foundry: Nextflow в Galaxy, учебный текстовый workflow

Реальный результат: три теста Planemo прошли в локальном Galaxy; шесть выходов побайтово совпали с результатами исходного Nextflow. Два процесса и два опубликованных файла сохранены. Это небольшой пользовательский DSL2 пример, не конверсия nf-core.

| Вход | ASCII-преобразование | Счетчик строк |
| --- | --- | --- |
| Исходные три строки | Совпадение с Nextflow | 3 |
| UTF-8, последняя строка без LF | Совпадение с Nextflow | 2 |
| Пустой файл | Пустой результат | 0 |

Выполнены 13 этапов cast pipeline `nextflow-to-galaxy` revision 5 с feedback. Авторские этапы исполнял текущий агент Codex по официальным SKILL.md; CLI и framework запускались реально. Ручные исправления сырой сводки раскрыты в `phase1-notes.md`. Точный ID модели и стоимость неизвестны, поэтому запуск не предлагается как точка сравнения конкретных моделей.

## Навигация

- `foundry-run-review.md`: результат, покрытие этапов и разбор пяти наблюдений.
- `foundry-run.yml`, `foundry-feedback.ledger.yml`: закрытые журналы запуска и feedback.
- `source/`: неизмененный исходный Nextflow; `nextflow-results/`, `nextflow-reference/`: настоящие исходные исполнения.
- `galaxy-workflow.gxwf.yml`, `galaxy-workflow.gxwf-tests.yml`: конкретный workflow и три теста.
- `reports/planemo-test-output.json`: настоящий отчет Planemo с invocation, history и job IDs; HTML/XML лежат рядом.
- `galaxy-results/`: шесть фактических скачиваний и их сопоставление с Nextflow.
- `reports/galaxy-dataset-metadata.json`: отдельная проверка фактического типа `txt` и состояния шести выходов.
- `workflow-debug-report.md`, `workflow-limitations.md`: первая ошибка среды, ее исправление и границы результата.
- `foundry-issue-drafts.md`: локально подготовленные предложения; отдельные issues/comments не отправлялись.
- `artifact-manifest.json`, `redactions.json`: хеши публикуемых файлов и раскрытие замены локальных путей.

## Повторный запуск

Нужны Planemo `0.75.48`, Python `3.12`, Galaxy и Conda. В исходном исполнении Galaxy `26.1.3.dev0` загружен Planemo штатно, без `--galaxy_branch`; точный Git commit tarball неизвестен. Использованы `gxwf 1.15.0`, Nextflow `26.10.4` build `14435`, Temurin `21.0.13+9`, macOS arm64.

Оба XML-инструмента устанавливаются из `bgruening/text_processing`, changeset `ab83aa685821`, wrapper version `9.5+galaxy3`. Зависимости: `sed=4.9` и `gawk=5.3.1`; исходные Conda builds указаны в `reports/execution.json`. Docker и Singularity для этого workflow не использовались.

Рабочий каталог следующей команды: эта папка run. Перед вызовом задайте `GX_SOURCE_ROOT` для подготовленного Galaxy, `GX_DEPENDENCY_PREFIX` для Conda с окружениями `__sed@4.9` и `__gawk@5.3.1`, `GX_PLANEMO_WORK` для рабочего каталога Planemo. Отчеты ниже пишутся в новый каталог и не затирают сохраненные результаты.

```bash
mkdir -p replay-reports
GX_TEST_TEMP=$(mktemp -d /tmp/bh31.XXXXXX)
TMPDIR="$GX_TEST_TEMP" planemo --directory "$GX_PLANEMO_WORK" test galaxy-workflow.gxwf.yml \
  --engine galaxy --galaxy_root "$GX_SOURCE_ROOT" --galaxy_python_version 3.12 \
  --conda_prefix "$GX_DEPENDENCY_PREFIX" --conda_exec "$GX_DEPENDENCY_PREFIX/bin/conda" \
  --conda_dependency_resolution --no_conda_auto_init --no_conda_auto_install \
  --no_install_resolver_dependencies --no_docker --no_singularity --no_use_cache --no_cleanup \
  --test_timeout 600 --summary compact \
  --test_output_json replay-reports/planemo-test-output.json \
  --test_output replay-reports/planemo-test-output.html \
  --test_output_xunit replay-reports/planemo-test-output.xml
```

Короткий TMPDIR нужен для Unix-сокетов на macOS; не удаляйте его до сохранения скачиваний. `reports/execution.json` содержит фактически исполненные argv и окружение данного запуска с замененными локальными префиксами. Установка Planemo описана в https://planemo.readthedocs.io/ .

Входы tests передаются через `contents`, поскольку проверенный клиент игнорировал `to_posix_lines:false` у файлов с `path`. Эталоны являются копиями реальных результатов Nextflow. Assertions не ослаблялись; два дополнительных граничных входа не называются исходными nf-test.
