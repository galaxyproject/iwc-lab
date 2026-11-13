# Workflow debug report — nf-core/demo Galaxy translation

Input: `workflow-test-result.json` → **status: pass**. All 1 test passed (`num_tests: 1`, `num_errors: 0`, `num_failures: 0`, planemo exit 0).

## Verdict

**Nothing to debug.** The final run produced every asserted output:

- `fastqc_html` — collection `list`, 6 elements, `SAMPLE1_PE_1` is `html`
- `trimmed_reads` — collection `list`, 6 elements, `SAMPLE1_PE_1` is `fastqsanger.gz`
- `multiqc_report` — dataset, `html`
- `cowpy_text` — dataset, `txt`, checksum `md5$9c8be9f4550989b40901f379cb1a605f`, contains `nf-core rules!`

The five earlier attempts never reached a green run; they are recorded here because each failed at a **different surface**, and none was an output/assertion problem:

| attempt | surface | classification | resolution |
|---|---|---|---|
| 1 | planemo CLI | not-run — bad flag (`--verbose`) | dropped the flag |
| 2–3 | workflow import / conversion | not-run — planemo's bundled gxformat2 converter failed to resolve `flatten_inputs/output` (step `label` shadows `id`); after that, Galaxy rejected frame colours (`#d9edf7` vs named literal) | converted steps to list form, removed step labels, named colours |
| 4 | test-data staging | not-run — `galaxy.tool_util.cwl.util.to_elements` asserts every element of a nested collection has `elements`, so a mixed `list:paired_or_unpaired` cannot be staged | input switched to a flat `list` of 6 files (workflow flattens downstream anyway) |
| 5 | tool/job failure | **fail** — FastQC exit 127; conda env `~/miniforge3/envs/__fastqc@0.12.1` exists but has no `bin/`, so activation fails and the binary is missing. Environment-level, not wrapper- or data-level | reran with `--biocontainers --docker` |

Attempt 5 is the only genuine red run, and its modality is a **dependency/environment failure** (shared conda env broken on this machine), not a workflow defect: the same workflow imported, invoked and scheduled correctly, and the identical workflow passed once each tool ran from its container.

## Residual risks (all unexercised, none observed)

- `skip_trim: true` (trim step skipped by `when:`) was not covered by the test.
- `multiqc_title` was exercised, but the no-title path was not.
- Only the 6-file test profile was run; no full-scale data.

## Recommended follow-ups

1. Treat the broken shared conda env as a host issue rather than a Foundry defect; container mode (`--biocontainers --docker`) is the reliable path on this machine.
2. Optionally add a second test case with `skip_trim: true` to cover the conditional branch.
