# nf-core/demo — Galaxy workflow interface brief

Source: `summary-nextflow.json` (nf-core/demo @ 671a0726), `nextflow-galaxy-reference-data.md` (no reference inputs).

## Inputs

| Label | Galaxy type | Datatype | Optional | Source | Confidence |
|---|---|---|---|---|---|
| `reads` | collection `list:paired_or_unpaired` | `fastqsanger.gz` | no | `params.input` → `samplesheetToList(assets/schema_input.json)` → `ch_samplesheet` | medium |
| `skip_trim` | boolean parameter, default `false` | — | yes | `params.skip_trim` (guard `!params.skip_trim` on SEQTK_TRIM) | high |
| `multiqc_title` | text parameter | — | yes | `params.multiqc_title` (MULTIQC `ext.args --title`) | high |

### `reads` shape rationale

- The sample sheet has `sample` (meta, `^\S+$`), `fastq_1` (required, `*.f(ast)q.gz`) and `fastq_2` (optional). An optional mate column means mixed single/paired samples, which maps to `paired_or_unpaired` as the innermost type.
- The only meta column is `sample`, and it becomes the element identifier. No other per-row metadata exists, so a `sample_sheet:paired_or_unpaired` adds no information over `list:paired_or_unpaired`. The plain list is chosen because fixtures and gxwf/planemo support for it are more established.
- Paired elements use `forward`/`reverse`; single-end elements use the `unpaired` member.
- **Multiple runs per sample.** `PIPELINE_INITIALISATION` groups rows by `sample` (`groupTuple`) and flattens their files into one item. The test sheet lists `SAMPLE3_SE` twice, giving one FASTQC/SEQTK task over two files. Every consuming process works per file and nothing aggregates by sample, so the Galaxy interface takes one element per sample run. Multi-run samples need distinct identifiers (e.g. `SAMPLE3_SE_1`, `SAMPLE3_SE_2`). The run-grouping axis is recorded as dropped in the ledger.

## Outputs

| Label | Producer | Galaxy shape | Datatype | Mirrors NF publish | Test use |
|---|---|---|---|---|---|
| `fastqc_html` | FASTQC `html` | `list:paired_or_unpaired` | `html` | `fastqc/<id>/*.html` | element identifiers + `has_text: FastQC` |
| `trimmed_reads` | SEQTK_TRIM `reads` | `list:paired_or_unpaired` | `fastqsanger.gz` | `fq/<id>/*.fastq.gz` | checkpoint: element count/identifiers, decompressed content |
| `cowpy_output` | COWPY `txt` | File | `txt` | `cowpy/cowpy.txt` | `has_text: nf-core rules!` (deterministic) |
| `multiqc_report` | MULTIQC `report` | File | `html` | `multiqc/multiqc_report.html` | smoke `has_text: MultiQC` |
| `multiqc_stats` | MULTIQC general-stats table | File | `tabular` | `multiqc/multiqc_data/multiqc_general_stats.txt` | checkpoint: sample names present |

- FASTQC `zip` is internal (it feeds MultiQC only; NF publishes `*.{html,json}`). It is not exposed.
- `versions.yml` / topic versions and `workflow_summary_mqc.yaml` / `methods_description_mqc.yaml` are Nextflow runtime provenance. They are not exposed; Galaxy records tool versions natively.
- `trimmed_reads` exists only when `skip_trim` is false (optional step output).

## Excluded params (runtime control)

`outdir`, `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size`, `publish_dir_mode`, `monochrome_logs`, `validate_params`, `trace_report_suffix`, `help*`, `show_hidden`, `version`, `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path`, plus reference params (`genome`, `fasta`, `igenomes_*`) per the reference-data brief.

## Not carried

- `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`: optional MultiQC customization files. The Galaxy MultiQC wrapper is configured through its own parameters, so these are recorded as dropped rather than exposed as raw files.

## Open questions

- Whether the selected Galaxy FastQC/seqtk/MultiQC wrappers map cleanly over `list:paired_or_unpaired` with a single-dataset input (expected: full map-over that preserves the nested structure). Settled in data-flow/implementation.
- A Galaxy tool for `cowpy` may not exist. Discovery happens in the draft loop.
