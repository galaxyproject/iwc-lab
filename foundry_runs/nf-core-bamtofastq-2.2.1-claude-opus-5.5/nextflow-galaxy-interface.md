# Galaxy interface — nf-core/bamtofastq 2.2.1

Source: `summary-nextflow.json` (nf-core/bamtofastq @ 8a29586), `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml` (3 open entries inherited).

## Workflow inputs

| Label | Type | collection_type / format | Optional | Default | Source | Confidence |
|---|---|---|---|---|---|---|
| `alignments` | collection | `list`, element format `bam` (CRAM accepted by tools that read `cram`; see notes) | no | — | `params.input` → `samplesheetToList(assets/schema_input.json)`; columns `sample_id`, `mapped`, `index`, `file_type` | medium |
| `reference_fasta` | data | `fasta` | yes | — | `params.fasta` (reference-data brief) | high |
| `chr` | string | — | yes | — | `params.chr` (space/`-`/`:` separated region list; gates `SAMTOOLS_CHR`) | medium |
| `skip_read_qc` | boolean | — | no | `false` | `params.no_read_QC` (ext.when on FASTQC_PRE/POST_CONVERSION) | high |
| `skip_stats` | boolean | — | no | `false` | `params.no_stats` (ext.when on SAMTOOLS_FLAGSTAT/IDXSTATS/STATS) | high |
| `collate_fast` | boolean | — | no | `false` | `params.samtools_collate_fast` (adds `-f -r <reads_in_memory>` to collate) | medium |
| `reads_in_memory` | int | — | no | `100000` | `params.reads_in_memory` | medium |

### Sample-sheet mapping decision: `list`, not `sample_sheet`

The nf-schema row schema has one data column plus metadata that Galaxy already carries natively:

| nf-schema column | Galaxy carrier |
|---|---|
| `sample_id` (meta, `^\S+$`) | element identifier |
| `mapped` (data, `*.bam|*.cram`) | element dataset |
| `index` (data, optional `*.bai|*.crai`) | dataset metadata — Galaxy `bam` sets `bam_index` on upload; `SAMTOOLS_INDEX` compute-if-missing is subsumed |
| `file_type` (meta, enum bam/cram) | element datatype (`bam` vs `cram`) |

No column survives as information a tool needs, so a plain `list` keeps the interface uploadable and test-friendly; a `sample_sheet` would add column definitions no step reads (and `columns` do not propagate to mapped outputs anyway). Recorded as decision `alignments-as-list-not-sample-sheet`.

## Workflow outputs

| Label | Producer (NF) | Shape / format | Test addressable | Notes |
|---|---|---|---|---|
| `paired_reads` | `CAT_FASTQ` (reads/`<id>_{1,2}.merged.fastq.gz`) | `list:paired`, `fastqsanger.gz` | yes — forward/reverse per sample | Primary product; snapshot has md5s for these. |
| `single_end_reads` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.fastq_other` (reads/`*other.fq.gz`) | `list`, `fastqsanger.gz` | yes | Empty for the default test (both samples paired). |
| `fastqc_pre_html`, `fastqc_pre_zip` | `FASTQC_PRE_CONVERSION` | `list` html / zip | count only | Skipped when `skip_read_qc`. BAM elements only in NF. |
| `fastqc_post_html`, `fastqc_post_zip` | `FASTQC_POST_CONVERSION` | per read file | count only | Skipped when `skip_read_qc`. |
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT` | `list` txt | yes (content) | Snapshot md5 available. |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS` | `list` tabular | yes (content) | Snapshot md5 available. |
| `samtools_stats` | `SAMTOOLS_STATS` | `list` txt | yes (content) | Snapshot md5 available but contains a header with command line/version → line assertions, not checksum. |
| `fastq_info` | `FASTQUTILS_INFO` (`fastqutils/<id>.txt`) | `list` txt | yes | Snapshot md5 available. Galaxy tool availability unverified. |

Checkpoint outputs: `samtools_flagstat` and `samtools_idxstats` are deterministic text products of the input BAMs and give a strong content check independent of FASTQ compression bytes.

## Excluded params

| source_param | class | effect | assessment | reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish | publishDir only | safe | Galaxy owns outputs. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | runtime | safe | — |
| `monochrome_logs`, `validate_params`, `trace_report_suffix`, `help`, `help_full`, `show_hidden`, `version` | runtime/CLI | runtime | safe | — |
| `config_profile_*`, `custom_config_*`, `pipelines_testdata_base_path` | institutional | runtime | safe | — |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference selector | selects FASTA via iGenomes | problematic → recorded drop | ledger `igenomes-genome-key-dropped`; user supplies `reference_fasta`. |
| `fasta_fai` | reference index | rebuilt if absent | safe | in-tool rebuild (ledger `fasta-fai-rebuild-in-wrapper-unverified`). |
| `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | report config | MultiQC only | see data-flow | MultiQC in 2.2.1 only aggregates versions/params/methods YAML; data-flow brief decides whether MultiQC is carried. |

## Open questions

- CRAM elements: FastQC pre-conversion is BAM-only in NF; Galaxy needs a filter or a BAM-only branch if mixed lists are allowed. Default test is BAM-only.
- Per-sample single/paired routing (CHECKPAIREDEND) is runtime, per element; the interface exposes both `paired_reads` and `single_end_reads`, one of which may be empty per sample. Data-flow must define how elements land in only one of them.
- `chr` changes element identifiers in NF (`<id>.<chr_joined>`); Galaxy element identifiers stay as sample ids.
