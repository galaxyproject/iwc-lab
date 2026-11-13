# Galaxy workflow interface brief — nf-core/bamtofastq → Galaxy

Source: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e) + `nextflow-galaxy-reference-data.md`. Design handoff for the data-flow and template Molds. Not a gxformat2 skeleton.

## Source interface recap

The pipeline takes one samplesheet (`params.input`, nf-schema `assets/schema_input.json`: `sample_id` meta/required, `mapped` data/required `.bam|.cram`, `index` data/optional `.bai|.crai`, `file_type` meta/required enum `bam|cram`), an optional reference FASTA + FAI, and scalar options (`chr`, `no_stats`, `no_read_qc`, `samtools_collate_fast`, `reads_in_memory`, MultiQC report customizations). It emits converted FASTQ reads, samtools stats/flagstat/idxstats, FastQC reports (pre and post conversion), fastq_utils info txts, and a MultiQC report (evidence: publishDir patterns in `conf/modules.config`, snapshot `tests/default.nf.test.snap`).

## Workflow inputs

| Label | gxformat2 type | Format / collection_type | Optional | Default | Source param(s) | Confidence |
|---|---|---|---|---|---|---|
| `alignments` | collection | `list`, elements `bam`/`cram` | no | — | `input` (sample sheet) | High |
| `reference_fasta` | data | `fasta` | yes | — | `fasta` | High |
| `reference_fai` | data | `fai` | yes | — | `fasta_fai` | High |
| `chr` | string | — | yes | — | `chr` | High |
| `no_stats` | boolean | — | no | `false` | `no_stats` | High |
| `no_read_qc` | boolean | — | no | `false` | `no_read_qc` | High |
| `samtools_collate_fast` | boolean | — | no | `false` | `samtools_collate_fast` | High |
| `reads_in_memory` | int | — | no | `100000` | `reads_in_memory` | High |
| `multiqc_config` | data | yaml | yes | — | `multiqc_config` | Medium |

### Input design notes

- **`alignments` — `list` collection, not `sample_sheet*`.** Rationale: every samplesheet column already has a Galaxy-native carrier — `sample_id` → element identifier, `file_type` → element datatype (`bam` vs `cram`), `index` → rebuild (see below). The `sample_sheet:record` variant that could carry the second path column (`index`) has poor tool-side support for the samtools wrappers this workflow maps over; the source pipeline itself rebuilds missing indexes (PREPARE_INDICES → SAMTOOLS_INDEX), so rebuilding always is faithful to the `index`-absent path. Users may mix `bam` and `cram` elements; the reference FASTA is required when any element is CRAM (open ledger entry `cram-requires-fasta`; help text must say so).
- **Per-element index rebuild.** `alignments` elements do not carry `.bai`/`.crai` sidecars. The data-flow brief must ensure each consumer either receives an index built by an explicit `samtools index` step (mirroring PREPARE_INDICES) or uses wrapper-side indexing. Recorded as dropped source capability (user-supplied indexes are always rebuilt; compute cost only, identical outputs).
- **`chr`** is kept as an optional string (not just a boolean gate): it both gates the SAMTOOLS_CHR branch and parameterizes the region (`ext.args2`). Empty/absent → branch skipped. The data-flow brief decides how the conditional branch is expressed in Galaxy.
- **`no_stats` / `no_read_qc`** are kept because they change which steps run (workflow-shape controls), not just publishing. They map to Galaxy step-level `when:` conditions on the gated steps — the data-flow brief owns the wiring.
- **`samtools_collate_fast` + `reads_in_memory`** change tool arguments (`samtools collate -f -r N`); kept as scalars. `reads_in_memory` only meaningful when `samtools_collate_fast` is true.
- **`multiqc_config`** kept as optional data input (report config consumed by the MultiQC tool, per nextflow-params-to-galaxy-inputs keep-list).
- **Reference inputs** follow the reference-data brief: explicit optional `fasta`/`fai` inputs, no data tables, iGenomes key dropped.

### Excluded params (per nextflow-params-to-galaxy-inputs control-param rules)

Consolidated notice: the Galaxy workflow is not a CLI replica of `nextflow run nf-core/bamtofastq`; the following params are not carried into the Galaxy interface.

