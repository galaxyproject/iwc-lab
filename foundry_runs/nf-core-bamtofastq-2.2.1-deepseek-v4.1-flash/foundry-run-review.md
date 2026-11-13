# Foundry run review — nf-core/bamtofastq → Galaxy

## Header

| field | value |
|---|---|
| Model | deepseek-v4.1-flash-thinking (claude-cz profile, CERIT-SC) |
| Harness | Claude Code (claude-cz plugin profile) |
| Foundry skills | `foundry-skills` 0.2.0 (plugin cache `.../galaxy-workflow-foundry/foundry-skills/0.2.0`) |
| Pipeline | `pipeline-nextflow-to-galaxy`, source_revision 5, `_assembly.json` sha256 `d67b4ca056f02fed2046b1ed6898371174f3889511cc7a8179cd4cec3c8a8abc` |
| Phases completed | 13/13 (main run); 9/9 phases of `pipeline-update-interview-to-galaxy` (revision round) |
| Planemo attempts | **18** in the main run (attempt 18 passed); 1 in the revision round (passed) |
| Wall time | main run 2026-11-09 **23:26:47 → 2026-11-10 00:53:19** (real timestamps, `date` + artifact mtimes); revision 2026-11-10 **15:31:53 → 15:51:30** (real) |
| Final result | main run PASS at **00:51:12**; revision PASS at **15:49:03** |

Written from this directory's artifacts (`model-test-log.md`, `planemo-test.log*`, `summary-nextflow.json`, `galaxy-workflow*.yml`, `open-requirements.ledger.yml`, `revision/`).

## A. Foundry skills / notes / research

### A1. `summarize-nextflow` edge extraction emits fragments; 18 of 34 edges are non-channel text — **Foundry**
- Evidence: `summary-nextflow.json` `workflow.edges` for bamtofastq contain `from` values `"[[:]"`, `"[]]"`, `"[id: 'bamtofastq']"`, `"files"`, `"}"`; `SAMTOOLS_CHR` has six fragment sources; `workflow.channels[]` and edges come from different workflow bodies.
- Change: reconcile edges against channels/process outputs; drop or flag non-channel fragments.

### A2. `reference_rebuilds[]` misses the `meta.index` compute-if-missing branch — **Foundry**
- Evidence: `summary-nextflow.json` `reference_rebuilds` is `[]` although `subworkflows/local/prepare_indices/main.nf:40-47` runs `SAMTOOLS_FAIDX` on the `meta.index == false` branch. The reference-data bundle documents the positive-form gap but not this `meta.index` form, so the asset had to be classified by re-reading source.
- Change: detect the `meta.index` branch (or add it to the documented known-gap list with a concrete example).

### A3. `tool-search` cannot find an existing iuc wrapper by its human name — **Foundry tooling (gxwf CLI)**
- Evidence: `gxwf tool-search "samtools view"` returns no iuc samtools hits and `"samtools collate fastq"`/`"collatefastq"` return none, while `gxwf tool-versions iuc~samtools_view~samtools_view` resolves `1.22+galaxy2`. A discovery pass trusting the phrase query would author a wrapper that already exists.
- Change: improve the lexical index or have `discover-shed-tool` try the underscore-collapsed candidate name when a phrase query misses.

### A4. No guidance that `pick_value` cannot carry whole collections — **Foundry (research gap)**
- Evidence: feeding two collections into `iuc/pick_value` yielded a `data_param` the downstream `samtools_collate` job could not read (exit 1, attempt 3→4). The conditional/collection notes present `pick_value` as the fan-in primitive without this restriction.
- Change: state the single-dataset restriction and recommend mutually exclusive `when:`-guarded producers + `__MERGE_COLLECTION__` for collections.

### A5. Optional-input `RuntimeValue` findings need explicit guidance — **Foundry**
- Evidence: revision round. Galaxy's editor reports unconnected optional datasets as "RuntimeValue"; explicit `null` is rejected by `gxwf` (`adapters/contaminants/limits: Expected never, actual null`), and per the orchestrator's correction that editor state is normal (87/133 IWC workflows). The bundle gives no way to know this from the skills.
- Change: document that unconnected optional datasets are correct and should be changed only when the source feeds them.

## B. gxwf tooling / validators

