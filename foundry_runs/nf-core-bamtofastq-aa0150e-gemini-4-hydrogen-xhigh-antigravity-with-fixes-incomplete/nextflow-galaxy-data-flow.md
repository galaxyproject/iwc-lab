# Galaxy Data-Flow Design Brief: nf-core/bamtofastq

- **`source_summary_ref`**: `summary-nextflow.json` (`nf-core/bamtofastq`, commit `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`), paired with `nextflow-galaxy-reference-data.md` and `nextflow-galaxy-interface.md`.

## 1. Workflow Inputs & Outputs

### `workflow_inputs`
- `input_alignments`: `collection` (`list`, elements `bam` or `cram`; element identifier = `sample_id`).
- `reference_fasta`: optional `data` (`fasta`).
- `chr`: optional `string` (default `null`; region filter passed to `samtools view`).
- `no_read_qc`: `boolean` (default `false`).
- `no_stats`: `boolean` (default `false`).
- `samtools_collate_fast`: `boolean` (default `false`).
- `reads_in_memory`: `int` (default `100000`).

### `workflow_outputs`
- `paired_reads`: `collection` (`list:paired`, `fastqsanger.gz`): merged forward/reverse reads from `ALIGNMENT_TO_FASTQ` (`CAT_FASTQ`).
- `single_end_reads`: `collection` (`list`, `fastqsanger.gz`): single-end reads (`samtools fastq -0`) from `SAMTOOLS_COLLATEFASTQ_SINGLE_END`.
- `fastq_info_reports`: `collection` (`list`, `txt`): combined per-sample validation logs from `FASTQUTILS_INFO`.
- `samtools_flagstat`: `collection` (`list`, `txt`): pre-conversion `samtools flagstat` (`!no_stats`).
- `samtools_idxstats`: `collection` (`list`, `tabular`): pre-conversion `samtools idxstats` (`!no_stats`).
- `samtools_stats`: `collection` (`list`, `txt`): pre-conversion `samtools stats` (`!no_stats`).
- `fastqc_pre_html`: `collection` (`list`, `html`): pre-conversion FastQC HTML on BAM elements (`!no_read_qc`).
- `fastqc_pre_data`: `collection` (`list`, `zip`): pre-conversion FastQC ZIP archives on BAM elements (`!no_read_qc`).
- `fastqc_post_html`: `collection` (`list`, `html`): post-conversion FastQC HTML across flattened paired + single-end reads (`!no_read_qc`).
- `fastqc_post_data`: `collection` (`list`, `zip`): post-conversion FastQC ZIP archives across flattened paired + single-end reads (`!no_read_qc`).
- `multiqc_report`: `data` (`html`): aggregated MultiQC HTML report (`!(no_stats && no_read_qc)`).

## 2. Structural Decisions: Subworkflow vs Inline `when:`, Indexing, and Branching

1. **Absorbed Nextflow Processes (`PREPARE_INDICES`, `SAMTOOLS_CHR_INDEX`)**:
   - `SAMTOOLS_INDEX` and `SAMTOOLS_FAIDX` in `PREPARE_INDICES`, plus `SAMTOOLS_CHR_INDEX`, are omitted as explicit workflow nodes in v1 because Galaxy generates `bam_index`, `cram_index`, and `fasta_fai` dataset metadata natively (carrying `reference-fasta-fai-rebuild-unverified` forward to Phase 7 tool inspection).
