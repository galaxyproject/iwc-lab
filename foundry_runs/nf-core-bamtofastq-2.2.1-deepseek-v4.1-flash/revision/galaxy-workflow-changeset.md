# Galaxy workflow change-set — nf-core-bamtofastq-deepseek revision

Baseline: `galaxy-workflow.before-revision.gxwf.yml` (= `starting-galaxy-workflow.gxwf.yml`).
Source: `orchestrator-findings-2026-11-10.md` (§1 missing state values, §2 frames).

## Decisions

**fastx_single flags.** Galaxy substituted the wrapper default `exclusive_filter: ['256','2048']`. That default equals `samtools fastq`'s own default (`-F 0x900`) and nf-core/bamtofastq passes no extra flag filter, so the substituted value is scientifically correct — but leaving it implicit makes the workflow non-deterministic across Galaxy versions. Made explicit. `copy_arb_tags`, `inclusive_filter` and `exclusive_filter_all` are set to their no-op forms.

**Optional datasets.** `adapters`, `contaminants`, `limits` (FastQC) and `image_content_input` (MultiQC) stay absent: `gxwf validate --strict` rejects an explicit `null` for optional data-typed parameters (`Expected never/undefined, actual null`), and an unconnected optional input is the correct representation. nf-core/bamtofastq supplies none of them.

**Frames.** `stage-input` ("Inputs and contig selection") and `stage-qc-stats` ("Pre-conversion QC and stats") are empty because their steps were dropped from this translation. An empty frame draws as an empty box, so both are removed. `stage-convert` and `stage-post` already group every remaining step and are untouched (their `position`/`size` unchanged).

| # | kind | anchor | decision | acceptance |
|---|---|---|---|---|
| 1 | change-parameter | step `fastx_single`, key `copy_arb_tags` | Set `null` (no arbitrary tag copying). | Key present and null; strict validation passes. |
| 2 | change-parameter | step `fastx_single`, key `inclusive_filter` | Set `[]` — no flags are required. | Empty list in state. |
| 3 | change-parameter | step `fastx_single`, key `exclusive_filter` | Set `['256','2048']` explicitly — identical to the substituted default and to samtools' own default; removes the implicit-substitution warning. | Explicit list in state. |
| 4 | change-parameter | step `fastx_single`, key `exclusive_filter_all` | Set `[]` — no "all flags" exclusion. | Empty list in state. |
| 5 | change-parameter | step `post_fastqc`, key `adapters` | Left absent (optional data; null rejected). | Key unchanged. |
| 6 | change-parameter | step `post_fastqc`, key `contaminants` | Left absent. | Key unchanged. |
| 7 | change-parameter | step `post_fastqc`, key `limits` | Left absent. | Key unchanged. |
| 8 | change-parameter | step `post_fastqc`, key `min_length` | Set `null` — no length limit. | Key present and null. |
| 9 | change-parameter | step `multiqc`, key `comment` | Set `""` — wrapper default. | Key present and empty. |
| 10 | change-parameter | step `multiqc`, key `image_content_input` | Left absent (null rejected). | Key unchanged. |
| 11 | annotate | frame `stage-input` | Remove the frame: empty `contains_steps`; its would-be steps were dropped as documented losses. | Frame absent; no step references it. |
| 12 | annotate | frame `stage-qc-stats` | Remove the frame for the same reason. | Frame absent. |

## Out of scope

- `position`/`size` of any step or frame (task rule).
- Step set, wiring, tool versions, outputs: unchanged.

## Carried obligations

`open-requirements.ledger.yml` passes through unchanged; the removed frames are UI-only and add no obligation.
