# Nextflow → Galaxy interface brief: nf-core/bamtofastq

- **Pipeline:** nf-core/bamtofastq at `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78` (`source/`)
- **Inputs:** `summary-nextflow.json` (phase-1 summary, reconciled); `nextflow-galaxy-reference-data.md` (phase-2 brief, binding for `fasta` and `fasta_fai`); `open-requirements.ledger.yml` (carried ledger)
- **Mold:** nextflow-summary-to-galaxy-interface (commit and revision from its `_provenance.json`, recorded in the feedback ledger)
- **Scope:** the Galaxy workflow surface only: inputs, outputs, labels, collection shapes, checkpoints. Not a gxformat2 skeleton.

## Summary

The workflow takes one sample sheet of BAM or CRAM rows and produces, per sample, paired or single FASTQ reads. It also produces the MultiQC report and three samtools reports on the input files.

| Kind | Galaxy name | Shape | Source |
|---|---|---|---|
| Input | `input` (label `samples`) | `sample_sheet` (one `bam`/`cram` dataset per row) | `--input` samplesheet, nf-schema `assets/schema_input.json` |
| Input | `fasta`, `fasta_fai` | optional `data` (`fasta`, `fai`) | reference brief |
| Input | `chr`, `no_stats`, `samtools_collate_fast`, `reads_in_memory` | scalars | control flags that change steps or commands |
| Input | `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | scalar and optional `data` | report customisation |
| Output | `paired_reads` | `list:paired` (`fastqsanger.gz`) | `CAT_FASTQ`, published to `reads/` |
| Output | `single_reads` | `list` (`fastqsanger.gz`) | `SAMTOOLS_COLLATEFASTQ_SINGLE_END`, published to `reads/` |
| Output | `multiqc_report` | single `html` | `MULTIQC`, published to `multiqc/` |
| Output (checkpoint) | `samtools_flagstat`, `samtools_idxstats`, `samtools_stats` | `list` (format omitted) | `SAMTOOLS_FLAGSTAT` / `_IDXSTATS` / `_STATS` on the input files, published to `samtools/`, gated by `no_stats` |

Not exposed (recorded as dropped in the ledger): the FastQC reports and `fastq_utils info` outputs, the `no_read_QC` gate, the pipeline software-versions YAML under `outdir`, and the per-row `index` column.

## Source evidence used

- `summary-nextflow.json`: `params[]` (35), `sample_sheets[0]` (4 columns), `workflow.channels[]` (17 after reconciliation), `workflow.conditionals[]` (3), subworkflow `invocations`, `processes[]` `script_summary`.
- `source/assets/schema_input.json`: row schema. `sample_id` (meta, required, `^\S+$`); `mapped` (data, required, `.bam` or `.cram`); `index` (data, optional, `.bai` or `.crai`); `file_type` (meta, required, enum `bam`/`cram`).
- `source/workflows/bamtofastq.nf`: `params.chr` branch (`SAMTOOLS_CHR` and rebinding of `meta.id` to `file.baseName`); `ch_reads_post_qc` (single and paired mixed for FastQC and fastq_utils only); `MULTIQC` inputs (versions, workflow summary, methods description; no QC reports); the `ALIGNMENT_TO_FASTQ.out.zip` line is commented out.
- `source/conf/modules.config`: `publishDir` for `CAT_FASTQ` (`*.fastq.gz`), `SAMTOOLS_COLLATEFASTQ_SINGLE_END`, `MULTIQC`, `SAMTOOLS_FLAGSTAT` (`*.flagstat`), `SAMTOOLS_IDXSTATS`, `SAMTOOLS_STATS`. **No `publishDir`** for `FASTQC_PRE_CONVERSION`, `FASTQC_POST_CONVERSION` or `FASTQUTILS_INFO`. `CHECKPAIREDEND` is `enabled: false`.
- `source/nextflow_schema.json` (`params`), `source/tests/*.nf.test` (all 9 cases use `-profile test`, one sample sheet each).
- `galaxy-sample-sheet-collections.md` (variants, `column_definitions`, mapping rules), `nextflow-params-to-galaxy-inputs.md` (control-param classes, requiredness), `nextflow-path-glob-to-galaxy-datatype.md` (formats), `nextflow-to-galaxy-channel-shape-mapping.md` (shapes), `galaxy-workflow-testability-design.md` (labels and checkpoints).

## Workflow inputs

| Label | Galaxy input | Source param | gxformat2 type | Format | Optional / default | Requiredness basis | Confidence |
|---|---|---|---|---|---|---|---|
| samples | `input` | `input` | `collection`, `collection_type: sample_sheet` | `bam` or `cram` (see element format) | required | nf-schema root `required` and `samplesheetToList` materialization | High |
| reference_fasta | `fasta` | `fasta` | `data` | `fasta` | optional; no default | reference brief: schema `required: false`; not enforced; CRAM rows need it | Medium |
| reference_fasta_index | `fasta_fai` | `fasta_fai` | `data` | `fai` | optional; no default | reference brief: compute-if-missing via `SAMTOOLS_FAIDX` | Medium |
| chromosome_filter | `chr` | `chr` | `string` | none | optional; no default | scalar; branch `if (params.chr)` | High |
| skip_samtools_reports | `no_stats` | `no_stats` | `boolean` | none | optional; default `false` | `ext.when` gate on the three samtools reports | High |
| collate_fast | `samtools_collate_fast` | `samtools_collate_fast` | `boolean` | none | optional; default `false` | changes `ext.args` on collate steps | High |
| reads_in_memory | `reads_in_memory` | `reads_in_memory` | `int` | none | optional; default `100000` | used only with `samtools_collate_fast` | High |
| multiqc_title | `multiqc_title` | `multiqc_title` | `string` | none | optional | changes the MultiQC `--title` argument | High |
| multiqc_config | `multiqc_config` | `multiqc_config` | `data` | none (see note) | optional | customisation consumed by `MULTIQC` | Medium |
| multiqc_logo | `multiqc_logo` | `multiqc_logo` | `data` | none (see note) | optional | customisation consumed by `MULTIQC` | Medium |
| multiqc_methods_description | `multiqc_methods_description` | `multiqc_methods_description` | `data` | none (see note) | optional | customisation consumed by `BAMTOFASTQ` (methods text) | Medium |

Notes:

- Format for `multiqc_*` is omitted. The datatype note has no registry-backed entry for YAML config, logo or methods files, so per its rule the format is left to Galaxy.
- `chr` changes downstream identifiers. See the element-identifier section.

### The `input` sample sheet

- **Variant:** `sample_sheet`. The row has one data element, `mapped`. This is the only variant whose elements the tools can map over; `sample_sheet:record` does not allow implicit mapping (galaxy-sample-sheet-collections, Mapping rules). The source's second data column (`index`) is therefore not carried; see the dropped entries.
- **Element format:** `bam` or `cram`, decided per row by `file_type`. Written as the list `[bam, cram]`. This is a medium-confidence choice: the datatype note has no mixed-format rule, so the gxformat2 multi-format spelling needs checking against the schema at template time.
- **`column_definitions`:**

  ```yaml
  column_definitions:
    - {name: sample_id, type: string, optional: false, validators: [{type: regex, expression: "^\\S+$"}]}
    - {name: file_type, type: string, optional: false, restrictions: [bam, cram]}
  ```

  `sample_id` is `meta.id` in the source, which names output files and identifies samples. `file_type` is `meta.filetype`, which decides whether `CHECKPAIREDEND` and the views get `--reference`. Both are kept.

- **Element identifiers:** expected to come from `sample_id`. Galaxy's element-identifier rule is not verified in this run (open question).

## Workflow outputs

| Label | Galaxy output | Collection shape | Format | Source producer | Publish evidence | Confidence |
|---|---|---|---|---|---|---|
| paired_reads | `paired_reads` | `list:paired` | `fastqsanger.gz` | `CAT_FASTQ.out.reads` → `tuple(meta, [R1, R2])` (repeated) | `conf/modules.config` `CAT_FASTQ` `*.fastq.gz` to `reads/` | High (shape), High (format from `.fastq.gz`) |
| single_reads | `single_reads` | `list` | `fastqsanger.gz` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` → `tuple(meta, path)` | `reads/` | High (shape), Medium (format; collate pattern not checked) |
| multiqc_report | `multiqc_report` | single `data` | `html` | `MULTIQC.out.report` (`toList`) | `multiqc/` | High |
| samtools_flagstat | `samtools_flagstat` | `list` | omitted | `SAMTOOLS_FLAGSTAT.out.flagstat` (input files, pre-conversion) | `samtools/*.flagstat` | High (shape), Low (format; generic text) |
| samtools_idxstats | `samtools_idxstats` | `list` | omitted | `SAMTOOLS_IDXSTATS.out.idxstats` (input files) | `samtools/*.idxstats` | High (shape), Low (format) |
| samtools_stats | `samtools_stats` | `list` | omitted | `SAMTOOLS_STATS.out.stats` (input files) | `samtools/*.stats` | High (shape), Low (format) |

Why two read outputs instead of one mixed collection: the source produces single-end and paired reads from two different producers (`SAMTOOLS_COLLATEFASTQ_SINGLE_END` and `CAT_FASTQ`), selected per sample by `CHECKPAIREDEND`. The source only mixes them for QC and fastq_utils, which the interface drops. Two collections keep each element's shape honest (`list` versus `list:paired`) and avoid `paired_or_unpaired`, which the channel-shape note marks as medium confidence. A sample appears in one of the two collections only.

The `samtools_*` reports describe the input BAM/CRAM files (pre-conversion), not the reads. They are gated by `no_stats`; when it is true the outputs are empty, which the interface states in the label.

## Checkpoint outputs for testing

- **`samtools_flagstat`** is the checkpoint the workflow test can address. Its content is stable and tied to the analysis: counts of records in each input file. An assertion on those counts can catch a wrong input or a broken reader, which an output-size check cannot. Per-sample `list` identifiers follow `sample_id`.
- **`paired_reads` and `single_reads`** give read-count and identifier checks. They are the scientific result.
- **`samtools_idxstats` and `samtools_stats`** are kept because they are published user-facing reports. They are secondary checkpoints.
- **`multiqc_report`** is a smoke check only. It is kept for users.

## Excluded Nextflow params (warning for the user)

The Galaxy target is not a faithful CLI replica. The list below is the consolidated notice. Each entry was checked against the summary's references (`workflow`, `processes[].resolved_args`, `publish_dir_matches`) before exclusion.

| Param | Class | Effect in source | Assessment | Reason |
|---|---|---|---|---|
| `outdir` | publish location | `publishDir` roots, and `collectFile(storeDir: "${outdir}/pipeline_info")` in channel construction | **problematic** | Referenced in channel construction. Resolved as a recorded loss: Galaxy history replaces the location; the versions YAML is dropped (ledger). |
| `no_read_QC` | process gate | `ext.when` on `FASTQC_PRE_CONVERSION` and `FASTQC_POST_CONVERSION` | **problematic** | Process guard. Resolved as a recorded loss: the gated FastQC outputs are not published and not consumed in the source, so the gate has no user-visible effect in the interface. Ledger entry records the drop. |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference selector | key expansion of `fasta` and `fasta_fai` | **problematic** | Resolved by the phase-2 dropped entry `genome-key-no-galaxy-data-table`. |
| `publish_dir_mode` | publish | `publishDir` mode only | safe | — |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | completion subworkflow only | safe | Galaxy owns notifications. |
| `monochrome_logs` | logs | logging only | safe | — |
| `validate_params` | runtime validation | nf-schema check at launch | safe | Galaxy's typed inputs replace it. |
| `pipelines_testdata_base_path` | test data | test profile location | safe | — |
| `trace_report_suffix` | reports | trace file naming | safe | — |
| `help`, `help_full`, `show_hidden`, `version` | CLI | help and version output | safe | — |
| `custom_config_version`, `custom_config_base`, `config_profile_name`, `config_profile_description`, `config_profile_contact`, `config_profile_url` | institutional config | `includeConfig` from remote | safe | Site configuration, not scientific input. |

Excluded outputs (not exposed; each is a dropped entry in the ledger):

- `FASTQC_PRE_CONVERSION`, `FASTQC_POST_CONVERSION` and `FASTQUTILS_INFO` outputs: computed but not published (no `publishDir`), not in MultiQC inputs, not emitted by the workflow.
- The collated software-versions YAML written to `${outdir}/pipeline_info`.
- The per-row `index` column of the sample sheet (see the input section).

## Labels

Labels are the names users and tests see. They are fixed here so that later Molds and the test plan can refer to them:

- Inputs: `samples`, `reference_fasta`, `reference_fasta_index`, `chromosome_filter`, `skip_samtools_reports`, `collate_fast`, `reads_in_memory`, `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`.
- Outputs: `paired_reads`, `single_reads`, `multiqc_report`, `samtools_flagstat`, `samtools_idxstats`, `samtools_stats`.

## Element identifiers

- Default: element identifiers are `sample_id` (`meta.id`) for every output collection.
- With `chr` set: `SAMTOOLS_CHR` runs, and `ch_input_new` rebinds `meta.id` to `file.baseName` of the chromosome-extracted BAM. Output identifiers then follow the chromosome-extracted file names, not the sample ids. This is a change to the output identifiers under a control flag. It is recorded as a non-blocking gap in the ledger because test assertions on identifiers depend on it.

## Interface decisions

1. `input` is a `sample_sheet`, not a flat CSV or a `list:paired`, because the row metadata (`sample_id`, `file_type`) is structural (the file type drives `--reference`) and the source reads it as typed columns.
2. Two read outputs, split by layout, following the two producers in the source (see the outputs section).
3. Control flags kept as scalar inputs: `chr`, `no_stats`, `samtools_collate_fast`, `reads_in_memory`. Each changes a step or an argument.
4. `no_read_QC` is not kept, because the gated outputs are not part of the interface (dropped entry).
5. Three samtools reports exposed as outputs, gated by `no_stats`, one of them the checkpoint.
6. MultiQC customisation inputs kept, because each one changes a user-visible report.
7. `fasta` and `fasta_fai` are exactly as the reference brief pins them.

## Open questions and unverified assumptions

1. **Element identifiers for `sample_sheet`.** Whether Galaxy takes element identifiers from `sample_id` or the first column is not verified in this run.
2. **Mixed BAM/CRAM element format.** The `format: [bam, cram]` spelling is unverified against the gxformat2 schema.
3. **`chr` and identifiers.** Output identifiers change with `chr`. The interface keeps `chr` as a plain string; the test plan must decide whether to assert identifiers under `chr`.
4. **FastQC in the Galaxy design.** The source computes FastQC but does not publish or consume it. The interface does not expose it. The data-flow Mold may choose to keep it as an unexposed QC step; this brief does not decide that.
5. **Collate output format.** The `fastqsanger.gz` format of `single_reads` assumes the collate module publishes `*.fastq.gz`, which was not checked.
6. **Sample-sheet index.** The user cannot supply a BAI or CRAI index in Galaxy v1. The source builds one when it is absent (`SAMTOOLS_INDEX`); whether the Galaxy tool step can do the same is an open entry.
7. **CRAM requires a reference.** Carried from the reference brief. The interface documents it in the input help (for `fasta`) but does not enforce it.