2. **Inline `when:` over Galaxy Subworkflows**:
   - `chr` filtering (`SAMTOOLS_CHR` + `pick_value`): single tool step; fits `conditional-transform-or-pass-through` directly.
   - `!no_stats` (`SAMTOOLS_FLAGSTAT`, `SAMTOOLS_IDXSTATS`, `SAMTOOLS_STATS`): three independent leaf QC tools; inline `when: $(!inputs.no_stats)` avoids subworkflow boundary wiring (`conditional-run-optional-step`).
   - `!no_read_qc` (`FASTQC_PRE_CONVERSION`, `FASTQC_POST_CONVERSION`): two leaf QC steps separated across the graph; inline `when: $(!inputs.no_read_qc)`.
   - `ALIGNMENT_TO_FASTQ`: kept as a flat labeled stage in the main top-level workflow (`workflow_comments` grouping) rather than a nested subworkflow, keeping all tool steps and `pick_value` merges directly inspectable in a single `.gxwf.yml`.
3. **Per-sample Single-End vs Paired-End Routing (`CHECKPAIREDEND`)**:
   - Because one `input_alignments` collection can contain mixed single-end and paired-end samples concurrently (and Galaxy maps per element rather than splitting channels via Groovy `.branch`/`.join`), `CHECKPAIREDEND` emits two per-sample marker outputs (`paired_marker`: non-empty iff paired; `single_marker`: non-empty iff single).
   - Built-in empty-dataset filtering (`__FILTER_EMPTY_DATASETS__`) followed by identifier synchronization (`sync-collections-by-identifier`) partitions `active_alignments` into `paired_alignments` (`list`) and `single_alignments` (`list`).
   - Either partition may safely contain 0 elements when all inputs belong to the opposite library layout.
4. **Upstream `MULTIQC` Discrepancy**:
   - Upstream `workflows/bamtofastq.nf` leaves `ALIGNMENT_TO_FASTQ.out.zip` commented out and omits `PRE_CONVERSION_QC` / `FASTQC_POST_CONVERSION` from `ch_multiqc_files`, feeding only nf-core boilerplate YAMLs (`versions`, `workflow_summary`, `methods_description`).
   - In Galaxy, boilerplate YAMLs are omitted; instead `MULTIQC` should aggregate the real QC outputs produced (`samtools_flagstat`, `samtools_idxstats`, `samtools_stats`, `fastqc_pre_data`, `fastqc_post_data`) guarded by `when: $(!(inputs.no_stats && inputs.no_read_qc))`, while Phase 7 verifies how Galaxy MultiQC handles partially skipped repeat inputs when only one of `no_stats` or `no_read_qc` is set (`multiqc-partial-skip-safety`).

## 3. Abstract Nodes (`nodes`)

