# Galaxy Workflow Interface Brief — nf-core/bamtofastq

## Source Provenance

- **Pipeline:** `nf-core/bamtofastq` (`https://github.com/nf-core/bamtofastq.git`)
- **Commit:** `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`
- **Primary Nextflow workflow:** `BAMTOFASTQ` (`workflows/bamtofastq.nf`)
- **Reference-data brief:** `nextflow-galaxy-reference-data.md`

## Workflow Inputs

| Galaxy Input ID | Label | Type | Collection Type | Format | Optional | Default | Source Param / Evidence | Confidence |
|---|---|---|---|---|---|---|---|---|
| `alignments` | Input BAM/CRAM alignments | `collection` | `list` | `bam` / `cram` (omit `format` or allow `[bam, cram]`) | `false` | — | `params.input` (`assets/schema_input.json`: `sample_id`, `mapped`, optional `index`, `file_type`) | High |
| `fasta` | Reference FASTA (for CRAM) | `data` | — | `fasta` | `true` | `null` | `params.fasta` (`reference_assets[]`) | High |
| `chr` | Chromosome / region filter | `string` | — | — | `true` | `null` | `params.chr` (`workflow.conditionals[]`) | High |
| `no_read_qc` | Skip FastQC read QC | `boolean` | — | — | `true` | `false` | `params.no_read_QC` (`conf/modules.config` `ext.when`) | High |
| `no_stats` | Skip Samtools alignment stats | `boolean` | — | — | `true` | `false` | `params.no_stats` (`conf/modules.config` `ext.when`) | High |
| `samtools_collate_fast` | Use samtools collate fast mode | `boolean` | — | — | `true` | `false` | `params.samtools_collate_fast` (`conf/modules.config` `ext.args`) | High |
| `reads_in_memory` | Reads in memory (samtools collate fast) | `int` | — | — | `true` | `100000` | `params.reads_in_memory` (`conf/modules.config` `ext.args`) | High |
| `multiqc_title` | MultiQC report title | `string` | — | — | `true` | `null` | `params.multiqc_title` (`conf/modules.config` `ext.args`) | Medium |

### Sample-Sheet (`params.input`) Mapping Decision

- Source `assets/schema_input.json` declares four columns: `sample_id` (`meta`, identifier), `mapped` (`data`, `bam|cram`), `index` (`data`, optional `bai|crai`), and `file_type` (`meta`, enum `bam|cram`).
- **Chosen Galaxy shape:** `type: collection`, `collection_type: list` (`alignments`), rather than `sample_sheet`:
  1. `sample_id` maps directly to Galaxy collection `element_identifier` and propagates through map-over.
  2. `index` (`.bai`/`.crai`) is a Galaxy sidecar index attached to BAM/CRAM dataset metadata automatically upon upload/creation (per `nextflow-path-glob-to-galaxy-datatype.md`, avoid exposing index sidecars as separate top-level inputs).
  3. `file_type` (`bam` vs `cram`) duplicates the Galaxy dataset's native datatype extension (`bam` / `cram`). Keeping `alignments` as a `list` collection ensures every standard Tool Shed wrapper (`samtools`, `fastqc`) maps over it directly without needing `__SAMPLE_SHEET_TO_TABULAR__`.
  4. **Known loss:** A user cannot supply an external custom `.bai`/`.crai` separate from Galaxy's dataset metadata; if an unindexed BAM/CRAM arrives, Galaxy/tools handle indexing automatically or via `PREPARE_INDICES`.

## Workflow Outputs (Public & Test Checkpoints)