| Param | Class | Effect | Assessment | Reason |
|---|---|---|---|---|
| `outdir` | publish | Galaxy owns history layout | safe | Runtime UX only. |
| `publish_dir_mode` | publish | Galaxy owns output exposure | safe | Runtime UX only. |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | Completion emails | safe | Galaxy notifications are history-level. |
| `monochrome_logs`, `validate_params`, `help`, `help_full`, `show_hidden`, `version`, `trace_report_suffix` | CLI plumbing | Nextflow CLI behavior | safe | No Galaxy analog needed; Galaxy validates input shapes itself. |
| `config_profile_*`, `custom_config_*`, `pipelines_testdata_base_path` | site config | Institutional configs | safe | Execution-environment plumbing. |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference resolution | iGenomes key resolution | safe | Dropped per reference-data brief (v1 no-data-tables posture); ledger entry `igenomes-key-dropped`. |
| `multiqc_title` | report cosmetics | MultiQC report title/filename | safe | Only renames the report dataset; Galaxy output naming is a design choice. |
| `multiqc_logo` | report cosmetics | MultiQC logo | safe | Report cosmetics only. |
| `multiqc_methods_description` | report content | Methods section inside MultiQC report | safe | Changes report prose only, no scientific output; falls back to a bundled asset template in source. Recorded as dropped in ledger. |

## Workflow outputs

Labels chosen for test addressability (per galaxy-workflow-testability-design); the default nf-test snapshot (`tests/default.nf.test.snap`) supplies expected content for the starred outputs.

| Label | Type | Shape / format | Source | Test evidence |
|---|---|---|---|---|
| `reads` ★ | collection | `list` of `fastqsanger.gz` | CAT_FASTQ reads (+ single-end collatefastq output) | snapshot md5s: `test_1.merged.fastq.gz` etc. |
| `flagstat` ★ | collection | `list` of `tabular` | SAMTOOLS_FLAGSTAT | snapshot md5s: `test.flagstat` etc. |
| `idxstats` ★ | collection | `list` of `tabular` | SAMTOOLS_IDXSTATS | snapshot md5s |
| `stats` ★ | collection | `list` of `tabular` | SAMTOOLS_STATS | snapshot md5s |
| `fastqc_pre_html`, `fastqc_pre_zip` | collections | `list` of `html` / `zip` | FASTQC pre-conversion | smoke (html/zip in `.nftignore`) |
| `fastqc_post_html`, `fastqc_post_zip` | collections | `list` of `html` / `zip` | FASTQC post-conversion | smoke |
| `fastqutils_info` ★ | collection | `list` of `txt` | FASTQUTILS_INFO | snapshot md5s: `test.txt`, `test2.txt` |
| `multiqc_report` | data | `html` | MULTIQC | smoke (multiqc in `.nftignore`) |

### Output design notes

- **`reads` as a flat `list`, not `list:paired`.** Per-sample read count varies at runtime: the source determines single-end vs paired-end per sample at runtime (CHECKPAIREDEND) and emits `_1`/`_2` files for paired samples and a single `*_other.fq.gz` for single-end samples. A statically-paired collection would be wrong for single-end samples. Element identifiers must preserve `{sample}_{1,2}` / `{sample}` so pairing is recoverable downstream. If a downstream consumer needs pairs, a later workflow can rebuild pairs by identifier rules.
- Pre-conversion FastQC emits one html+zip per sample (input alignment); post-conversion emits one html+zip per output read file (`test.post_conversion_1_fastqc.html`, `..._2_fastqc.html`).
- `pipeline_info/*` (versions yml, reports) is not carried: Galaxy records tool versions in provenance; recorded as dropped in ledger.
- The per-step `versions` outputs (nf-core topic channels) are not carried as workflow outputs (Galaxy provenance subsumes them).

## Checkpoint outputs for tests

The starred outputs above are the test surface: `flagstat`, `idxstats`, `stats`, `fastqutils_info`, `reads` carry stable md5s in the upstream snapshot for the default test (2 BAM samples, paired-end) and give content assertions much stronger than element-count smoke checks. FastQC and MultiQC outputs get element-presence/size smoke checks only (`.nftignore` excludes them upstream, so no expected content exists).

## Open questions

1. **Per-sample endedness routing** (ledger entry `endedness-per-element-routing`): CHECKPAIREDEND decides single vs paired conversion per sample at runtime. Galaxy needs per-element conditional routing (e.g. mapped `param_value_from_file` + step `when:`, or a conditional pick). Resolved in the data-flow brief.
2. **CRAM conditional FASTA requiredness** (existing ledger entry `cram-requires-fasta`): FASTA input is optional but required for CRAM elements; documented in input help text, failure surfaces at tool runtime.
3. **`chr` branch** (ledger entry `chr-branch-conditional`): region-filter subgraph gated on a non-empty `chr` string; Galaxy `when:` on a string input needs a non-empty test — data-flow brief to pin the expression (e.g. step `when` comparing the input to `''`).
