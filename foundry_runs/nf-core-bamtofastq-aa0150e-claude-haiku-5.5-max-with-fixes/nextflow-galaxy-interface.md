# Interface brief: nf-core/bamtofastq (aa0150e) as a Galaxy workflow

**Status:** draft for review.
**Produced by:** nextflow-summary-to-galaxy-interface (mold revision 6).
**Source summary:** `summary-nextflow.json` (phase 1, hand-corrected), sha256 `42bb9975d1c73d3b5ea635a4578190932b209a45b4cb43d6ff065489b36a0624`.
**Upstream brief:** `nextflow-galaxy-reference-data.md` (phase 2).
**Source pin:** nf-core/bamtofastq aa0150e (local clone).
**Ledger:** `open-requirements.ledger.yml` (phase 2 entries carried forward; this step's entries appended, section 10).

## 1. Summary

- **Inputs:** one sample sheet (`sample_sheet:record`, one BAM or CRAM per row, optional index), two optional reference inputs (phase 2), five scalar analysis inputs, and three report inputs plus a title.
- **Outputs:** ten public outputs. The converted reads and the MultiQC report are the main products. The samtools QC tables, the FastQC reports and the fastq_info check are exposed because the MultiQC report leaves them out. Gated outputs follow their gating inputs.
- **Excluded:** publishing, notification, logging, CLI and institutional-config parameters (section 5). The iGenomes key is not carried (phase 2).
- **Open:** record-slot syntax for the optional index, the mixed single/paired reads collection, and the CRAM-without-reference case (section 9).

## 2. Galaxy workflow inputs

| Public id | Source param | Galaxy type | Format | Collection | Optional / default | Label | Basis |
|---|---|---|---|---|---|---|---|
| `samplesheet` | `input` (nf-schema, `assets/schema_input.json`) | collection | per slot (section 3) | `sample_sheet:record` | required | Sample sheet: one alignment per row | Loaded by `samplesheetToList` in the utils subworkflow (line 109). |
| `fasta` | `fasta` | data | `fasta` | none | optional | Reference FASTA (needed for CRAM rows) | Phase 2 brief. |
| `fasta_fai` | `fasta_fai` | data | `fai` | none | optional | Reference FASTA index (built when absent) | Phase 2 brief. |
| `chr` | `chr` | string | none | none | optional, none | Restrict reads to a chromosome or region | Gates the chromosome extraction steps (`if (params.chr)`). |
| `no_read_QC` | `no_read_QC` | boolean | none | none | default false | Skip FastQC read QC | Gates the FastQC steps (`ext.when`, `conf/modules.config`). |
| `no_stats` | `no_stats` | boolean | none | none | default false | Skip samtools flagstat, idxstats and stats | Gates three QC steps (`ext.when`). |
| `samtools_collate_fast` | `samtools_collate_fast` | boolean | none | none | default false | Use fast samtools collate | Changes the collate arguments (`ext.args`). |
| `reads_in_memory` | `reads_in_memory` | int | none | none | default 100000 | Reads held in memory per collate (fast mode only) | Argument of the fast collate path. Kept, not dropped (section 6). |
| `multiqc_title` | `multiqc_title` | string | none | none | optional, none | MultiQC report title | Passed as `--title` (`conf/modules.config` line 32). |
| `multiqc_config` | `multiqc_config` | data | none | none | optional | Custom MultiQC configuration | Report customisation. The schema gives no format (ledger `multiqc-customisation-formats`). |
| `multiqc_logo` | `multiqc_logo` | data | none | none | optional | Custom MultiQC logo | As above. Its file name must also be set in the MultiQC config (schema description). |
| `multiqc_methods_description` | `multiqc_methods_description` | data | none | none | optional | Custom methods description (MultiQC YAML) | Read by the methods-description step. |

## 3. Sample sheet

- **Variant:** `sample_sheet:record`. Each element is one alignment file. The element identifier is the row's `sample_id`. The pipeline names its outputs from `meta.id`, so the identifier also becomes the output prefix.
- **Column definitions:** `file_type` (string, restrictions `bam` and `cram`, required). It is metadata (`meta` in the schema), and the source reads it for the datatype decision.
- **Record slots:**
  - `mapped`: data, required, format `bam` or `cram`. Pattern `^\S+\.(bam|cram)$`, existence checked.
  - `index`: data, optional, format `bai` or `crai`. Pattern `^\S+\.(bai|crai)$`, existence checked. When it is absent, the pipeline builds the index per sample (`SAMTOOLS_INDEX`, gated by the index flag).
- **Validation loss:** no Galaxy validator can check that `file_type` agrees with the `mapped` extension, because validators work per column. Recorded as a note on the input.
- **Duplicate `sample_id` values:** the schema constrains the pattern only, so it accepts duplicates. Galaxy element identifiers must be unique (ledger `samplesheet-duplicate-sample-ids`).
- **Why not `sample_sheet`:** each source row can carry a companion index, and a one-dataset-per-row variant would drop it. **Why not `sample_sheet:paired`:** a row is one alignment file, not a read pair. Decision `samplesheet-as-sample-sheet-record`.

## 4. Galaxy workflow outputs

| Public id | Source evidence | Galaxy type | Format | Gate | Label | Checkpoint |
|---|---|---|---|---|---|---|
| `reads` | `ch_reads_post_qc`: the paired `CAT_FASTQ` output mixed with the single-end `SAMTOOLS_COLLATEFASTQ_SINGLE_END` `fastq_other`. Published to `reads/` (default snapshot lines 85-88). | collection `list:paired_or_unpaired`, identified by `sample_id` | `fastqsanger.gz` (high) | always | Converted reads per sample | Yes: read content |
| `multiqc_report` | `MULTIQC` report, published to `multiqc/` (snapshot line 81). | data | `html` (high) | always | MultiQC report | No (smoke only) |
| `fastqc_pre_conversion_html` | `FASTQC_PRE_CONVERSION`, BAM rows only (`fastqc/`, snapshot lines 61-62). | collection `list` | `html` (high) | `no_read_QC` false | FastQC of input alignments | No (smoke only) |
| `fastqc_post_conversion_html` | `FASTQC_POST_CONVERSION` on converted reads (`fastqc/`, snapshot lines 57-60 and 63-66). Each paired sample gives two HTML files. | collection `list`, flattened per read end (ledger `fastqc-post-paired-html-flattening`) | `html` (high) | `no_read_QC` false | FastQC of converted reads | No (smoke only) |
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT` (`samtools/*.flagstat`, snapshot lines 90 and 93). | collection `list` | not set (generic text) | `no_stats` false | samtools flagstat per sample | Yes: read counts |
| `samtools_stats` | `SAMTOOLS_STATS` (`*.stats`, snapshot lines 92 and 95). | collection `list` | not set (generic text) | `no_stats` false | samtools stats per sample | Yes: summary statistics |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS` (`*.idxstats`, snapshot lines 91 and 94). | collection `list` | `tabular` (medium) | `no_stats` false | samtools idxstats per sample | Yes: per-reference counts |
| `fastqutils_info` | `FASTQUTILS_INFO` (`fastqutils/*.txt`, snapshot lines 70-71). | collection `list` | not set (generic text) | always | fastq_info check per sample | Yes: presence (the check ran) |
| `chr_alignments` | `SAMTOOLS_CHR` `bam` or `cram` output. No selector sets publishDir for it, so the global default publishes it to `samtools/`. Not run. | collection `list` | `bam` or `cram` (high) | `chr` set | Chromosome-restricted alignments | No |
| `chr_alignments_index` | `SAMTOOLS_CHR_INDEX` output (`bai` or `crai`). | collection `list` | `bai` or `crai` (high) | `chr` set | Chromosome-restricted alignment indexes | No |

- **Gate** means the source produces the output only under that condition. The template step decides how a skipped output appears (an empty collection or no output).
- **`reads`** is the scientific product. Its checkpoint role is read-content and count checks in the test plan. Expected values must come from the nf-test snapshots, not from a Galaxy run.
- **Why QC outputs are exposed separately:** the MultiQC report leaves out FastQC, fastq_utils and samtools QC (phase 1, `ch_multiqc_files`). Without these outputs, users would lose them.

## 5. Excluded parameters

| Source param(s) | Class | Effect in source | Assessment | Reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish control | Output location and copy mode | safe | Galaxy owns histories and outputs. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | Email reports | safe | Runtime reporting, not science. |
| `monochrome_logs`, `trace_report_suffix`, `validate_params` | logs and runtime | Log style, report naming, parameter validation switch | safe | Execution UX. |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | Nextflow CLI behaviour | safe | Not a Galaxy interface concern. |
| `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url`, `custom_config_version`, `custom_config_base`, `pipelines_testdata_base_path` | institutional config | Profile metadata, remote config location, test-data base path | safe | Site and run environment. |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference (phase 2) | iGenomes key and loader | safe | Not carried. See the phase 2 brief. |

Dropped outputs (not exposed; section 8).

## 6. Scalar analysis gates kept (decision `scalar-analysis-gates-kept`)

`chr`, `no_read_QC`, `no_stats`, `samtools_collate_fast` and `reads_in_memory` change which steps run, or which arguments a command gets, so each stays a scalar input. `reads_in_memory` matters only with `samtools_collate_fast`. Galaxy has no conditional inputs, so it is always shown and its label says so. Excluding it would drop a parameter the source exposes. The assessment is "problematic" under the parameter-inputs note's rule (it is referenced outside publishDir), so it is kept rather than silently excluded.

## 7. Checkpoints for tests

Promoted checkpoints: `reads`, `samtools_flagstat`, `samtools_stats`, `samtools_idxstats` and `fastqutils_info`. Each has stable, deterministic content, or a presence check that shows the check ran. `multiqc_report` and the FastQC HTML are smoke checks only, because their content varies between runs. Assertion values come from the nf-test snapshots in phase 9.

## 8. Dropped outputs

| Item | Units | Reason |
|---|---|---|
| `pipeline_info` software versions YAML | the versions file | The same versions appear in the MultiQC report (`multiqc_software_versions.txt`, snapshot line 79). |
| `multiqc_data/` and plot directories | MultiQC side outputs | The HTML report carries their content (snapshot lines 74-80). |
| FastQC zip archives | `fastqc/*.zip` | The HTML reports are exposed. The archives are per-tool outputs that Galaxy keeps in the history (not verified). |

## 9. Open questions

1. **Record-slot syntax and optional slots.** The sample-sheet research note names `sample_sheet:record` but gives no slot syntax or optionality rule (feedback `galaxy-sample-sheet-record-slots-undocumented`). Verify with a Galaxy fixture before the template step (ledger `samplesheet-record-optional-index-slot`).
2. **Mixed reads collection.** `reads` mixes paired and single samples. `list:paired_or_unpaired` must work with the downstream tools (ledger `reads-mixed-collection-type`).
3. **CRAM without a reference.** The interface makes `fasta` optional, with a note on CRAM rows. Whether a CRAM run without it fails cleanly is unverified (ledger `cram-without-reference-unverified`).
4. **Paired FastQC HTML identifiers.** Two HTML files per paired sample need identifiers (ledger `fastqc-post-paired-html-flattening`).
5. **Report input formats.** MultiQC config, logo and methods files have no format in the schema or the registry note (ledger `multiqc-customisation-formats`).
6. **Chromosome outputs.** That `SAMTOOLS_CHR` outputs are published is inferred from configuration, not from a run.

## 10. Ledger and feedback record

- **Open-requirements ledger:** the five phase 2 entries are carried through unchanged, except `fasta-required-for-cram-not-expressible`, which is resolved here: the interface expresses it as an optional `fasta` with a CRAM note. Added: 6 gaps and 3 dropped entries (`software-versions-yaml-not-exposed`, `multiqc-data-directory-not-exposed`, `fastqc-zip-archives-not-exposed`). Decisions added: 5. Discoveries added: 4.
- **Feedback ledger:** 2 entries, both local: `default-publishdir-not-captured` (summarize-nextflow) and `galaxy-sample-sheet-record-slots-undocumented` (research note).

## 11. Provenance

- **Summary:** `summary-nextflow.json` (phase 1), sha256 `42bb9975d1c73d3b5ea635a4578190932b209a45b4cb43d6ff065489b36a0624`.
- **Source (aa0150e):** `workflows/bamtofastq.nf`; `subworkflows/local/alignment_to_fastq/main.nf`, `pre_conversion_qc/main.nf` and `prepare_indices/main.nf`; `subworkflows/local/utils_nfcore_bamtofastq_pipeline/main.nf`; `conf/modules.config` (global publishDir at lines 13-18; MULTIQC at line 31); `tests/default.nf.test.snap`.
- **Research notes:** galaxy-sample-sheet-collections, galaxy-workflow-testability-design, nextflow-to-galaxy-channel-shape-mapping, nextflow-path-glob-to-galaxy-datatype, nextflow-params-to-galaxy-inputs.
