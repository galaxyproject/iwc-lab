# Galaxy interface brief — nf-core/bamtofastq 2.2.1

## Provenance

- Source: https://github.com/nf-core/bamtofastq
- Commit: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`
- Summary: `summary-nextflow.json` (schema-validated)
- Public workflow label: **nf-core/bamtofastq: BAM/CRAM to FASTQ**

## Inputs

| Public name | Source param | Galaxy shape | Required/default | Confidence and notes |
|---|---|---|---|---|
| `alignment_samples` | `input` | `collection`, `sample_sheet:record`; each row has a `mapped` BAM/CRAM dataset and optional `index` BAI/CRAI slot | Required | High. Row element identifier is `sample_id`; metadata column `file_type` is a required string restricted to `bam` or `cram`. Preserve the source `^\S+$`, BAM/CRAM, and BAI/CRAI filename guidance; file-exists checks are native dataset behavior. The index belongs to the same row and is not a read mate. |
| `chromosome` | `chr` | `string` | Optional; empty means all reads | High. Passed to the chromosome/region selection branch without changing its source syntax. |
| `skip_read_qc` | `no_read_QC` | `boolean` | `false` | High. Gates pre- and post-conversion FastQC outputs. |
| `skip_alignment_stats` | `no_stats` | `boolean` | `false` | High. Gates flagstat, idxstats, and stats. |
| `fast_collate` | `samtools_collate_fast` | `boolean` | `false` | High. Selects `samtools collate -f -r <reads_in_memory>`. |
| `reads_in_memory` | `reads_in_memory` | `int` | `100000` | High. Relevant when fast collate is enabled. |
| `reference_fasta` | `fasta` | optional `data`, `fasta` | Optional except reference-requiring CRAM operations | High. See open conditional-requiredness obligation. |
| `reference_fai` | `fasta_fai` | optional `data`, `fai` | Optional; matching FASTA required when supplied | High. Rebuild-on-absence remains unverified until tool selection. |
| `multiqc_config` | `multiqc_config` | optional `data`, `yaml` | Optional | Medium. Hidden in nf-core CLI but promoted because it changes report content. |
| `multiqc_title` | `multiqc_title` | optional `string` | Optional | High. |
| `multiqc_logo` | `multiqc_logo` | optional `data` | Optional; format left for Galaxy sniffing | Medium. Image subtype is not pinned in source. |
| `multiqc_methods_description` | `multiqc_methods_description` | optional `data`, `yaml` | Optional | Medium. Custom report text, not an execution-only option. |

### Sample-sheet contract

`alignment_samples` is **not** `list:paired`: BAM/CRAM and BAI/CRAI are heterogeneous inputs. `sample_id` supplies stable row identifiers, `file_type` supplies the alignment format, `mapped` supplies the primary dataset, and `index` is optional. The data-flow design must use these row slots together and preserve sample identifiers through every mapped step. A converted single/paired read result is not a BAM/BAI pair.

## Outputs and test checkpoints

| Public name | Shape | Datatype | Purpose |
|---|---|---|---|
| `converted_reads` | `paired_or_unpaired` collection keyed by sample | `fastqsanger.gz` | Primary merged output from mapped and unmapped read streams; supports both paired and single-end inputs. |
| `pre_conversion_fastqc_html` | list collection keyed by sample | `html` | Pre-conversion QC; absent/skipped when requested. |
| `pre_conversion_fastqc_zip` | list collection keyed by sample | `zip` | Machine-readable pre-conversion QC archive. |
| `post_conversion_fastqc_html` | list collection keyed by sample/read output | `html` | Post-conversion QC. |
| `post_conversion_fastqc_zip` | list collection keyed by sample/read output | `zip` | Machine-readable post-conversion QC archive. |
| `fastq_validation` | list collection keyed by sample | `txt` | `fastq_info` validation reports; stable nf-snapshot content provides strong assertions. |
| `alignment_flagstat` | list collection keyed by sample | `tabular` | Checkpoint with source nf-snapshot MD5 evidence. |
| `alignment_idxstats` | list collection keyed by sample | `tabular` | Checkpoint with source nf-snapshot MD5 evidence. |
| `alignment_stats` | list collection keyed by sample | `txt` | Detailed alignment statistics; source nf-snapshot MD5 evidence. |
| `multiqc_report` | single dataset | `html` | Final report. Content can vary; use type/size smoke checks only unless stable text is established. |
| `multiqc_data` | single directory/archive representation chosen during wrapper implementation | unspecified | Retain the emitted/published MultiQC data output rather than dropping it; exact Galaxy representation remains open. |
| `software_versions` | single dataset | `yaml` | Aggregated tool-version checkpoint corresponding to the pipeline-info versions YAML. |

Collection outputs that are entirely disabled by a skip flag may be empty or conditional according to the implemented gxformat2 mechanism; tests must not assert them in skipped-mode runs.

## Excluded and replaced parameters

The following are deliberately not Galaxy inputs. Each exclusion was checked for scientific effect:

| Parameters | Class | Assessment | Galaxy disposition |
|---|---|---|---|
| `outdir`, `publish_dir_mode` | Publishing | Safe substitution | History datasets and named workflow outputs replace filesystem publishing. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | Notification | Safe | Galaxy/server notification mechanisms own this plane. |
| `monochrome_logs`, `validate_params`, `trace_report_suffix` | Runtime UX/validation/tracing | Safe | Galaxy job logs and native input/tool validation replace these controls. Source timeline/report/trace/DAG files are not workflow outputs. |
| `custom_config_version`, `custom_config_base`, `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url`, `pipelines_testdata_base_path` | Institutional/site configuration | Safe | No institutional Nextflow config or test-data base path is needed by the converted scientific workflow. |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | Safe | Galaxy workflow documentation and provenance provide the equivalent user-facing metadata. |
| `igenomes_ignore`, `igenomes_base` | Reference lookup plumbing | Substituted | Explicit FASTA/FAI inputs replace automatic iGenomes resolution; no admin-managed data table is introduced. |
| `genome` | Reference nickname selector | Feature dropped, scientific capability substituted | The nickname lookup itself is not portable; users select actual reference datasets. Recorded as a dropped feature. |

## Open implementation obligations

1. Route single-end and paired-end samples correctly after `CHECKPAIREDEND`, without mixing marker-text datasets with alignments or losing sample identity.
2. Preserve `sample_id` on all mapped read/QC/stat outputs; sample-sheet metadata itself does not automatically propagate through Galaxy mapping.
3. Implement skip flags without fabricating QC/stat datasets and without blocking the retained conversion path.
4. Find concrete producers for the MultiQC data directory/archive and aggregated version manifest, or record a specific drop during implementation.
5. Resolve the previously recorded FAI rebuild and CRAM/FASTA requirements with actual wrapper behavior and tests.

## Testability decisions

Use `converted_reads`, `fastq_validation`, and the three alignment statistics collections as stable content checkpoints. The default nf-test snapshot supplies expected MD5 values for these file classes; checksums must come from that source snapshot, not from Galaxy's own outputs. FastQC HTML/ZIP and MultiQC are secondary smoke-check outputs. Keep all public names stable when authoring tests.
