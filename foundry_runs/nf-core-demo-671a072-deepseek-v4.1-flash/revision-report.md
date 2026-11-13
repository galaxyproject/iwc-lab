# Revision report — nf-core-demo-deepseek (2026-11-10)

Baseline preserved as `galaxy-workflow.before-revision.gxwf.yml`. Revised workflow: `galaxy-workflow.gxwf.yml`.

## Findings and decisions

Source: `orchestrator-findings-2026-11-10.md`.

| # | finding | decision | why |
|---|---|---|---|
| 1 | `fastqc.adapters` missing from state | **unchanged** | Optional data input. nf-core/demo passes no adapter list, and `gxwf validate --strict` rejects an explicit `null` (`Expected never, actual null`). An omitted key is the correct unconnected-input representation; Galaxy's "RuntimeValue" note is the editor's rendering of that optionality. |
| 2 | `fastqc.contaminants` missing | **unchanged** | Same: optional data, null rejected by the schema. |
| 3 | `fastqc.limits` missing | **unchanged** | Same. |
| 4 | `fastqc.min_length` missing | **changed → `null`** | Optional integer; explicit null states "no lower length limit" and is schema-legal. |
| 5 | `multiqc.comment` missing | **changed → `""`** | Text parameter; the wrapper default and nf-core's behaviour, made explicit. |
| 6 | `multiqc.image_content_input` missing | **unchanged** | Optional data; `null` is rejected (`Expected undefined, actual null`), so the absent key is the only legal "unset" form. |

Frames: the findings report none for this run; no frame was touched.

Applied diff (whole revision):

```
72a73
>     min_length: null
113a115
>     comment: ''
```

No step, wiring, tool version, output, or `position`/`size` changed.

## Foundry skills and commands used

Pipeline `foundry-skills:pipeline-update-interview-to-galaxy` (revision 3), phases:

1. `foundry-skills:summarize-galaxy-workflow` → `revision/summary-galaxy-workflow.json` (validated with `foundry validate-summary-galaxy-workflow --schema-sha256 55831dd0…`) + `revision/starting-galaxy-workflow.gxwf.yml`.
2. `foundry-skills:interview-to-galaxy-workflow-changeset` → `revision/galaxy-workflow-changeset.md` (findings file as the interview input).
3. `foundry-skills:apply-galaxy-workflow-changeset` → direct edits applied inline to `revision/galaxy-workflow-draft.gxwf.yml`, then to `galaxy-workflow.gxwf.yml`. Probe with `gxwf validate --strict` used to classify which missing values are expressible.
4. `advance-galaxy-draft-step` loop — **no-op**: the change-set contains only direct edits, so the workflow stayed concrete (`draft: false`).
5. `changeset-to-galaxy-test-plan` — baseline test plan carried forward unchanged (`revision/galaxy-test-plan.revised.yml`); no behavioural delta to augment.
6. `implement-galaxy-workflow-test` — existing `galaxy-workflow.gxwf-tests.yml` carried unchanged.
7. `validate-galaxy-workflow` — `gxwf validate galaxy-workflow.gxwf.yml --connections --strict --json` → 5/5 ok, `connection_report.valid: true` (`revision/validation.json`).
8. `run-workflow-test` — `flock /tmp/galaxy-arash-planemo.lock planemo test galaxy-workflow.gxwf.yml --biocontainers --docker --test_output revision/test-output --test_output_json revision/planemo-test-result.json`.
9. `debug-galaxy-workflow-output` — not needed (green).

## Results

- **gxwf validation:** pass (5/5 tool states, connections valid).
- **planemo test:** **PASS**, `All 1 test(s) executed passed`, exit 0, 2026-11-10 15:45:20 (`revision/planemo-test.log`, `revision/planemo-test-result.json`).
- Test assertions unchanged (the same four workflow outputs as before the revision).

## Blocked / notes

- No blockers.
- The three optional FastQC datasets and MultiQC's image input cannot be given an explicit "unset" value in gxformat2 state; Galaxy will keep showing its informational hint for them. That is a wrapper/editor representation limit, not a workflow defect, and no value was fabricated.
- The revision pipelines' fixed filenames (`foundry-run.yml`, `foundry-feedback.ledger.yml`) were **not** overwritten: the completed run records are preserved and revision artifacts live under `revision/`.

## Correction incorporated (2026-11-10)

The orchestrator clarified that a `RuntimeValue` entry for an **unconnected optional dataset** is not a defect — it is exactly what Galaxy's own editor saves (87 of 133 IWC workflows carry this state, 553 occurrences). An optional dataset should be connected only if the nf-core source actually feeds it. Checked against the source: nf-core/demo and nf-core/bamtofastq pass no adapter list, contaminant list, limits file or MultiQC image content to these tools (`FASTQC` receives only `--quiet`; `MULTIQC` receives neither), so the correct resolution is to leave those inputs unconnected. The revision therefore changes none of them, and the reports' earlier schema-based justification is superseded by this stronger, corpus-grounded one.
