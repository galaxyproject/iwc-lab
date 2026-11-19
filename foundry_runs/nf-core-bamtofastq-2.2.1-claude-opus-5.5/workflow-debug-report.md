# Workflow debug report — nf-core/bamtofastq → Galaxy

Input: `workflow-test-result.json` (phase 12).

## Classification

**No failure to triage.** run-workflow-test reports `status: pass`: planemo ran 1 of 1 test and it passed, with no output problems. The invocation was scheduled with 44 jobs `ok` and 2 `skipped`. The skipped jobs are the two `chr_extract` jobs, gated by `when: chr != null` because `chr` is unset in the default test, and their `pick_value` fallback was used. The history's aggregate state is `skipped` because of those two skipped datasets. That is expected and not an error.

## Earlier failure (phase 10 run, for the record)

| Surface | Evidence | Classification | Resolution |
|---|---|---|---|
| assertion / test format | `planemo/phase10/test-output.json` → `output_problems: ["No path specified for expected output file [single_end_reads]"]`. The invocation itself was ok (44 ok / 2 skipped), and no other output assertion failed (nested FASTQ compares are confirmed evaluated; see model-test-log.md). | Test-file construct, not a workflow defect. planemo's `for_collections()` treats an output test as a collection only when it has `element_tests`. Galaxy verify skips `count` when it is 0. | `single_end_reads` asserted as `{class: Collection, element_tests: {}}` (existence only). The unenforceable `element_count: 0` was removed and recorded as a plan omission and a feedback entry. It was not a relaxation that masks a real failure: the count was never checkable. |

## Residual risks not exercised by the passing test

From `galaxy-workflow-validation-result.json`: the single-end branch, chr extraction (only the skip path ran), collate fast mode, the skip toggles, and CRAM inputs (no reference on the shed samtools steps). The next step is to translate the remaining nf-test cases (`chr`, `cram`, `collate_fast`, `no_qc`, `no_stats`, plus a single-end fixture) as more Galaxy test cases.