| Node ID | Stage | Abstract Operation | Conditional / Trigger | Tool Need Summary | Confidence | Rationale |
|---|---|---|---|---|---|---|
| `n_idxstats` | Pre-QC | Run `samtools idxstats` per alignment | Inline `when: !no_stats` | `samtools idxstats` wrapper | High | Direct 1:1 map-over on `input_alignments`. |
| `n_flagstat` | Pre-QC | Run `samtools flagstat` per alignment | Inline `when: !no_stats` | `samtools flagstat` wrapper | High | Direct 1:1 map-over on `input_alignments`. |
| `n_stats` | Pre-QC | Run `samtools stats` (with optional `reference_fasta`) | Inline `when: !no_stats` | `samtools stats` wrapper | High | Verify `reference_fasta` optionality for BAM vs CRAM in Phase 7. |
| `n_filter_bam` | Pre-QC | Filter `input_alignments` keeping only `bam` elements (`skip cram`) | Conditional on `!no_read_qc` | Collection datatype/extension filter placeholder | Medium | Upstream skips CRAM for `FASTQC_PRE_CONVERSION`; Galaxy FastQC rejects CRAM. |
| `n_fastqc_pre` | Pre-QC | Run FastQC (`--quiet`) on BAM-only inputs | Inline `when: !no_read_qc` | `fastqc` wrapper | High | 1:1 map-over filtered BAM list. |
| `n_check_paired` | Split | Run `samtools view` on up to 1000 records, compare `-c -f 1` to line count; emit non-empty `paired_marker` or `single_marker` | Always | Local script (`CHECKPAIREDEND` UDT or equivalent) | High | Exact parity with `modules/local/checkpairedend/main.nf` (`0x1` flag check). |
| `n_samtools_chr` | Region Filter | Subset alignments to `chr` (`samtools view -hb <in> <chr>`) | Inline `when: chr non-empty` | `samtools view` region filter | High | Matches `SAMTOOLS_CHR`; Galaxy BAM metadata absorbs `SAMTOOLS_CHR_INDEX`. |
| `n_pick_active` | Region Filter | Select `n_samtools_chr` output if run, else fallback `input_alignments` | Always (`pick_value`) | Galaxy `pick_value` (`first_non_null`) | High | Standard `conditional-transform-or-pass-through`. Verify mapped collection behavior in Galaxy. |
| `n_keep_paired_ids` | Split | Drop empty datasets from `paired_marker` | Always | Built-in `__FILTER_EMPTY_DATASETS__` | High | Removes non-paired elements without failing jobs. |
| `n_keep_single_ids` | Split | Drop empty datasets from `single_marker` | Always | Built-in `__FILTER_EMPTY_DATASETS__` | High | Removes paired elements without failing jobs. |
| `n_sync_paired` | Split | Keep elements in `active_alignments` matching `n_keep_paired_ids` | Always | Built-in `sync-collections-by-identifier` | High | Yields `paired_alignments` (`list`). |
| `n_sync_single` | Split | Keep elements in `active_alignments` matching `n_keep_single_ids` | Always | Built-in `sync-collections-by-identifier` | High | Yields `single_alignments` (`list`). |
| `n_se_collate_fastq` | Single-End | `samtools collate [-f -r N] -O \| samtools fastq -N -0 <out>.fq.gz` on `single_alignments` | Mapped (0 jobs if empty) | `samtools collate` + `samtools fastq` (`-0`) wrapper/UDT | High | Extracts `-0` single-end FASTQ reads (`fastq_other` output). |
| `n_pe_view_map_map` | Paired-End | `samtools view -b -f1 -F12` (optional `reference_fasta`) | Mapped (0 jobs if empty) | `samtools view` flag filter | High | Both reads mapped paired subset -> BAM. |
| `n_pe_view_map_unmap` | Paired-End | `samtools view -b -f8 -F260` (optional `reference_fasta`) | Mapped (0 jobs if empty) | `samtools view` flag filter | High | Read mapped, mate unmapped -> BAM. |
| `n_pe_view_unmap_map` | Paired-End | `samtools view -b -f4 -F264` (optional `reference_fasta`) | Mapped (0 jobs if empty) | `samtools view` flag filter | High | Read unmapped, mate mapped -> BAM. |
| `n_pe_view_unmap_unmap` | Paired-End | `samtools view -b -f12 -F256` (optional `reference_fasta`) | Mapped (0 jobs if empty) | `samtools view` flag filter | High | Both mates unmapped -> BAM. |
| `n_pe_merge_unmap` | Paired-End | `samtools merge` across `[map_unmap, unmap_map, unmap_unmap]` per sample | Mapped | `samtools merge` wrapper | High | Combines all unmapped/half-mapped BAM subsets per sample. |
| `n_pe_collate_map` | Paired-End | `samtools collate [-f -r N] -O \| samtools fastq -N -1 -2` on `map_map` | Mapped | `samtools collate` + `samtools fastq` (`-1/-2`) wrapper/UDT | High | Emits paired FASTQ (`list:paired`). |
| `n_pe_collate_unmap` | Paired-End | `samtools collate [-f -r N] -O \| samtools fastq -N -1 -2` on `merged_unmap` | Mapped | `samtools collate` + `samtools fastq` (`-1/-2`) wrapper/UDT | High | Emits paired FASTQ (`list:paired`). |
| `n_pe_unzip_map` | Paired-End | Unzip `list:paired` (`map`) into `forward` (`list`) & `reverse` (`list`) | Always | Built-in `__UNZIP_COLLECTION__` | High | Separates R1 and R2 streams per sample. |
| `n_pe_unzip_unmap` | Paired-End | Unzip `list:paired` (`unmap`) into `forward` (`list`) & `reverse` (`list`) | Always | Built-in `__UNZIP_COLLECTION__` | High | Separates R1 and R2 streams per sample. |
| `n_pe_cat_r1` | Paired-End | Concatenate `[map_R1, unmap_R1]` per sample into merged `fastqsanger.gz` | Mapped | Dataset concatenation (`cat` preserving `.fastqsanger.gz`) | Medium | Exact `CAT_FASTQ` parity for R1; check gzip handling in wrapper discovery. |
| `n_pe_cat_r2` | Paired-End | Concatenate `[map_R2, unmap_R2]` per sample into merged `fastqsanger.gz` | Mapped | Dataset concatenation (`cat` preserving `.fastqsanger.gz`) | Medium | Exact `CAT_FASTQ` parity for R2; check gzip handling in wrapper discovery. |
| `n_pe_zip_reads` | Paired-End | Re-pair `[merged_R1, merged_R2]` -> `paired_reads` (`list:paired`) | Always | Built-in `__ZIP_COLLECTION__` | High | Restores `list:paired` collection keyed by `sample_id`. |
| `n_fastqutils_paired` | Post-QC | Run `fastq_info <R1.fq.gz> <R2.fq.gz>` per pair in `paired_reads` | Mapped (0 jobs if empty) | `fastq_utils` (`fastq_info`) wrapper/UDT | High | Paired mate validation matches `FASTQUTILS_INFO` `[R1, R2]` CLI. |
| `n_fastqutils_single` | Post-QC | Run `fastq_info <reads.fq.gz>` per element in `single_end_reads` | Mapped (0 jobs if empty) | `fastq_utils` (`fastq_info`) wrapper/UDT | High | Single-end validation matches `FASTQUTILS_INFO`. |
| `n_merge_fastqinfo` | Post-QC | Merge `[fastqutils_paired, fastqutils_single]` -> `fastq_info_reports` (`list`) | Always | Built-in `__MERGE_COLLECTION__` | High | Combines disjoint paired & single sample reports into one `list`. |
| `n_flatten_paired` | Post-QC | Flatten `paired_reads` (`list:paired` -> `list` of `*_forward`, `*_reverse`) | Conditional/Pre-FastQC | Built-in `__FLATTEN__` | High | Prepares paired FASTQs for FastQC aggregation alongside single-end reads. |
| `n_merge_post_reads` | Post-QC | Merge `[flattened_paired_reads, single_end_reads]` -> `post_qc_reads` (`list`) | Always | Built-in `__MERGE_COLLECTION__` | High | Feeds unified FASTQ list to `FASTQC_POST_CONVERSION`. |
| `n_fastqc_post` | Post-QC | Run FastQC (`--quiet`) on `post_qc_reads` | Inline `when: !no_read_qc` | `fastqc` wrapper | High | Emits `fastqc_post_html` & `fastqc_post_data`. |
| `n_multiqc` | Reporting | Aggregate QC/stats archives into `multiqc_report` | Inline `when: !(no_stats && no_read_qc)` | `multiqc` wrapper | Medium | Verify optional/skipped repeat input behavior when one of `no_stats` / `no_read_qc` is true. |

