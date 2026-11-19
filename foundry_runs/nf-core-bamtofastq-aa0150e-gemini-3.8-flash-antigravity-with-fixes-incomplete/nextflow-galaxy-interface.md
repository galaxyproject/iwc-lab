# Nextflow to Galaxy Interface Brief: nf-core/bamtofastq

## Source Pipeline Provenance
- **Source**: nf-core/bamtofastq @ aa0150e
- **Ecosystem**: nf-core DSL2
- **Description**: Convert BAM/CRAM files back to FASTQ format with comprehensive pre- and post-conversion quality control.

## Workflow Inputs

| Galaxy Input Name | Type | Collection Type | Format | Optional | Default | Description | Nextflow Source Param | Confidence |
|---|---|---|---|---|---|---|---|---|
| `input_bams` | collection | `list` | `bam,cram` | false | - | Input BAM or CRAM alignments per sample with sample IDs as element identifiers | `params.input` | High |
| `reference_fasta` | data | - | `fasta` | true | - | Reference genome FASTA (required for CRAM decoding if reference not embedded) | `params.fasta` | High |
| `chr` | string | - | - | true | `""` | Optional chromosome or region filter (e.g. `chr1` or `chr{1..22}`) | `params.chr` | High |
| `no_stats` | boolean | - | - | true | `false` | If true, skip pre-conversion BAM QC and stats computation (samtools stats, flagstat, idxstats, pre-FastQC) | `params.no_stats` | High |
| `no_read_qc` | boolean | - | - | true | `false` | If true, skip post-conversion read QC (post-FastQC and fastqutils info) | `params.no_read_QC` | High |

## Excluded Nextflow Parameters

| Param Name | Classification | Assessment | Rationale |
|---|---|---|---|
| `outdir`, `publish_dir_mode` | Publishing / storage | Safe | Managed natively by Galaxy histories and workflow output dataset handling |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | Notification | Safe | Runtime notification / email plumbing not applicable to Galaxy workflows |
| `monochrome_logs`, `validate_params`, `trace_report_suffix` | Logging / UX | Safe | Nextflow CLI execution and reporting options |
| `custom_config_version`, `custom_config_base`, `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url` | Institutional config | Safe | Host/institutional execution profile settings |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | Safe | Nextflow CLI options |
| `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | Report customization | Safe | MultiQC template defaults can be supplied internally or default tool configurations used |

## Workflow Outputs

| Galaxy Output Name | Type | Collection Type | Format | Tool Producer | Description |
|---|---|---|---|---|---|
| `extracted_fastqs` | collection | `list:paired` | `fastqsanger.gz` | `cat_fastq` (or `samtools_collatefastq`) | Extracted paired-end FASTQ read files |
| `multiqc_report` | data | - | `html` | `multiqc` | Aggregated MultiQC report |
| `pre_conversion_fastqc_html` | collection | `list` | `html` | `fastqc` (pre-conversion) | FastQC HTML reports on input BAM files |
| `post_conversion_fastqc_html` | collection | `list` | `html` | `fastqc` (post-conversion) | FastQC HTML reports on extracted FASTQ reads |
| `samtools_stats` | collection | `list` | `tabular` | `samtools_stats` | Samtools alignment statistics |
| `samtools_flagstat` | collection | `list` | `txt` | `samtools_flagstat` | Samtools flagstat alignment counts |
| `samtools_idxstats` | collection | `list` | `tabular` | `samtools_idxstats` | Samtools idxstats mapped/unmapped counts per chromosome |
| `fastqutils_info` | collection | `list` | `txt` | `fastqutils_info` | FastqUtils format and integrity check reports |

## Collection Shapes and Mapping Rationale

- In Nextflow, `params.input` is a CSV samplesheet specifying `sample_id`, `mapped` (bam/cram), `index` (optional bai/crai), and `file_type`.
- In Galaxy, samples are naturally represented as a dataset collection of type `list` with datatype `bam,cram`. Element identifiers carry `sample_id`.
- The extracted reads are paired-end reads matching nf-core's `reads/test_1.merged.fastq.gz` and `test_2.merged.fastq.gz`, represented in Galaxy as a nested `list:paired` collection or separate forward/reverse collections.
- Outputs for MultiQC are reduced across all samples to produce a single comprehensive HTML report.
