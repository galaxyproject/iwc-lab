# Galaxy data-flow brief — nf-core/bamtofastq

## Design commitments

Preserve the complete scientific path from `BAMTOFASTQ`, `PREPARE_INDICES`, `PRE_CONVERSION_QC`, and `ALIGNMENT_TO_FASTQ`. Do not reduce the workflow to a single generic `samtools fastq`: the source deliberately separates mapped/unmapped flag classes, converts mapped and unmapped paired reads separately, and concatenates corresponding mates.

Use `sample_id` as the unique key for default nf-test rows (`test`, `test2`) and all intermediate collections. The source permits arbitrary unique sample identifiers, not positional pairing. `mapped`/`index` are record slots, not mates; `_1`/`_2` suffixes are mates only in FASTQ outputs.

Indices are rebuilt in **workflow-tier fan-out steps** rather than in every consumer. Alignment indices feed QC and up to five view/filter paths, and FAI is shared across classification, filtering, stats, merge, and collate operations. This is the repeated-use exception to the earlier in-tool-rebuild preference, not an assumption that wrappers can rebuild.

## Abstract topology

### 1. Input projection and index preparation

| Node | Operation and shape | Inputs → outputs | Galaxy idiom / tool need | Confidence |
|---|---|---|---|---|
| `project_alignment_samples` | Split each sample record into synchronized mapped/index views while retaining `sample_id` and `file_type` | `sample_sheet:record` → keyed BAM/CRAM list and optional BAI/CRAI list | Record-slot projection plus keyed synchronization; do not infer pairing from order | High for shape; implementation recipe open |
| `classify_index_presence` | Per-row branch on supplied index | Optional index list → booleans | Per-element conditional metadata | High |
| `build_alignment_indices` | `samtools index` only for rows lacking BAI/CRAI | BAM/CRAM list → BAI/CRAI list | Mapped per-element conditional step | High |
| `select_alignment_indices` | Choose supplied or rebuilt index per row | Both index lists → one keyed index list | `pick_value`-style alternative fan-in, not concatenation | High |
| `build_reference_fai` | `samtools faidx FASTA` when FASTA exists and FAI is absent | One FASTA → one FAI | Inline `when` gate | High |
| `select_reference_fai` | Choose supplied or rebuilt FAI | Two alternatives → one shared FAI | `pick_value`; FASTA/FAI broadcast to consumers | High |

Any CRAM consumer receives the matched FASTA and selected FAI. A missing-reference error must be explicit for CRAM. Purely BAM runs retain empty-reference semantics.

### 2. Pre-conversion QC

Run each node over the keyed alignment+index views:

- `pre_conversion_flagstat`: `samtools flagstat`, gated by `!skip_alignment_stats`; output list of `*.flagstat`.
- `pre_conversion_idxstats`: `samtools idxstats`, gated by `!skip_alignment_stats`; output list of `*.idxstats`.
- `pre_conversion_stats`: `samtools stats`, gated by `!skip_alignment_stats`; broadcast FASTA/FAI where needed; output list of `*.stats`.
- `filter_bam_for_precqc`: retain only rows whose source `file_type == bam`; preserve `sample_id`. CRAM rows are intentionally excluded by the source.
- `pre_conversion_fastqc`: FastQC over the filtered BAM list, gated by `!skip_read_qc`; outputs synchronized HTML and ZIP lists.

The first three are independent mapped steps. The FastQC branch needs an explicit datatype filter, not a tool failure on CRAM. Every optional branch uses inline `when`; no subworkflow adds useful cohesion beyond the source's small QC grouping.

### 3. Pairing classification and optional chromosome/region filter

| Node | Semantics | Tool need / collection behavior |
|---|---|---|
| `classify_paired_end` | Inspect alignment flags with the source `CHECKPAIREDEND` logic, using reference arguments for CRAM | Custom/local tool or discovered equivalent producing per-sample paired/single classification and marker text |
| `filter_chromosome` | Optional `samtools view -hb <alignment> <chr>` on every sample | Inline `when` on non-empty `chromosome`; mapped BAM/CRAM output preserving type |
| `index_chromosome_alignment` | Index each filtered alignment | Mapped `samtools index`, same gate |
| `select_conversion_alignment` | Use filtered alignment+index when chromosome was supplied, otherwise original | `pick_value` alternative fan-in keyed by `sample_id`; no duplicated downstream conversion tree |
| `route_by_pairing` | Split paired and unpaired samples using `classify_paired_end` | Identifier-preserving filters plus branch wiring; marker text is not passed as FASTQ |

### 4. Single-end conversion

Map `single_end_collatefastq` over the single-end branch:

- Run `samtools collate -O` piped to `samtools fastq -N` with reference arguments for CRAM and optional fast-collate `-f -r reads_in_memory`.
- Retain the source's published `fastq_other` stream as the final single-end reads, matching the source's explicit post-conversion wiring. Do not substitute the singleton stream.
- Shape: one keyed FASTQ.GZ dataset per sample.

