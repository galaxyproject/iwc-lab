# Debug report — nf-core/atacseq → Galaxy test on test.galaxyproject.org

Produced by `debug-galaxy-workflow-output` from `workflow-test-result.json`. Galaxy 27.0.dev0,
external mode, `planemo test --engine external_galaxy --no_shed_install`. **Final state: pass**
(attempt 3: invocation `585d40391400052f`, history `b1251ce3b0e2e90fcb93b239532c69a3`,
182/182 jobs ok, all assertions passed).

## Attempt 1 — workflow import rejected

| | |
|---|---|
| Surface | workflow import response (`POST /api/workflows`, bioblend `import_workflow_dict`) |
| HTTP | 400, `err_code 400008` |
| Body | `Input should be 'none', 'black', 'blue', 'turquoise', 'green', 'lime', 'orange', 'yellow', 'red' or 'pink' in ('frame', 'color')`, input `"lightblue"` |
| Planemo artifacts | none (import failed before structured output); `run/planemo.log` |
| Classification | workflow-content error (handled 400 naming a schema field) |
| Routes to | `nextflow-summary-to-galaxy-template` — the "Merge lanes" frame was emitted with `color: lightblue`; the packaged comments note lists the legal palette, so this was an authoring slip |
| Validator gap | `gxwf draft-validate --concrete --strict-state` and `gxwf validate --strict` both accepted the value (feedback `gxwf-validate-misses-frame-color-enum`) |
| Bisection | not needed beyond one controlled change: the identical workflow with only that colour changed (`yellow`) imported (attempt 2), which is the passing control |

## Attempt 2 — tool/job failure (featureCounts on single-end libraries)

| | |
|---|---|
| Surface | Galaxy job API |
| Invocation | `bb3f64d789035923` scheduled 90/90 steps; jobs ok 176, error 3, paused 3 |
| Failed jobs | `3cfd783266481e23`, `66e0243907a4dd86`, `201d110e04cb9cf0` — `iuc/featurecounts/featurecounts/2.1.1+galaxy3`, exit 255 |
| stderr | `ERROR: No paired-end reads were detected in paired-end read library` |
| Paused | `counts_matrix`, `deseq2_qc`, `multiqc` (downstream of the failed elements) |
| Classification | tool-job failure caused by a design choice: one featureCounts step mapped over the merged PE+SE library collection with `paired_end_status: PE_fragments`. nf-core runs subread 2.0.1, which tolerates `-p` on SE BAMs; Galaxy's 2.1.1 aborts. Flagged in advance as a residual risk in `galaxy-workflow-validation-result.json`. |
| Routes to | template tier (topology): the per-element SE/PE flag is lost after `merge_bams_for_counts`, the same reason the lanes exist |
| Repair applied | `merge_bams_for_counts` + `featurecounts` replaced by `pe_featurecounts` (PE_fragments, input `pe_bam_sync`) and `se_featurecounts` (single_end, input `se_bam_sync`), joined by `merge_counts` (`__MERGE_COLLECTION__`) before `counts_matrix`; MultiQC reads both summaries. 80 steps, re-validated (`draft-validate --concrete --strict-state`, `validate --strict`, `validate-tests`). |

Everything else in attempt 2 ran green, including the three user-defined tools
(`include_regions_bed`, `pe_remove_orphans`, `deseq2_qc` was paused, not failed).

## Attempt 3 — pass

182/182 jobs ok; Planemo: `All 1 test(s) executed passed`. Observed values (from attempt 2,
same upstream steps):

| Output | Observation |
|---|---|
| `library_peaks` | 634–1,483 broadPeak calls per library (9 columns) |
| `library_frip` | 0.32–0.43 |
| `library_flagstat` | 37,686–236,588 mapped reads; PE libraries 99.8% properly paired after filtering |
| `consensus_peaks_bed` | 1,874 consensus intervals (`Interval_<n>`) |

## Follow-ups

- Tighten assertions: they are design intent (no upstream expected outputs exist). The observed
  values above can become fixture-derived checks (e.g. peak-count ranges, consensus row count).
- Deviations from nf-core still carried as open ledger entries: bamCoverage instead of
  genomecov (bin 10), GTF instead of SAF for featureCounts, no HOMER `-gid`, read group ID only,
  `macs_gsize` supplied rather than computed, no trimmed-read FastQC.
