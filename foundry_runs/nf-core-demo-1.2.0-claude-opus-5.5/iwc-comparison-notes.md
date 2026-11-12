# IWC exemplar comparison — nf-core/demo 1.2.0

Inputs: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`, `open-requirements.ledger.yml`. Corpus: `galaxyproject/iwc` @ `9f111cb` (`~/.foundry/iwc`).

## Ranking

| Rank | IWC workflow | Domain | Input topology | Tool families | DAG motifs | Confidence |
|---|---|---|---|---|---|---|
| 1 | `read-preprocessing/short-read-qc-trimming/short-read-quality-control-and-trimming` | short-read QC + trimming (same) | `list:paired` (ours: `list:paired_or_unpaired`) | fastp + MultiQC (ours: FastQC + seqtk + MultiQC) | map-over trim → reduce into MultiQC | **Medium** |
| 2 | `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-paired-end` | amplicon QC (adjacent) | `list:paired` | FastQC, MultiQC (+fastp, Trimmomatic, …) | FastQC `text_file` → MultiQC `software: fastqc` | Low (idiom source only) |

No IWC workflow uses seqtk trimfq, cowpy, or a `paired_or_unpaired` input, and none mixes single/paired reads in one input. Nearest = rank 1 (Medium): same analysis intent and map→reduce shape; tool families only partly overlap.

## Structural diff vs design briefs

| # | Finding | Briefs | Exemplar | Routed to |
|---|---|---|---|---|
| D1 | Input collection type | `list:paired_or_unpaired` + explicit flatten N1 | `list:paired`, trimming tool consumes the paired collection directly (`single_paired_selector: paired_collection`) | template/data-flow — keep `paired_or_unpaired` (the source test sheet really is mixed); no corpus precedent, recorded in ledger |
| D2 | QC tool feeding MultiQC | FastQC per file → MultiQC | rank 2: FastQC `text_file` (raw data) → MultiQC `results_0|software_cond` `software: fastqc`, `output_N|input` | tool-step — wire FastQC **`text_file`**, not zip; `fastqc_zip` checkpoint becomes FastQC raw text |
| D3 | MultiQC stats output | `multiqc_stats` shape open | MultiQC wrapper has a `stats` output (rank 2 promotes it as "MultiQC statistics") | template — `multiqc_stats` ← `multiqc/stats`; closes `multiqc-stats-output-shape` |
| D4 | Trimmed reads output | per-file `list` | promoted as public output with `rename` + `add_tags: name:Reads` | template — promote `trimmed_reads`; tags optional |
| D5 | Report output labels | snake_case labels | human-readable ids (`MultiQC HTML report`) | template — snake_case is fine; IWC accepts either, labels must stay stable |
| D6 | Conditional trimming (`when:` on `skip_trim`) | inline `when` | exemplar has no conditional | none — engine-supported (see conditional note); flag for reviewers |
| D7 | Standalone no-input step (cowpy) | source step | no precedent | tool-step — discovery decides |
| D8 | Tests | md5 / text checks on cowpy, trimmed reads, MultiQC stats | exemplar: `has_text` assertions on report + per-element JSON `element_tests` | test — use `element_tests` keyed by element identifier; `has_text` on MultiQC html |

## Nearest exemplar (gxformat2) excerpt

IWC `read-preprocessing/short-read-qc-trimming/short-read-quality-control-and-trimming`, steps `fastp`, `MultiQC` (fuller slice, plus the FastQC idiom from rank 2: `iwc-exemplar.gxwf.yml`):

```yaml
inputs:
  - id: Raw reads
    type: collection
    collection_type: list:paired
outputs:
  - id: fastp trimmed reads
    outputSource: fastp/output_paired_coll
  - id: MultiQC HTML report
    outputSource: MultiQC/html_report
steps:
  - id: fastp
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp/1.4.0+galaxy0
    in:
      - id: single_paired|paired_input
        source: Raw reads
    out:
      - id: output_paired_coll
        rename: Trimmed reads
  - id: MultiQC
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5
    in:
      - id: results_0|software_cond|input
        source: fastp/report_json
    out:
      - id: html_report
      - id: stats
    tool_state:
      results:
        - software_cond: {software: fastp}
# rank-2 idiom: FastQC (devteam/fastqc 0.74+galaxy1) out text_file ->
#   MultiQC results_0|software_cond {software: fastqc} output_0|input
```

## Guidance for the template Mold

1. Keep `reads: list:paired_or_unpaired` and the flatten placeholder; this is a deliberate divergence because the source test data is mixed.
2. Model FastQC → MultiQC with FastQC's raw-text output and MultiQC's `fastqc` software block; expose `multiqc/stats` as `multiqc_stats`.
3. Keep seqtk as a mapped `when:`-gated step with a promoted `trimmed_reads` output.
4. Leave wrappers for FastQC/MultiQC identity-pinned at most; seqtk/cowpy deferred to discovery.
