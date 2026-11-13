# Interface brief — nf-core/atacseq 2.1.2 → Galaxy

Produced by `nextflow-summary-to-galaxy-interface` from `summary-nextflow.json`,
`nextflow-galaxy-reference-data.md`, and `open-requirements.ledger.yml`.
Galaxy target: test.galaxyproject.org.

## Scope (user decision, 2026-11-12)

**Core library spine, BWA only.** Carried:
FastQC (raw + trimmed) → Trim Galore → BWA-MEM → per-library merge of runs → Picard MarkDuplicates
→ BAM filter (bamtools + samtools; include-regions BED) → normalised bigWig → MACS2 peaks + FRiP +
peak counts + HOMER annotatePeaks → consensus peaks (bedtools merge) + featureCounts + DESeq2 QC →
MultiQC.

Dropped (each a `kind: dropped` ledger entry): Bowtie2/Chromap/STAR aligners; merged-replicate
level (`PICARD_MERGESAMFILES_REPLICATE`, `MERGED_REPLICATE_*`); ataqv; IGV session; deepTools
plotProfile/plotHeatmap/plotFingerprint; Picard CollectMultipleMetrics; Preseq (already off by
default); control-sample pairing (`with_control`); `min_trimmed_reads` sample filter.

## Inputs

| Label | gxformat2 type | Shape / format | Optional | Default | Source param | Evidence | Confidence |
|---|---|---|---|---|---|---|---|
| `reads` | collection | `list:paired_or_unpaired`, elements `fastqsanger.gz` | no | — | `input` | `sample_sheets[0]` (ad-hoc via `SAMPLESHEET_CHECK` + `splitCsv`); `INPUT_CHECK.out.reads` = `tuple(meta, [r1(,r2)])` per run | medium |
| `genome_fasta` | data | `fasta` | no | — | `fasta` | reference brief | high |
| `genome_gtf` | data | `gtf` | no | — | `gtf` | reference brief | high |
| `blacklist_bed` | data | `bed` | **yes** | — | `blacklist` | reference brief; `ch_blacklist.ifEmpty([])` | high |
| `macs_gsize` | int | — | no | — | `macs_gsize` | reference brief (computed in NF via khmer when unset) | medium |
| `mito_name` | string | — | yes | — | `mito_name` | test: `MT`; used by include-regions BED | high |
| `keep_mito` | boolean | — | no | `false` | `keep_mito` | params default | high |
| `narrow_peak` | boolean | — | no | `false` | `narrow_peak` | switches MACS2 broad↔narrow, FRiP/consensus input format | high |
| `broad_cutoff` | float | — | no | `0.1` | `broad_cutoff` | MACS2 `--broad-cutoff` when broad | high |
| `macs_fdr` | float | — | yes | — | `macs_fdr` | MACS2 `-q` | high |
| `macs_pvalue` | float | — | yes | — | `macs_pvalue` | MACS2 `-p` | high |
| `min_reps_consensus` | int | — | no | `1` | `min_reps_consensus` | consensus peak filter | high |
| `fragment_size` | int | — | no | `200` | `fragment_size` | SE read extension in genomecov | high |
| `keep_dups` | boolean | — | no | `false` | `keep_dups` | bamtools filter drops duplicates unless set | high |
| `keep_multi_map` | boolean | — | no | `false` | `keep_multi_map` | bamtools/samtools filter | high |
| `bwa_min_score` | int | — | yes | — | `bwa_min_score` | BWA `-T` | medium |
| `deseq2_vst` | boolean | — | no | `true` | `deseq2_vst` | DESeq2 QC transform | high |

### `reads` element identifiers

nf-core rows are **runs**. `bin/check_samplesheet.py` names each run `<sample>_REP<replicate>_T<n>`
and the workflow groups runs into libraries by stripping `_T\d+$`
(`ch_genome_bam.map{…}.groupTuple`). The Galaxy collection carries the same identifiers, e.g. for
the `test` profile:

| element identifier | inner | from samplesheet row |
|---|---|---|
| `OSMOTIC_STRESS_T0_PE_REP1_T1` | paired | SRR1822153 |
| `OSMOTIC_STRESS_T0_PE_REP2_T1` | paired | SRR1822154 |
| `OSMOTIC_STRESS_T15_PE_REP1_T1` | paired | SRR1822157 |
| `OSMOTIC_STRESS_T15_PE_REP1_T2` | paired | SRR1822158 |
| `OSMOTIC_STRESS_T100_SE_REP1_T1` | unpaired | SRR1822153_1 |
| `OSMOTIC_STRESS_T100_SE_REP2_T1` | unpaired | SRR1822154_1 |
| `OSMOTIC_STRESS_T150_SE_REP1_T1` | unpaired | SRR1822157_1 |
| `OSMOTIC_STRESS_T150_SE_REP1_T2` | unpaired | SRR1822158_1 |

The workflow regroups by identifier (Apply Rules regex `^(.+_REP\d+)_T\d+$`) into libraries
(`list:list` of BAMs) before merging. `sample` and `replicate` metadata live in the identifier
rather than in `sample_sheet` columns: the `sample_sheet:paired_or_unpaired` variant would carry
them as typed columns, but metadata does not propagate through map-over and the target lacked
sample-sheet built-ins on a prior run. Recorded as a decision; the identifier convention is a
user-facing contract documented on the input.

