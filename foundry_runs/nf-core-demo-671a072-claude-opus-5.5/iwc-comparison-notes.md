# IWC comparison — nf-core/demo

Corpus: `galaxyproject/iwc` @ `980fc00` (2026-11-04), cloned to `~/.foundry/iwc`.

## Candidates and ranking

| Rank | IWC workflow | Confidence | Why |
|---|---|---|---|
| 1 | `read-preprocessing/short-read-qc-trimming/short-read-quality-control-and-trimming` | **Medium** | Same intent (raw-read QC + quality trimming + MultiQC aggregate). Input is `list:paired`, not `list:paired_or_unpaired`. Trimming is fastp, not seqtk, and there is no standalone FastQC. |
| 2 | `transcriptomics/rnaseq-pe/rnaseq-pe` | Low (motif only) | Different domain (RNA-seq). Contains the exact per-file QC → MultiQC motif: `__FLATTEN__` (`list:paired` → `list`, `join_identifier: _`) → Falco (FastQC reimplementation) `text_file` → MultiQC `software: fastqc`, `output type: data`. |
| — | `mgnify-amplicon-…-quality-control-*`, `genome-assembly/quality-and-contamination-control-raw-reads` | Low | Share FastQC/MultiQC only, which is generic. |

No IWC workflow uses `seqtk trimfq`. No workflow wires a FastQC-family tool over `list:paired_or_unpaired`; the only `paired_or_unpaired` users are `variant-calling/giraffe-deep-variant-pangenome-calling` and `virology/influenza-isolates-consensus-and-subtyping`, both out of domain.

## Structural diff vs. design briefs

| # | Finding | Owner |
|---|---|---|
| 1 | **Input topology.** IWC QC workflows take `list:paired` (sibling SE workflows exist for amplicon QC). The brief's `list:paired_or_unpaired` has no in-domain precedent. It is valid Galaxy and matches the mixed SE/PE test sheet, so keep it, but treat map-over of single-dataset QC tools over it as an implementation-time check. | template / tool-step |
| 2 | **Per-file QC idiom.** rnaseq-pe flattens the paired collection (`__FLATTEN__`, `join_identifier: _`) before Falco, which makes MultiQC sample names `<sample>_forward` / `<sample>_reverse`. The brief maps FastQC directly over the nested collection. Both work. Direct map-over keeps `fastqc_html` addressable as `<sample>/forward`, and MultiQC accepts a nested collection through a multiple=true data input. Prefer direct map-over and add a flatten only if the MultiQC step rejects the nested input. | template |
| 3 | **MultiQC wiring.** Exemplars use `toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5`, a `results` repeat with `software_cond.software: fastqc` and `output_0.type: data` fed from the FastQC/Falco **text** output (not the zip), `title` set, and `stats` output hidden. To expose `multiqc_stats` as a checkpoint, set that output unhidden and promoted. | tool-step |
| 4 | **Output promotion.** The exemplar promotes the trimmed collection and per-sample JSON reports alongside the MultiQC HTML, and tests the JSON with `element_tests` content asserts. That matches the brief's `trimmed_reads` + `multiqc_stats` checkpoints. | test |
| 5 | **Test data.** The exemplar uses Zenodo `location:` URLs with `filetype: fastqsanger.gz`. The demo fixtures are on `raw.githubusercontent.com/nf-core/test-datasets` — acceptable for a translation run; IWC submission would want Zenodo. | test |
| 6 | **COWPY** has no corpus counterpart (expected; it is a toy step). | tool-step |

## Nearest exemplar (gxformat2) excerpt

From `read-preprocessing/short-read-qc-trimming` (steps `Raw reads` → `fastp` → `MultiQC`); full slice in `iwc-exemplar.gxwf.yml`:

```yaml
  - id: MultiQC
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5
    in:
      - id: results_0|software_cond|input
        source: fastp/report_json
    out:
      - id: stats
        hide: true
      - id: html_report
        rename: MultiQC report
    tool_state:
      results:
        - __index__: 0
          software_cond:
            software: fastp
            input: {__class__: ConnectedValue}
      title: ""
```

Low-confidence pattern excerpt (rnaseq-pe `More QC` subworkflow + main MultiQC), FastQC-family motif only:

```yaml
  - tool_id: __FLATTEN__            # list:paired -> list
    in: [{id: input, source: Collection paired FASTQ files}]
    tool_state: {join_identifier: _}
  - tool_id: toolshed.g2.bx.psu.edu/repos/iuc/falco/falco/1.3.2+galaxy0
    in: [{id: input_file, source: FASTQ collection}]
    out: [{id: html_file}, {id: text_file}]
  # MultiQC:
  - id: results_3|software_cond|output_0|input
    source: More QC/Falco text output   # software: fastqc, output type: data
```

## Guidance for the template

- Keep three inputs (`reads` `list:paired_or_unpaired`, `skip_trim`, `multiqc_title`) and four tool steps.
- MultiQC: pin the IUC wrapper family and feed the FastQC text/raw-data output into a `fastqc` results block; wire `title` from `multiqc_title`.
- Expose `multiqc_stats` by not hiding `stats`.
