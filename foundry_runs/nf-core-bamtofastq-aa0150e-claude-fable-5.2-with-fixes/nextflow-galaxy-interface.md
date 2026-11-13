# Galaxy interface brief — nf-core/bamtofastq

Source: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e), `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`.

## Workflow inputs

| # | Galaxy label | gxformat2 | Format | Optional | Source | Confidence |
|---|---|---|---|---|---|---|
| 1 | `Alignments` | `type: collection`, `collection_type: list` | `bam` | no | `params.input` sample sheet (`samplesheetToList`, `assets/schema_input.json`) | high for BAM |
| 2 | `Reference genome FASTA` | `type: data` | `fasta` | yes | `params.fasta` | medium — kept only if CRAM input is carried (see below) |
| 3 | `Regions to extract` | `type: string` | — | yes | `params.chr` | low — depends on the samtools view wrapper (see below) |

### Input 1 — why a plain `list`, not `sample_sheet*`

The sample sheet has four columns. Each one already has a native Galaxy home, so no row metadata is left to carry:

| Column | nf-schema | Galaxy home |
|---|---|---|
| `sample_id` (meta, required) | string, `^\S+$` | element identifier of the list |
| `mapped` (data, required) | path, `.bam` or `.cram` | the element dataset |
| `index` (data, optional) | path, `.bai` or `.crai` | none needed: a Galaxy `bam` dataset carries its index as metadata, built at upload. `SAMTOOLS_INDEX` in `PREPARE_INDICES` is subsumed. |
| `file_type` (meta, enum bam/cram) | string | the dataset's datatype |

The params note says to use `sample_sheet*` "when row metadata should survive as invocation-time structured metadata", and the reference-data note says a sheet whose columns map to direct inputs should become direct inputs. So: `list` of `bam`. Shape evidence: repeated `tuple(meta, alignment, index)` → `list` (channel-shape note, high).

**CRAM rows.** The source accepts `.cram` + `.crai`. In Galaxy this needs every consuming wrapper to take `cram` with a history reference, and FastQC pre-conversion must skip CRAM elements (the source does this with a per-element `branch` on `meta.filetype`). This brief sets `format: bam` only. Ledger entry `cram-input-support-unverified` stays open for the data-flow phase and tool discovery to carry or drop with a cited reason.

### Input 2 — reference

From the reference-data brief: one optional `fasta` data input, no `fai`, no genome key. It affects results only for CRAM. If CRAM is dropped downstream, this input must be dropped with it (an unused optional input is noise). Ledger entry `optional-reference-vs-tool-conditional` stays open.

### Input 3 — `chr`

`params.chr` (e.g. `"chrX chrY X Y"`) switches on `SAMTOOLS_CHR` (`samtools view -hb <regions>`) + `SAMTOOLS_CHR_INDEX` and renames the sample id to `<id>.<regions joined by _>`. It changes workflow shape, so it is not a silent exclude. Proposed: an optional `string` input wired to the region argument of one samtools view step placed before conversion. Whether an empty value can mean "no region filter" depends on the wrapper; if not, the choice is a fixed design default (no region filter) and a recorded drop. New ledger entry `chr-region-filter-unverified`.

### Per-sample single-end / paired-end routing (no input)

The source detects pairedness per sample (`CHECKPAIREDEND`) and routes each sample to a single-end or a paired-end conversion branch. This is internal, not a launch param, so it creates no workflow input. It does shape the outputs (two read collections, below).

## Scalar and control params not exposed

