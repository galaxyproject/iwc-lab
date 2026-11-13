# Galaxy Workflow Interface Design Brief: nf-core/bamtofastq

- **Source**: `nf-core/bamtofastq` (`aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`)
- **Upstream artifacts**: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`

## 1. Design Posture & Input Collection Shape

In `nf-core/bamtofastq`, `params.input` is a CSV samplesheet (`assets/schema_input.json`) with four columns: `sample_id` (`string`, required, maps to `meta.id`), `mapped` (`file-path`, required, `*.bam` or `*.cram`), `index` (`file-path`, optional, `*.bai` or `*.crai`), and `file_type` (`enum ["bam", "cram"]`, required, maps to `meta.filetype`).

- **Chosen Galaxy input shape**: `collection` (`collection_type: list`, `format: [bam, cram]`) named `input_alignments`.
- **Rationale**:
  1. Galaxy dataset collections carry `sample_id` directly as each element's `element_identifier`.
  2. Galaxy datasets carry their format (`bam` vs `cram`) natively as dataset extension (`ext`), eliminating the redundant `file_type` metadata column.
  3. Galaxy natively creates and attaches `bam_index` / `cram_index` metadata on `bam`/`cram` datasets upon upload and tool output creation, removing the need for a separate optional `index` file port.
  4. Using a `sample_sheet:record` collection to bundle optional `index` datasets would disable Galaxy `allow_implicit_mapping` (`allow_implicit_mapping: false` on `record` collections), blocking implicit mapping over standard Tool Shed wrappers (`samtools`, `fastqc`). Using a plain `list` of `[bam, cram]` preserves implicit mapping across every step.

## 2. Galaxy Workflow Inputs

| Galaxy Input ID | Source Param | Type | Format / Collection Type | Optional | Default | Purpose / Wiring |
|---|---|---|---|---|---|---|
| `input_alignments` | `params.input` | `collection` (`data_collection_input`) | `collection_type: list`, `format: [bam, cram]` | `false` | N/A | Aligned BAM or CRAM inputs keyed by `sample_id`. |
| `reference_fasta` | `params.fasta` | `data` (`data_input`) | `fasta` | `true` | `null` | Reference FASTA genome; required when inputs include CRAM files without embedded reference sequences and optionally used by `samtools stats`. |
| `chr` | `params.chr` | `string` (`parameter_input`) | `text` | `true` | `null` | Optional chromosome/region filter (`samtools view <region>` via `SAMTOOLS_CHR`). When unset or empty, region subsetting is skipped. |
| `no_read_qc` | `params.no_read_QC` | `boolean` (`parameter_input`) | `boolean` | `false` | `false` | When `true`, skips `FASTQC_PRE_CONVERSION` and `FASTQC_POST_CONVERSION`. |
| `no_stats` | `params.no_stats` | `boolean` (`parameter_input`) | `boolean` | `false` | `false` | When `true`, skips pre-conversion `samtools flagstat`, `samtools idxstats`, and `samtools stats`. |
| `samtools_collate_fast` | `params.samtools_collate_fast` | `boolean` (`parameter_input`) | `boolean` | `false` | `false` | Enables fast mode (`-f`) in `samtools collate` for single-end and paired-end extraction. |
| `reads_in_memory` | `params.reads_in_memory` | `int` (`parameter_input`) | `integer` | `false` | `100000` | Number of reads held in memory (`samtools collate -r`) when `samtools_collate_fast` is enabled. |

## 3. Reference-Data Disposition (Carried from Phase 2)

- **`fasta` -> `reference_fasta`**: Carried as an optional `data` (`fasta`) workflow input.
- **`fasta_fai`**: Deferred to in-tool / Galaxy native FASTA handling unless Phase 7 wrapper discovery shows a selected wrapper requires an explicit `.fai` input (`reference-fasta-fai-rebuild-unverified` in `open-requirements.ledger.yml`).
- **`genome`**: Dropped per Galaxy v1 portability posture (`drop-igenomes-genome-key-for-explicit-fasta`).

## 4. Workflow Outputs & Testability Checkpoints

All outputs remain exposed as explicit top-level workflow outputs so downstream tools and automated workflow tests can verify every scientific artifact and conditional QC stage independently:

| Galaxy Output ID | Source Output | Type | Format / Collection Type | Condition | Testability Checkpoint Role |
|---|---|---|---|---|---|
| `paired_reads` | `ALIGNMENT_TO_FASTQ.out.reads` (`CAT_FASTQ`) | `collection` | `collection_type: list:paired`, `format: fastqsanger.gz` | Paired-end samples | Primary R1/R2 FASTQ deliverables (`reads/*_{1,2}.merged.fastq.gz`). Split from single-end reads because Galaxy enforces homogeneous `list:paired` vs `list` collection types. |
| `single_end_reads` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` | `collection` | `collection_type: list`, `format: fastqsanger.gz` | Single-end samples | Primary single-end FASTQ deliverables (`reads/*other.fq.gz`). |
| `fastq_info_reports` | `FASTQUTILS_INFO.out.info` | `collection` | `collection_type: list`, `format: txt` | Unconditional | Post-conversion FASTQ integrity reports (`fastqutils/*.txt`) asserted in `tests/default.nf.test.snap`. |
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT.out.flagstat` | `collection` | `collection_type: list`, `format: txt` | `!no_stats` | Pre-conversion alignment flagstat summaries (`samtools/*.flagstat`). |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS.out.idxstats` | `collection` | `collection_type: list`, `format: tabular` | `!no_stats` | Pre-conversion per-contig index stats (`samtools/*.idxstats`). |
| `samtools_stats` | `SAMTOOLS_STATS.out.stats` | `collection` | `collection_type: list`, `format: txt` | `!no_stats` | Pre-conversion comprehensive `samtools stats` reports (`samtools/*.stats`). |
| `fastqc_pre_html` | `FASTQC_PRE_CONVERSION.out.html` | `collection` | `collection_type: list`, `format: html` | `!no_read_qc` (BAM only) | Pre-conversion FastQC HTML reports for BAM inputs. |
| `fastqc_pre_data` | `FASTQC_PRE_CONVERSION.out.zip` | `collection` | `collection_type: list`, `format: zip` | `!no_read_qc` (BAM only) | Pre-conversion FastQC raw archive data for BAM inputs. |
| `fastqc_post_html` | `FASTQC_POST_CONVERSION.out.html` | `collection` | `collection_type: list` (or flattened), `format: html` | `!no_read_qc` | Post-conversion FastQC HTML reports across converted reads. |
| `fastqc_post_data` | `FASTQC_POST_CONVERSION.out.zip` | `collection` | `collection_type: list` (or flattened), `format: zip` | `!no_read_qc` | Post-conversion FastQC raw archive data across converted reads. |
| `multiqc_report` | `MULTIQC.out.report` | `data` | `format: html` | Optional / workflow summary | Aggregated MultiQC HTML report (`multiqc/multiqc_report.html`). Note: upstream `workflows/bamtofastq.nf` only wires collated versions and nf-core YAML metadata into `MULTIQC`; check Phase 4 for wiring Galaxy QC/stats into MultiQC. |

> **Note on output collection shapes across branches**: When both single-end and paired-end samples or conditional branches exist, Galaxy collection filtering (`CHECKPAIREDEND` split, `!no_stats`, `!no_read_qc`, BAM-vs-CRAM split) can leave one output collection empty in single-type runs. Output ports keep fixed types (`list:paired` vs `list`) so downstream type inference and tests remain well-typed regardless of which branch is populated.

## 5. Excluded Nextflow Parameters Assessment

Every parameter from `summary-nextflow.json` (`params[]`) outside Section 2 is excluded from the Galaxy workflow interface for one of the standard reasons:

| Source Param | Disposition | Reason |
|---|---|---|
| `genome` | Dropped | Replaced by explicit optional `reference_fasta`; avoids iGenomes `.loc` table coupling. |
| `fasta_fai` | Deferred | Handled by Galaxy FASTA metadata / in-tool indexing unless Phase 7 wrapper requires an explicit `.fai` input. |
| `outdir`, `publish_dir_mode` | Excluded | Galaxy manages history outputs natively instead of Nextflow publish directories. |
| `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | Excluded | Cosmetic / nf-core branding & institutional reporting parameters not needed for core Galaxy execution; default Galaxy MultiQC configuration suffices. |
| `igenomes_ignore`, `igenomes_base` | Excluded | Nextflow iGenomes loading flags irrelevant to explicit-FASTA Galaxy workflows. |
| `custom_config_version`, `custom_config_base`, `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url` | Excluded | nf-core institutional profile resolution plumbing. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size`, `monochrome_logs`, `version`, `validate_params`, `pipelines_testdata_base_path`, `trace_report_suffix`, `help`, `help_full`, `show_hidden` | Excluded | Nextflow CLI UX, notification, validation, and runtime tracing boilerplate. |

## 6. Carried Obligations & Open Questions

1. **BAM vs CRAM filtering in mixed `list` (`input_alignments`)**: Verify in Phase 4 (`data-flow`) and Phase 7 (`advance-galaxy-draft-step`) how Galaxy separates `.bam` elements from `.cram` elements before `FASTQC_PRE_CONVERSION` (which skips CRAMs in upstream `PRE_CONVERSION_QC`) and how wrappers handle mixed BAM/CRAM datasets cleanly.
2. **Paired vs single-end output parity**: `paired_reads` (`list:paired`) and `single_end_reads` (`list`) preserve exact collection typing; verify `FASTQC_POST_CONVERSION` and `FASTQUTILS_INFO` collection flattening/mapping across both branches in Phase 4.
3. **MultiQC upstream wiring discrepancy**: Upstream `workflows/bamtofastq.nf` commented out `ALIGNMENT_TO_FASTQ.out.zip` and did not mix `PRE_CONVERSION_QC` or `FASTQC_POST_CONVERSION` outputs into `ch_multiqc_files`, feeding only nf-core version/summary/methods YAML. Decide in Phase 4 whether Galaxy `MULTIQC` should ingest the real FastQC and `samtools` QC outputs when enabled (without nf-core boilerplate YAMLs).
