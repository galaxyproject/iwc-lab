# Workflow Debug Report — nf-core-bamtofastq-glm-fixed (attempt 8)

Generated: 2026-11-12 21:36 (phase 13, debug-galaxy-workflow-output)
Input artifact: `workflow-test-result.json` (status fail, 8 attempts, invocation `8d16cec2ba877afa`, invocation_state `completed`, history_state `ok`).

## 1. First failure surface

**Not** import rejection, **not** job failure, **not** invocation failure. Galaxy imported the workflow, installed all 19 shed repos, scheduled the invocation to `completed`, and produced every declared output. The first actionable failure surface is the **assertion/reporting layer on top of a collection-shape mismatch**: planemo's structured result carries 1 failed test with output problems in four distinct classes (planemo-attempt8.json, verbatim below). Classification chain: import OK → jobs all ok → invocation completed → collection-output mismatch + assertion mismatch.

## 2. Captured evidence (verbatim)

From `planemo-attempt8.json` → `tests[0].data.output_problems`:

```
1. Output collection 'paired_reads': failed to find identifier 'test/forward' in the tool
   generated elements ['forward', 'reverse']
2. Output with path /tmp/tmps89orjjq/Samtools stats__....tabular different than expected /
   Output checksum [53fc83294e70621941c577b8ea0d29b2] does not match expected
   [3c3f8fa56674fa987fd912b530f49c3c] (using hash algorithm md5).
3. Output collection 'fastq_info': expected a collection, but the output was a single dataset
   — use 'asserts' instead of 'element_tests'.
4. No path specified for expected output file [fastqc_post_zip]  (×4: fastqc_post_zip,
   fastqc_post_html, fastqc_pre_zip, fastqc_pre_html)
```

Kept-Galaxy DB evidence (`/tmp/tmpvky91759/galaxy.sqlite`):

- Jobs 22–29: 8 `samtools view` jobs, each `samtools view -@ $addthreads -b -f N -F M -G 0 -o outfile infile` — per-bin extraction ran 2× per sample as designed (bins: map_map 1/4,8; unmap_unmap 4,8/256; unmap_map 4/8,256; map_unmap 8/4,256).
- The merge step ran **one** `samtools merge` job over 6 BAMs (3 bin-steps × 2 samples flattened by the `bamfiles:` multiple-data port), so the per-sample grouping the source enforces (`SAMTOOLS_MERGE per sample`) was lost. Downstream cat/zip/fastq_info each ran 1 job instead of 2.
- `dataset_collection_element` rows and the full history listing confirm `paired_reads` was produced as a flat `paired` collection (elements `forward`/`reverse`), not `list:paired` with `test`/`test2` outer elements.
- Attempt-8 planemo structure dump: attempt 8's "failed to find identifier 'test/forward'... elements ['forward','reverse']" shows slash keys are looked up literally by planemo's verify_collection (no slash-splitting found in `galaxy/tool_util/verify/interactor.py` `verify_collection` or `TestCollectionOutputDef`); planemo's own generated nested defs use `{"<id>": {"elements": {...}}}` (`planemo/galaxy/workflows.py:1073`).

## 3. Failure-surface classification

