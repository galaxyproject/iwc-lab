# Galaxy template handoff

## Topology and resolution

Создан galaxy-workflow-draft.gxwf.yml, class GalaxyWorkflowDraft. Топология окончательная: один обязательный одиночный txt-вход text_input, затем uppercase -> count_lines. Первый результат одновременно опубликован как uppercase_text и подан в count_lines; второй опубликован как line_count_summary. Идентификаторы и labels публичного интерфейса совпадают. Два статических имени dataset: uppercase.txt и summary.txt.

Оба шага имеют уровень Deferred: tool_id=TODO и только имена портов TODO_*. Неизвестных узлов, источников, форм входа, выходов или ветвей в топологии нет. _plan_state, _plan_context, _plan_in и _plan_out передают исходные команды, точную семантику и назначение портов. Синтетические source output_* не становятся именами портов Galaxy.

Packaged galaxy-tabular-patterns содержит общие табличные рецепты, но не совместно подтвержденные параметры для нашей пары ASCII uppercase и AWK NR. Подходящего IWC exemplar тоже нет. Поэтому произвольные обертки и состояния на этой фазе не закреплены. Проверенные harness кандидаты tp_sed_tool и tp_awk_tool проверяет фаза 7; список кандидатов сам по себе не доказывает байтовую эквивалентность их настроек.

## Computability review

uppercase получает исходный текст и может вычислить требуемый текст без внешней информации. count_lines получает именно этот результат и может вычислить NR с фиксированной русской подписью. Оба результата полностью определяются поданными файлами и константными правилами. Отсутствующих производителей или скрытых вторых dataset-входов нет. Дополнительные узлы, коллекции, условия, справочные активы и структурные блокеры не добавлены.

В журнал добавлено решение settled-text-template-topology. Обязательства drop-outdir-publication-interface и text-semantics-needs-executable-evidence сохранены open без изменения содержания и provenance. Реализация и фактический тест еще должны доказать текстовую семантику; структура draft не закрывает это обязательство.

## Actual validation

- gxwf draft-validate galaxy-workflow-draft.gxwf.yml --json: exit 0, ok=true, structure_errors=[], topology_errors=[], semantic_errors=[], warnings=[]. Лог logs/phase6-draft-validation.json; stderr logs/phase6-draft-validation.stderr.log пуст.
- gxwf draft-next-step galaxy-workflow-draft.gxwf.yml: exit 0, draft=true, step=[uppercase]. Лог logs/phase6-draft-next-step.json; stderr logs/phase6-draft-next-step.stderr.log пуст.
- jsonschema.Draft202012Validator проверил YAML по полному packaged references/schemas/galaxy-workflow-draft.schema.json: exit 0, status=pass, errors=[]. Лог logs/phase6-schema-validation.json.

Восемь TODO-ссылок/полей остаются только в разрешенной поверхности оберток и портов. draft=true означает, что фаза реализации еще нужна. Проверка состояния конкретных инструментов, импорт и выполнение Galaxy этими проверками не объявляются успешными.

## Feedback

no feedback: полный skill и примененные packaged references покрыли разрешенный Deferred-уровень, точные имена интерфейса, публичный checkpoint, граф и вычислимость. Новых наблюдений об ошибках Foundry или связанных проектов нет. Три записи обратной связи фазы 1 сохранены. Источник, Foundry source и lifecycle не изменены.
