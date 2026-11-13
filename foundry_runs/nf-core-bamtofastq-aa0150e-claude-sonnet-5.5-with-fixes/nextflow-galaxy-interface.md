# Galaxy interface brief: nf-core/bamtofastq

Source: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e, MIT). Reference-data posture from `nextflow-galaxy-reference-data.md`. Shapes follow the channel-shape, sample-sheet, params-to-inputs and testability notes.

## Purpose
Convert aligned reads (BAM/CRAM) back to FASTQ, with optional pre-/post-conversion QC and a MultiQC report.

## Workflow inputs

| Galaxy label (id) | Type | Shape / datatype | Req. | Source | Notes |
|---|---|---|---|---|---|
| `Alignments (BAM/CRAM)` | collection | `list`, element identifier = sample id; formats `bam`, `cram` | yes | samplesheet (`sample_id`, `mapped`, `index`, `file_type`) | **Not a `sample_sheet`**: the four columns reduce to the element identifier (`sample_id`), the dataset (`mapped`), the datatype (`file_type`) and the BAM/CRAM index, which Galaxy datasets carry/compute implicitly. No leftover metadata column needs `column_definitions`. The `index` column (optional) is not exposed. Confidence: high. |
| `Reference genome FASTA` | data | `fasta` | optional | `--fasta` | Required in practice for CRAM; see reference-data brief. `--fasta_fai` and `--genome` (iGenomes) are **not** exposed. |
| `Restrict to region (chr)` | parameter | `text`, optional | optional | `--chr` | Region as in the BAM (`chr1`, `chr1:100-200`). Empty = all reads. Maps to samtools view region argument. |
| `Skip read QC` | parameter | `boolean`, default false | optional | `--no_read_QC` | Disables FastQC pre/post conversion. |
| `Skip alignment stats` | parameter | `boolean`, default false | optional | `--no_stats` | Disables flagstat, idxstats, stats (and per the schema text FastQC on input). |
| `Samtools collate fast mode` | parameter | `boolean`, default false | optional | `--samtools_collate_fast` | `collate -f -r <reads_in_memory>`. |
| `Reads in memory (fast collate)` | parameter | `integer`, default 100000 | optional | `--reads_in_memory` | Only used with the fast mode. |

### Params deliberately not exposed
- Runtime/infra: `outdir`, `publish_dir_mode`, `email*`, `plaintext_email`, `max_multiqc_email_size`, `monochrome_logs`, `trace_report_suffix`, `validate_params`, `help*`, `version`, `custom_config_*`, `config_profile_*`, `pipelines_testdata_base_path`, `igenomes_*`, `genome` (runtime control / not meaningful in Galaxy). Recorded in the ledger (`dropped`) only for the user-visible ones: `genome`/iGenomes (already recorded), MultiQC cosmetics below.
- `multiqc_title`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`: MultiQC cosmetics / provenance text. Dropped (ledger entry).

## Workflow outputs (public, stable names)

| Output label | Shape | Producer (source) | Why exposed |
|---|---|---|---|
| `Converted reads (paired-end)` | `list:paired`, `fastqsanger.gz` | `CAT_FASTQ` ← mapped + unmapped collate | Main product. Published to `reads/` in the source (`<id>_1/2.merged.fastq.gz`). Primary test checkpoint (md5 in nf-test snapshot). |
| `Converted reads (single-end)` | `list`, `fastqsanger.gz` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`fastq_other`) | Published to `reads/`. Present only when single-end inputs exist — open question OQ-1. |
| `Flagstat` | `list` of `txt`/tabular | `SAMTOOLS_FLAGSTAT` | Stable text checkpoint (snapshot md5s exist). Optional (`no_stats`). |
| `Idxstats` | `list` of `tabular` | `SAMTOOLS_IDXSTATS` | Stable checkpoint. Optional (`no_stats`). |
| `Stats` | `list` of `txt` | `SAMTOOLS_STATS` | Stable checkpoint. Optional (`no_stats`). |
| `FastQC pre-conversion (HTML)` / `(raw data)` | `list` html / tabular | `FASTQC_PRE_CONVERSION` | QC report; BAM inputs only in the source. Optional (`no_read_QC`). |
| `FastQC post-conversion (HTML)` / `(raw data)` | `list` | `FASTQC_POST_CONVERSION` | QC report. Optional. |
| `FASTQ integrity check (fastq_utils info)` | `list` of `txt` | `FASTQUTILS_INFO` | Stable text checkpoint (md5 in snapshot). |
| `MultiQC report` | `html` | `MULTIQC` | Aggregated QC. Not a stable checkpoint (HTML/versions vary); smoke-check only. |

Not exposed: intermediate BAMs (`SAMTOOLS_VIEW_*`, merged unmapped), `versions.yml`/`pipeline_info`, `CHECKPAIREDEND` marker files, and FASTA/BAM index files.

## Collection-shape decisions
- `Alignments`: one dataset per sample ⇒ `list` (not `paired`; nothing to pair at input).
- Converted paired reads: `list:paired` (forward/reverse), identifiers preserved from the input element identifiers (and, with `chr`, the source appends the region to the id — carried to data-flow).
- Single-end reads: `list` (one-element lists in nf-core are not `paired`).

## Provenance and checkpoints
Test candidates in the summary are nf-test whole-pipeline cases (`default`, `chr`, `cram`, `fai`, `no_bai`, `no_crai`, `no_qc`, `no_stats`, `collate_fast`); the default case (`-profile test`, BAM inputs `test`, `test2`, with `--fasta`) snapshots md5s for the merged FASTQs, flagstat/idxstats/stats and fastq_utils text, plus FastQC/MultiQC file names. Public output names above are chosen so those checkpoints are addressable.

## Open questions
- **OQ-1 (single vs. paired split):** the source routes each sample by a content check (`CHECKPAIREDEND`) into single- or paired-end branches at run time. Galaxy cannot branch collection elements on file content without extra steps. Proposal: decide in the data-flow brief; the minimal-risk option is a paired-end-only conversion with the single-end branch recorded as dropped.
- **OQ-2 (mixed BAM/CRAM in one collection):** allowed by datatype, but FastQC pre-conversion in the source runs only on `bam`. Proposal: keep one collection; document.
- **OQ-3 (`--chr` effect on identifiers):** source renames ids with the region and re-indexes. Proposal: keep ids unchanged in Galaxy unless the data-flow brief finds a cheap way; log if dropped.
