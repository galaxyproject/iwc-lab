# Change-set: nf-core-bamtofastq-claude revision (2026-11-10)

Workflow: `starting-galaxy-workflow.gxwf.yml` (= `galaxy-workflow.before-revision.gxwf.yml`), summarized in `summary-galaxy-workflow.json`.

There was no live interview. These sources stood in for it:

- `orchestrator-findings-2026-11-10.md`: Galaxy's "Issues loading this workflow" messages, 59 parameters across 10 steps.
- nf-core/bamtofastq 2.2.1 (`source/bamtofastq`), which settles whether nf-core actually uses each parameter.

## Decision rule

Galaxy fills a missing key with the tool default, so the job command line is the same either way. No entry here changes behavior. The only purpose is to stop the editor dialog by writing the tool default Galaxy already uses:

- `null` where the message names no default (optional integer, float, text or select left empty);
- `false` where the message says `Using default: 'False'`.

Parameters marked "a value set at runtime" are unconnected optional dataset inputs. They stay unchanged unless nf-core feeds that input. It feeds none of them (see "Left unchanged").

Nothing nf-core passes for these steps maps to a flagged parameter:

- `SAMTOOLS_VIEW_*`: `ext.args` is only `-b -f/-F` flags.
- `SAMTOOLS_CHR`: `-hb` plus the region.
- `SAMTOOLS_STATS`: no `ext.args`.
- `SAMTOOLS_MERGE_UNMAP`: no `ext.args`.
- `FASTQC_*`: `--quiet` only.

So `null`/`false` is also the nf-core value.

## Edits (ordered; all direct `change-parameter`, no tool change)

### 1. change-parameter — anchors `chr_extract`, `view_map_map`, `view_unmap_unmap`, `view_unmap_map`, `view_map_unmap` (samtools_view 1.22+galaxy2)
- tool_state keys:
  - `mode|filter_config|cigarcons` = null
  - `mode|filter_config|library` = null
  - `mode|filter_config|quality` = null
  - `mode|filter_config|tag` = null
  - `mode|output_options|adv_output|collapsecigar` = false
  - `mode|subsample_config|subsampling_mode|seed` = null
- Intent: write the defaults Galaxy fills in, 6 keys × 5 steps = 30.
- Acceptance: the editor shows no message for these keys on import, and the samtools_view command lines are unchanged (planemo regression test passes with the same assertions).

### 2. change-parameter — anchor `stats` (samtools_stats 2.0.9)
- tool_state keys:
  - `cov_threshold` = null
  - `gc_depth` = null
  - `insert_size` = null
  - `most_inserts` = null
  - `read_group` = null
  - `read_length` = null
  - `trim_quality` = null
  - `remove_overlaps` = false
  - `sparse` = false
- Intent: write the defaults, 9 keys.
- Acceptance: no message for `stats` on import, and the `samtools_stats` output assertions still pass.

### 3. change-parameter — anchors `fastqc_pre`, `fastqc_post_single`, `fastqc_post_paired` (fastqc 0.74+galaxy1)
- tool_state key: `min_length` = null
- Intent: write the default, 1 key × 3 steps = 3.
- Acceptance: the only message left on these steps is for the runtime dataset inputs.

### 4. change-parameter — anchor `merge_unmapped` (samtools_merge 1.22+galaxy2)
- tool_state key: `region` = null
- Intent: write the default, 1 key.
- Acceptance: the only message left on this step is for the runtime dataset inputs.

Total: 30 + 9 + 3 + 1 = **43 keys**.

## Left unchanged (16 runtime-value entries)

| Step(s) | Key | Why left |
|---|---|---|
| chr_extract, view_* (5) | `mode|filter_config|qname_file` | nf-core passes `[[:],[]]` for `qname` in every `SAMTOOLS_VIEW_*` / `SAMTOOLS_CHR` call (`subworkflows/local/alignment_to_fastq/main.nf:23-32`, `workflows/bamtofastq.nf:121`), so the input is never fed. |
| fastqc_pre, fastqc_post_single, fastqc_post_paired (3 each) | `adapters`, `contaminants`, `limits` | The nf-core FASTQC module takes only reads, and `ext.args` is `--quiet`. No adapter, contaminant or limits file is given. |
| merge_unmapped | `bed_file`, `headerbam` | `SAMTOOLS_MERGE_UNMAP` takes `(meta, bams, [])` plus the fasta/fai and has no `ext.args`, so no region BED or header BAM is given. |

5 + 9 + 2 = **16**. Galaxy's substituted RuntimeValue is the standard state for an unconnected optional dataset input.

## Out of scope (not in this change-set)

- The `orchestrator-review-2026-11-10.md` items (pipefail, fastq_info exit codes, chr filter order, CRAM): deferred by the coordinator.
- Canvas `position` and frames: layout is out of scope. The findings note no frames exist, and the template marks them optional.
