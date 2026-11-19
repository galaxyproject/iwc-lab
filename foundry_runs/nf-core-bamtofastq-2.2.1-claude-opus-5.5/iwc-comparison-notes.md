# IWC exemplar comparison — nf-core/bamtofastq → Galaxy

Corpus: `galaxyproject/iwc` @ 9f111cb (2026-11-09), cloned to `~/.foundry/iwc`.
Inputs: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`, `open-requirements.ledger.yml`.

## Search

Domain = alignment → reads (BAM/CRAM to FASTQ, read-preprocessing / data conversion). Searched every `.ga` for `samtools_fastx`, `samtools_view`, `samtools_merge`, `samtools_collate`, `bamtofastq`. No IWC workflow takes a list of BAMs as its *input* and emits FASTQ. The closest workflows produce a BAM internally, split it by mapping state and extract FASTQ:

| Candidate | Domain | Input topology | Shared tool families | Motif | Confidence |
|---|---|---|---|---|---|
| `microbiome/host-contamination-removal/host-contamination-removal-long-reads` | host read removal | `list` fastq → BAM | `bamtools_split_mapped`, `samtools_fastx` on a list | split by mapped/unmapped → FASTQ per element | **low–medium** (nearest) |
| `microbiome/pathogen-identification/nanopore-pre-processing` | read QC + host removal | `list` fastq | `samtools_fastx` ×2, `collapse_dataset`, `Cut1`, `Grep1`, FastQC | split + fastx + collapse/cut tabular bridge | low |
| `VGP-assembly-v2/post-curation-processing` | assembly | — | samtools ×4 | unrelated | none |
| `microbiome/host-contamination-removal/host-contamination-removal-short-reads` | host removal | `list:paired` | bowtie2 + `pick_value` | `when` + `pick_value` branch selection | pattern only |

Nearest: **`microbiome/host-contamination-removal/host-contamination-removal-long-reads`**, steps `Split BAM`, `_unlabeled_step_7` (samtools_fastx). Confidence **low–medium**: same tool family and per-element map-over of a BAM → FASTQ conversion, but different domain intent (host removal), single-end long reads, and BAM is internal rather than the workflow input.

## Nearest exemplar (gxformat2) excerpt

Full subgraph: `iwc-exemplar.gxwf.yml`.

```yaml
  - id: _unlabeled_step_7
    doc: Extractions of FastQ from the unmapped reads
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
    in:
      - id: input
        source: Split BAM/unmapped
    out:
      - id: output
        rename: Reads without host or contamination reads
    state:
      output_fmt_cond:
        output_fmt_select: fastqsanger
        output_quality: false
        ilumina_casava: false
      outputs:
        - other
      copy_tags: false
      read_numbering: ""
      exclusive_filter:
        - "256"
        - "2048"
      idxout_cond:
        idxout_select: "no"
```

## Structural diff and guidance

| # | Finding | Owner |
|---|---|---|
| 1 | IWC extracts FASTQ with **`samtools_fastx`**, whose `outputs` multi-select chooses which streams (`other`, `r1`, `r2`, …) and `read_numbering` maps to `-N`/`-n`. The brief's "collate \| fastq" nodes (16, 17, 20) should first try `samtools_fastx`; the exemplar does not collate (input there is name-grouped minimap2 output). For coordinate-sorted BAM input, collation matters (`samtools fastq` pairs mates only when adjacent). | tool-step (discovery) |
| 2 | IWC splits by mapping state with **`bamtools_split_mapped`** (one tool, two outputs). The brief's four flag-filter `samtools view` nodes (11–14) are finer-grained (pair-level mapped/unmapped classes, needed to keep pairs intact). Keep the four views; the bamtools split is per-read and would break pairs. | template (keep) |
| 3 | `exclusive_filter: [256, 2048]` matches `samtools fastq` default `-F 0x900`; keep the default to match nf-core. | tool-step |
| 4 | Per-element routing via **collapse_dataset + Cut1/Grep1** tabular bridge is corpus-observed in `nanopore-pre-processing`; supports data-flow nodes 8–9. | template (confirms) |
| 5 | `when` + `pick_value` (`iuc/pick_value` tool, not a native module) is corpus-observed in `host-contamination-removal-short-reads` for transform-or-pass-through. The data-flow node 6 should use the `pick_value` **tool** `toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value`; its data mode takes datasets — collection support must be verified (ledger `pick-value-collections`). | tool-step |
| 6 | Outputs in IWC carry public labels (`Reads without Host or Contamination`) and `rename` post-job actions; follow the interface brief labels. | template |
| 7 | IWC test style: `host-or-contamination-removal-on-long-reads-tests.yml` — not used for bamtofastq; defer to test-plan Molds. | test |
| 8 | No IWC exemplar for a list-of-BAM workflow *input*, the four-way pair-class split, or ordered mapped+unmapped FASTQ concatenation. These are structural divergences with no corpus precedent. | template (recorded in ledger) |