### 5. Paired-end conversion

Map the following over each paired sample, broadcasting FASTA/FAI as needed:

| Node | Exact source behavior | Output |
|---|---|---|
| `view_mapped_mapped` | `samtools view -b -f1 -F12` | mapped/mapped BAM or CRAM |
| `view_unmapped_unmapped` | `samtools view -b -f12 -F256` | unmapped/unmapped BAM or CRAM |
| `view_unmapped_mapped` | `samtools view -b -f4 -F264` | unmapped/mapped BAM or CRAM |
| `view_mapped_unmapped` | `samtools view -b -f8 -F260` | mapped/unmapped BAM or CRAM |
| `merge_unmapped` | Merge the three unmapped classes by keyed dot-product; preserve BAM/CRAM type | One merged unmapped alignment per sample |
| `collate_mapped` | `samtools collate -O | samtools fastq -N`; optional fast mode | Keyed mapped R1/R2 |
| `collate_unmapped` | Same operation on merged unmapped alignment | Keyed unmapped R1/R2 |
| `join_paired_conversion` | Join mapped and unmapped mate collections by `sample_id`; map-over pairs, never positional union | Four FASTQ files per sample in mapped-R1, mapped-R2, unmapped-R1, unmapped-R2 semantics |
| `concatenate_mates` | `cat fastq` mapped+unmapped separately for R1 and R2 | Final merged R1/R2 per sample |
| `pair_converted_reads` | Zip final R1/R2 into `paired` elements | Keyed `list:paired` |

The three-way unmapped join is keyed and remainder-tolerant in source. Empty classes remain valid inputs to merge; do not interpret absent classes as missing samples. The paired stream and single stream are mutually exclusive per sample. Fan them into one `paired_or_unpaired` collection without duplicating identifiers, or expose separate paired/single collections if the concrete Galaxy collection tools cannot safely construct the mixed type.

### 6. Post-conversion validation

- `post_conversion_fastqc`: mapped FastQC over every converted read element, gated by `!skip_read_qc`; HTML and ZIP outputs follow the converted sample/read identifiers.
- `validate_fastq`: mapped `fastq_info` over converted reads; its text report is unconditional in the source and is a stable content checkpoint.
- Any required flattening preserves whether the source was single or paired and keeps mate identity explicit.

### 7. Aggregation

- `aggregate_versions`: collect version records from every executed tool and emit one YAML `software_versions` dataset. Exact producer unresolved.
- `collect_multiqc_inputs`: collect all non-skipped FastQC, samtools statistics, fastq validation and version/config/summary inputs; skip values are not converted into fake reports.
- `multiqc`: one reduction over the collected inputs using optional config, title, logo and methods description; outputs HTML report and the tool's data directory/archive.
- `methods_description`: use the supplied dataset or the pipeline-equivalent default content if supported; do not silently claim Nextflow template function behavior without a producer.

## Shape and conditional recipes

- **Map-over:** all per-sample index, QC, classification, view, merge, collate, FastQC and validation operations.
- **Reduction:** one MultiQC invocation and one version manifest, not one per sample.
- **Keyed joins:** alignment+index; mapped+unmapped FASTQ; three unmapped classes; supplied/rebuilt index alternatives.
- **Conditional fan-in:** original/filtered conversion alignment and supplied/built indices use `pick_value` semantics, never a generic merge that duplicates data.
- **Optional outputs:** skipped QC/stat branches produce no asserted content. Downstream MultiQC tolerates skipped inputs by filtering them before reduction.
- **Mixed reads:** preserve single/paired structure through final assembly; only collapse to a flat list for tools that explicitly require it, then restore mate structure.

## Abstract tool needs

1. BAM/CRAM indexing, FASTA indexing, view/filter, flagstat, idxstats, stats, merge, collate+fastq (matching samtools 1.23.1 behavior).
2. FastQC 0.12.1-compatible HTML+ZIP generation on BAM and FASTQ.
3. CHECKPAIREDEND equivalent using samtools flag inspection.
4. CAT_FASTQ equivalent preserving mate order and gzip output.
5. fastq_info 0.25.3-compatible validation and text report.
6. MultiQC report+data output, aggregation and report customization.
7. Version manifest aggregation and any record projection/keyed collection reshaping the template cannot express by wiring alone.

## Open handoff points

- Exact Galaxy representation of sample-record slots and `paired_or_unpaired` output assembly.
- Extraction/filtering by `file_type` and per-sample pairing classification without positional mismatches.
- Concrete version and MultiQC data producers.
- CRAM-without-FASTA validation and fixture coverage for supplied versus rebuilt FAI.
- Default nf-test covers paired BAM samples; additional source candidates cover CRAM, missing indices, chromosome filtering, fast collate and skip flags. Their implementation should not be assumed tested by the default case alone.
