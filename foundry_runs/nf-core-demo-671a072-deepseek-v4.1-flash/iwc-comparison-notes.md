# IWC exemplar comparison — nf-core/demo

Design briefs compared: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`.
Corpus: IWC checkout at `~/.foundry/iwc` @ `9f111cb8661fa446e43f92ec4863e6a66972a91c` (2026-11-09).

## Ranking

| candidate | domain/intent | input topology | tools | DAG motif | confidence |
|---|---|---|---|---|---|
| `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-single-end` | read QC → report (closest intent) | `list` collection | FastQC + MultiQC (+ trimmomatic/prinseq) | map FastQC over collection → single MultiQC reduction | **medium** — same intent and motif; single-end input, extra QC tools |
| `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-paired-end` | same | `list:paired` | same | same, plus `__UNZIP_COLLECTION__` after fastp | medium — paired topology but a merge step we do not have |
| `transcriptomics/rnaseq-pe` | RNA-seq quantification (different domain) | `list:paired` | fastp + FastQC + MultiQC | `__FLATTEN__` → QC subworkflow `when:`-gated → `pick_value` over two MultiQC branches | low as a domain exemplar; **high-value structural precedent** for flatten/when/pick_value |

No IWC workflow matches "generic FASTQ QC demo" exactly; no QC-named workflow exists in the corpus. The MGnify QC SE subgraph is the nearest domain exemplar; `rnaseq-pe` supplies the two structural recipes the briefs actually needed.

## Nearest exemplar — relevant subgraph

IWC id: `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-quality-control-single-end`, steps 0 → 8 → 21 (the per-FastQC `Replace` step is elided; it only rewrites output identifiers for MultiQC). Full converted view: `iwc-exemplar.gxwf.yml`.

```yaml
inputs:
  - id: Single-end reads
    type: collection
    collection_type: list
steps:
  - id: fastqc
    tool_id: toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc/0.74+galaxy1
    in:
      - id: input_file
        source: Single-end reads
    out:
      - id: html_file
      - id: text_file
  - id: multiqc
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5
    in:
      - id: results_0|software_cond|output_0|input
        source: fastqc/text_file
    out:
      - id: html_report
      - id: stats
```

## Structural diff against the briefs

| brief decision | exemplar evidence | verdict | owner |
|---|---|---|---|
| input `list:paired_or_unpaired` | MGnify uses `list` (SE) or `list:paired` (PE); `rnaseq-pe` uses `list:paired` | keep `paired_or_unpaired` — it is the only shape that represents optional mates; IWC has no exemplar for mixed rows, so confidence stays medium | template (surface only) |
| map FastQC over the input collection, then flatten the *output* (`flatten_html`, `flatten_zip`) | `rnaseq-pe` flattens the **input** collection once (`__FLATTEN__`, `join_identifier: "_"`, step 11) and maps FastQC over the resulting **flat per-file list** | **adopt the input-flatten idiom.** It removes both placeholder steps: FastQC/trim map over a flat list, outputs are flat lists, MultiQC consumes the flat list directly. Mate-level identifiers (`SAMPLE1_PE_1`, `SAMPLE1_PE_2`) match nf-core's per-mate report names in the test snapshot. | template/data-flow — see revision in `nextflow-galaxy-data-flow.md` |
| FastQC output `zip` feeds MultiQC | MGnify feeds FastQC `text_file` (raw data) to MultiQC's `software_cond` input; MultiQC consumes whatever raw QC text/zip the wrapper exposes | template picks the wrapper and wires its raw-data output; do not assume `zip` by name | tool step |
| `trimmed_reads` output as `list:paired_or_unpaired` | after input flatten, every IWC per-file step outputs a flat list; `rnaseq-pe` never re-pairs per-file QC outputs | expose `trimmed_reads` as a flat `list` with element identifiers `sample_1`/`sample_2`; pairing is not restored anywhere downstream | template/interface |
| inline `when:` on the trim step | `rnaseq-pe` gates a QC subworkflow with `when: $(inputs.when)` driven by a boolean param; MGnify has no conditional | inline `when:` is fine for one step (no subworkflow in the source, no fan-in); no `pick_value` needed | template |
| MultiQC single invocation over the flat list | MGnify: one MultiQC step consuming a collection through `results_0|software_cond|output_0|input` | matches; MultiQC wrapper takes the collection on one `software_cond` slot | template |
| `cowpy` output | no IWC precedent (dropped/absent) | carried as a standalone node; discovery decides | discovery |

### `none` on MultiQC config

Neither exemplar exposes a MultiQC config file input; the wrapper accepts optional config in other IWC workflows, but not here. The `multiqc_config` optional input stays unverified (ledger entry `multiqc-wrapper-config-input-unverified`).

## Guidance for the template Mold

1. Start from a flat per-file list: `__FLATTEN__` the `list:paired_or_unpaired` input with `join_identifier: "_"`, then map FastQC, trim, and MultiQC over it. Element identifiers become `SAMPLE_1`/`SAMPLE_2`.
2. Do **not** create `flatten_html`/`flatten_zip` steps; the data-flow brief's placeholder transforms are superseded by the input flatten.
3. Gate the trim step with inline `when:` on `!(inputs.skip_trim)`; no `pick_value`.
4. Wire MultiQC from the FastQC wrapper's raw-data output; add the optional config input only if the chosen wrapper has one.
5. Keep `cowpy` as one un-mapped step.

## Pattern issues (routed, not blocking)

- The `__FLATTEN__`-the-input-then-map idiom appears in `rnaseq-pe` and is not recorded in the channel-shape-mapping note; also filed as foundry feedback from the data-flow phase.
- No IWC exemplar combines a `paired_or_unpaired` input with map-over QC; the template should treat that shape as medium-confidence and let the workflow test confirm it.
