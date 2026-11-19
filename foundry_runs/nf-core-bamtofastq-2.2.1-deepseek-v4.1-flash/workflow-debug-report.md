# Workflow debug report — nf-core/bamtofastq Galaxy translation

Input: `workflow-test-result.json` → **status: pass**. `planemo test` ran 1/1 tests green (exit 0, 2026-11-10 00:51:12).

## Verdict

**Nothing to debug.** The final invocation produced every asserted output:

- `converted_reads_single` — collection `list`, 1 element (`test3`), `fastqsanger`
- `post_fastqc_html` — collection `list`, 1 element (`test3`), `html`
- `fastqutils_info` — collection `list`, 1 element (`test3`), `txt`
- `multiqc_report` — dataset, `html`

## Why it took 18 attempts (failure surfaces, all recorded in `model-test-log.md` and `open-requirements.ledger.yml`)

| # | surface | classification | resolution |
|---|---|---|---|
| 1–2 | import / conversion | not-run — gxformat2 converter: step `label` shadows `id`; format2 inputs must be a mapping and `format` a list | normalised the workflow file |
| 3 | gxformat2 conversion | not-run — stale `chr_extract` reference after a topology edit | rewired inputs |
| 4–6 | workflow invocation | fail — `when: $(inputs.fasta)` is not boolean (`when_not_boolean`) | explicit null/empty tests |
| 7 | workflow invocation | fail — `pick_value` cannot carry whole collections; its output broke `samtools collate` | removable pick_value steps avoided |
| 8–10 | tool request | fail — `samtools view` region filtering needs a BAM index that the Galaxy chain cannot attach; the toy BAM also has contigs 1/2, not chrX/chrY | `chr` filtering dropped |
| 11–13 | tool request | fail — a single reference dataset cannot map over a collection (`samtools_view` validation_failed) | reference wiring dropped (BAM-only) |
| 14 | tool request | fail — devteam `samtools_stats`/`flagstat`/`idxstats` (2.0.x) validation_failed under map-over | stats steps dropped |
| 15 | tool request | fail — `fastx_single` was skipped by a stale `when: $(inputs.input_layout == 'single')`; FastQC received the 4-byte `null` sentinel (confirmed in the preserved job dir with `--no_cleanup`) | stale guard removed |
| 16–17 | tool request / assertion | fail — converted `tool_state` lacked `__current_case__` markers for nested conditionals; then an assertion-format error (`No path specified for expected output file [post_fastqc_html]`) | case markers added; element-level assertion added |
| 18 | — | **pass** | — |

The dominant, non-obvious root cause was #15: the stale `when:` guard silently produced a `null` dataset, and every downstream failure (FastQC exit 1, MultiQC errors, `validation_failed` on consumers) was a symptom of that single skipped step.

## Residual risks (not exercised)

- Only one single-end BAM is tested; multi-element collections are untested.
- `no_read_QC` / `no_stats` switches exist as inputs but no steps consume them in the final translation.
- MultiQC aggregates FastQC data only (title wired); other QC sections were dropped.

## Recommended follow-ups

1. Restore the dropped capture in this order of value: stats/flagstat/idxstats (needs fully-encoded wrapper state or newer wrappers), then chr filtering (needs an index step that Galaxy can attach), then CRAM support (needs reference broadcast), then paired-end.
2. Add a second test with two input BAMs to exercise collection map-over.
