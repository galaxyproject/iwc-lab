# Workflow debug report — nf-core/bamtofastq → Galaxy

## Final status: green — no open failure surface

`workflow-test-result.json` reports `status: pass`: planemo attempt 7 exited 0 with **"All 1 test(s) executed passed"**. There is no failing output to triage in the final run. This report records the final-run evidence and classifies the failure surfaces encountered (and closed) across planemo attempts 1–6.

## Final-run evidence (attempt 7, planemo-managed Galaxy on the galaxy-arash checkout, biocontainers)

- **Invocation**: state `scheduled`, no error message, no failure messages; workflow id = invocation id = history id `3bbc9b8f289e9cb5` (planemo-managed, torn down after the run).
- **Jobs**: 50 total — 46 `ok`, 4 `skipped`, 0 `error`/`failed`. All six embedded user-defined tools executed (`bamtofastq_check_endedness`, `bamtofastq_collate_fastq` ×2 call sites, `bamtofastq_samtools_merge`, `bamtofastq_cat_fastq`, `bamtofastq_fastq_utils_info`) with exit code 0 under their containers.
- **Conditional routing verified from job states**: the 4 skipped jobs are exactly `samtools_chr_view` ×2 (chr input empty — the when gate skipped the region branch per element, and `chr_pick` passed the original alignments through) and `collate_fastq_single` ×2 (both samples detected paired-end — the per-element endedness routing skipped the single-end path for both elements). The engine-verified per-element `when` mechanism behaved exactly as designed.
- **Assertions**: all passed — flagstat/idxstats md5s equal to the upstream nf-test snapshot (also independently reproduced by running the source pipeline's commands on the fixtures in the source container); reads compare:diff+decompress against those source-command outputs; stats SN lines; fastqc non-empty smoke; fastq_utils has_text.

## Failure surfaces encountered and closed across attempts 1–6

| Attempt | Surface (this skill's classification) | Root cause | Fix |
|---|---|---|---|
| 1–2 | Workflow conversion failure before import (planemo's gxformat2) | `ValueError: int('check_endedness')`: `in: source:` references resolve through gxformat2's label map (`step.label or step.id`); dict-keyed steps without labels (attempt 1) or with display labels ≠ ids (attempt 2) are unresolvable | Set every step's `label` equal to its id |
| 3 | Workflow import rejection (HTTP 400, handled) | Local Galaxy's `WorkflowComment` pydantic model requires `frame.position`/`frame.size`; my position-less comment frames passed gxwf validate but were rejected | Dropped the optional `comments:` stage frames |
| 4 | Workflow invocation scheduling failure (step 30, `__MERGE_COLLECTION__`) | Output collection `type_source 'inputs_0|input'` could not resolve because the step's tool_state lacked the `inputs` repeat entries the corpus carries | Added `inputs: [{__index__: 0..2}]` repeat state |
| 5 | Output verification: fastqc outputs | planemo `runnable.py` treats an output entry without `element_tests` as a dataset expecting a `path`; bare `element_count` is not runnable there | Converted the four fastqc smoke checks to `element_tests` with `has_size min 1` (non-empty check), keeping `element_count` |
| 6 | Assertion mismatch (test2 flagstat checksum) | Transcription typo in the tests file — the expected md5 was 31 chars (a dropped `2`); the produced output's md5 matched the upstream snapshot exactly | Corrected the md5; all checksums then programmatically verified against snapshot + independent source-run hashes |

## Residual observations (no action required)

- The `when`-input connections (named `when`, `chr_gate`) are expression-only pseudo-inputs the tools do not declare; Galaxy logs an unmatched-connection warning and ignores them at the tool layer. Corpus-proven (atacseq, mgnify) and now also proven by this run.
- The reads output element identifiers (`test_1`, `test_2`, `test2_1`, `test2_2`) came from `__MERGE_COLLECTION__` `suffix_conflict _#` exactly as designed.
- `tool_test_output.json` (137 MB, attempt 7) and the kept `--no_cleanup` job directories under `/tmp/tmp*` hold the full per-job evidence; the run is green, so no deeper job-directory inspection was needed.

## Reference-gap follow-ups

None open for this workflow. The three upstream friction points found during attempts 1–6 (gxformat2 label resolution, `__MERGE_COLLECTION__` repeat state, planemo element_count-only outputs) are recorded in `foundry-feedback.ledger.yml` as related-project entries.