## 4. Data Edges & Shape Transitions (`edges`)

| Producer -> Consumer | Shape Before | Shape After | Idiom / Recipe | Source Evidence | Confidence |
|---|---|---|---|---|---|
| `input_alignments` -> `n_idxstats`, `n_flagstat`, `n_stats` | `list[bam\|cram]` | `list[tabular\|txt]` | Implicit map-over + `when: !no_stats` | `PRE_CONVERSION_QC` (`workflows/bamtofastq.nf`) | High |
| `input_alignments` -> `n_filter_bam` -> `n_fastqc_pre` | `list[bam\|cram]` | `list[bam]` -> `list[html]`, `list[zip]` | Collection datatype filter (`bam` only) + implicit map-over + `when: !no_read_qc` | `PRE_CONVERSION_QC` `.filter { filetype == 'bam' }` | Medium |
| `input_alignments` (+ optional `reference_fasta`) -> `n_samtools_chr` -> `n_pick_active` | `list[bam\|cram]` | `list[bam\|cram]` (`bam` if filtered) | `conditional-transform-or-pass-through` (`when:` + `pick_value`) | `workflows/bamtofastq.nf` `if (params.chr)` + `SAMTOOLS_CHR` | High |
| `input_alignments` (+ optional `reference_fasta`) -> `n_check_paired` -> `n_keep_*_ids` -> `n_sync_*` (`active_alignments`) | `list[bam\|cram]` | `paired_alignments` (`list`) + `single_alignments` (`list`) | `sync-collections-by-identifier` (`__FILTER_EMPTY_DATASETS__` + identifier sync replacing Groovy `.join` + `.branch`) | `CHECKPAIREDEND` + `.join` + `.branch` | High |
| `single_alignments` (+ optional `reference_fasta`, `samtools_collate_fast`, `reads_in_memory`) -> `n_se_collate_fastq` | `list[bam\|cram]` | `single_end_reads` (`list[fastqsanger.gz]`) | Implicit map-over (`-0` single-end stream) | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`fastq_other`) | High |
| `paired_alignments` (+ optional `reference_fasta`) -> 4x `n_pe_view_*` -> `n_pe_merge_unmap` | `list[bam\|cram]` | 4x `list[bam]` -> `merged_unmap` (`list[bam]`) | Implicit map-over + 3-way collection bundle (`[map_unmap, unmap_map, unmap_unmap]`) replacing `.join(..., remainder: true)` | `ALIGNMENT_TO_FASTQ` (`SAMTOOLS_VIEW_*` + `SAMTOOLS_MERGE_UNMAP`) | High |
| `n_pe_view_map_map`, `n_pe_merge_unmap` -> `n_pe_collate_map`, `n_pe_collate_unmap` | `list[bam]` | `list:paired[fastqsanger.gz]` | Implicit map-over (`samtools collate \| samtools fastq -1 -2`) | `COLLATE_FASTQ_MAP`, `COLLATE_FASTQ_UNMAP` | High |
| `n_pe_collate_*` -> `n_pe_unzip_*` -> `n_pe_cat_r{1,2}` -> `n_pe_zip_reads` | `list:paired` + `list:paired` | `paired_reads` (`list:paired[fastqsanger.gz]`) | `__UNZIP_COLLECTION__` -> mapped pair concat -> `__ZIP_COLLECTION__` replacing Groovy `join` + `eachWithIndex` | `CAT_FASTQ` in `ALIGNMENT_TO_FASTQ` | Medium |
| `paired_reads`, `single_end_reads` -> `n_fastqutils_{paired,single}` -> `n_merge_fastqinfo` | `list:paired`, `list` | `fastq_info_reports` (`list[txt]`) | Paired vs flat consumption + `__MERGE_COLLECTION__` replacing `.mix` | `FASTQUTILS_INFO` on `ch_reads_post_qc` | High |
| `paired_reads` -> `n_flatten_paired` + `single_end_reads` -> `n_merge_post_reads` -> `n_fastqc_post` | `list:paired`, `list` | `list[fastqsanger.gz]` -> `list[html]`, `list[zip]` | `__FLATTEN__` + `__MERGE_COLLECTION__` + implicit map-over + `when: !no_read_qc` | `FASTQC_POST_CONVERSION` on `ch_reads_post_qc` | High |
| `{n_idxstats, n_flagstat, n_stats, n_fastqc_pre, n_fastqc_post}` -> `n_multiqc` | Multiple `list[txt\|tabular\|zip]` | `multiqc_report` (`html`) | Multi-branch report reduction + `when: !(no_stats && no_read_qc)` | Galaxy QC aggregation (diverges from unwired upstream `MULTIQC`) | Medium |