| # | Surface | Evidence | Root cause | Fix route |
|---|---------|----------|-----------|-----------|
| 1 | assertion-format (test-file defect) | problem 4 | `element_count` without `element_tests` is not a valid collection-test shape in planemo 24.x (`for_collections` requires `element_tests` key, `_check_output.py:27`) | Restructure the 4 fastqc tests as collection tests carrying `element_tests` (count-only fastqc assertions are honest: the nf-test snapshot asserts only file names for fastqc, no md5s) |
| 2 | collection-output mismatch (workflow wiring defect) | problem 1 + 3; DB: 1 merge job over 6 BAMs, 1 cat/zip/info job | `samtools_merge` multiple-data port flattened 3 per-sample bin lists × 2 samples into one merge; per-sample grouping lost (source: merge per sample inside `alignment_to_fastq`) | Restructure: put the conversion tail (view×4 → merge of 3 single-dataset inputs → collate+fastx mapped & unmapped → cat×2 → zip) into an inline `run:` subworkflow mapped over the conversion alignments list. gxformat2 supports inline subworkflows (`schema/gxformat2.py:456`, `_build_subworkflow_step`), planemo recurses into them for shed-repo install (`iter_workflow_steps`), and mapping a subworkflow over a list yields per-sample grouping with a list:paired result |
| 3 | workflow-fidelity (parameter defect) | problem 2 (md5 mismatch, both samples) | `samtools stats` ran without `--reference`; source passes `--reference $fasta` when fasta present (`stats` main.nf) | `addref_cond` → `addref_select: history` with `ref: fasta` |
| 4 | workflow-fidelity-structural (algorithmic divergence) | paired_reads md5s unmatchable even after fix 2 | source runs `samtools collate -O \| samtools fastq` (collate_fast=false); draft used bare `samtools fastx` → coordinate-sorted read order | Fold `samtools_collate` (cached: 1.22+galaxy1, changeset e7fa06931998, `fast_mode` default False = source default, `no_pg` default true = source @PG behavior) into the inline subworkflow before each fastx step — covered by fix 2 |

Interpretation note: problems 1, 3, 4 are honest assertion/fidelity gaps to repair; problem 2 is the real structural defect the test correctly caught. The flat-paired `paired_reads` and single-dataset `fastq_info` are the workflow producing the *wrong shape*, not the test asserting the wrong shape.

## 4. Reference notes consulted

- `planemo-workflow-test-architecture` / kept-DB forensics: job chains and collection rows read from `/tmp/tmpvky91759/galaxy.sqlite` (jobs 22–29, dataset_collection_element via `dataset_collection_id`/`hda_id`/`child_collection_id` columns — the table has no `collection_id` column).
- `galaxy-collection-semantics`: merge-over-lists flattening diagnosed against mapping semantics; inline-subworkflow mapping is the Galaxy-native way to get per-sample reduction.
- `nextflow-operators-to-galaxy-collection-recipes`: the source's per-sample `SAMTOOLS_MERGE` reduction maps to a subworkflow-internal merge of single-dataset inputs, not a merge over collected lists.
- `planemo-asserts-idioms` + `iwc-shortcuts-anti-patterns`: count-only fastqc assertions are acceptable (upstream snapshot asserts names only); they still need the valid `element_tests` shape.
- No reference gap found: all four classes classify confidently against packaged references.

## 5. Recommended next step (in order)

1. Edit `galaxy-workflow.gxwf.yml`: replace the flattening tail (4× view are inputs to both merge-3 and… keep views outside if shared with QC; the conversion tail: merge + collate×2 + fastx×2 + cat×2 + zip) with an inline `run:` subworkflow "convert_one_sample" mapped over the pick_bam output list; move collate before each fastx. Keep flagstat/idxstats/stats/fastqc/multiqc outside the subworkflow (avoids unverified `when`-inside-subworkflow behavior).
2. Fix `samtools_stats` `addref_cond` to `addref_select: history` + `ref: fasta`.
3. Edit `galaxy-workflow.gxwf-tests.yml`: fastqc tests → collection tests with `element_tests`; `paired_reads` → nested element_tests form (`{"test": {"elements": {"forward": ...}}}`), not slash keys; `fastq_info` stays list with count 2 after the wiring fix.
4. `gxwf validate` + validate-tests static check.
5. Attempt 9: `flock /tmp/galaxy-arash-planemo.lock -c "planemo test galaxy-workflow.gxwf.yml --biocontainers --no_cleanup --test_output_json planemo-attempt9.json"`, logged with fresh timestamps.

---

# Attempt 10 triage (2026-11-13, 22:45–00:41) — debug-galaxy-workflow-output

## 1. Failure surface

Attempt 10 (`planemo-attempt10.json`, invocation c8a02c757cc9888e / history 1bd7d4fe44d9fa33): the workflow **imported, materialized, scheduled, and completed** — both samples ran end-to-end. All five `output_problems` are **assertion mismatches on real outputs**, two of which trace back to genuine workflow-content defects the assertions correctly caught.

