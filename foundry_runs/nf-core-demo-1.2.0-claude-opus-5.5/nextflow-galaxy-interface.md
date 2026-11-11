# Galaxy interface brief — nf-core/demo 1.2.0

Source: `summary-nextflow.json` (nf-core/demo @ 32893af, primary workflow `DEMO`), `nextflow-galaxy-reference-data.md` (classification: **None**), `open-requirements.ledger.yml`.
Consumers: nextflow-summary-to-galaxy-data-flow, nextflow-summary-to-galaxy-template, nextflow-test-to-galaxy-test-plan.

## Workflow inputs

| Label | gxformat2 type | Shape / format | Optional | Default | Source | Confidence |
|---|---|---|---|---|---|---|
| `reads` | `collection` | `collection_type: list:paired_or_unpaired`; elements `fastqsanger.gz` | no | — | `params.input` via `samplesheetToList(assets/schema_input.json)` → `ch_samplesheet` | medium |
| `skip_trim` | `boolean` | — | no | `false` | `params.skip_trim`, guard `!params.skip_trim` on `SEQTK_TRIM` | high |
| `multiqc_title` | `string` | — | yes | none | `params.multiqc_title` → MULTIQC `ext.args --title` | high |

### `reads` — shape rationale

- Sample sheet columns (`summary.sample_sheets[input]`, `discovered_via: nf-schema`): `sample` (meta `id`, `^\S+$`), `fastq_1` (required file-path, `*.f(ast)q.gz`), `fastq_2` (**optional** file-path). Optional second mate ⇒ mixed single/paired ⇒ `paired_or_unpaired` inner type (nextflow-params-to-galaxy-inputs §Sample sheets).
- **`list:` rather than `sample_sheet:`**: the row schema has no metadata column besides the identifier (`sample` → element identifier). A `sample_sheet` would carry empty `column_definitions` and add nothing, while `list:paired_or_unpaired` has broader tool/test-fixture support. `sample` `pattern ^\S+$` is a Galaxy element-identifier constraint already.
- **Multi-run grouping is not reproduced.** Source `PIPELINE_INITIALISATION` `groupTuple()`s rows sharing `sample`, validates consistent endedness, and flattens all FASTQs into one per-sample list (the test sheet has `SAMPLE3_SE` on two rows). Galaxy element identifiers must be unique, so each **row (run)** becomes one element with a unique identifier (e.g. `SAMPLE3_SE_1`, `SAMPLE3_SE_2`). Every per-sample consumer (FASTQC, SEQTK_TRIM) runs per FASTQ file and MULTIQC aggregates all files, so the scientific result is unchanged; only per-sample output grouping/naming differs. Recorded as a `dropped` ledger entry.
- Datatype: pattern `\.f(ast)?q\.gz$` with no quality-encoding evidence; `fastqsanger.gz` is the Galaxy convention for Illumina gz FASTQ (nextflow-path-glob-to-galaxy-datatype). Confidence medium.

### Excluded params

| source_param | class | effect | assessment | reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish | publishDir only | safe | Galaxy owns history/outputs |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | completion email | safe | runtime reporting |
| `monochrome_logs`, `validate_params`, `trace_report_suffix` | runtime UX | logging/validation | safe | execution UX |
| `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path` | institutional config | config loading | safe | site config |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | CLI | safe | Nextflow CLI behaviour |
| `genome`, `fasta`, `igenomes_base`, `igenomes_ignore` | reference selector | none (unconsumed) | safe | reference-data brief: classification None; existing ledger entry `reference-genome-params-not-exposed` |
| `multiqc_config` | report config | selects MultiQC YAML (default bundled `assets/multiqc_config.yml`) | problematic (minor) | changes report presentation, not QC values; Galaxy MultiQC wrapper has its own config surface. Fixed to wrapper defaults; ledger entry `multiqc-custom-config-not-exposed` |
| `multiqc_logo`, `multiqc_methods_description` | report config | report cosmetics / methods text | safe | presentation only |

User warning: the Galaxy workflow is not a CLI replica — 24 params above are dropped (publish, notification, runtime UX, CLI, unused reference, report-cosmetics).

## Workflow outputs

| Label | Shape / format | Producer (source) | Conditional | Public/checkpoint | Confidence |
|---|---|---|---|---|---|
| `fastqc_html` | `list` (per FASTQ) of `html` | `FASTQC.out.html` (published `fastqc/<id>/*.html`) | no | public | high |
| `fastqc_zip` | `list` of `zip` | `FASTQC.out.zip` (MultiQC input; not published by source) | no | checkpoint (feeds MultiQC; addressable for tests) | medium |
| `trimmed_reads` | `list:paired_or_unpaired` (or per-file `list`) of `fastqsanger.gz` | `SEQTK_TRIM.out.reads` (published `fq/<id>/*.fastq.gz`) | **yes** — absent when `skip_trim` | public | medium |
| `cowpy_output` | `File`, `txt` | `COWPY.out.txt` (published `cowpy/cowpy.txt`) | no | public | high |
| `multiqc_report` | `File`, `html` | `MULTIQC.out.report` (emitted as `multiqc_report`) | no | public | high |
| `multiqc_stats` | `File` or `list` of `tabular` (MultiQC data tables, e.g. `multiqc_general_stats.txt`, `multiqc_fastqc.txt`) | `MULTIQC.out.data` | no | **checkpoint** — stable content in source snapshot (md5s in `tests/default.nf.test.snap`) | medium |

Not exposed: `pipeline_info/nf_core_demo_software_mqc_versions.yml` (topic `versions` collation) — Galaxy records tool versions per job; `MULTIQC.out.plots` (images vary across runs, weak test value). Both recorded in the ledger as dropped.

## Labels and testability

- Labels are stable snake_case and match the table above; tests should address `fastqc_html`, `trimmed_reads`, `cowpy_output`, `multiqc_report`, `multiqc_stats`.
- Collection element identifiers come from the `reads` element identifiers (sample/run names) and must be preserved through mapping so tests can address e.g. `SAMPLE1_PE`.
- Strongest content checks available from source evidence: `cowpy.txt` md5 `9c8be9f4…` (deterministic), trimmed FASTQ md5s, MultiQC `multiqc_general_stats.txt` / `multiqc_fastqc.txt`. Report HTML: smoke check only.

## Open questions (carried in ledger)

1. Can FastQC/seqtk wrappers be mapped over `list:paired_or_unpaired` directly, or does data-flow need an explicit flatten/split to a per-file `list`? (`reads-paired-or-unpaired-mapping`)
2. Does the Galaxy MultiQC wrapper expose a `data` collection equivalent to Nextflow `multiqc_data/`? (`multiqc-stats-output-shape`)