### B1. `validate --connections` reports `source_step: NaN` for built-in step sources — **gxwf**
- Evidence: every consumer of `__FLATTEN__`, `pick_value`, `__MERGE_COLLECTION__`, `__ZIP_COLLECTION__` is reported `status: "skip"`, `"Cannot resolve … on step NaN"`, while `valid: true`. Cross-step collection compatibility is therefore unchecked for most of this workflow.
- Change: resolve built-in sources by index or emit an explicit unsupported diagnostic.

### B2. `gxwf` accepts `when:` expressions that reference non-existent inputs — **Foundry validator gap (critical for this run)**
- Evidence: after removing `input_layout`, `fastx_single` still carried `when: $(inputs.input_layout == 'single')`. `gxwf draft-validate --concrete --strict-state` and `gxwf validate --strict` both passed (7/7 validated), yet Galaxy evaluated the missing input as null and **skipped the step**, which then fed the 4-byte `null` sentinel into FastQC (confirmed with `--no_cleanup`). This silent skip drove attempts 9–15 and most of the feature removals.
- Change: have `draft-validate`/`validate` check `when:` expressions against declared inputs (and step outputs) and fail on unknown references. A one-line reference check would have saved ~8 attempts.

### B3. Validator accepts conditional state that Galaxy rejects — **Foundry validator gap / gxformat2**
- Evidence: `fastx_single` state passed `--strict-state` but Galaxy failed the request until explicit `__current_case__` markers were added (attempt 16→17). Planemo's converter does not synthesize them.
- Change: require/synthesize case indices so validation matches Galaxy's expectations.

### B4. Map-over arity is not validated — **gxwf**
- Evidence: connecting a single `fasta` dataset to steps mapped over a collection produced `state=validation_failed` at scheduling (attempt 13), which `gxwf` accepted statically.
- Change: connection check should flag a non-collection source feeding a mapped-over tool input (or explicitly state it is unsupported), instead of leaving it to runtime.

## C. gxformat2 / planemo

### C1. Step `label` shadows step `id` in reference resolution — **gxformat2**
- Evidence: `_register_labels` uses `step.label or step.id`; `draft-extract` emits both, so `flatten_inputs/output` fails with `ValueError: invalid literal for int(): 'flatten_inputs'` (attempt 1). Removing labels fixed it.
- Change: register the id in addition to the label; and/or stop emitting shadowing labels from `draft-extract`.

### C2. Converter expects dict-form `inputs` and list-form `format` — **gxformat2**
- Evidence: list-form `inputs` rejected (`Input should be a valid dictionary`); `format: fasta` rejected until `format: [fasta]`. `gxwf` accepts both forms.
- Change: align the readers, or document the converter's expected shape.

### C3. `__current_case__` not synthesized during conversion — **gxformat2**
- Evidence: see B3; native `tool_state` from planemo's converter carried nested conditionals without case indices.

### C4. Failed-job evidence is deleted unless `--no_cleanup` — **planemo / Foundry guidance**
- Evidence: the decisive evidence (FastQC input = 4 bytes `null`) existed only because attempt 15 was run with `--no_cleanup`; earlier attempts' job dirs were gone.
- Change: `run-workflow-test` should recommend `--no_cleanup` (or an evidence-preserving mode) for any failing run, and say what to look for.

### C5. Count-only collection assertions are rejected at test time — **planemo/tests-format**
- Evidence: `post_fastqc_html` with `element_count` but no `element_tests` → `No path specified for expected output file [post_fastqc_html]` (attempt 17).
- Change: accept count-only assertions or make the error name the remedy.

## D. Galaxy

### D1. `when:` must be boolean — **Galaxy**
- Evidence: `when: $(inputs.fasta)` → `when_not_boolean, details=Type is: NoneType` (attempt 2).
- Change: document the boolean requirement in the Foundry conditional note; consider engine coercion.

### D2. Unguarded consumers run on a skipped step's `null` sentinel — **Galaxy**
- Evidence: `fastx_single` skipped; `post_fastqc` ran on a 4-byte file containing `null` and failed with "FastQC returned non zero exit code", hiding the real cause for several attempts.
- Change: propagate skip/fail clearly to consumers, or make the sentinel unreadable as a dataset.

### D3. Region queries need an index the workflow cannot attach — **Galaxy (wrapper/workflow gap)**
- Evidence: `samtools view -hb <regions>` requires a `.bai`; the iuc `samtools_view` wrapper has no index input, and Galaxy cannot attach a separately computed index to a mapped dataset. The toy BAM's contigs are `1`/`2`, so the chr filter would yield nothing anyway.
- Change: wrappers accepting regions should index internally or accept an index collection; otherwise document the limitation.