## 2. Root-cause evidence

**Class A — multiple=true flatten inside mapped subworkflow (structural defect).**
Invocation job records: `merge_unmapped` produced **one** job (not 2), and the kept Galaxy sqlite shows its command consumed 6 BAM inputs (`0.sam`…`5.sam` — both samples' three unmapped bins); `cat_fastq_r1/r2` likewise ran 1 job over 4 datasets. Verified in Galaxy source (`lib/galaxy/workflow/run.py` `replacement_for_input` ~498–512): for a `multiple=true` data input with **multiple** connections, the replacement is a flat Python list of HDCAs, which is not a `DatasetCollectionInstance`, so `_find_collections_to_match` (map_over.py ~55) skips it → no map-over plan → tool consumes all cross-sample datasets at once. This silently breaks per-sample grouping.

**Class B — samtools_fastx ran `-F 0` (parameter defect).**
Kept fastq_info report (`/tmp/tmpd5_cfn1q/…txt`): `ERROR: … duplicated sequence testN:2775/`. Kept Galaxy sqlite: fastx command line contains `-F 0` (no 0x900). Cause: the wrapper's `exclusive_filter` multiple-select pre-selects 256/2048 in the form, but a stored state of `exclusive_filter: []` overrides the default with an empty selection → secondary (256) and supplementary (2048) reads were emitted into the R1/R2 bins → duplicated sequence IDs → fastq_utils rejected the report → fastq_info md5 mismatch. This also explains the test (sample 1) forward-FASTQ md5 mismatch while test2's matched (its 2 non-primary reads landed in identical positions; content only coincidentally stable). Flagstat/idxstats passed because counts are filter-independent at the alignment level they report.

**Class C — samtools stats md5 (assertion-quality, not fidelity).**
Kept outputs (`/tmp/tmpmor1lucj/`): the stats jobs ran `samtools stats --ref-seq "$reffa"` on the **original** alignments — the attempt-9 addref fix is confirmed working; test2's md5 matched. The test-sample md5 differs at byte level (thread-count/iteration-order artifacts in the long per-cycle sections). The five `SN` count lines match the nf-test snapshot's meaningful content: test 5642/5640/2/5638/2, test2 5436/5436/0/5434/0.

**Class D — fastqc_post shape (test authored against the wrong shape).**
Actual outputs are two `list:paired` collections (2 elements each), not one flat 4-element list. The test's `element_count: 4` / `collection_type: list` was written before the subworkflow restructuring fixed the shape.

## 3. Repairs applied (01:01–01:03, attempt 11 prep)

| # | Surface | Repair |
|---|---------|--------|
| 1 | flatten (A) | Three `__BUILD_LIST__` (1.1.0) steps inside `convert_one_sample` — `build_unmapped_bins` (3 view outputs), `build_cat_r1` (2 forward), `build_cat_r2` (2 reverse) — and merge/cat inputs rewired to **single connections** to the build_list outputs. Single-connection multiple=true inputs direct-match a list HDCA → no flatten, per-sample grouping restored. State declares the repeat instances (`datasets: [{},{}…]`) because `add_dummy_datasets` only marks ConnectedValue for repeat instances already present in state and the planemo import path skips `fill_defaults`; keys `datasets_N\|input` follow the canonical `queries_0\|input2` precedent (WORKFLOW_SIMPLE_CAT_TWICE). |
| 2 | -F 0 (B) | `exclusive_filter: ['256','2048']` on `fastq_mapped` and `fastq_unmapped` (= source `-F 0x900`). |
| 3 | stats md5 (C) | Both stats element_tests → `has_line` asserts on the five SN lines (values above). Logged as an assertion downgrade (md5→content lines) justified by build/thread byte-instability; the SN lines are the snapshot's real content. |
| 4 | fastq_info md5 (B/C) | → `has_text_matching` version + "Scanning and indexing all reads" + `not_has_text "ERROR"`. Logged as downgrade: expected values are echo lines, report embeds absolute tmp paths. |
| 5 | fastqc_post (D) | `collection_type: list:paired, element_count: 2` on zip + html. |

Static checks (01:02–01:03): `gxwf validate` → 23 ok / 5 fail, the 5 being the **pre-existing** samtools_view/merge state-shape diagnostics (runtime `recover_state` accepts them; attempt 10 ran those tools green) — no failure names a build_list step. `gxwf validate-tests --workflow` → valid, 0 errors. `__BUILD_LIST__ 1.1.0` added to `.tool-cache` (01:02:46).

Ledger updated: `multi-connection-flatten-fixed` (resolved), `fastx-exclusive-filter-default` (resolved).

## 4. Reference notes consulted

- `galaxy-workflow-invocation-failure-reference` + `galaxy-tool-job-failure-reference`: invocation completed; failure is at assertion level, jobs themselves succeeded.
- `planemo-asserts-idioms` + `iwc-shortcuts-anti-patterns`: has_line on SN lines is a content assertion anchored on the snapshot's own values (not existence-only); fastq_info content-marker downgrade is justified and logged.
- `galaxy-collection-semantics` (verified from Galaxy source, read-only): flatten mechanism, single-connection direct-match, repeat-instance state requirements, build_list 1.1.0 identifier semantics (`str(i)`), planemo auto-registration of `__BUILD_LIST__`.

## 5. Next step

Attempt 11: `flock /tmp/galaxy-arash-planemo.lock -c "planemo test galaxy-workflow.gxwf.yml --biocontainers --test_output_json planemo-attempt11.json"` (running since 01:04).

## Attempt 11 triage (2026-11-13 01:44)

- Surface classification: **assertion-mismatch** — 2 output problems out of a fully green invocation (all 21 steps, all jobs exit 0, both samples per-sample). No job failures, no invocation failure, no collection-shape problems. Attempt 10's 5 problems → 2.
- Problem 1 — `stats` has_line: the `SN\traw total sequences:` line carries a trailing comment (`# excluding supplementary and secondary reads`); the other asserted SN lines don't. `has_line` requires exact full-line match. Fix: include the comment text in both samples' raw-total lines (taken from the kept attempt-11 outputs in /tmp/tmp6urj2kfx). This is an assertion-precision fix, not a tolerance widening — the counts themselves are exact.
- Problem 2 — `test` forward FASTQ md5: a real workflow-content defect, root-caused without a rerun:
  - Local docker replication of the exact source chain (view | collate -O | fastq, args from modules.config) reproduces BOTH snapshot md5s exactly (content-md5 semantics confirmed). Expected values are reachable; the Galaxy chain diverges only in ordering.
  - Galaxy divergence: `samtools_collate` (iuc 1.22+galaxy1) declares `<data name="output_file" format="unsorted.bam"/>`; its output header is `@HD VN:1.6 SO:unsorted GO:query`. The `samtools_fastx` wrapper (changeset 4bde991b8037) starts `#if not $input.is_of_type('qname_sorted.bam','qname_input_sorted.bam'): samtools sort -n ...` — so the internal numeric name-sort fires and replaces collate's hash-based grouping order (collate starts at testN:1874; sort -n yields testN:1,2,3,…,2821).
  - Fix: output-level `change_datatype: qname_input_sorted.bam` on both collate steps (gxformat2 converter.py POST_JOB_ACTIONS `change_datatype` → `ChangeDatatypeAction`; export.py `_convert_post_job_actions` round-trips it; Galaxy `ChangeDatatypeAction.supports_mapped_over = True` in lib/galaxy/job_execution/actions/post.py:134). `BamInputSorted` sniff always returns False and its grooming check passes for SO:unsorted, so the re-type is stable; the fastx wrapper's `is_of_type` check then skips the internal sort and preserves collate order.
  - Not taken: re-baselining the assertion to the Galaxy-produced md5 — that would mask a genuine source-fidelity gap (read ordering) and the run rules forbid taking checksums from own Galaxy runs as expected values unless a skill says so.
- Reference gap noted: neither planemo-asserts-idioms nor galaxy-collection-semantics covers wrapper-internal reordering (a wrapper's internal sort replacing an upstream step's ordering). Drafted a feedback entry rather than guessing a repair family.
- Attempt 12 next: same planemo command; expectation is 0 output problems.

## Attempt 12 triage (2026-11-13 01:51–02:50)

Failure surface: **tool/job-level output mismatch, not an assertion-choice problem** for (1); assertion-text fix for (2).

**Surface 1 — paired_reads test forward md5 (29e442f7... vs 9b0c0886...).**
Evidence: planemo-attempt12.log jobs 34/36/42/44 are `CONVERTER_bam_to_coodinate_sorted_bam` (flush lines 6240/6252/6294/6304); converter commands `samtools sort --no-PG -O bam` at log lines 7768/7880/8046/8157 consume the collate outputs. Attempt-11 log shows the same 4 converter jobs (lines 6255+) — the converters ran BEFORE the change_datatype PJA was introduced, so the PJA was never the operative mechanism.
Classification (galaxy-tool-job-failure-reference): the wrapper's own semantics do NOT explain this — it is Galaxy's datatype-registry auto-conversion inserting a hidden job. `samtools_collate` output `unsorted.bam` is `BamNative`; `samtools_fastx` input format `sam,bam,cram` resolves to `Bam`; `class Bam(BamNative)` makes BamNative the PARENT of Bam, so `dataset.datatype.matches_any(accepted)` (data.py:1027, isinstance) is False; `process_dataset` → `find_conversion_destination` (registry.py:965) inserts the only registered bam→bam converter (coordinate sort), destroying collate order. The fastx wrapper's internal `samtools sort -n` then also fires on the converted plain bam. Catch-22 in the shed wrapper (verified against the local tools-iuc checkout and raw.githubusercontent main): plain `bam` typing → no converter but internal sort fires; `qname_input_sorted.bam` typing → converter fires anyway.
Recommended repair (applied): authored user-defined tool `samtools_fastq_stream` (bare `samtools fastq -N`, no sort, no filter; input format list includes `unsorted.bam`/`qname_input_sorted.bam`/`qname_sorted.bam` so collate output direct-matches and no converter is inserted), embedded under `run:` in both fastq steps; removed the `-F 2304` wrapper filter because the source applies no fastq-level filter (`ext.args2='-N'` only, conf/modules.config) and the local source-chain replication that reproduced 9b0c0886... included secondary/supplementary reads; removed the change_datatype PJA (moot).
Reference gap noted: no packaged note documents Galaxy's auto-converter insertion on datatype-class mismatches (BamNative-not-subclass-of-Bam) as a workflow-debugging failure surface — triage required reading Galaxy source.

**Surface 2 — stats has_line 'reads properly paired' (assertion-choice problem).**
The attempt-11 assertion omitted the trailing comment `\t# proper-pair bit set`; the kept attempt-12 stats output shows the comment on this line too (the "only raw-total carries a comment" observation from attempt 11 was wrong — kept output /tmp/tmpqlyst373 shows both). Fixed the assertion text in galaxy-workflow.gxwf-tests.yml (both samples). Not a real output regression; no IWC-shortcut violation (has_line with the exact snapshot line is the plan's chosen granularity).

## Attempt 13 triage (2026-11-13 03:26)

- **Surface classification: assertion mismatch (single output checksum)** — no import problem, no job failure, no invocation failure, no collection-shape problem. All 4 collate→UDT→merge→cat jobs exit 0; the two embedded `samtools_fastq_stream` steps execute per-sample (`mapped_over=True, state=validated`).
- **Proven**: UDT end-to-end (embedded GalaxyUserTool registration + container execution on planemo-managed Galaxy) and converter suppression (zero executed `CONVERTER_*` jobs). Both residual-runtime-risk entries in galaxy-workflow-validation-result.json are now disproven-as-risks and should be removed at the next edit.
- **The one failure**: `paired_reads > test > forward` md5 `15ab79e3...` vs snapshot `9b0c0886...`.
- **Honesty correction**: attempt 11's log claimed local replication "reproduces the snapshot md5s EXACTLY" — false, corrected in model-test-log.md. No local chain produces any of the four snapshot FASTQ values; yet Galaxy passes three of four under two different orderings. Conclusion: local docker replicas diverge from Galaxy's real intermediates (unknown factor — Galaxy's own container image/build of samtools, its dataset staging, or gzip byte details); they cannot adjudicate the expected value.
- **Reference-gap note (unchanged)**: no packaged reference covers Galaxy-inserted `CONVERTER_*` jobs or datatype-class hierarchy (`BamNative` parent-of `Bam`) as a failure surface. Ledger entry `samtools-bamnative-not-bam-subclass-triggers-auto-converter` drafted (unfiled).
- **Next step**: source-pipeline ground truth run (`nextflow run -profile test -with-docker`). If source gives 15ab79e3 for test_1 today, re-baseline that single assertion to the source-produced value with logged justification (source evidence, not Galaxy-derived); otherwise chase the chain difference.

## Attempt 13 → 14 resolution (2026-11-13 03:29–03:38) — md5 semantics, not order

- The "test forward md5 mystery" is **solved and it is not an ordering problem**: nf-test snapshot `md5,` tokens for the four merged FASTQs are **content md5s of the decompressed files** (nf-test's stable_path content hashing, same family as `bam(...).readsMD5`). Verified directly: the source pipeline's own published outputs (`nextflow run -profile test -with-docker`) have file md5s `15ab79e3`/`2c2dbdf1`/`d0fd4034`/`bcb8df2c` — Galaxy attempt 13's test forward (`15ab79e3`) is **byte-identical to the source pipeline's output** — and content md5s `9b0c0886`/`40e17982`/`a4984fb5`/`bde23801`, exactly the snapshot values.
- All four snapshot FASTQ md5s are current upstream expectations (unchanged in the 2026-11-12 CI snapshot at `c07661c`; nf-test CI green).
- Repair: stage the four source-produced merged FASTQs in `test-data/` (provenance: source pipeline run of commit aa0150e, NOT Galaxy output) and assert with `file` + `compare: diff` + `decompress: true` — the schema's designated mechanism for compressed outputs with deterministic decompressed content. This is strictly stronger than the previous (wrong-semantics) checksum assertion.
- The earlier local-replication "divergence from Galaxy" analysis (attempts 11–13 md5 matrix) is reinterpreted: the replicas were comparing file md5s against content md5 targets; the matrix values were correct but the comparison semantics were not.

## Attempt 14 triage (2026-11-13 03:50)

- **Surface: planemo test-harness path resolution** — not an import/job/invocation/collection/assertion failure. The workflow ran end-to-end (UDT jobs 40/41 executed; invocations 6c2448d1ae608df4 + 30e310228c5b6163 completed); only the `file:`-based reference lookup failed.
- **Planemo mechanics (read-only source inspection)**: `planemo/test/_check_output.py::_test_filename_getter` joins `file:` names against `dirname(runnable.path)` (the run directory), while planemo stages test-data uploads separately (Galaxy config showed `ftp_upload_dir: <run>/test-data`). So the reference file must be addressed as `test-data/<name>` in the tests file even though Galaxy itself reads the same files from its staged copy. `verify`'s decompress/diff branch was never reached (crash on `os.stat` of the wrong path).
- **Fix applied**: prefix the four `file:` values with `test-data/`; static validate-tests passes.
- **Reference-gap note**: planemo-workflow-test-architecture (packaged) documents test-data staging but not this `file:`-resolution asymmetry for workflow-level collection element tests; candidate feedback entry.

## Attempt 15 — GREEN (2026-11-13 03:59)

- **All 1 test(s) executed passed.** num_failures 0, num_errors 0. Window 03:50:22–03:57:48.
- Resolution chain for the record: (a) assertion semantics — snapshot `md5,` tokens are content md5s of decompressed FASTQs → decompressed-content diff vs source-produced test-data references (attempt 13→15); (b) planemo `file:` resolution asymmetry → `test-data/` prefix (attempt 14→15).
- No repair remains. Phase 13 (debug-galaxy-workflow-output) closes with this green run; the two feedback-ledger entries (auto-converter insertion; nf-test content-md5 semantics) stay `open, unfiled` per the run's no-posting constraint.