| Source param | Class | Effect | Assessment | Decision |
|---|---|---|---|---|
| `no_read_QC` | skip flag | gates `FASTQC_PRE_CONVERSION`, `FASTQC_POST_CONVERSION` (`ext.when`) | problematic by rule (gates processes) but outputs feed nothing except reports | fixed design default: QC always runs (source default `false`). Recorded as dropped. |
| `no_stats` | skip flag | gates `SAMTOOLS_FLAGSTAT`, `SAMTOOLS_IDXSTATS`, `SAMTOOLS_STATS` | same | fixed design default: stats always run. Recorded as dropped. |
| `samtools_collate_fast`, `reads_in_memory` | tool tuning | adds `-f -r N` to `samtools collate` | safe for the read set (`-f` keeps primary alignments only; `samtools fastq` drops secondary/supplementary anyway) but a real performance option | not exposed unless the wrapper has the option; ledger entry `collate-fast-mode-unverified` |
| `genome`, `igenomes_base`, `igenomes_ignore` | reference key | iGenomes lookup | recorded in reference brief | not exposed |
| `fasta_fai` | reference index | skips `SAMTOOLS_FAIDX` | safe (in-tool rebuild) | not exposed |
| `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | report config | MultiQC cosmetics | safe | not exposed |
| `outdir`, `publish_dir_mode` | publish | output location | safe | excluded |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | — | safe | excluded |
| `monochrome_logs`, `validate_params`, `trace_report_suffix`, `version`, `help`, `help_full`, `show_hidden` | runtime UX / CLI | — | safe | excluded |
| `custom_config_version`, `custom_config_base`, `config_profile_*`, `pipelines_testdata_base_path` | institutional config | — | safe | excluded |

One consolidated notice for users: the Galaxy workflow is not a CLI replica; the params above are not inputs.

## Workflow outputs

Published outputs come from `publishDir` selectors in `conf/modules.config` and the stable-name list in `tests/default.nf.test.snap`.

| Galaxy label | Shape | Format | Source (publish path) | Notes |
|---|---|---|---|---|
| `Paired-end reads` | `list:paired` | `fastqsanger.gz` | `reads/<id>_{1,2}.merged.fastq.gz` (`CAT_FASTQ`) | primary product; contains only samples detected as paired-end |
| `Single-end reads` | `list` | `fastqsanger.gz` | `reads/<id>_other.fq.gz` (`SAMTOOLS_COLLATEFASTQ_SINGLE_END`, pattern `*other.fq.gz`) | primary product; only samples detected as single-end |
| `Samtools flagstat` | `list` | `txt` | `samtools/<id>.flagstat` | test checkpoint (deterministic text) |
| `Samtools idxstats` | `list` | `tabular` | `samtools/<id>.idxstats` | test checkpoint (deterministic table) |
| `Samtools stats` | `list` | `txt` | `samtools/<id>.stats` | header holds version and command line |
| `FastQC pre-conversion report` | `list` | `html` | `fastqc/<id>.pre_conversion_fastqc.html` | Galaxy FastQC gives HTML + raw text instead of HTML + zip |
| `FastQC pre-conversion data` | `list` | `txt` | (inside `..._fastqc.zip`) | test checkpoint (e.g. Total Sequences) |
| `FastQC post-conversion report` | collection (paired and single samples) | `html` | `fastqc/<id>.post_conversion_{1,2}_fastqc.html` | |
| `FastQC post-conversion data` | same | `txt` | (inside zip) | test checkpoint |
| `FASTQ validation` | `list` | `txt` | `fastqutils/<id>.txt` (`FASTQUTILS_INFO`) | the source file is a fixed sentence written only if `fastq_info` exits 0 |
| `MultiQC report` | `File` | `html` | `multiqc/multiqc_report.html` | see deviation below |

Not exposed as outputs:

| Source output | Reason |
|---|---|
| `pipeline_info/nf_core_bamtofastq_software_mqc_versions.yml` | Galaxy records tool versions per job; no file equivalent. Recorded as dropped. |
| `multiqc/multiqc_data/*` | all volatile (`.nftignore`); the report is exposed |
| `*_fastqc.zip` | Galaxy FastQC wrapper exposes raw text data instead |
| unpublished intermediates (`publishDir enabled: false`): `SAMTOOLS_VIEW_*`, `SAMTOOLS_MERGE_UNMAP`, `COLLATE_FASTQ_*`, `CHECKPAIREDEND`, indexes | hidden intermediates |
| `samtools/<id>.<chr>.bam` (`SAMTOOLS_CHR`, default publishDir) | follows the fate of input 3 |

**MultiQC deviation.** In this source revision `MULTIQC` receives only software-versions, workflow-summary and methods YAML files (the line that would add QC files is commented out). A Galaxy MultiQC step with no QC inputs has nothing to show. Proposed: feed it the FastQC and samtools stats outputs — the pipeline's documented intent, a superset of what the source does. Recorded as a decision.

## Identifiers and labels

- Element identifiers = `sample_id` values (`test`, `test2` in the selected test). They must survive every mapped step so tests can address `test` and `test2` in each output collection.
- Paired members are addressed as `forward` / `reverse`.
- Labels above are the public test keys; renaming one is a test-interface change.

## Checkpoint outputs worth testing

1. `Samtools flagstat` and `Samtools idxstats` — plain deterministic text; the nf-test snapshot holds md5s for both samples.
2. `FastQC ... data` — `Total Sequences` lines tie the read counts before and after conversion.
3. `Paired-end reads` — forward and reverse must have equal read counts.

## Provenance and confidence

| Decision | Evidence | Confidence |
|---|---|---|
| list of bam | `sample_sheets[0]` columns; channel shape `tuple(meta, alignment, index)` | high |
| index column subsumed | Galaxy `bam` datatype (index as metadata); datatype note: `.bai` "usually sidecar — avoid separate top-level input" | high |
| two read output collections | `workflow.edges` (branch on `meta.single_end`), publishDir patterns | high |
| reference optional | reference brief | medium |
| `chr` input | `conditionals[] guard params.chr` | low until wrapper known |

## Open questions

1. Carry CRAM (and with it the FASTA input) or drop both? → data-flow + tool discovery.
2. Can `chr` be an optional string, or does it become a fixed default? → tool discovery.
3. Shape of the post-conversion FastQC outputs when both paired and single samples exist (one merged list vs two collections) → data-flow.