## 5. Placeholder Transformations & Unresolved Tool Needs

### `placeholder_transformations`
1. **`n_filter_bam` (BAM-only collection filter)**: Keep only elements in `input_alignments` whose dataset datatype is `bam` (skipping `cram`) prior to `FASTQC_PRE_CONVERSION`. If no built-in Galaxy collection tool filters cleanly by datatype without failing on `cram`, consider an expression tool, lightweight UDT filter, or datatype-checking shim in Phase 6/7.
2. **`n_sync_paired` & `n_sync_single` (identifier synchronization)**: Sync `active_alignments` to surviving non-empty `paired_marker` and `single_marker` identifiers (`__FILTER_FROM_FILE__` or corpus-observed `sync-collections-by-identifier` recipe).
3. **`n_pe_cat_r1` & `n_pe_cat_r2` (gzip-safe FASTQ pair concatenation)**: Concatenate `(mapped_mate, unmapped_mate)` into `fastqsanger.gz` without corrupting compression headers or dropping `.gz` datatype.

### `unresolved_tool_needs`
- `samtools` tools: `samtools_idxstats`, `samtools_flagstat`, `samtools_stats`, `samtools_view` (region filtering + SAM flag filtering), `samtools_merge` (check Tool Shed `iuc` wrappers & whether `fasta` works without `fasta_fai` and whether BAM/CRAM mixed `list` works cleanly).
- `samtools_collate_fastq`: combined `samtools collate ... -O | samtools fastq -N ...` (check if Tool Shed `samtools_fastx` / `samtools` wrapper supports `collate` + `fastq -N -0` / `-1 -2`, or needs a user-defined tool YAML via `author-galaxy-tool-wrapper`!). Likely UDT or inspect IUC `samtools_fastx`!
- `checkpairedend`: local script (`samtools view` first 1000 lines, `-c -f 1`, emitting non-empty `paired` / `single` markers) -> strong candidate for `author-galaxy-tool-wrapper` (UDT).
- `fastqutils_info`: `fastq_utils` (`fastq_info` CLI v0.25.3) -> check Tool Shed, else UDT (`author-galaxy-tool-wrapper`).
- `fastqc` & `multiqc` & gzip-safe `concatenate`: check IUC wrappers (`fastqc`, `multiqc`, `cat1` / `concatenate_datasets`).