### D4. devteam `samtools_stats`/`flagstat`/`idxstats` (2.0.x) are stale and their requests show transient `validation_failed` — **Galaxy (wrappers)**
- Evidence: the trio is only on the shed under `devteam` at 2.0.x; request-monitor lines read `validation_failed` while jobs were still set up and dispatched (attempt 14, `planemo-test.log.attempt14:3937,3944`).
- Change: publish current iuc stats/flagstat/idxstats wrappers; the transient state also contributed to my misdiagnosis.

### D5. FastQC wrapper cannot decode BAM and mishandles gzip elements — **Galaxy (wrapper)**
- Evidence: `fastqc -f bam` fails in `quay.io/biocontainers/fastqc:0.12.1` (no samtools); `-f fastq` fails on gzip when the mapped element is named `test3` without `.gz` (reproduced locally: exit 1 gzip, exit 0 uncompressed).
- Change: detect format/compression inside the wrapper.

## E. Model issues (mine)

- I introduced the stale `when:` guard (removed `input_layout`, left its guard). This is the run's dominant failure; see B2 for the validator gap that let it pass.
- I treated Galaxy's transient `workflow tool request state: … validation_failed` line as a step verdict and removed working steps on that basis. The attempt-14 log shows the stats trio's requests proceeding to job setup/dispatch; the removals were unjustified.
- I used `test_candidates[0]` (chr) instead of `test_selection.selected_candidate_id` (`tests/default.nf.test`), and read only `snapshot.captures` although the md5s live in `snapshot.parsed_content` (e.g. `summary-nextflow.json:2138`). The plan's "no upstream expected outputs" warning is an artifact of that misread.
- After attempt 15 identified the root cause, I did not restore the features removed in attempts 8–14 and re-test them, despite the ledger's "could be restored" notes (lines 81, 151). The final 4-step workflow is far smaller than the source pipeline as a result.
- Recording gaps: the chr-filter removal has no dedicated ledger entry (only the run log), and `open-requirements.ledger.yml:120` still says fastx reads the chr-filtered BAM — stale. Both acknowledged in `orchestrator-questions-answers.md`.

## F. Revision round (2026-11-10)

Findings from `orchestrator-findings-2026-11-10.md`. Used `pipeline-update-interview-to-galaxy`: `summarize-galaxy-workflow` → `interview-to-galaxy-workflow-changeset` → `apply-galaxy-workflow-changeset` (direct edits; draft loop no-op) → baseline plan/tests unchanged → `validate-galaxy-workflow` → `run-workflow-test`.

Changes (`galaxy-workflow.before-revision.gxwf.yml` → `galaxy-workflow.gxwf.yml`):

```diff
@@ step post_fastqc state
+      min_length: null
@@ step multiqc state
+      comment: ''
@@ step fastx_single state
+      copy_arb_tags: null
+      inclusive_filter: []
+      exclusive_filter: ['256', '2048']
+      exclusive_filter_all: []
@@ comments
-  stage-input     (empty frame: "Inputs and contig selection")
-  stage-qc-stats  (empty frame: "Pre-conversion QC and stats")
```

Why:
- `fastx_single`: Galaxy had substituted `exclusive_filter: ['256','2048']`. That equals both the wrapper default and `samtools fastq`'s own `-F 0x900`, and nf-core adds no filter, so the value is correct — made explicit so the workflow no longer depends on an editor substitution. The other three flags are set to their no-op/neutral forms.
- `post_fastqc.min_length: null` and `multiqc.comment: ""`: legal explicit defaults (verified with `gxwf validate --strict`).
- The optional datasets (`adapters`, `contaminants`, `limits`, `image_content_input`) were left unconnected: explicit null is rejected by the validator, and per the orchestrator's correction an unconnected optional dataset is normal Galaxy editor state, changed only when the source feeds it (nf-core feeds none — verified in the module sources).
- The two frames were removed because their member steps were dropped in the main run; an empty frame only draws an empty box. `stage-convert` and `stage-post` already cover every remaining step; no `position`/`size` was touched.

Validation: `gxwf validate --connections --strict` 4/4 ok; planemo PASS at **15:49:03**.
