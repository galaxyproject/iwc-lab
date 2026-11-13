# Galaxy Data-Flow Design Brief — nf-core/bamtofastq

## Source Summary Reference

- **Artifact:** `summary-nextflow.json` (`nf-core/bamtofastq` @ `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`)
- **Primary workflow:** `BAMTOFASTQ`
- **Local subworkflows:** `PREPARE_INDICES`, `PRE_CONVERSION_QC`, `ALIGNMENT_TO_FASTQ`
- **Upstream briefs:** `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`

## Workflow Inputs & Outputs Summary

- **Inputs:** `alignments` (`list` of `bam`/`cram`), `fasta` (`fasta`, optional), `chr` (`string`, optional), `no_read_qc` (`boolean`, default `false`), `no_stats` (`boolean`, default `false`), `samtools_collate_fast` (`boolean`, default `false`), `reads_in_memory` (`int`, default `100000`), `multiqc_title` (`string`, optional).
- **Outputs:** `paired_reads` (`list:paired` `fastqsanger.gz`), `single_end_reads` (`list` `fastqsanger.gz`), `fastqutils_info` (`list` `txt`), `samtools_flagstat` (`list` `txt`), `samtools_idxstats` (`list` `tabular`), `samtools_stats` (`list` `txt`), `fastqc_pre_conversion_html` (`list` `html`), `fastqc_pre_conversion_zip` (`list` `zip`), `fastqc_post_conversion_html` (`list` `html`), `fastqc_post_conversion_zip` (`list` `zip`), `multiqc_report` (`data` `html`).

## Subworkflow & Infrastructure Disposition

- **`PREPARE_INDICES` (`SAMTOOLS_INDEX`, `SAMTOOLS_FAIDX`):**
  - `SAMTOOLS_INDEX` (and `SAMTOOLS_CHR_INDEX` after `SAMTOOLS_CHR`) are **subsumed by Galaxy dataset index metadata** (`bam`/`cram` datasets carry `.bai`/`.crai` metadata automatically in Galaxy). Confidence: **High**.
  - `SAMTOOLS_FAIDX` is **deferred to in-tool FASTA indexing** per `nextflow-galaxy-reference-data.md` (`fasta-fai-in-tool-rebuild-unverified` stays open until tool discovery confirms whether chosen wrappers accept `fasta` directly without `.fai`).
- **`PRE_CONVERSION_QC` and `ALIGNMENT_TO_FASTQ`:** Flattened cleanly into the single workflow DAG with explicit grouping/prefix conventions and map-over semantics (`when:` on optional QC stages). No nested Galaxy subworkflow boundary is needed because the workflow has ~17 domain nodes and linear per-branch data flow.

## Abstract Nodes & Tool Needs

