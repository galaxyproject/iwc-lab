# Galaxy interface brief — nf-core/bamtofastq

Source: summary-nextflow.json (nf-core/bamtofastq @ aa0150e) + nextflow-galaxy-reference-data.md.
Consumers: nextflow-summary-to-galaxy-data-flow, nextflow-summary-to-galaxy-template, test-plan work.

## Workflow inputs

### I1. Alignment samples — `sample_sheet:record` (data)

- **source_param**: `input` (required, nf-schema schema `assets/schema_input.json`).
- **Galaxy shape**: `type: collection`, `collection_type: sample_sheet:record`, one row per sample.
  - Element identifier = `sample_id` (nf-schema `meta: [id]` → element_identifier; no separate column).
  - Slot `mapped` — the BAM/CRAM dataset (required).
  - Slot `index` — optional `.bai`/`.crai` dataset (absent → empty slot; the data-flow decides rebuild vs. requirement, see reference brief §3).
- **Dropped column: `file_type`.** The nf-schema `meta: [filetype]` enum (bam|cram) is derivable in Galaxy from the dataset's own datatype (`bam` vs `cram`), so the interface does not carry it as a column. Recorded as a decision; the runtime extension check the source performs (`error('The file extension does not fit the specified file_type...')`) becomes implicit in Galaxy datatype handling.
- **Datatypes**: `bam` or `cram` per slot. A single collection may hold mixed bam/cram elements; tools accepting both formats (Galaxy samtools wrappers with `bam,cram` inputs) map over it. **Risk flagged**: many Galaxy samtools wrappers declare only `bam`; if the chosen wrappers reject CRAM, the workflow needs either separate branches per datatype or cram-format-restricted wrappers. Open question for tool-step implementation.
- **Why not `sample_sheet:paired_or_unpaired`**: the source's single/paired split is *computed* (CHECKPAIREDEND), not declared; rows are not fastq pairs. `record` keeps the mapped/index pairing per row without pretending to be a read pair.
- **Confidence**: medium. sample_sheet:record is defined in Galaxy (PR #19305) but no IWC exemplar uses it for alignment inputs; tool-side consumption requires the data-flow to unzip slots (e.g. `__UNZIP_COLLECTION__` / Apply Rules) before samtools tools.

### I2. Reference FASTA — optional `data`

- **source_param**: `fasta` (dynamic, getGenomeAttribute).
- `type: data`, `format: fasta` (high confidence), `optional: true`.
- Description: "Reference genome FASTA — required when converting CRAM files".

### I3. Reference FASTA index — optional `data`

- **source_param**: `fasta_fai` (dynamic, getGenomeAttribute).
- `type: data`, `format: fai`, `optional: true`.
- Requiredness/rebuild disposition per reference brief (workflow-tier `samtools faidx` vs in-tool) — decided in data-flow phase.

### I4. Scalar parameters

| Galaxy input | source_param | type | default | optional | Confidence | Evidence |
|---|---|---|---|---|---|---|
| `chr` | `chr` | `string` | — | true | high | Branch guard `if (params.chr)` in BAMTOFASTQ; also read by SAMTOOLS_CHR ext.prefix/args2. |
| `no_read_qc` | `no_read_QC` | `boolean` | false | true | high | Gates FASTQC_PRE/POST_CONVERSION via `ext.when`. |
| `no_stats` | `no_stats` | `boolean` | false | true | high | Gates SAMTOOLS_FLAGSTAT/IDXSTATS/STATS via `ext.when`. |
| `samtools_collate_fast` | `samtools_collate_fast` | `boolean` | false | true | high | Changes COLLATEFASTQ `ext.args` (`-f -r N`). |
| `reads_in_memory` | `reads_in_memory` | `int` | 100000 | true | medium | Only meaningful with `samtools_collate_fast`; resource tuning that alters the command line. |
| `multiqc_title` | `multiqc_title` | `string` | — | true | high | Read by MULTIQC `ext.args` closure. |

### I5. Optional MultiQC config — `data`

- **source_param**: `multiqc_config`. `type: data`, `format: yaml` (low-medium confidence — Galaxy `yaml` extension exists; if unsure omit format), `optional: true`. MultiQC wrapper consumes a config file directly.

## Excluded launch params (per nextflow-params-to-galaxy-inputs)

| source_param | class | assessment | reason |
|---|---|---|---|
| `outdir` | publish | safe | Galaxy owns histories/outputs. |
| `publish_dir_mode` | publish | safe | idem. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | safe | Runtime reporting. |
| `monochrome_logs`, `validate_params`, `trace_report_suffix` | runtime UX | safe | Execution UX. |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | safe | Nextflow CLI behavior. |
| `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url`, `custom_config_version`, `custom_config_base` | institutional config | safe | Site config. |
| `pipelines_testdata_base_path` | testdata plumbing | safe | Test fixture location only. |
| `igenomes_base`, `igenomes_ignore`, `genome` | reference selector | safe | Dropped with the iGenomes key (ledger `igenomes-key-dropped`); user supplies FASTA/FAI directly. |
| `multiqc_logo` | report customization | safe | nf-core boilerplate branding; MultiQC wrapper's logo support is config-file-mediated. |
| `multiqc_methods_description` | report customization | safe | nf-core boilerplate methods text; not a scientific input. |

No param was classified problematic: none of the excluded params is referenced inside a process script or changes which scientific files are produced (the `ext.when` gates that do change output sets are kept as `no_read_qc`/`no_stats`).

## Workflow outputs

| Galaxy output | source | shape | format | notes |
|---|---|---|---|---|
| `paired_reads` | CAT_FASTQ (`*.merged.fastq.gz`, paired path) | `list:paired` (`_1`/`_2`) | `fastqsanger.gz` | The pipeline's product for paired-end samples. |
| `single_reads` | SAMTOOLS_COLLATEFASTQ (single-end path, `fastq_other` publish pattern `*{other.fq.gz}`) | `list` | `fastqsanger.gz` | Single-end samples' extracted reads. |
| `flagstat` | SAMTOOLS_FLAGSTAT (`*.flagstat`) | `list` | `tabular` | Stable-content checkpoint (md5 in nf-test snapshot). |
| `idxstats` | SAMTOOLS_IDXSTATS (`*.idxstats`) | `list` | `tabular` | Stable-content checkpoint. |
| `stats` | SAMTOOLS_STATS (`*.stats`) | `list` | `tabular` | Stable-content checkpoint. |
| `fastq_utils_info` | FASTQUTILS_INFO (`*.txt`) | `list` | `txt` | Post-conversion sanity marker. |
| `fastqc_pre_conversion_html` | FASTQC_PRE_CONVERSION (`*.html`) | `list` | `html` | Published but NOT aggregated into MultiQC by the source (commented-out line) — faithful translation keeps it as a separate output. |
| `fastqc_post_conversion_html` | FASTQC_POST_CONVERSION (`*.html`) | `list` | `html` | idem. |
| `multiqc_report` | MULTIQC (`*.html`) | `File` (single) | `html` | The source's only top-level emit. |

Checkpoint/testability notes (per galaxy-workflow-testability-design):
- The three samtools stat outputs and the FASTQ products have stable content on the test path — they are the assertions that catch a wrong conversion; MultiQC HTML is a smoke check.
- Element identifiers must stay `sample_id`-derived (`test`, `test2`) through every mapped step so collection member assertions stay addressable. WATCH: the source renames ids when `chr` is set (`file.baseName` becomes e.g. `test.chrX_chrY_X_Y`); tests for the chr branch must expect renamed elements.
- Conditional-output problem: for a BAM-only paired run, `single_reads` is empty and vice versa. gxformat2 optional/conditional outputs are weak — if the single-end path cannot be wired conditionally, expose both and record the loss, or pick one primary branch for v1. **Open question, decided in data-flow.**

## Provenance and confidence summary

- Inputs derived from `params[]` + `sample_sheets[]` + `workflow.channels[].from_param` per the translation order; process inputs used only to refine shapes.
- Overall confidence: high for scalars and the reference inputs; medium for the `sample_sheet:record` input and the mixed bam/cram handling; medium for the mixed single/paired output shape.
