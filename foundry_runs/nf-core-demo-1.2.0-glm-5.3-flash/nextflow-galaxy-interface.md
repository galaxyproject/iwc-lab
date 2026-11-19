# Galaxy interface brief — nf-core/demo (1.2.0)

Source: `summary-nextflow.json`; reference-data brief: `nextflow-galaxy-reference-data.md` (classification: none — no reference inputs).

## Workflow-level shape

Reads in → QC reports out. Primary workflow: `DEMO` (workflows/demo.nf), invoked via `NFCORE_DEMO` ← `PIPELINE_INITIALISATION` (samplesheet materialization). Steps: FASTQC, SEQTK_TRIM (gated by `skip_trim`), COWPY, MULTIQC.

## Galaxy inputs

### 1. `Input samplesheet` — `type: collection`, `collection_type: sample_sheet:paired_or_unpaired`

- source_param: `input` (required, `format: file-path`, `mimetype: text/csv`, nf-schema schema `assets/schema_input.json`, materialized via `samplesheetToList` → `construct: samplesheetToList`, `from_param: input`, `required_runtime: true`).
- Variant choice: the schema has two path columns (`fastq_1` required, `fastq_2` optional) → inner element is paired-or-unpaired. Confirmed by the test data: SAMPLE1_PE/SAMPLE2_PE are paired, SAMPLE3_SE rows are single-end.
- Column mapping:
  - `sample` (meta, required, pattern `^\S+$`) → element identifier (requiredness enforced by sample-sheet validator `regex`).
  - `fastq_1` (data, required, `^\S+\.f(ast)?q\.gz$`) → forward slot; datatype `fastqsanger.gz`.
  - `fastq_2` (data, optional, same pattern) → reverse slot; datatype `fastqsanger.gz`.
  - No additional `column_definitions` needed (the only meta column is the identifier).
- `column_definitions`: none (validator regexes live on the element datatype/identifier; nf-schema patterns beyond regex are dropped to prose).
- requiredness_basis: schema `required: ["input","outdir"]` + `required_runtime: true`. → `optional: false`.
- confidence: medium. Losses: nf-schema `exists: true` check (Galaxy sample sheets do not verify file existence at design time); samplesheetToList's single_end/paired-end consistency validation is a runtime behavior with no Galaxy-side equivalent — recorded as validation loss.
- Open question (ledgered): FastQC/seqtk wrappers must accept a `sample_sheet:paired_or_unpaired` collection mapped over their multi-dataset input. If a wrapper's declared `collection_type` allowlist rejects it, fall back to `list:paired` + separate single-end `list` input split. Not verifiable inside this Mold (needs `gxwf tool-search` / wrapper inspection in the data-flow phase).

### 2. `Skip trimming` — `type: boolean`, default `false`

- source_param: `skip_trim` (Process skipping options, default `false` in `nextflow.config` params block).
- Effect: gates SEQTK_TRIM (`if (!params.skip_trim) { SEQTK_TRIM(ch_samplesheet) }`) — a mode switch that changes which steps run, so it is kept per the control-params rule. In gxformat2 this gates the SEQTK_TRIM step's `when` (data-flow phase decides the exact mechanism).
- confidence: high.

## Excluded control params (consolidated notice)

The Galaxy target is not a faithful nf-core CLI replica. Dropped, all `assessment: safe` (traced in the summary; each only affects Nextflow runtime/publish/CLI behavior, never scientific output):

| source_param | class | effect |
|---|---|---|
| `outdir` | publish | Galaxy owns history/output placement. |
| `publish_dir_mode` | publish | publishDir mode only. |
| `email`, `email_on_fail`, `plaintext_email` | notification | PIPELINE_COMPLETION only; no Galaxy equivalent. |
| `max_multiqc_email_size` | notification | email attachment size only. |
| `monochrome_logs`, `validate_params`, `version` | runtime UX / CLI plumbing | log color, schema validation, version banner. |
| `help`, `help_full`, `show_hidden` | CLI plumbing | Nextflow help output. |
| `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`, `multiqc_title` | runtime UX | customize the MultiQC report inputs; MultiQC in the Galaxy target consumes a fixed design (default config, no logo/custom methods). *Assessment nuance:* these are "real data input if the target includes that customization" — the v1 design fixes them to the pipeline defaults rather than exposing 4 optional inputs; recorded as a deliberate simplification, safe because they change report cosmetics, not the report's existence or core contents. |
| `genome`, `fasta`, `igenomes_base`, `igenomes_ignore` | reference plumbing | vestigial; see reference-data brief. |
| `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path`, `trace_report_suffix` | institutional/runtime config | site config and report naming only. |

## Galaxy outputs

| Output (public name) | producer | type/format | Purpose |
|---|---|---|---|
| `multiqc_report` | MULTIQC `report` | `data`, `html` | The pipeline's primary product (nf-core/demo's whole point). Smoke check: file exists, non-trivial size. |
| `cowpy_txt` | COWPY `txt` | `data`, `txt` | Checkpoint output: content-stable (`cowpy.txt` md5 `9c8be9f4550989b40901f379cb1a605f` in the source snapshot) — strong cheap assertion that the container/tool chain ran. |
| `trimmed_reads` | SEQTK_TRIM `reads` | `collection` (list), elements `fastqsanger.gz` | Checkpoint output: per-sample trimmed reads; snapshot carries stable md5s for all 4 trimmed files → content assertions catch trimming failures. Addressable element identifiers must preserve sample names (data-flow phase must keep `SAMPLE1_PE_sample1_R1.fastq.gz`-style names or map sample→element cleanly). |
| `fastqc_reports` | FASTQC `html` | `collection` (list), elements `html` | User-visible QC reports + smoke-level shape check (6 elements for the 3-sample test data). Content is not md5-stable across FastQC versions (excluded from snapshot content via `.nftignore`) — assertions limited to count/size. |
| `fastqc_archives` | FASTQC `zip` | `collection` (list), elements `zip` | Companion archives, user-visible in the publish tree; smoke check only. |

Checkpoint promotion rationale: the nf-test snapshot's stable-content assertions (cowpy.txt, trimmed fastqs, multiqc txt tables) are the strongest available evidence; `multiqc_general_stats.txt`/`fastqc_sequence_counts_plot.txt` remain inside the MultiQC data directory, which Galaxy's MULTIQC wrapper emits as a single html output + data files only when the wrapper exposes them — not promoted here; the test plan falls back to trimmed-reads and cowpy content assertions.

## Labels

Stable public names (entry `id`s): `Input samplesheet`, `Skip trimming`, `multiqc_report`, `cowpy_txt`, `trimmed_reads`, `fastqc_reports`, `fastqc_archives`. Every promoted output is addressed by name, not position.

## Provenance & confidence summary

- Inputs: `input` → sample_sheet:paired_or_unpaired (medium), `skip_trim` → boolean (high).
- Outputs: from `DEMO.out.multiqc_report`, `COWPY.out.txt`, `SEQTK_TRIM.out.reads`, `FASTQC.out.html`, `FASTQC.out.zip` (high — direct emit declarations in workflows/demo.nf).
- Losses: single_end consistency validation (runtime-only), nf-schema exists checks, MultiQC customization inputs, versions.yml aggregation (`ch_versions`/`collectFile` pipeline_info files are Nextflow reporting plumbing, not promoted).

## Open questions

1. Wrapper acceptance of `sample_sheet:paired_or_unpaired` for FastQC/seqtk (see above; carried to data-flow).
2. Element-identifier preservation for `trimmed_reads` (seqtk output names `<prefix>_<basename>` vs Galaxy dataset names) — data-flow phase.
