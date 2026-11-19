# IWC exemplar comparison — nf-core/bamtofastq

IWC corpus: `~/.foundry/iwc` @ `c07557f` (pulled 2026-11-12).

## Search

- Domain/intent: BAM/CRAM → FASTQ format conversion with pre/post read QC. IWC has **no workflow whose primary intent is alignment-to-FASTQ conversion**.
- Searched all `.ga` for `samtools_fastx`, `samtools_collate`, `bam_to_fastq`, `picard_SamToFastq`: 2 hits, both microbiome host-removal (long reads). Searched `samtools_flagstat|samtools_stats|samtools_idxstats`: 21 workflows (variant calling, viral consensus) — tool-family overlap only.
- Idiom checks: `__FILTER_FROM_FILE__` used in 8 workflows (e.g. `virology/influenza-isolates-consensus-and-subtyping`), `collapse_dataset` widely used (e.g. `microbiome/pathogen-identification/nanopore-pre-processing`).

## Ranking

| Rank | IWC workflow | Confidence | Why |
|---|---|---|---|
| 1 | `microbiome/host-contamination-removal/host-contamination-removal-long-reads/host-or-contamination-removal-on-long-reads` | **Low** (cross-domain structural) | Shares the motif "split BAM by mapped/unmapped → samtools_fastx → FASTQ list" and a `list` input; different science (host removal), single-end long reads, alignment produced in-workflow by minimap2. |
| 2 | `microbiome/pathogen-identification/nanopore-pre-processing/Nanopore-Pre-Processing` | Low | Same samtools_fastx + collapse_dataset idioms, FastQC pre/post; long-read domain. |
| 3 | `variant-calling/generic-variant-calling-wgs-pe/Generic-variation-analysis-on-WGS-PE-data` | Low | samtools stats/flagstat over a list of BAMs only. |

No High/Medium domain exemplar. The excerpt below is a **pattern comparison**, not a domain exemplar.

## Pattern excerpt (low confidence) — steps `Split BAM`, `_unlabeled_step_7` (samtools_fastx)

Full subgraph: `iwc-exemplar.gxwf.yml`.

```yaml
  - id: _unlabeled_step_7
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
      outputs:
        - other
      read_numbering: ""
      exclusive_filter: ["256", "2048"]
      idxout_cond:
        idxout_select: "no"
```

## Structural diff vs briefs (routed)

| # | Finding | Owner |
|---|---|---|
| 1 | IWC uses `samtools_fastx` (iuc) for BAM→FASTQ; its `outputs` multi-select (`other`, R1/R2, singletons) maps onto the source's `-0/-1/-2/-s`. Whether it runs `samtools collate` first (source does) must be checked at discovery — if not, a separate collate/sort-by-name step is needed. | tool-step |
| 2 | IWC splits mapped/unmapped with one `bamtools_split_mapped` step; the brief keeps four `samtools view` flag filters to match the source's exact flag sets (`-f1 -F12`, `-f12 -F256`, `-f4 -F264`, `-f8 -F260`) — a 2-way split would not reproduce them. Keep the brief's design. | template (no change) |
| 3 | IWC exemplars expose FASTQ outputs with `rename` and hide intermediates (`hide: true` on split outputs). Template should hide the four view outputs, the bundle and the merge. | template |
| 4 | IWC exemplars commonly end with MultiQC; the brief drops MultiQC because the source's MultiQC carries no QC content. Divergence is intentional (ledger `multiqc-report-not-carried`). | template (no change) |
| 5 | The brief's classifier → `collapse_dataset` → filter → `__FILTER_FROM_FILE__` chain has corpus precedent for each piece (collapse_dataset, Cut1/Grep1 filtering, `__FILTER_FROM_FILE__`), though not as one recipe. | pattern |
| 6 | IWC tests use `has_text` / `has_n_lines` content assertions per element; the snapshot md5s for samtools reports may be usable as `md5` only if wrapper output is byte-identical (version headers in `samtools stats` make that unlikely). | test |
