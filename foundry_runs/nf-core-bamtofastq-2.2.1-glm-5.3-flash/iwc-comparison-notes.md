# IWC comparison notes — nf-core/bamtofastq → Galaxy

*Inputs: nextflow-galaxy-interface.md, nextflow-galaxy-data-flow.md (same run). Corpus: ~/.foundry/iwc @ 9f111cb8 (133 .ga workflows, already up to date). Written 2026-11-09 23:5x local (via `date`).*

## Retrieval and ranking

Feature hierarchy applied: (1) domain = BAM/CRAM alignment → read extraction + QC, (2) input collection topology, (3) tool families (samtools, fastqc, multiqc), (4) DAG motifs, (5) outputs, (6) tests.

Search: full-corpus scan for samtools_view / samtools_fastq(-fastx) / fastqc / flagstat co-occurrence, then manual inspection of the top candidates (mgnify QC pipelines, MAGs-generation, Nanopore-Pre-Processing, host-contamination-removal, atacseq, rnaseq-pe).

### Candidates

| Workflow | samtools_view | samtools_fastq/x | FastQC | MultiQC | Assessment |
|---|---|---|---|---|---|
| **microbiome/pathogen-identification/nanopore-pre-processing/Nanopore-Pre-Processing** | 0 | 2 | 3 | 2 | **nearest** — see below |
| mgnify-amplicon-pipeline-v5-quality-control-single-end | 0 | 0 | 4 | 1 | reads-in/QC-out per sample; right QC shape, wrong input domain (FASTQ, not alignments) |
| microbiome/mags-building/MAGs-generation | 0 | 0 | 0 | 1 | heavy collection-idiom workflow (Apply Rules ×4, pick_value ×3, FILTER_EMPTY ×2) — idiom source, not domain exemplar |
| microbiome/host-contamination-removal (short+long reads) | 1 | 1 | 0 | 1 | alignment → extraction, but the extraction is host-removal plumbing, one linear path, no per-sample QC fan-out |
| epigenetics/atacseq | 1 | 0 | 0 | 1 | flagstat/idxstats sibling + samtools_view + pick_value pair + MultiQC; right conditional+reduction idioms, wrong domain (peaks, not read extraction) |

### Nearest exemplar: Nanopore-Pre-Processing — confidence: **Medium**

Same subdomain (alignment → per-sample read extraction → FastQC → MultiQC reduction), same primary tool families (samtools extraction + FastQC + MultiQC reduction over per-sample collections). Partial match, not canonical: its input is a `list` of FASTQs going *into* alignment, whereas bamtofastq's input is a sample_sheet of BAM/CRAMs coming *out of* one; it has no pairedness branch, no flag-split, no chr conditional, no samtools stats family. Useful for the extraction→QC→reduce subgraph idioms and for promoted-output conventions; not for the input tier or the conditionals.

## Structural diff against the briefs

