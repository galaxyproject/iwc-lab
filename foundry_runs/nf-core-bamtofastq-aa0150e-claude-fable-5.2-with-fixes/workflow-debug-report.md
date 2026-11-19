# Workflow debug report — nf-core/bamtofastq Galaxy workflow

Input: `workflow-test-result.json` (attempt 1, status `fail`), `planemo/attempt-1/tool_test_output.json`, `planemo/attempt-1/report-compact.json`.

## Attempt 1

### 1. First failure surface: assertion mismatch

Not an import rejection, not a job failure, not an invocation failure, not a missing output.

| Check | Evidence |
|---|---|
| Workflow import | accepted, including the embedded user-defined tool (`Classify pairedness`) |
| Invocations | 3 of 3 `scheduled`; histories `ok` |
| Jobs | every job of all 28 invocation steps in state `ok` in all 3 tests (0 not-ok) |
| Outputs | every asserted output was present |
| Output problems | two kinds, below |

### 2. Finding A — read order (`compare: diff` on reads)

`Paired-end reads` (all 3 tests) and `Single-end reads` (test 2): same number of lines as the expected files, different order. Expected starts `@testN:1874/1`, Galaxy output starts `@testN:1/1` (name order).

Cause, from the job records of test 1:

- `Collate mapped pairs` ran `samtools collate … -o <dataset 0713fa50…>`; its output was retyped to `qname_input_sorted.bam` by the post-job action.
- `Mapped pairs to FASTQ` did **not** receive that dataset. Its input is another dataset (`f570025a…`): Galaxy inserted an implicit datatype conversion back to `bam`, because the tool's input accepts `sam,bam,cram` and `qname_input_sorted.bam` is not a kind of `bam`.
- Its command line then starts with `samtools sort -@ … -n '<f570025a…>' … > input && samtools fastq -N -1 forward.fastqsanger.gz -2 reverse.fastqsanger.gz -f 0 -F 2304 -G 0 -s singletons.fastqsanger.gz input`.

So `iuc/samtools_fastx` 1.22+galaxy2 name-sorts its input in every case that can reach it from a workflow. The wrapper branch that skips sorting needs an input typed `qname_sorted.bam`/`qname_input_sorted.bam`, and such an input is converted away before the tool runs. The topology repair made in phase 7 (three collate steps + retyping) does nothing useful.

Classification: **workflow design vs. wrapper behaviour**, exposed by a correct assertion. It is not a wrong result: a hand run of `samtools sort -n | samtools fastq -N` on the upstream fixtures gives exactly the same lines as the expected files once both are sorted (checked for test, test2 forward/reverse and test3), and the offline Galaxy verifier passes `compare: diff` + `sort: true` + `decompress: true` on such a file while failing without `sort`.

Recommended repair (routes to `repair-galaxy-draft-topology`, fold clause — the consumer's wrapper does the work itself):

1. `remove-step` ×3: `Collate mapped pairs`, `Collate unmapped-mate pairs`, `Collate single-end reads`; `rewire` the three BAM→FASTQ steps to the filter/split outputs.
2. `remove-input`: `Collate in fast mode` (nothing left to wire it to) — recorded as a drop; test case 3 goes with it.
3. Record a plain ledger entry: read order is name order, not the source's collate order.
4. Tests: add `sort: true` to the read comparisons.

Is step 4 a masking relaxation? No, for these reasons: the mechanism is named in the job record; the multiset of lines is identical to files whose md5 equals the upstream snapshot tokens; and `sort: true` still fails on any missing, extra or altered read. What it no longer checks: the order of reads, and which header line belongs to which sequence/quality line. Mate synchronisation between forward and reverse is checked separately by the paired `fastq_info` report (`OK`).

Not recommended: authoring a custom collate+fastq tool (an existing wrapper runs the step's work), or another retyping variant.

### 3. Finding B — "No path specified for expected output file"

`Single-end reads`, `FASTQ validation (single-end)`, `FastQC post-conversion report` (test 1). These are collection outputs asserted with `element_count` only. Planemo 0.75.48 decides "this is a collection assertion" by `"element_tests" in test_properties` (`planemo/test/_check_output.py`); without that key the output is checked as a single file and fails.

Classification: **test-definition problem** (assertion form), not a workflow problem. `gxwf validate-tests --workflow` accepted the file.

Repair: always emit `element_tests` for collection outputs (an empty map for the two empty collections; a real per-element check for the FastQC HTML reports).

Related limit found while reading the verifier (`galaxy.tool_util.verify.interactor.verify_collection`): `if output_collection_def.count and count != actual` — an expected count of `0` is falsy and is **not enforced**. So `element_count: 0` cannot prove a collection is empty. The two empty-collection assertions are therefore type-only checks; the evidence that no sample went to the single-end branch is the `Pairedness per sample` table.

### 4. What attempt 1 did prove

- Embedded user-defined tool imports and runs under a Planemo-managed Galaxy.
- An empty `output_discarded` side schedules fine through three mapped steps and a collection merge.
- No output problem was reported for: flagstat and idxstats checksums (snapshot md5s), samtools stats, FastQC data (pre and post), paired `fastq_info` reports, `Pairedness per sample`, MultiQC, FastQC pre-conversion report.

### 5. Reference gaps (recorded as feedback)

- Tool summaries carry no command block, and reading tools-iuc `main` XML was not enough to predict the implicit datatype conversion.
- Packaged assertion notes do not mention `sort:` for order-insensitive comparison, nor the `element_tests`-key requirement, nor the unenforced zero count.

## Attempt 2

Input: `workflow-test-result.json` (attempt 2, status `pass`), `planemo/attempt-2/report-compact.json`.

Nothing to triage. Planemo exit 0, "All 2 test(s) executed passed"; both invocations `scheduled`, histories `ok`; 24 invocation steps each (1 input + 23 tool steps); 37 jobs (test 1) and 45 jobs (test 2), all `ok`; no output problems.

What the pass confirms about attempt 1's findings:

- Finding A: with the collate steps removed, the reads compare equal to the snapshot-verified expected files as sorted lines (`compare: diff`, `sort: true`, `decompress: true`), for paired samples `test`, `test2` and the single-end sample `test3`.
- Finding B: collection outputs carrying `element_tests` are checked as collections; the two empty collections in test 1 pass as type-only checks.

Still open after a green run (not failures, recorded as limits):

1. Read order is name order, not the source's collate order (ledger `read-order-is-name-sorted`).
2. An empty collection cannot be asserted by count; emptiness of the single-end branch in test 1 rests on `Pairedness per sample`.
3. `fastq_info` reports are asserted on their `OK` line because the wrapper does not fail the job on invalid FASTQ.
4. Side observation on the evidence itself: each test's `problem_log` in the Planemo JSON is about 188 MB because it embeds the whole Galaxy server log of the local checkout (its first lines are dated 2026-05-27). The per-attempt JSON files were gzip-compressed; `report-compact.json` holds the parts used here.
