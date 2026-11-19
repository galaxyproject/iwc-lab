# Workflow debug report: nf-core-bamtofastq (aa0150e), Galaxy workflow

- **Run directory:** `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-haiku-max-fixed`
- **Handoff:** `workflow-test-result.json` (phase 12, `status: pass`)
- **Final run:** attempt 5. Planemo 0.75.48, exit 0, "All 2 test(s) executed passed."
- **Phase 13 start:** 20:34:05

## 1. Classification of the final run

**No failure surface.** The final run passed, so there is no failing output to classify.

| Check | default-paired | no_bai-mixed |
|---|---|---|
| Planemo status | passed | passed |
| `execution_problem` | null | null |
| `output_problems` | none | none |
| Invocation messages | none | none |
| Invocation id (encoded) | `716c95874166f012` | `6b883b20fe85b665` |
| Invocation state | scheduled | scheduled |
| Jobs | every executed job `ok` (exit 0); `single_collate` and `single_fastx` `skipped` by design (no single-end sample) | all 20 tool steps `ok` |

Invocation `scheduled` is the state planemo treats as successful scheduling. The assertions are what confirm the outputs, and they passed.

What the final pass establishes, by assertion family (from `galaxy-workflow.gxwf-tests.yml`):

- **Checksum (10):** upstream nf-test md5 tokens for flagstat and idxstats. These are the only byte-level content checks.
- **`has_n_lines`, decompressed (9):** FASTQ line counts from the fixture BAMs (4 × complete pairs, and 4 × 12473 for test3). These check record counts, not sequence content.
- **`has_text` (3):** samtools `raw total sequences` for test2 and test3. These check counts.
- **`element_count` (4):** counts 2 and 1 are enforced. Count 0 is not (see §7).
- **Element identity (21 entries, plus nested keys):** presence only.
- **`class` and `collection_type` (18):** type checks only.

Per the packaged shortcuts note, a size, shape or existence check "can establish that an output was produced, but it cannot establish that the analysis is correct". So the pass does not establish FASTQ sequence content, stats content for test, FastQC or MultiQC content, fastq_info content, or the MultiQC report beyond existence.

## 2. Debugging history (attempts 1 to 4)

| Attempt | Lock, start to end, exit | First failure surface | Evidence captured | Route and next surface | Change | Result |
|---|---|---|---|---|---|---|
| 1 | 19:25:49 to 19:30:03, exit 1 | Workflow import rejected (HTTP 400, `err_code` 400007) | Response body: three validation errors naming `frame.color` (`#e8f1df`), `frame.position` and `frame.size`, plus the handled traceback in the body. `planemo-attempt1.log` lines 2771–2772. No planemo report: the test never started. | Workflow-content error, routed to the phase that emitted the comments (the phase 6 template, and the phase 7 frame rebuild). Validator gap: `gxwf validate --strict` accepted the same comments. | Frames given named Galaxy colours, plus `position` and `size`. | Import succeeded in attempt 2. |
| 2 | 19:40:18 to 19:46:07, exit 1 | Job failure in a stock tool, surfaced as an invocation failure | Invocation message (planemo JSON, test 0): reason `dataset_failed`, workflow step index 9 (`single_collate`), dataset `421b8b21077e10c8`. Failing job `fcfc191edac9ace6` (`cut_paired_count`, Cut1 1.0.2): state `error`, exit 255, command `cutWrapper.pl <input> '1' Sp <output>`, `tool_stderr`: "No columns specified, columns are not preceded with 'c', or commas are not used to separate column numbers: 1". | The job record explains the failure, so no `--no_cleanup` rerun was needed. Routed to tool binding: the value came from the cached summary, which dropped the declared default. | `columnList` `"1"` changed to `"c1"`. | Jobs ran; attempt 3. |
| 3 | 19:47:32 to 19:59:33, exit 1 | Missing workflow outputs (label drift) | Planemo `output_problems`: "Expected output [id] not found in results" for all nine outputs in both tests. Invocation messages empty. Every job `ok`. Step-level outputs present (for example `fastqc_post`: `html_file`, `text_file`; `multiqc`: `html_report`, `stats`). | The surface is the workflow's output labels, not the jobs. Galaxy names a workflow output by `output.label or output.id` (`_wire_workflow_outputs`, gxformat2 in `galaxy-arash/.venv`). The test file keys outputs by id. The `validate-tests` label cross-check passed. | Each output's `label` set to its id; descriptions moved to comments. | All nine outputs found in attempt 4. |
| 4 | 20:01:36 to 20:14:13, exit 1 | Test-file expectation (assertion-choice problem) | Planemo `output_problems` for default-paired: "No path specified for expected output file [reads_single]". no_bai-mixed passed. | Planemo routes an expected output as a collection only when it has `element_tests` (`planemo/test/_check_output.py`, `for_collections`). Without it, the expectation is checked as a file. Not a workflow regression: the output was produced. Routed to the test translation (phase 10). | `element_tests: {}` added to default-paired `reads_single`. | Attempt 5 passed. |

