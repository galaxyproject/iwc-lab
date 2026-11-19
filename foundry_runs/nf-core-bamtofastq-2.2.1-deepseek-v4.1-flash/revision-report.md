# Revision report — nf-core-bamtofastq-deepseek (2026-11-10)

Baseline preserved as `galaxy-workflow.before-revision.gxwf.yml`. Revised workflow: `galaxy-workflow.gxwf.yml`.

## Findings and decisions

Source: `orchestrator-findings-2026-11-10.md`.

### §1 "Issues loading this workflow"

| # | finding | decision | why |
|---|---|---|---|
| 1 | `fastx_single.copy_arb_tags` missing | **changed → `null`** | Optional text; no arbitrary tags are copied. Explicit null is schema-legal and states the intent. |
| 2 | `fastx_single.inclusive_filter` missing | **changed → `[]`** | No flags are required; nf-core passes no `-f`. |
| 3 | `fastx_single.exclusive_filter` missing | **changed → `['256','2048']`** | Galaxy substituted this default. It equals both the wrapper default and `samtools fastq`'s own `-F 0x900`, and nf-core adds no filter, so the value is scientifically correct — made explicit so the workflow no longer depends on an editor substitution. |
| 4 | `fastx_single.exclusive_filter_all` missing | **changed → `[]`** | No "all flags" exclusion. |
| 5 | `post_fastqc.adapters` missing | **unchanged** | Optional data input; nf-core passes none and `gxwf` rejects an explicit `null` (`Expected never, actual null`). Omitted key = unconnected optional input. |
| 6 | `post_fastqc.contaminants` missing | **unchanged** | Same. |
| 7 | `post_fastqc.limits` missing | **unchanged** | Same. |
| 8 | `post_fastqc.min_length` missing | **changed → `null`** | Optional integer; explicit null is legal and states "no length limit". |
| 9 | `multiqc.comment` missing | **changed → `""`** | Text; wrapper default made explicit. |
| 10 | `multiqc.image_content_input` missing | **unchanged** | Optional data; null rejected (`Expected undefined, actual null`). |

### §2 Frames

| # | finding | decision | why |
|---|---|---|---|
| 11 | frame `stage-input` ("Inputs and contig selection") empty | **removed** | Its intended members (`normalize_inputs`, `chr_extract`, `pick_value` steps) were dropped from this translation as recorded losses (`open-requirements.ledger.yml`), so an empty frame only draws an empty box. |
| 12 | frame `stage-qc-stats` ("Pre-conversion QC and stats") empty | **removed** | Same: its members (`stats`, `flagstat`, `idxstats`, `pre_fastqc`) were dropped. |

Remaining frames `stage-convert` and `stage-post` already group every remaining step and were left untouched, including their `position`/`size`.

### Applied diff (whole revision)

```
87a88
>       min_length: null
127a129
>       comment: ''
153a156,161
>       copy_arb_tags: null
>       inclusive_filter: []
>       exclusive_filter:
>       - '256'
>       - '2048'
>       exclusive_filter_all: []
155,176d162
<   stage-input: … (12 lines removed)
<   stage-qc-stats: … (10 lines removed)
```

No step set, wiring, tool version, output, or step `position` changed.

## Foundry skills and commands used

Pipeline `foundry-skills:pipeline-update-interview-to-galaxy` (revision 3), phases:

1. `foundry-skills:summarize-galaxy-workflow` → `revision/summary-galaxy-workflow.json` (validated with `foundry validate-summary-galaxy-workflow --schema-sha256 55831dd0…`) + `revision/starting-galaxy-workflow.gxwf.yml`.
2. `foundry-skills:interview-to-galaxy-workflow-changeset` → `revision/galaxy-workflow-changeset.md`.
3. `foundry-skills:apply-galaxy-workflow-changeset` → direct edits applied to `revision/galaxy-workflow-draft.gxwf.yml` and to `galaxy-workflow.gxwf.yml`. `gxwf validate --strict` was used to classify which missing values are expressible (explicit nulls accepted for `copy_arb_tags`/`min_length`/`comment`; rejected for optional data parameters).
4. `advance-galaxy-draft-step` loop — **no-op**: only direct edits, workflow stayed concrete.
5. `changeset-to-galaxy-test-plan` — baseline test plan carried unchanged (`revision/galaxy-test-plan.revised.yml`); the flag-filter values reproduce the previous effective behaviour, so no assertion delta.
6. `implement-galaxy-workflow-test` — `galaxy-workflow.gxwf-tests.yml` carried unchanged; `gxwf validate-tests … --workflow` OK.
7. `validate-galaxy-workflow` — `gxwf validate galaxy-workflow.gxwf.yml --connections --strict --json` → 4/4 ok, `connection_report.valid: true` (`revision/validation.json`).
8. `run-workflow-test` — `flock /tmp/galaxy-arash-planemo.lock planemo test galaxy-workflow.gxwf.yml --biocontainers --docker --test_output revision/test-output --test_output_json revision/planemo-test-result.json`.
9. `debug-galaxy-workflow-output` — not needed (green).

## Results

- **gxwf validation:** pass (4/4 tool states; connections valid).
- **planemo test:** **PASS**, `All 1 test(s) executed passed`, exit 0, 2026-11-10 **15:49:03** (`revision/planemo-test.log`, `revision/planemo-test-result.json`). Started 15:47:07; no retries.
- Test assertions unchanged (4 workflow outputs; count/type-level as before).

## Blocked / notes

- No blockers.
- The FastQC optional datasets and MultiQC `image_content_input` cannot carry an explicit "unset" in gxformat2 state; the editor's informational hint will remain for them. No value was fabricated.
- The original run's `foundry-run.yml` and `foundry-feedback.ledger.yml` were not overwritten; revision artifacts live under `revision/`.

## Correction incorporated (2026-11-10)

The orchestrator clarified that a `RuntimeValue` entry for an **unconnected optional dataset** is not a defect — it is exactly what Galaxy's own editor saves (87 of 133 IWC workflows carry this state, 553 occurrences). An optional dataset should be connected only if the nf-core source actually feeds it. Checked against the source: nf-core/demo and nf-core/bamtofastq pass no adapter list, contaminant list, limits file or MultiQC image content to these tools (`FASTQC` receives only `--quiet`; `MULTIQC` receives neither), so the correct resolution is to leave those inputs unconnected. The revision therefore changes none of them, and the reports' earlier schema-based justification is superseded by this stronger, corpus-grounded one.