## 6. Handoff Notes & Carried Open Questions

- **To `compare-against-iwc-exemplar` & Template**: Check IWC exemplars using `sync-collections-by-identifier`, `samtools` suites, `fastqc` + `multiqc`, and `pick_value` over mapped collections.
- **Open questions carried in `open-requirements.ledger.yml`**:
  1. `reference-fasta-fai-rebuild-unverified` (from Phase 2): confirm wrapper FASTA behavior.
  2. `cram-mixed-list-preqc-filtering` (from Phase 3): settle `n_filter_bam` realization for mixed `[bam, cram]` lists.
  3. `multiqc-galaxy-qc-wiring` / `multiqc-partial-skip-safety`: verify `multiqc` repeat input handling when either `no_stats` or `no_read_qc` is true (`NO_REPLACEMENT` tolerance) or insert guarded collection merges / fallbacks.
  4. `samtools-collate-fastq-wrapper-gap`: verify whether a Tool Shed `samtools` wrapper supports combined `samtools collate` + `samtools fastq -N` (`-0` and `-1/-2` + `-f -r reads_in_memory`) or requires a UDT.
  5. `cat-fastq-gzip-parity`: confirm how the selected Galaxy concatenation tool handles two `.fastqsanger.gz` inputs (raw multi-member gzip vs decompress/recompress).