| Galaxy Output ID | Label | Type | Collection Type | Format | Source / Purpose | Test Checkpoint Role |
|---|---|---|---|---|---|---|
| `paired_reads` | Paired-end converted FASTQ reads | `collection` | `list:paired` | `fastqsanger.gz` | `CAT_FASTQ` (`ALIGNMENT_TO_FASTQ`) | Primary scientific output for paired-end inputs; supports per-sample `forward`/`reverse` MD5/content checks from `default.nf.test.snap`. |
| `single_end_reads` | Single-end converted FASTQ reads | `collection` | `list` | `fastqsanger.gz` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`fastq_other`) | Primary scientific output for single-end inputs (empty when all inputs are paired-end). |
| `fastqutils_info` | FASTQ integrity check reports | `collection` | `list` | `txt` | `FASTQUTILS_INFO` (`*.txt`) | Verifies converted FASTQ validity (`fastq_info` pass message); exact snapshot MD5s available in `default.nf.test.snap` (`test.txt`, `test2.txt`). |
| `samtools_flagstat` | Samtools flagstat reports | `collection` | `list` | `txt` | `SAMTOOLS_FLAGSTAT` (`*.flagstat`, gated by `!no_stats`) | Pre-conversion QC checkpoint; exact snapshot MD5s available in `default.nf.test.snap`. |
| `samtools_idxstats` | Samtools idxstats reports | `collection` | `list` | `tabular` | `SAMTOOLS_IDXSTATS` (`*.idxstats`, gated by `!no_stats`) | Pre-conversion QC checkpoint; exact snapshot MD5s available in `default.nf.test.snap`. |
| `samtools_stats` | Samtools stats reports | `collection` | `list` | `txt` | `SAMTOOLS_STATS` (`*.stats`, gated by `!no_stats`) | Pre-conversion QC checkpoint; exact snapshot MD5s available in `default.nf.test.snap`. |
| `fastqc_pre_conversion_html` | Pre-conversion FastQC HTML | `collection` | `list` | `html` | `FASTQC_PRE_CONVERSION` (`*.html`, BAM only, gated by `!no_read_qc`) | Pre-conversion FastQC report checkpoint. |
| `fastqc_pre_conversion_zip` | Pre-conversion FastQC ZIP | `collection` | `list` | `zip` | `FASTQC_PRE_CONVERSION` (`*.zip`, BAM only, gated by `!no_read_qc`) | Feeds MultiQC / archive check. |
| `fastqc_post_conversion_html` | Post-conversion FastQC HTML | `collection` | `list` or `list:paired` | `html` | `FASTQC_POST_CONVERSION` (`*.html`, gated by `!no_read_qc`) | Post-conversion FastQC report checkpoint. |
| `fastqc_post_conversion_zip` | Post-conversion FastQC ZIP | `collection` | `list` or `list:paired` | `zip` | `FASTQC_POST_CONVERSION` (`*.zip`, gated by `!no_read_qc`) | Feeds MultiQC / archive check. |
| `multiqc_report` | MultiQC report | `data` | — | `html` | `MULTIQC` (`*.html`) | Top-level workflow report output. |

## Excluded Nextflow Parameters (Control / Boilerplate Audit)

Warning: Galaxy owns history layout, file publishing, and notifications; the following Nextflow parameters are omitted from the Galaxy workflow interface.

| `source_param` | `class` | `effect` | `assessment` | Reason |
|---|---|---|---|---|
| `outdir` | Output location/publishing | Sets Nextflow `publishDir` root | `safe` | Galaxy stores outputs in the target history. |
| `publish_dir_mode` | Output location/publishing | Sets symlink/copy publish mode | `safe` | Galaxy manages dataset storage. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | Email/notification | Sends pipeline completion email | `safe` | Runtime notification only; no scientific impact. |
| `trace_report_suffix`, `monochrome_logs`, `validate_params` | Runtime UX / logs | Controls Nextflow trace filenames, colors, schema check | `safe` | Nextflow CLI execution UX only. |
| `custom_config_version`, `custom_config_base`, `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url`, `pipelines_testdata_base_path` | Institutional/profile config | Resolves external institutional/test configs | `safe` | Nextflow launch environment only. |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | Prints CLI help/version and exits | `safe` | Nextflow CLI plumbing only. |
| `genome`, `igenomes_base`, `igenomes_ignore` | Reference/iGenomes key | Resolves `fasta`/`fasta_fai` via `getGenomeAttribute` | `safe` | Replaced by explicit optional `fasta` input per v1 reference-data brief (`igenomes-key-not-carried`). |
| `fasta_fai` | Reference index sibling | Optional `.fai` index for `fasta` | `safe` | Deferred to in-tool FASTA indexing per v1 reference-data brief (`fasta-fai-in-tool-rebuild-unverified`). |
| `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | Report customization boilerplate | Overrides nf-core MultiQC YAML/logo/methods text | `safe` | Standard Galaxy MultiQC report does not require nf-core template boilerplate overrides. |

## Open Questions & Interface Notes

1. **MultiQC input wiring in `nf-core/bamtofastq` (`aa0150e`):** In `workflows/bamtofastq.nf`, `PRE_CONVERSION_QC` and `FASTQC_POST_CONVERSION` outputs are not actually mixed into `ch_multiqc_files` (a commented-out line `// NOTE: TEMPORARILY DISABLED BY ASP FOR DEBUGGING!!!!` left only software versions, workflow summary, and methods description in `ch_multiqc_files`). In Galaxy, `multiqc` expects QC tool outputs (FastQC zip, samtools flagstat/idxstats/stats) as inputs — Phase 4 (`data-flow`) and Phase 7 (`advance-galaxy-draft-step`) should check Galaxy's `multiqc` wrapper inputs and decide whether to feed the QC outputs into MultiQC (improving Galaxy report usefulness) or note the source quirk.
2. **Mixed single-end and paired-end samples:** Because `alignments` is a `list` of BAM/CRAM files and `CHECKPAIREDEND` classifies each element dynamically as single-end or paired-end, Phase 4 (`data-flow`) must handle splitting/filtering the `list` into single-end vs paired-end branches cleanly in Galaxy without failing when one branch is empty (e.g. all-paired test run).
3. **`no_read_QC` parameter casing:** `nextflow.config` spells the param `no_read_QC` (note uppercase `QC`), while `tests/no_qc.nf.test` erroneously passed `no_read_qc` (so its snapshot still ran FastQC). Galaxy input `no_read_qc` cleanly binds to the `!params.no_read_QC` gate.
