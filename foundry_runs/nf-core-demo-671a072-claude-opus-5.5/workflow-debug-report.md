# Workflow debug report: nf-core/demo Galaxy translation

Input: `workflow-test-result.json` (status `fail`, modality `assertion-mismatch`).

## Classification

| Surface | Result |
|---|---|
| Workflow import | OK. The embedded GalaxyUserTool (cowpy) imported with `GALAXY_CONFIG_OVERRIDE_ENABLE_BETA_TOOL_FORMATS=true`. |
| Invocation | OK. All 7 steps scheduled. |
| Jobs | OK. 14/14 jobs `ok` (cowpy 1, FastQC 6, seqtk 6, MultiQC 1). |
| Collection shape | OK. FastQC and seqtk mapped over every leaf of `list:paired_or_unpaired`. |
| **Assertions** | **2 failures, with different root causes.** |

## Failure 1: `trimmed_reads` checksum. Wrong assertion, not a regression.

- The test asserted `checksum: md5$7dd2fd…` with `decompress: true`.
- Galaxy `tool_util/verify/__init__.py` computes `_verify_checksum(output_content, …)` on the stored (gzip) bytes. `decompress` is applied only to `asserts` and `compare`.
- **The output content is correct.** Running `seqtk trimfq -q 0.05 -l 30` (the wrapper's bound state) in the same `quay.io/biocontainers/seqtk:1.4--he4a0461_1` image on `sample1_R1.fastq.gz` gives decompressed md5 `7dd2fd0d542d9259d9aed53550907fae`, identical to the nf-test snapshot. The `has_n_lines` (decompressed) checks passed.
- Surface: assertion choice (implement-galaxy-workflow-test). Recommended fix: replace `checksum` with `compare: diff` + `decompress: true` against the nf-core run's own trimmed file for one anchor element, and keep the decompressed `has_n_lines` checks for every element. Not a weakening, because the diff is a full-content equality check.

## Failure 2: `multiqc_stats` has 4 lines instead of 7. Real output defect.

- The FastQC wrapper (`rgFastQC.xml` l.16) names each report after `$input_file.element_identifier`. Mapped directly over `list:paired_or_unpaired`, the leaf identifiers are only `forward`, `reverse` and `unpaired`, so the 6 FastQC reports collapse to 3 MultiQC sample rows and samples become indistinguishable in the report.
- This is a collection element-identifier mismatch that comes from the data-flow/template decision to map FastQC directly over the nested collection. The IWC comparison (finding #2) flagged the alternative: rnaseq-pe uses `__FLATTEN__` (`join_identifier: _`) before Falco for this reason.
- Surface: topology (repair-galaxy-draft-topology tier). Recommended fix: insert `__FLATTEN__` 1.0.0 (`join_identifier: _`) between `reads` and `fastqc`. MultiQC samples become `SAMPLE1_PE_forward` … `SAMPLE3_SE_run2_unpaired` (6 rows, 7 lines), matching the 6 NF FastQC rows. `fastqc_html` becomes a flat `list`. seqtk stays on the nested collection, so `trimmed_reads` keeps `list:paired_or_unpaired`.

## Recommended next step

Apply both fixes, re-extract, re-validate, and re-run `planemo test`. Results: see "Post-debug repair" below.

## Post-debug repair (applied after triage, outside the harness's 13 phases)

- Draft: added step `flatten_reads` (`__FLATTEN__` 1.0.0, `join_identifier: _`) feeding `fastqc`. `fastqc_html` is now `list` (6 elements). Re-extracted `galaxy-workflow.gxwf.yml`; `gxwf validate` gives 5/5 tool states OK.
- Tests: `trimmed_reads` checksum replaced by `compare: diff` + `decompress: true` against the nf-core run's `SAMPLE1_PE_sample1_R1.fastq.gz` (`test-data/expected/`), plus decompressed `has_n_lines` on all 6 leaves. `fastqc_html` checks `element_count: 6` and named elements. `multiqc_stats` checks 7 lines and the `SAMPLE1_PE_forward` / `SAMPLE3_SE_run1_unpaired` sample names.
- Re-run (`planemo-run2/`): **passed**, 1/1 test. All 8 steps scheduled, 15 jobs `ok`.
