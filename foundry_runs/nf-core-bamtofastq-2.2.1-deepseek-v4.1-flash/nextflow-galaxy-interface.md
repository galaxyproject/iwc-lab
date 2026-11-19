# Galaxy interface brief — nf-core/bamtofastq

Source: `nf-core/bamtofastq` @ `aa0150e` (v2.4.0). Inputs: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`.

Scope: `workflow BAMTOFASTQ` and its three pipeline subworkflows (`PREPARE_INDICES`, `PRE_CONVERSION_QC`, `ALIGNMENT_TO_FASTQ`). `PIPELINE_INITIALISATION` / `PIPELINE_COMPLETION` are nf-core plumbing and are not designed.

## Workflow inputs

| label | source param | Galaxy type | format / collection_type | optional | default | confidence | evidence |
|---|---|---|---|---|---|---|---|
| `input_alignments` | `--input` | `collection` | `list`; elements `bam` or `cram` | false | — | high | `sample_sheets[input]` (`nf-schema`, `assets/schema_input.json`): `sample_id` (meta, required), `mapped` (data, required, `*.bam|*.cram`), `index` (data, optional, `*.bai|*.crai`), `file_type` (meta enum bam/cram). The workflow's `PREPARE_INDICES` builds an index when absent (`SAMTOOLS_INDEX` on `meta.index == false`), so pre-built indexes are **not** exposed; `file_type` is redundant with the dataset datatype. |
| `fasta` | `--fasta` | `data` | `fasta` | true | — | high | reference-data brief: needed only for CRAM input; `.fai` handled in-tool |
| `chr` | `--chr` | `string` | — | true | — | high | `workflow.conditionals[0]` guard `params.chr` gates `SAMTOOLS_CHR` + `SAMTOOLS_CHR_INDEX`. Value is a space-separated contig list (test profile: `chrX chrY X Y`). |
| `no_read_QC` | `--no_read_QC` | `boolean` | — | false | `false` | high | `conf/modules.config` `ext.when = { !params.no_read_QC }` on `FASTQC_PRE_CONVERSION` and `FASTQC_POST_CONVERSION` |
| `no_stats` | `--no_stats` | `boolean` | — | false | `false` | high | `ext.when = { !params.no_stats }` on `SAMTOOLS_FLAGSTAT`, `SAMTOOLS_IDXSTATS`, `SAMTOOLS_STATS` |
| `samtools_collate_fast` | `--samtools_collate_fast` | `boolean` | — | false | `false` | high | `ext.args` on the collate steps: `-f -r <reads_in_memory>` |
| `reads_in_memory` | `--reads_in_memory` | `integer` | — | false | `100000` | high | only meaningful when `samtools_collate_fast` is set |
| `multiqc_title` | `--multiqc_title` | `string` | — | true | — | medium | `MULTIQC ext.args --title` |
| `multiqc_config` | `--multiqc_config` | `data` | `data` (yml) | true | — | low | forwarded to MultiQC; whether the Galaxy wrapper exposes a config input is unverified (ledger) |

### Why `list` and not a sample-sheet collection

The samplesheet is a heterogeneous per-sample record (a BAM/CRAM plus an optional index). Galaxy's `sample_sheet:record` could carry it, but:

- the optional index column is a performance shortcut the pipeline itself reproduces by indexing when absent, so it adds no capability;
- `file_type` duplicates the dataset datatype;
- the remaining metadata (`sample_id`) is exactly the Galaxy element identifier.

A plain `list` of `bam`/`cram` datasets therefore carries everything the workflow needs. Recorded as a deliberate simplification (see open question 1 for the fidelity loss).

## Workflow outputs

Published by `conf/modules.config`:

| label | source | Galaxy type | format / collection | confidence | notes |
|---|---|---|---|---|---|
| `converted_reads_single` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` (`reads/*_other.fq.gz`) | `collection` | `list` of `fastq.gz` | high | single-end samples |
| `converted_reads_paired` | `CAT_FASTQ.out.reads` (`reads/*.fastq.gz`) | `collection` | `list` of `fastq.gz` | high | paired-end samples, R1+R2 concatenated by CAT_FASTQ |
| `chr_alignment` | `SAMTOOLS_CHR.out.bam`/`out.cram` (`samtools/<id>.<chr>.bam`) | `collection` | `list` of `bam`/`cram` | high | only when `chr` is set |
| `pre_fastqc_html` | `FASTQC_PRE_CONVERSION.out.html` (`fastqc/<id>.pre_conversion.html`) | `collection` | `list` of `html` | high | BAM inputs only; gated by `no_read_QC` |
| `post_fastqc_html` | `FASTQC_POST_CONVERSION.out.html` (`fastqc/<id>.post_conversion.html`) | `collection` | `list` of `html` | high | gated by `no_read_QC` |
| `samtools_stats` | `SAMTOOLS_STATS.out.stats` (`samtools/*.stats`) | `collection` | `list` of `txt` | high | gated by `no_stats` |
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT.out.flagstat` (`samtools/*.flagstat`) | `collection` | `list` of `txt` | high | gated by `no_stats` |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS.out.idxstats` (`samtools/*.idxstats`) | `collection` | `list` of `txt` | high | gated by `no_stats` |
| `fastqutils_info` | `FASTQUTILS_INFO.out.txt` (`fastqutils/*.txt`) | `collection` | `list` of `txt` | high | post-conversion FASTQ sanity report |
| `multiqc_report` | `MULTIQC.out.report` (`multiqc/`) | `data` | `html` | high | single report |

Not exposed: intermediate BAMs under `samtools/*.map_map.bam` etc. (`publishDir enabled: false`), built indexes (`SAMTOOLS_INDEX`/`SAMTOOLS_FAIDX` unpublished), `versions.yml`, `pipeline_info/*`.

## Excluded params (control surface)

| param | class | effect | assessment |
|---|---|---|---|
| `outdir`, `publish_dir_mode` | publish | output layout | safe |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | notification | completion mail | safe |
| `multiqc_logo`, `multiqc_methods_description` | report config | MultiQC decoration | safe — no Galaxy wrapper input expected |
| `genome`, `igenomes_ignore`, `igenomes_base`, `fasta_fai` | reference | unused / in-tool index | safe — reference-data brief |
| `version`, `help`, `help_full`, `show_hidden`, `validate_params`, `monochrome_logs`, `trace_report_suffix` | CLI/runtime UX | nf-core plumbing | safe |
| `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path` | site config | institutional defaults | safe |

No excluded param changes the workflow's scientific output; the three scientific switches (`chr`, `no_read_QC`, `no_stats`) plus the collate tuning knobs are kept as inputs.

## Source provenance

- `workflows/bamtofastq.nf:48-200` — take-block, conditional `chr` branch, single/paired split, post-conversion QC.
- `subworkflows/local/prepare_indices/main.nf` — index-if-missing branch.
- `subworkflows/local/pre_conversion_qc/main.nf` — stats + pre-conversion FastQC (BAM only).
- `conf/modules.config` — publish paths and per-process args.

## Open questions

1. Fidelity loss: a user who supplies pre-built `.bai/.crai` indexes gets them rebuilt in Galaxy. Acceptable for v1; noted in the requirements ledger.
2. `multiqc_config` datatype and wrapper support — verify during tool discovery.
3. Whether the Galaxy FastQC wrapper accepts BAM input for the pre-conversion step (nf-core runs FastQC on BAM directly). If it does not, the pre-conversion QC becomes a recorded drop rather than a silent change.

## Revision after data-flow design (phase 4)

The source's `CHECKPAIREDEND` decides single vs paired from BAM flags at runtime. Galaxy cannot branch on file content, so the data-flow brief adds one workflow input:

| label | Galaxy type | restrictions | optional | note |
|---|---|---|---|---|
| `input_layout` | `string` | `single`, `paired` | false | replaces `CHECKPAIREDEND`; gates the single-end collate step vs the paired-end view/merge/collate chain |

All files in one run must share a layout (source semantics: the branch is per sample, but the Galaxy branches are workflow-wide `when:` guards, so mixing layouts in one invocation is not supported — recorded in the ledger).
