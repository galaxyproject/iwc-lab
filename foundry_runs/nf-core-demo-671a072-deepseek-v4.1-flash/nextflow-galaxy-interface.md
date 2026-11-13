# Galaxy interface brief — nf-core/demo

Source: `nf-core/demo` @ `671a0726cb489b22636d90b7c7352baed473790d` (v1.2.0, MIT).
Inputs: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`.

Target: a Galaxy gxformat2 workflow replacing `main.nf` → `NFCORE_DEMO` → `DEMO`. Utility subworkflows (`PIPELINE_INITIALISATION`, `PIPELINE_COMPLETION`) and their params have no Galaxy analogue and are not designed here.

## Workflow inputs

| label | source param | Galaxy type | format / collection_type | optional | default | confidence | evidence |
|---|---|---|---|---|---|---|---|
| `input_samples` | `--input` | `collection` | `list:paired_or_unpaired` | false | — | high | `sample_sheets[input]` (`nf-schema`, `assets/schema_input.json`): `sample` (meta, required), `fastq_1` (data, required), `fastq_2` (data, optional, `file-path`, `exists`). Materialized by `samplesheetToList`, `required: true` in nf-schema. |
| `skip_trim` | `--skip_trim` | `boolean` | — | false | `false` | high | `workflow.conditionals[0]` guard `!params.skip_trim` gates `SEQTK_TRIM`; scalar param in `nextflow_schema.json`. |
| `multiqc_title` | `--multiqc_title` | `string` | — | true | — | medium | `conf/modules.config` `MULTIQC ext.args` uses it for `--title`; only affects the report title. |
| `multiqc_config` | `--multiqc_config` | `data` | `yml` | true | — | medium | `DEMO` take-slot forwarded to `MULTIQC`; `conf/modules.config` has no publish effect. Optional: the pipeline falls back to `assets/multiqc_config.yml`, which a Galaxy workflow cannot ship, so omission changes report styling only. |

### Collection shape rationale

`list:paired_or_unpaired` rather than `sample_sheet:paired_or_unpaired`:

- The row schema's only non-path column is `sample`, which in Galaxy is already the element identifier. There is no typed metadata column left to carry in `column_definitions[]`, so a sample-sheet collection would add validation surface without preserving anything the plain collection cannot.
- Per-row layout (`fastq_1` required, `fastq_2` optional) is exactly `paired_or_unpaired`: one job per sample, single-end rows carry one mate.
- Confidence: high for the layout, medium for the exact `collection_type` choice (see open question).

`fastq_1`/`fastq_2` carry no Galaxy datatype on the collection elements; the downstream FastQC/Trimmer tools sniff `fastqsanger.gz`. If an explicit type is wanted on outputs only, `fastqsanger.gz` is the safe extension per the datatype note.

## Workflow outputs

Published by `conf/modules.config` `publishDir` (the only publish surface; `versions.yml` is filtered out by `saveAs`).

| label | source process / channel | Galaxy type | format / collection_type | confidence | notes |
|---|---|---|---|---|---|
| `fastqc_html` | `FASTQC.out.html` (`${outdir}/fastqc/<sample>/*.html`) | `collection` | `list` | high | One HTML per sample; element identifier = sample. |
| `trimmed_reads` | `SEQTK_TRIM.out.reads` (`${outdir}/fq/<sample>/*.fastq.gz`) | `collection` | `list:paired_or_unpaired` | high | Only populated when `skip_trim` is false. |
| `multiqc_report` | `MULTIQC.out.report` (`${outdir}/multiqc/…html`) | `data` | `html` | high | Single report; also the `NFCORE_DEMO` emit. |
| `multiqc_data` | `MULTIQC.out.data` (`${outdir}/multiqc/*_data`) | `data` | `directory`/`data` | medium | Optional: a directory output; expose only if the wrapper emits it as a collection/file. |
| `cowpy_text` | `COWPY.out.txt` (`${outdir}/cowpy/*.txt`) | `data` | `txt` | high | Local module, one file. |

Not exposed: `FASTQC.out.zip` (`publishDir` pattern is `*.{html,json}` only, so the zip is unpublished), `versions.yml` outputs (filtered by `saveAs`), `pipeline_info/*` (produced by `PIPELINE_COMPLETION`, no Galaxy analogue).

## Checkpoint outputs (testability)

Promote these internal outputs as workflow outputs for the test plan even though they are not published by the source:

- `fastqc_html` — stable per-sample HTML set; snapshot-listable.
- `multiqc_report` — single file; assert exists/non-empty.
- `cowpy_text` — stable content marker independent of the input samples.
- `trimmed_reads` — assert sample identifiers survive trimming.

## Excluded params (control surface)

| source param | class | effect | assessment |
|---|---|---|---|
| `outdir` | publish | output root | safe — Galaxy histories own layout |
| `publish_dir_mode` | publish | publish copy/symlink | safe |
| `email`, `email_on_fail`, `plaintext_email` | notification | completion mail | safe |
| `multiqc_logo` | report config | MultiQC logo | safe — Galaxy MultiQC wrapper does not take a logo input; report cosmetics only |
| `multiqc_methods_description` | report config | methods YAML | safe — defaults to a file shipped in the pipeline repo; no Galaxy equivalent |
| `multiqc_custom_config`/`multiqc_config` default | report config | styling | safe (custom config still exposed as optional input) |
| `version`, `help`, `help_full`, `show_hidden` | CLI plumbing | CLI UX | safe |
| `validate_params` | runtime UX | nf-schema validation | safe |
| `monochrome_logs`, `trace_report_suffix` | runtime UX | logging | safe |
| `genome`, `fasta`, `igenomes_ignore`, `igenomes_base` | reference | unused template params | safe — see reference-data brief (classification: none) |
| `custom_config_version`, `custom_config_base`, `config_profile_*` | institutional config | site config | safe |
| `max_multiqc_email_size`, `pipelines_testdata_base_path` | runtime/config | limits, test data root | safe |

No excluded param changes scientific output: `skip_trim` is the only scientific branch and is kept as an input.

## Source provenance

- `summary-nextflow.json`: `samplesheetToList(params.input, 'assets/schema_input.json')`; `workflow DEMO` take-block; `workflow.conditionals[]`.
- `conf/modules.config`: publish paths and per-process args.
- Contract: `DEMO` emits `multiqc_report` only; `NFCORE_DEMO` re-emits it.

## Open questions

1. `list:paired_or_unpaired` vs `sample_sheet:paired_or_unpaired` — chosen plain list because the only metadata column is the element identifier. If a later phase finds Galaxy's sample-sheet workbook UX worth the extra typing, the column set would be empty, so there is nothing to migrate.
2. `multiqc_config` datatype (`yml` vs `data`) and whether the Galaxy MultiQC wrapper exposes a config input — verify during tool discovery.
3. `multiqc_data`/`cowpy_text` exposure depends on whether the MultiQC wrapper emits a data directory; keep optional.
