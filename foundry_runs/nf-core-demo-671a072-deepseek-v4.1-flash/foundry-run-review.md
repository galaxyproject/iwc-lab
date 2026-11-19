# Foundry run review — nf-core/demo → Galaxy

## Header

| field | value |
|---|---|
| Model | deepseek-v4.1-flash-thinking (claude-cz profile, CERIT-SC) |
| Harness | Claude Code (claude-cz plugin profile) |
| Foundry skills | `foundry-skills` 0.2.0 (plugin cache `.../galaxy-workflow-foundry/foundry-skills/0.2.0`) |
| Pipeline | `pipeline-nextflow-to-galaxy`, source_revision 5, `_assembly.json` sha256 `d67b4ca056f02fed2046b1ed6898371174f3889511cc7a8179cd4cec3c8a8abc` |
| Phases completed | 13/13 (main run); 9/9 phases of `pipeline-update-interview-to-galaxy` (revision round) |
| Planemo attempts | 6 in the main run (attempt 6 passed); 1 in the revision round (passed) |
| Wall time | main run 2026-11-09 **18:16:37 → 19:28:40** (real timestamps, `date` + artifact mtimes); revision 2026-11-10 **15:31:53 → 15:48** (real) |
| Final result | main run PASS at 19:25:38; revision PASS at 15:45:20 |

Everything below is written from this run's artifacts in this directory (`model-test-log.md`, `summary-nextflow.json`, `galaxy-workflow*.yml`, `revision/`, `planemo-test.log*`). File:line references are to those files.

## A. Foundry skills / notes / schemas / validators