`meta.single_end` is carried by the inner shape (paired vs unpaired) instead of a column. Libraries
never mix SE and PE runs in the test data; mixed libraries are not supported (ledger entry).

## Outputs

| Label | Type / shape | Format | Producer (NF) | Test checkpoint? |
|---|---|---|---|---|
| `multiqc_report` | data | `html` | `MULTIQC` | yes (existence) |
| `fastqc_raw_html` | list (per run) | `html` | `FASTQC` (raw) | — |
| `trimming_reports` | list (per run) | `txt` | `TRIMGALORE` logs | — |
| `library_bam` | list (per library) | `bam` | `MERGED_LIBRARY_FILTER_BAM.out.bam` | yes |
| `markduplicates_metrics` | list (per library) | `txt` | `PICARD_MARKDUPLICATES.out.metrics` | — |
| `library_flagstat` | list (per library) | `txt` | filtered BAM `SAMTOOLS_FLAGSTAT` | yes (mapped-read sanity) |
| `library_bigwig` | list (per library) | `bigwig` | `MERGED_LIBRARY_BAM_TO_BIGWIG.out.bigwig` | yes (existence) |
| `library_peaks` | list (per library) | `bed` (broadPeak / narrowPeak content) | `MACS2_CALLPEAK` | yes |
| `library_frip` | list (per library) | `tabular` | `FRIP_SCORE` | — |
| `library_peaks_annotated` | list (per library) | `tabular` | `HOMER_ANNOTATEPEAKS` | — |
| `consensus_peaks_bed` | data | `bed` | `MACS2_CONSENSUS` | yes |
| `consensus_peaks_annotated` | data | `tabular` | consensus `HOMER_ANNOTATEPEAKS` | — |
| `consensus_counts` | data | `tabular` | `SUBREAD_FEATURECOUNTS` | yes |
| `deseq2_qc_plots` | data | `pdf` | `DESEQ2_QC` | — |

Labels are snake_case and stable for tests. Per-library lists keep identifiers
`<sample>_REP<r>` (NF `meta.id` after `_T` stripping).

## Excluded params

| Param(s) | Class | Effect | Assessment | Reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode`, `save_reference`, `save_trimmed`, `save_align_intermeds`, `save_unaligned`, `save_macs_pileup` | publish | publishDir only (`save_unaligned` is a bowtie2 arg — aligner dropped) | safe | Galaxy owns outputs |
| `email`, `email_on_fail`, `plaintext_email`, `hook_url`, `max_multiqc_email_size` | notification | runtime | safe | — |
| `monochrome_logs`, `validate_params`, `validation*`, `help`, `version` | CLI/runtime | runtime | safe | — |
| `config_profile_*`, `custom_config_*`, `max_cpus`, `max_memory`, `max_time` | institutional/resources | runtime | safe | — |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference selector | resolves reference paths | safe | per reference brief; user supplies fasta/gtf |
| `gff`, `gene_bed`, `tss_bed`, `bwa_index`, `bowtie2_index`, `chromap_index`, `star_index`, `ataqv_mito_reference`, `read_length` | reference | rebuilt/derived | safe | per reference brief ledger entries |
| `aligner` | mode switch | selects aligner subworkflow | **problematic → fixed `bwa`** | other aligners dropped |
| `with_control` | mode switch | control pairing for MACS2/fingerprint | **problematic → fixed `false`** | dropped branch; test profile has no controls |
| `skip_trimming`, `skip_fastqc`, `skip_qc`, `skip_peak_annotation`, `skip_peak_qc`, `skip_consensus_peaks`, `skip_deseq2_qc`, `skip_multiqc` | skip flags | gate kept steps | **problematic → fixed design default (all run)** | no step-level `when:` in v1 |
| `skip_merge_replicates`, `skip_picard_metrics`, `skip_preseq`, `skip_plot_profile`, `skip_plot_fingerprint`, `skip_ataqv`, `skip_igv`, `fingerprint_bins` | skip/tuning for dropped stages | — | safe (stage dropped) | scope |
| `clip_r1`, `clip_r2`, `three_prime_clip_r1`, `three_prime_clip_r2`, `trim_nextseq` | trimming tuning | Trim Galore args; default unset = no-op | safe at default | fixed unset in v1 |
| `min_trimmed_reads` | sample filter | drops runs with < 10000 reads after trimming | **problematic → dropped** | ledger `kind: dropped` |
| `seq_center` | read-group tag | `CN:` in `@RG` | safe | read group set from element identifier |
| `bamtools_filter_pe_config`, `bamtools_filter_se_config` | bundled config | filter rules JSON | safe → inline tool params | data-flow encodes rules as bamtools filter conditions |
| `multiqc_config`, `multiqc_title`, `multiqc_logo`, `multiqc_methods_description` | report config | report cosmetics | safe | fixed defaults |

## Open questions

1. Does `devteam/bwa/bwa_mem` (and Trim Galore, FastQC) on the target map cleanly over
   `paired_or_unpaired` elements, or must reads split into `list:paired` + `list` branches and
   re-merge before library grouping? (ledger `paired-or-unpaired-mapping-unverified`)
2. `macs_gsize` test value (carried from reference brief).