| Node ID | Source Process / Alias | Abstract Tool Need | Input Shapes | Output Shapes | Map-Over / Gate | Confidence |
|---|---|---|---|---|---|---|
| `samtools_flagstat` | `SAMTOOLS_FLAGSTAT` | Alignment flag summary (`samtools flagstat`) | `alignments` (`list`) | `list` (`txt`) | Mapped over `alignments`; `when: !no_stats` | High |
| `samtools_idxstats` | `SAMTOOLS_IDXSTATS` | Per-contig alignment counts (`samtools idxstats`) | `alignments` (`list`) | `list` (`tabular`) | Mapped over `alignments`; `when: !no_stats` | High |
| `samtools_stats` | `SAMTOOLS_STATS` | Comprehensive alignment stats (`samtools stats`) | `alignments` (`list`), optional `fasta` (`File`) | `list` (`txt`) | Mapped over `alignments`; `when: !no_stats` | High |
| `filter_bam_inputs` | `PRE_CONVERSION_QC` BAM branch | Filter `alignments` to BAM-only elements (exclude CRAM from FastQC) | `alignments` (`list`) | `bam_alignments` (`list`) | Collection / format filter | Medium |
| `fastqc_pre_conversion` | `FASTQC_PRE_CONVERSION` | Read/alignment QC (`fastqc --quiet`) | `bam_alignments` (`list`) | `html` (`list`), `zip` (`list`) | Mapped over `bam_alignments`; `when: !no_read_qc` | High |
| `samtools_chr` | `SAMTOOLS_CHR` (`SAMTOOLS_VIEW`) | Filter alignments to region `params.chr` (`-hb <chr>`) | `alignments` (`list`), optional `fasta` (`File`), `chr` (`string`) | `list` (`bam`/`cram`) | Mapped over `alignments`; `when: chr` non-empty | High |
| `select_effective_alignments` | `if (params.chr)` merge | `pick_value` (`first_non_null`) selecting filtered or original alignments | `[samtools_chr_out, alignments]` | `effective_alignments` (`list`) | Conditional pass-through (`conditional-transform-or-pass-through`) | Medium |
| `check_paired_end` | `CHECKPAIREDEND` | Inspect alignments with `samtools view` (`-c -f 1` on first ≤1000 reads) to emit non-empty paired vs single indicator | `alignments` (`list`), optional `fasta` (`File`) | `paired_flag` (`list`), `single_flag` (`list`) | Mapped over `alignments` | High |
| `split_paired_single` | `ch_paired_end` / `ch_single_end` + `.branch` | Filter empty flags (`__FILTER_EMPTY__`), extract identifiers, filter `effective_alignments` (`__FILTER_FROM_FILE__`) into paired vs single subcollections | `effective_alignments` (`list`), `paired_flag` (`list`), `single_flag` (`list`) | `paired_alignments` (`list`), `single_alignments` (`list`) | Collection cleanup + identifier sync | Medium |
| `samtools_collatefastq_single` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` | Name-collate and extract single-end reads (`-0`/`fastq_other`, optional `-f -r reads_in_memory`) | `single_alignments` (`list`), optional `fasta` (`File`), `samtools_collate_fast`, `reads_in_memory` | `single_end_reads` (`list` `fastqsanger.gz`) | Mapped over `single_alignments` | Medium |
| `samtools_view_map_map` | `SAMTOOLS_VIEW_MAP_MAP` | Extract mapped+mate-mapped pairs (`-b -f1 -F12`) | `paired_alignments` (`list`), optional `fasta` (`File`) | `list` (`bam`/`cram`) | Mapped over `paired_alignments` | High |
| `samtools_view_unmap_unmap` | `SAMTOOLS_VIEW_UNMAP_UNMAP` | Extract both-unmapped pairs (`-b -f12 -F256`) | `paired_alignments` (`list`), optional `fasta` (`File`) | `list` (`bam`/`cram`) | Mapped over `paired_alignments` | High |
| `samtools_view_unmap_map` | `SAMTOOLS_VIEW_UNMAP_MAP` | Extract read-unmapped/mate-mapped pairs (`-b -f4 -F264`) | `paired_alignments` (`list`), optional `fasta` (`File`) | `list` (`bam`/`cram`) | Mapped over `paired_alignments` | High |
| `samtools_view_map_unmap` | `SAMTOOLS_VIEW_MAP_UNMAP` | Extract read-mapped/mate-unmapped pairs (`-b -f8 -F260`) | `paired_alignments` (`list`), optional `fasta` (`File`) | `list` (`bam`/`cram`) | Mapped over `paired_alignments` | High |
| `samtools_merge_unmap` | `SAMTOOLS_MERGE_UNMAP` | Merge the 3 unmapped alignment sets per sample (`samtools merge`) | `unmap_unmap`, `unmap_map`, `map_unmap` (`list` each, synchronized per sample), optional `fasta` | `merged_unmap` (`list`) | Mapped over 3 aligned `list` inputs (or zipped/merged per-sample `list:list`) | Medium |
| `collate_fastq_map` | `COLLATE_FASTQ_MAP` | Collate & extract paired FASTQ from `map_map` (`-N`, optional `-f -r reads_in_memory`) | `map_map` (`list`), optional `fasta`, `samtools_collate_fast`, `reads_in_memory` | `mapped_paired` (`list:paired` `fastqsanger.gz`) | Mapped over `map_map` | High |
| `collate_fastq_unmap` | `COLLATE_FASTQ_UNMAP` | Collate & extract paired FASTQ from `merged_unmap` (`-N`, optional `-f -r reads_in_memory`) | `merged_unmap` (`list`), optional `fasta`, `samtools_collate_fast`, `reads_in_memory` | `unmapped_paired` (`list:paired` `fastqsanger.gz`) | Mapped over `merged_unmap` | High |
| `cat_paired_fastq` | `CAT_FASTQ` | Concatenate `mapped_R1 + unmapped_R1` and `mapped_R2 + unmapped_R2` preserving `fastqsanger.gz` and sample IDs | `mapped_paired` (`list:paired`), `unmapped_paired` (`list:paired`) | `paired_reads` (`list:paired` `fastqsanger.gz`) | Mapped over pairs (or unzip -> concat R1s & R2s -> re-zip) | Medium |
| `prepare_post_qc_reads` | `ch_reads_post_qc` (`mix`) | Flatten `paired_reads` (`list:paired` -> `list`) and merge with `single_end_reads` (`list`) for FastQC | `paired_reads` (`list:paired`), `single_end_reads` (`list`) | `all_post_qc_reads` (`list`) | `__FLATTEN__` + `__MERGE_COLLECTION__` | Medium |
| `fastqc_post_conversion` | `FASTQC_POST_CONVERSION` | Read QC on converted FASTQs (`fastqc --quiet`) | `all_post_qc_reads` (`list`) | `html` (`list`), `zip` (`list`) | Mapped over `all_post_qc_reads`; `when: !no_read_qc` | High |
| `fastqutils_info` | `FASTQUTILS_INFO` | Validate FASTQ integrity/pairing (`fastq_info`) and emit verification text report | `paired_reads` (`list:paired`) + `single_end_reads` (`list`) | `fastqutils_info` (`list` `txt`) | Mapped per sample (paired branch + single branch merged) | Medium |
| `multiqc` | `MULTIQC` | Aggregate QC reports into MultiQC HTML | `samtools_flagstat`, `samtools_idxstats`, `samtools_stats`, `fastqc_pre_conversion_zip`, `fastqc_post_conversion_zip`, optional `multiqc_title` | `multiqc_report` (`File` `html`) | Reduction over QC collections; `when: !(no_read_qc && no_stats)` | Medium |

## Nextflow Operator Translation Table

| Source Operator / Pattern | Target Galaxy Mechanism | Class | Confidence | Notes |
|---|---|---|---|---|
| `samplesheetToList` -> `ch_samplesheet` | `alignments` (`list` collection) | Collection semantics | High | Sample IDs are collection element identifiers; map-over preserves identifiers end-to-end. |
| `PREPARE_INDICES` (`is_indexed` / `to_index`) | Galaxy dataset index metadata | Channel-only / subsumed | High | Galaxy manages `.bai`/`.crai` as dataset metadata. |
| `PRE_CONVERSION_QC` `.branch { bam / cram }` | Filter `alignments` to BAM datasets before `FASTQC_PRE_CONVERSION` | Explicit Galaxy step | Medium | FastQC cannot consume CRAM; CRAM elements must not enter `FASTQC_PRE_CONVERSION`. |
| `if (params.chr) { SAMTOOLS_CHR ... }` | Inline `when:` on `samtools_chr` + `pick_value` (`first_non_null`) | Conditional pattern | Medium | Single-step transform-or-pass-through; verify `pick_value` over `list` collections in validation/testing. |
| `CHECKPAIREDEND` + `.join` + `.branch` | Per-element classification + `__FILTER_EMPTY__` + identifier extraction + `__FILTER_FROM_FILE__` | Explicit Galaxy steps | Medium | Splits `effective_alignments` into non-empty `paired_alignments` and `single_alignments` without leaving `null` slots in `paired_reads`. |
| `all_unmapped_bam = join(..., remainder: true)` | Synchronized 3-way collection input (`list:list` via `__BUILD_LIST__` or 3-input map-over) | Collection semantics + explicit step | Medium | All 3 `SAMTOOLS_VIEW_*` steps map over identical `paired_alignments` identifiers (each emits a BAM/CRAM, possibly with 0 reads, so identifiers stay aligned). |
| `COLLATE_FASTQ_MAP` + `COLLATE_FASTQ_UNMAP` -> `CAT_FASTQ` | Map `samtools_collatefastq` -> `list:paired`; unzip/concat/rezip (or paired concat tool) | Collection semantics + explicit step | Medium | Preserves `fastqsanger.gz` byte concatenation semantics (`cat R1_map R1_unmap > R1_merged.fastq.gz`). |
| `ch_reads_post_qc = mix(single, paired)` | `__FLATTEN__` (`paired_reads`) + `__MERGE_COLLECTION__` with `single_end_reads` for FastQC; separate paired/single `fastq_info` merged into `fastqutils_info` | Explicit Galaxy steps | Medium | Preserves `fastq_info R1 R2` paired validation semantics for paired-end samples (matching `default.nf.test.snap` 1 `.txt` per sample) while supporting single-end samples too. |
| `topic: versions` -> `softwareVersionsToYAML` -> `MULTIQC` | Wire actual QC collections (`samtools_*`, `fastqc_*_zip`) to `MULTIQC` | Explicit Galaxy reduction | Medium | In `nf-core/bamtofastq` (`aa0150e`), `PRE_CONVERSION_QC` and `FASTQC_POST_CONVERSION` were left disconnected from `ch_multiqc_files` (commented out); wiring them in Galaxy makes MultiQC meaningful while keeping optional-branch safety. |

## Open Questions & Risks Carried Forward

1. **`pick_value` over mapped `list` collections (`chr` branch):** Verify in template/testing whether Galaxy `pick_value` (`first_non_null`) accepts a skipped mapped `list` collection and a non-skipped `list` collection (`alignments`), or whether `__PICK_VALUE__` / conditional routing behaves differently on collections vs single datasets.
2. **Empty collection map-over (`single_alignments` when all samples are paired-end, or vice versa):** Verify whether mapping `samtools_collatefastq_single`, `fastqutils_info`, and `__MERGE_COLLECTION__` over an empty `list` (`0` elements) executes cleanly in Galaxy without error.
3. **BAM vs CRAM filtering for `FASTQC_PRE_CONVERSION`:** In `default.nf.test`, all inputs are BAM, whereas `cram.nf.test` uses CRAM; during implementation, ensure CRAM elements are excluded from `FASTQC_PRE_CONVERSION`.
4. **MultiQC with partial QC skipped (`no_stats` or `no_read_qc`):** Ensure `multiqc` input connections tolerate skipped (`NO_REPLACEMENT`) upstream collections when only one of FastQC or Samtools stats is enabled.
5. **Element identifiers in `default.nf.test`:** From `tests/default.nf.test.snap`, the two sample IDs are `test` and `test2` (unique per sample), giving `test` and `test2` in `paired_reads` (`forward`/`reverse`), `fastqutils_info`, `samtools_flagstat`, `samtools_idxstats`, and `samtools_stats`.