| Aspect | Briefs (bamtofastq) | Exemplar | Guidance for template tier |
|---|---|---|---|
| Input topology | `sample_sheet` collection (1 alignment/row, optional fai + 5 scalars) | `list` collection of FASTQs + host reference + params | No corpus precedent for a sample_sheet input on an alignment-QC workflow — template must rely on the sample-sheet note's YAML shape (column_definitions), not the exemplar. Divergence flagged, not a fix. |
| Split-by-mapping-status | N3/N4 runtime pairedness split (verdict-driven collection split) | `bamtools_split_mapped` splits one BAM's reads by mapped status — a *within-file* split, not a *between-samples* split | The exemplar cannot source the C1 split. The per-element routing remains the brief's medium-confidence open item (`single-paired-runtime-branch-representation`). Template should not pattern-match the exemplar here. |
| Extraction step | N5–N9 samtools view/collatefastq per alias | `samtools_fastx` ×2 (mapped/unmapped) with explicit filter flags `256`, `2048` and `output_fmt_select: fastqsanger.gz` | Confirms corpus idiom: extraction tools are configured via flag-list tool state and output datatype is forced with `change_datatype: fastq.gz` on the output — carry the `change_datatype` idiom to the template for the merged/other FASTQ outputs. |
| Failure cleanup | not in briefs | `__FILTER_FAILED_DATASETS__` after extraction | Corpus-attested pattern the briefs didn't name: if extraction tools can fail per element, a filter-failed step before QC is idiomatic. Optional; note for template. |
| Collapse before reduce | N13 MultiQC over merged flat list | `collapse_dataset` to pool per-sample text into one file before MultiQC | MultiQC in the exemplar consumes pooled tabular + reports. bamtofastq's MultiQC takes the reports directly; the briefs' T6 (merge collections → flat list) is the right shape — no change. |
| QC fan-out/reduce | N2 pre-conversion FastQC + N1 stats family + N11 post-conversion FastQC → N13 | FastQC ×3 (raw, post-trim, post-extraction) + MultiQC ×2 (before/after) | Corpus confirms per-sample FastQC collections feeding MultiQC reductions is standard. The briefs' two-stage QC (pre/post) is finer than the exemplar but structurally compatible. |
| Conditional idiom | C2/C3 inline `when:`; C4 transform-or-pass-through with pick_value | pick_value ×1 pair (steps 22–23) resolving mapped/unmapped alternates | Confirms `pick_value` is live corpus practice (also in MAGs-generation ×3, host-removal, atacseq ×2). C4's pick_value disposition has direct corpus grounding. |
| Output promotion | 9 outputs incl. 6 collections | ~30 promoted outputs, flat ids, verbose kebab labels, `change_datatype` on select outputs | Corpus convention is verbose descriptive output ids; the briefs' 9-output surface is fine, but keep ids descriptive rather than terse (`merged_reads` ok; consider `fastqc_pre_conversion_reports` style over `fastqc_reports_html`). |
| Element identifiers | snapshot-derived (`test.post_conversion_1_fastqc.html` …) | element identifiers are dataset names, relabeled via `rename:` at step level | The `rename:` idiom on step outputs (seen throughout the converted file) is the template's lever for meeting the snapshot's expected name shapes — route the `fastqc-element-identifiers` obligation through step-level renames or Apply Rules. |
| Test style | nf-test snapshot checksums | (not inspected — test style not retrieval driver) | n/a |

## Inline excerpt (bounded, labeled)

Excerpt from the converted exemplar — the BAM-split → extraction → failure-filter subgraph (steps 11, 13, 14, 16 of Nanopore-Pre-Processing). Full sibling file: `iwc-exemplar.gxwf.yml` (bounded to these steps).

```yaml
  - id: _unlabeled_step_11
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/bamtools_split_mapped/bamtools_split_mapped/2.5.3+galaxy0
    in:
      - id: input_bam
        source: _unlabeled_step_8/alignment_output
    out:
      - id: mapped
        rename: host_sequences_bam
      - id: unmapped
        rename: non_host_sequences_bam
  - id: _unlabeled_step_13
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/samtools_fastx/samtools_fastx/1.22+galaxy2
    in:
      - id: input
        source: _unlabeled_step_11/mapped
    out:
      - id: output
        change_datatype: fastq.gz
        rename: host_sequences_fastq
    state:
      output_fmt_cond:
        output_fmt_select: fastqsanger.gz
      outputs:
        - other
      exclusive_filter:
        - "256"
        - "2048"
  - id: _unlabeled_step_16
    tool_id: __FILTER_FAILED_DATASETS__
    in:
      - id: input
        source: _unlabeled_step_13
```

## Routing findings forward

- **Template/data-flow**: input topology has no corpus precedent (sample_sheet of alignments) — keep the brief's `sample_sheet` decision; don't reshape to the exemplar's `list`-of-FASTQs. Extraction outputs should carry `change_datatype` (fastq.gz) in the template.
- **Pattern issue**: none new — pick_value, FILTER_FAILED, collapse, Apply Rules are all already documented in the packaged pattern notes; this corpus pass confirms them in use.
- **Tool-step issue**: samtools_fastx here is a different wrapper family than the source's view/collatefastq aliasing — do not import the exemplar's tool choices; per-step discovery decides.
- **Test issue**: none surfaced.

## Non-blocking verdict

No High-confidence exemplar exists for this shape (alignment-input read-extraction with runtime pairedness branching). The Medium-confidence Nanopore-Pre-Processing anchors the extraction→QC→reduce subgraph idioms; the input tier, the C1 split, and the conditionals remain brief-owned decisions. Downstream template authoring proceeds on the briefs.

**Ledger**: no entries appended and none closed — the comparison confirms the briefs' dispositions rather than answering any open obligation; `single-paired-runtime-branch-representation` stays open (the exemplar's within-file split is explicitly *not* a substitute for the between-samples split).

**Feedback pass**: no feedback. The corpus scan (4 scripted passes over the full 133-workflow corpus) and the convert run behaved as the skill describes; the initial retrieval queries returned empty sets due to my own scan-script case-sensitivity, not because of a corpus or skill defect, and I corrected it within the phase.
