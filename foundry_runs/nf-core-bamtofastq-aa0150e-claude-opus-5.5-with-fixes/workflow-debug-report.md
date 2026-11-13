# Workflow debug report — planemo attempt 1

Input: `workflow-test-result.json` (attempt 1), `planemo/attempt1/test.json`.

## Classification
**First failure surface: collection-output mismatch** (not import, not job, not invocation). Invocation fully scheduled; every job `ok`. The assertion report lists 4 output problems:

- `fastq_paired`, `fastqc_post_paired_raw`, `fastqc_post_paired_html`: elements are `forward`/`reverse` — a `paired`, not `list:paired`.
- `fastq_info_paired`: single dataset, not a list.

## Evidence
- Step 25 `cat_r1` (tp_cat 9.11+galaxy0) ran **1 job** (expected 2). Its command line is
  `cat <R1 map test> >> out && cat <R1 map test2> >> out && cat <R1 unmap ...>` — both samples' files concatenated into one dataset.
- `tp_cat` declares `inputs` as `data multiple="true"` (summaries/cat.galaxy-tool-summary.json: `inputs data ext=txt,fastq.gz,... multiple`). Galaxy collection semantics: a `list` connected to a `multiple` data input is **reduced** (one job over all elements), not mapped.
- Downstream zip (1 job) therefore built one `paired`; fastq_info (1 job) one dataset; fastqc (2 jobs = one per mate).
- Source operator: `COLLATE_FASTQ_MAP.out.fastq.join(COLLATE_FASTQ_UNMAP.out.fastq).map{...}` → per-sample CAT_FASTQ — a keyed join, i.e. map-over two lists with matching identifiers, which a reducing input cannot express.

## Root cause and route
Wrapper-choice mismatch at implementation tier (phase 7, steps `cat_r1`, `cat_r2`): the chosen wrapper runs the work but its input cardinality reduces the collection. Topology is fine.

## Recommended repair
Re-resolve `cat_r1` / `cat_r2` to stock **`cat1`** 1.0.0 ("Concatenate multiple datasets or collections", `tools/filters/catWrapper.xml` in the target Galaxy, listed in its `tool_conf.xml.sample`): `input1` and `queries_N|input2` are single `data` params, so the two lists map element-wise; output `format_source="input1"` keeps `fastqsanger.gz`; command is plain `cat` (gzip members concatenate validly, matching nf-core CAT_FASTQ).

Not a test-assertion problem: no assertion is relaxed. Passing evidence kept: nf-test md5 parity for flagstat and idxstats (4/4), stats SN and fastqc_pre checks.

## Outcome
Repair applied (cat_r1/cat_r2 → cat1 1.0.0). Planemo attempt 2 (13:52:45–13:56:45): **pass**, 1/1 test, all assertions green; cat_r1/cat_r2 ran 2 jobs each, zip 2, fastq_info_paired 2, fastqc_post_paired 4.
