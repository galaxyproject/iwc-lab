# Galaxy interface brief — nf-core/bamtofastq @ aa0150e

> Superseded in phase 7: `reference_fasta` became required; `collate_fast`/`reads_in_memory` dropped; FastQC `*_zip` outputs became `*_raw` (text). See open-requirements.ledger.yml and galaxy-workflow.gxwf.yml.

Source: `summary-nextflow.json` (params[], sample_sheets[0], workflow.conditionals[], test_candidates[default]); `nextflow-galaxy-reference-data.md`.

## Inputs

| Label | Source param | gxformat2 type | collection_type / format | Optional | Default | Requiredness basis | Confidence |
|---|---|---|---|---|---|---|---|
| `alignments` | `input` (sample sheet `assets/schema_input.json`) | collection | `list`; format `bam` (CRAM: `cram` also accepted) | no | — | nf-schema `required: [input]` | medium |
| `reference_fasta` | `fasta` | data | `fasta` | yes | — | schema optional; needed only for CRAM / samtools stats `--reference` | high |
| `run_read_qc` (data-flow decision; was skip_read_qc) | `no_read_QC` (negated) | boolean | — | no | `true` | ext.when `!params.no_read_QC` gates FASTQC_PRE/POST | high |
| `run_stats` (data-flow decision; was skip_stats) | `no_stats` (negated) | boolean | — | no | `true` | ext.when `!params.no_stats` gates SAMTOOLS_FLAGSTAT/IDXSTATS/STATS | high |
| `collate_fast` | `samtools_collate_fast` | boolean | — | no | `false` | changes samtools collate args (`-f -r reads_in_memory`) | medium (depends on wrapper exposure) |
| `reads_in_memory` | `reads_in_memory` | int | — | no | `100000` | only read when `collate_fast` | medium |

### Sample-sheet → `list` decision

The row schema is `sample_id` (meta, pattern `^\S+$`), `mapped` (bam/cram path), `index` (optional bai/crai path), `file_type` (enum bam|cram).
- `sample_id` → collection **element identifier**.
- `mapped` → the element dataset.
- `index` → dropped as a column: Galaxy stores the BAM index as `bam` datatype metadata (`bam_index`) and builds it on upload; the pipeline's `SAMTOOLS_INDEX` compute-if-missing branch is therefore implicit in Galaxy. CRAM: Galaxy `cram` datatype also generates `.crai` metadata.
- `file_type` → dropped as a column: equal to the Galaxy datatype extension of the element.
With no remaining per-row metadata a plain `list` carries everything the source uses; a `sample_sheet` would add an unused metadata schema. Recorded as a decision in the ledger.

## Outputs (public, labelled) — final label list (reconciled with data-flow brief)

| Label | Source | Shape | Format | Notes |
|---|---|---|---|---|
| `fastq_paired` | `CAT_FASTQ.out.reads` (`reads/<id>_{1,2}.merged.fastq.gz`) | `list:paired` | `fastqsanger.gz` | paired-end samples |
| `fastq_single_end` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` | `list` | `fastqsanger.gz` | single-end samples; empty in default test |
| `fastqc_pre_html` / `fastqc_pre_zip` | `FASTQC_PRE_CONVERSION` (BAM only) | `list` | `html` / `zip` | `when: run_read_qc` |
| `fastqc_post_paired_html` / `fastqc_post_paired_zip` | `FASTQC_POST_CONVERSION` (paired) | `list:paired` | `html` / `zip` | `when: run_read_qc` |
| `fastqc_post_single_html` / `fastqc_post_single_zip` | `FASTQC_POST_CONVERSION` (single) | `list` | `html` / `zip` | `when: run_read_qc`; empty in default test |
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT` | `list` | `txt` | `when: run_stats` |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS` | `list` | `tabular` | `when: run_stats` |
| `samtools_stats` | `SAMTOOLS_STATS` | `list` | `txt` | `when: run_stats` |
| `fastq_info_paired` | `FASTQUTILS_INFO` (paired) | `list` | `txt` | — |
| `fastq_info_single` | `FASTQUTILS_INFO` (single) | `list` | `txt` | empty in default test |

Checkpoint outputs for testability: the three samtools reports and `fastq_info` carry stable content (md5 in `tests/default.nf.test.snap`), so they are promoted as public outputs. FASTQ outputs are gz; content checks (read count / first record) are stronger than gz md5.

## Excluded params

| source_param | class | effect | assessment | reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish | output location | safe | Galaxy owns history |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | runtime | safe | — |
| `monochrome_logs`, `validate_params`, `trace_report_suffix`, `help`, `help_full`, `show_hidden`, `version` | runtime UX / CLI | runtime | safe | — |
| `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path`, `igenomes_base`, `igenomes_ignore` | institutional config | runtime | safe | — |
| `genome` | reference selector | selects FASTA via iGenomes | problematic → handled | replaced by explicit `reference_fasta` (reference-data brief) |
| `fasta_fai` | reference index | skips SAMTOOLS_FAIDX | safe | wrapper-side indexing (reference-data brief) |
| `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | report config | MultiQC customisation | problematic → dropped | MultiQC step itself is dropped (see below) |
| `chr` | workflow-shape control | runs SAMTOOLS_CHR + SAMTOOLS_CHR_INDEX region filter and renames ids | problematic → dropped | see ledger `chr-region-filter-not-carried` |

## Dropped outputs / features

- **MultiQC report** (`multiqc/multiqc_report.html`): in the source, `ch_multiqc_files` only receives the nf-core software-versions YAML, the params summary and methods-description YAML; QC mixing is commented out (`workflows/bamtofastq.nf`, "TEMPORARILY DISABLED"). Galaxy has no versions-topic equivalent, so the report would carry no analysis content. Dropped; ledger entry.
- **`pipeline_info/nf_core_bamtofastq_software_mqc_versions.yml`**: Nextflow runtime provenance; Galaxy job metadata replaces it.
- **`--chr` region extraction**: dropped (ledger). Would need an optional-string-gated conditional subgraph plus id renaming.

## Open questions

- Per-sample single-end vs paired-end routing (CHECKPAIREDEND) — data-flow decides between per-element `when` gating with `pick_value` rejoin, or running both conversions on every sample.
- Whether the chosen samtools collate wrapper exposes `-f -r` (fast mode); if not, `collate_fast`/`reads_in_memory` are dropped at implementation.
- Mixed BAM + CRAM in one list: Galaxy collection inputs accept multiple formats; FastQC pre-conversion runs only on BAM rows in the source — in Galaxy it would need per-element filtering by datatype.