### A1. `summarize-nextflow` emits non-channel fragments as graph edges and misses input channels — **Foundry**
- Evidence: `summary-nextflow.json` `workflow.edges` contains `from` values `"[[:]"`, `"[]]"`, `"files"`, `"}"`; `workflow.channels[]` lists only the anonymous `main.nf` glue channels (`ch_collated_versions`, `ch_multiqc_files`, …) while the edges come from `workflows/demo.nf`; `ch_samplesheet` appears in edges but not in `channels[]`.
- Change: reconcile edges against declared channels and process outputs; drop or flag non-channel fragments; emit `channels[]` for the same workflow that produced the edges. (Filed as feedback in the run's ledger.)

### A2. `summarize-nextflow` drops config-load-time parameter overrides — **Foundry**
- Evidence: `main.nf:29` sets `params.fasta = getGenomeAttribute('fasta')`, but `summary-nextflow.json` reports `params[fasta].source_kind = "nextflow_schema"` with `source_expression: null`. The procedure names this exact example as one to record.
- Change: when a param exists in `nextflow_schema.json` *and* is assigned later at config-load time, record the later assignment (or carry both).

### A3. `galaxy-workflow-comments` note example does not match `gxwf draft-validate` — **Foundry (note)**
- Evidence: the note shows `comments:` as a YAML array of `- type: frame` entries with `text:`. `gxwf draft-validate` rejects that shape (structure error, exit 2) and requires a mapping keyed by comment id with `type: frame` + `title:`. Source: `references/notes/galaxy-workflow-comments.md:39-48` vs the validator.
- Change: show the validator-accepted mapping form; state that the array form is rejected.

### A4. IWC corpus handling is unsafe for parallel runs — **Foundry (skill procedure)**
- Evidence: `compare-against-iwc-exemplar` instructs cloning/pulling into the single shared `~/.foundry/iwc`. A second model-test run on the same machine shares that checkout; a pull during another run's read races. This run skipped the pull and used the checkout at `9f111cb` read-only.
- Change: make the pull opt-in/per-run (run-scoped worktree keyed by commit), or state explicitly that an existing checkout is used read-only.

### A5. Revision guidance does not cover optional-input `RuntimeValue` findings — **Foundry (guidance)**
- Evidence: Galaxy's editor reports unconnected optional datasets as "No value found … Using default: RuntimeValue". Both optional-data `null` encodings I tried were rejected by the validator (`contaminants: Expected never, actual null`; `image_content_input: Expected undefined, actual null`). Per the orchestrator's later correction this state is normal (87/133 IWC workflows, 553 occurrences), but the skills give an agent no way to know that from the bundle.
- Change: state in the summarize/apply guidance that an unconnected optional dataset is the correct representation and must be changed only if the source feeds it; do not attempt to "fix" it with an explicit null.

## B. gxwf tooling

### B1. `gxwf validate --connections` cannot resolve connections sourced from built-in steps — **gxwf**
- Evidence: in both the demo and bamtofastq runs, every consumer of `__FLATTEN__`/`pick_value`/`__MERGE_COLLECTION__` is reported with `source_step: "NaN"`, `status: "skip"`, `"Cannot resolve output … on step NaN"`, while `connection_report.valid` remains true. The built-in's own input connection resolves normally (e.g. `0 output -> 3 input ok`).
- Change: resolve built-in step sources by step index, or emit an explicit "unsupported source" diagnostic instead of `NaN`.

## C. gxformat2 / planemo conversion and staging

### C1. Step `label` shadows the step id in planemo's bundled gxformat2 converter — **gxformat2**
- Evidence: `gxformat2/normalized/_conversion.py::_register_labels` registers `step.label or step.id`. The demo workflow emitted by `draft-extract` carries both `id: flatten_inputs` and a human `label`, so `flatten_inputs/output` fails with `ValueError: invalid literal for int(): 'flatten_inputs'`. Removing every step `label:` fixed conversion; the same happened in bamtofastq with `select_bam`.
- Change: register the id as a reference key in addition to the label. Meanwhile, `draft-extract` could stop emitting labels that shadow ids.

### C2. Planemo's converter rejects the format2 form `gxwf` produces and accepts — **gxformat2**
- Evidence: list-form `inputs:` was rejected (`inputs … Input should be a valid dictionary`), and a data input's `format: fasta` had to be a list (`format: [fasta]`). `gxwf validate` accepts both. The demo workflow needed dict-form inputs + list-form format to convert.
- Change: align the two format2 readers, or document the converter's expected form so a Foundry run does not discover it by bisecting.

### C3. Planemo's collection stager cannot stage a mixed `list:paired_or_unpaired` — **planemo**
- Evidence: `galaxy/tool_util/cwl/util.py::to_elements` asserts `"elements" in value` for every element of a nested collection, so a `list:paired_or_unpaired` with `Collection` (paired) and `File` (unpaired) elements fails with a bare `AssertionError` before any job runs (attempt 4 of the main run).
- Change: support the `paired_or_unpaired` element model, or raise a descriptive staging error naming the unsupported shape.

### C4. Collection assertions need an element-level test or planemo errors at test time — **planemo/tests-format**
- Evidence: a `class: Collection` output with `element_count` but no `element_tests` fails with `No path specified for expected output file [post_fastqc_html]` (bamtofastq attempt 17).
- Change: accept count-only collection assertions, or make the error name the fix ("add element_tests or elements with paths").

### C5. Converter does not synthesize `__current_case__` for nested conditionals; `gxwf` accepts the state Galaxy rejects — **gxformat2 / Foundry validator gap**
- Evidence: bamtofastq `fastx_single` state passed `gxwf draft-validate --concrete --strict-state` but Galaxy failed the tool request until explicit `__current_case__` markers were added to `output_fmt_cond`/`idxout_cond` (attempt 16→17). The native `tool_state` emitted by planemo's converter carried the conditionals without case indices.
- Change: synthesize case indices during conversion, and/or have `gxwf` require them so the failure surfaces before a Galaxy run.

## D. Galaxy

### D1. Comment frame colours must be named literals — **Galaxy**
- Evidence: import rejected with 400 `Input should be 'none', 'black', 'blue', … in ('frame','color')` for `color: "#d9edf7"` (main run attempt 3).
- Change: accept hex colours, or document the enum in the editor/import error (the error text does name the values, which is how it was fixed).

### D2. Workflow `when:` must evaluate to a boolean — **Galaxy/gxformat2**
- Evidence: `when: $(inputs.fasta)` produced `reason=when_not_boolean, details=Type is: NoneType` (bamtofastq run). The Foundry conditional note does not warn that a File/None value is not a boolean; `$(inputs.fasta != null)` is required.
- Change: document the boolean requirement in the conditional note; consider coercing in the engine.

### D3. A skipped step's output is consumed as the literal text `null` by unguarded consumers — **Galaxy**
- Evidence: with `fastx_single` skipped, `post_fastqc` ran and its input file was 4 bytes of ASCII `null` (confirmed in the preserved job dir), producing `FastQC returned non zero exit code` rather than a clear "upstream skipped" error. The Foundry conditional note says skipped steps emit typed null outputs, but does not describe this downstream consumption behaviour.
- Change: Galaxy should mark consumers of skipped outputs as skipped or fail with a clear message; the Foundry note should describe what actually happens.

### D4. FastQC wrapper cannot consume gzip or BAM without extra tooling — **Galaxy (wrapper)**
- Evidence: FastQC invoked as `fastqc -f bam` on a BAM fails in `quay.io/biocontainers/fastqc:0.12.1` because the image has no `samtools` (bamtofastq attempt 5). `fastqc -f fastq` on a gzip stream fails when the Galaxy element name has no `.gz` (mapped element named `test3`), reproduced locally: exit 1 on gzip, exit 0 on the same bytes uncompressed.
- Change: wrapper should detect compression/format instead of forcing `-f fastq`; container should include samtools if BAM input is advertised.

## E. Model issues (mine, recorded for completeness)

- I introduced the stale `when: $(inputs.input_layout == 'single')` in bamtofastq when removing the `input_layout` input; `gxwf validate` did **not** flag a `when` expression referencing a non-existent input, and Galaxy silently skipped the step. (Tooling gap noted in the bamtofastq review; the edit itself was my error.)
- I over-read Galaxy's transient `workflow tool request state: … validation_failed` line as a verdict on a step, and removed working steps on that basis. In demo the runtime failures were: conda env missing `bin/` for `__fastqc@0.12.1`, and a stale/bad input rather than the tools named in the transient lines.
- In the revision round I initially tried explicit `null` for optional datasets before checking that Galaxy's `RuntimeValue` state is normal; corrected by the orchestrator.

## F. Revision round (2026-11-10)

Findings came from `orchestrator-findings-2026-11-10.md` (state-completeness only; no frame problems in this run). Used `pipeline-update-interview-to-galaxy`: `summarize-galaxy-workflow` → `interview-to-galaxy-workflow-changeset` → `apply-galaxy-workflow-changeset` (direct edits, draft loop no-op) → baseline test plan/tests carried unchanged → `validate-galaxy-workflow` → `run-workflow-test`.

Changes applied (whole diff, `galaxy-workflow.before-revision.gxwf.yml` → `galaxy-workflow.gxwf.yml`):

```diff
@@ step fastqc state
+    min_length: null
@@ step multiqc state
+    comment: ''
```

Why: `min_length` is an optional integer (explicit null is legal and states "no limit"); `comment: ""` is the wrapper default. The FastQC optional datasets (`adapters`, `contaminants`, `limits`) and MultiQC `image_content_input` were left unconnected — first because `gxwf` rejects explicit null for optional data params, and, per the orchestrator's correction, because an unconnected optional dataset is normal Galaxy editor state to be changed only when the source feeds it (nf-core/demo feeds none). Validation: `gxwf validate --connections --strict` 5/5 ok; planemo PASS at **15:45:20**.