## 3. Import rejection: trigger isolation (procedure step 3)

The attempt 1 response named the three fields and the offending values, so the trigger was identified directly. I did not bisect with synthetic variants. Step 3's bisection is aimed at rejections whose trigger is unclear (a 500, or a 400 that does not say what is wrong). A 400 that names the fields is the case the step's routing rule covers directly, so I took that rule instead. This is recorded as a reference gap (§8).

Route: workflow-content error, back to the phase that emitted the construct. Static validation accepted the construct, so the validator gap is its own finding: `gxwf-validate-passes-comment-fields-galaxy-import-rejects` (ledger).

## 4. Job failure: evidence check (procedure step 4)

- The failing job's own record explains the failure. It is in state `error`, exit 255, and `tool_stderr` names the bad column specification. Its command line shows `'1'` as the column argument.
- The upstream job `grep_paired_line` is `ok`. I did not inspect the input contents, because the stderr explains the failure without them.
- The `--no_cleanup` rerun and the kept job directory were not needed. Attempts 1 to 5 all ran without `--no_cleanup`, so no kept directories exist.

## 5. Invocation failure (procedure step 5)

- **Attempt 2:** the invocation message (surfaced in planemo's JSON) is `dataset_failed` at workflow step 9, `single_collate`. That step's gated `when` input comes from `paired_count`, which depends on `cut_paired_count`. The step states agree: `single_collate` is `new` and never scheduled, and `paired_count`'s jobs are `paused` and `new`.
- **Attempt 3:** no invocation message (`messages: []`). The invocation reported `scheduled`, which matches every job being `ok`.
- **Attempt 5:** no invocation message in either test.

## 6. Collection mismatches (procedure step 6)

- In the final run the collection checks passed. `reads_paired` has two sample elements, each with forward and reverse sub-elements (count 2 enforced). `reads_single` has one element, `test3`, in no_bai-mixed (count 1 enforced). The post-conversion FastQC elements are named `<sample>_forward` and `<sample>_reverse`.
- No collection-shape or element-identifier mismatch appeared in any attempt. The only collection-related failure, in attempt 4, was a routing problem in the test file, not a shape problem.
- Operator translations are not implicated: no wrong nesting, missing element or bad join was observed.

## 7. Assertion failures and limits (procedure step 7)

- No assertion failed in the final run.
- **Known limit, not a failure:** the default-paired `reads_single` count of 0 is not enforced. Planemo's `verify_collection` tests `count`, `min` and `max` by truthiness (`galaxy/tool_util/verify/interactor.py`, lines 1533–1541), so a count of 0 is never checked. The expectation therefore reduces to a type check (`class: Collection`, `collection_type: list`, with `element_tests: {}`). The pass does not show the output is empty. The test file records this in a comment.
- **Options** (none applied in phase 13, which makes no workflow or test change):
  - (a) Keep the declaration as a documented limit. This is the current state.
  - (b) Replace it with a checkpoint that can be checked, for example an output that reports the record count. This needs a workflow change, so it is out of scope here.
  - (c) An upstream fix to planemo's truthiness check (ledger entry `planemo-verify-collection-zero-count-not-enforced`).
- **Weakening check** (`iwc-shortcuts-anti-patterns`): no assertion was weakened, widened or turned into an existence check in attempts 4 and 5. The `element_tests` change routes the expectation without relaxing it. Keeping `element_count: 0` with a limit note is not a relaxation, but it is a count the tool cannot test, so it is recorded as such.

## 8. Reference gaps and follow-ups (procedure step 8)

- **Passing runs:** the debug procedure and its output specification cover failing runs only. A passing handoff has no defined output and no stopping rule. This report is the phase 13 output for a pass (ledger entry `debug-procedure-undefined-for-passing-handoff`).
- **Import bisection:** step 3 requires bisection for any import rejection. A 400 that names the fields needs none (ledger entry `import-bisection-required-even-when-400-names-fields`).
- **Assertion guidance:** `planemo-asserts-idioms` does not state the collection routing rule (`element_tests`) or the zero-count limit. Recorded earlier (ledger entry `assertion-guidance-silent-on-collection-routing-and-zero-count`).
- **Not performed** (out of phase 13, which runs no planemo or Galaxy job):
  1. A negative-control run with one deliberately wrong expected value, to show the checks are live in this environment.
  2. Fixtures for a mixed-file sample and for a single-end-only job.
  3. An upstream fix to planemo's zero-count check.

## 9. Artifacts

- `workflow-test-result.json` (phase 12) and `model-test-log.md` (the full attempt record).
- `planemo-attempt1.log`; `planemo-attempt2.{log,json,html}` to `planemo-attempt5.{log,json,html}`. The JSON reports are 271 to 295 MB each, because planemo embeds the Galaxy server log.
- `foundry-feedback.ledger.yml` (local only; nothing filed).
- Final workflow `galaxy-workflow.gxwf.yml` and final tests `galaxy-workflow.gxwf-tests.yml`.
- Kept job directories: none.

## 10. Next command

None is required for the pass. The optional negative-control run in §8 is not performed.
