# Galaxy data-flow brief — nf-core/bamtofastq @ aa0150e

> Superseded in phase 7: `reference_fasta` became required; `collate_fast`/`reads_in_memory` dropped; FastQC `*_zip` outputs became `*_raw` (text). See open-requirements.ledger.yml and galaxy-workflow.gxwf.yml.

Source summary: `summary-nextflow.json` (workflow BAMTOFASTQ + subworkflows PREPARE_INDICES, PRE_CONVERSION_QC, ALIGNMENT_TO_FASTQ). Interface: `nextflow-galaxy-interface.md`. Reference: `nextflow-galaxy-reference-data.md`.

## Workflow inputs (from interface brief, one label change)

- `alignments` — `list` of `bam`/`cram`, element identifier = `sample_id` (unique per row in every test samplesheet: `test`, `test2`, `test3`).
- `reference_fasta` — optional `fasta`.
- `run_read_qc` — boolean, default `true` (= `!params.no_read_QC`).
- `run_stats` — boolean, default `true` (= `!params.no_stats`).
- `collate_fast` (boolean, default false) / `reads_in_memory` (int, default 100000) — only if the collate wrapper exposes them.

**Decision:** the interface's `skip_read_qc`/`skip_stats` are re-expressed with positive polarity (`run_*`) so step `when:` expressions are a plain `$(inputs.when)` (the IWC-observed form) instead of a negation. Same behaviour, defaults flipped accordingly.

## Nodes

### A. PREPARE_INDICES → implicit (no steps)
- `SAMTOOLS_INDEX` (index BAM/CRAM when the `index` column is empty): Galaxy `bam`/`cram` datatypes build the index as dataset metadata on upload. No step. Confidence high.
- `SAMTOOLS_FAIDX`: Galaxy samtools wrappers index a history FASTA themselves. No step. Confidence medium (verify per wrapper; ledger `fai-rebuild-unverified`).

### B. PRE_CONVERSION_QC (map over `alignments`)
| Node | Source | In → Out | Tool need | Gate | Confidence |
|---|---|---|---|---|---|
| `flagstat` | SAMTOOLS_FLAGSTAT | list bam/cram → list txt | samtools flagstat | `when: run_stats` | high |
| `idxstats` | SAMTOOLS_IDXSTATS | list bam/cram (indexed) → list tabular | samtools idxstats | `when: run_stats` | high |
| `stats` | SAMTOOLS_STATS (with `--reference` if FASTA) | list bam/cram + optional fasta → list txt | samtools stats | `when: run_stats` | high |
| `fastqc_pre` | FASTQC_PRE_CONVERSION (`--quiet`, BAM rows only) | list **bam only** → list html + list zip | FastQC on BAM | `when: run_read_qc` | medium |

BAM-only filter for `fastqc_pre`: source `branch { bam: meta.filetype == 'bam' }`. Galaxy: membership filter by identifier (pattern *sync-collections-by-identifier*): see node C's classifier, which also emits the file type.

### C. CHECKPAIREDEND → per-element classifier + membership split
Source: CHECKPAIREDEND emits an optional `*paired.txt` or `*single.txt` per sample; `ch_input.join(...)` then `branch { single_end }` routes each sample. Galaxy cannot route per element by an optional output, so translate as classifier + filter (operators note: "per-element conditional routing usually needs explicit filters/classifiers"):

1. `classify_alignment` — mapped over `alignments`; per element writes one line `<paired|single>\t<bam|cram>` using the source logic (samtools view of first ≤1000 records; paired iff all sampled records carry flag 0x1; `--reference` for CRAM when given). Tool need: small samtools script (likely authored user-defined tool). in: list bam/cram (+ optional fasta) → out: list txt. Confidence medium.
2. `collect_classes` — collapse the per-element class files into one table with the element identifier prepended as column 1 (`id\tpairing\tfiletype`). Tool need: collection → table with identifiers. Confidence high.
3. `paired_ids` — select column 1 where column 2 == `paired`. Tool need: tabular filter/awk. → txt.
4. `bam_ids` — select column 1 where column 3 == `bam`. → txt.
5. `split_by_pairing` — filter `alignments` by `paired_ids`: kept = `alignments_paired` (list), discarded = `alignments_single` (list). Tool need: built-in filter-collection-from-identifier-file. Confidence high.
6. `bam_only` — filter `alignments` by `bam_ids` → list bam for `fastqc_pre`.

### D. Single-end conversion (SAMTOOLS_COLLATEFASTQ_SINGLE_END) — map over `alignments_single`
| Node | Source | In → Out | Tool need |
|---|---|---|---|
| `collate_fastq_single` | samtools collate (`ext.args` fast mode) \| samtools fastq `-N` with `-0 other -1 _1 -s singleton` | list bam/cram (+fasta) → list fastqsanger.gz (`other` output only is used, per source comment) | samtools collate+fastq |

Public output `fastq_single_end` = the `other` FASTQ. Empty list in the default test.

### E. ALIGNMENT_TO_FASTQ (paired) — map over `alignments_paired`
Keep the source's structure (4 filtered views → merge unmapped → collate each → concatenate) so read order and content match the source.

| Node | Source (ext.args) | In → Out | Tool need |
|---|---|---|---|
| `view_map_map` | SAMTOOLS_VIEW_MAP_MAP `-b -f1 -F12` | list → list bam | samtools view with include/exclude flags |
| `view_unmap_unmap` | `-b -f12 -F256` | list → list bam | same |
| `view_unmap_map` | `-b -f4 -F264` | list → list bam | same |
| `view_map_unmap` | `-b -f8 -F260` | list → list bam | same |
| `bundle_unmapped` | `join(...).map{[meta,[uu,um,mu]]}` | 3 × list bam → `list:list` (sample → 3 bams) | build list per element (collection op; pattern *fan-in-bundle-consume-and-flatten*) |
| `merge_unmapped` | SAMTOOLS_MERGE_UNMAP | list:list → list bam (inner list reduced into merge's multi-input) | samtools merge |
| `collate_fastq_mapped` | COLLATE_FASTQ_MAP `-N`, prefix `<id>.mapped` | list bam → R1/R2 per sample | samtools collate+fastq, paired outputs |
| `collate_fastq_unmapped` | COLLATE_FASTQ_UNMAP | list bam → R1/R2 per sample | same |
| `cat_r1`, `cat_r2` (or one paired-aware concatenate) | CAT_FASTQ: `[map_R1, unmap_R1]` → `_1.merged.fastq.gz`; same for R2 | parallel map over two lists → list fastqsanger.gz | concatenate datasets (gz members concatenate validly) |
| `zip_pairs` | (implicit in tuple `[meta,[r1,r2]]`) | list R1 + list R2 → `list:paired` | built-in zip collection |

Whether collate output already arrives as `list:paired` (forward/reverse) depends on the wrapper; if so, a single paired-aware concatenation over two `list:paired` collections replaces `cat_r1`/`cat_r2`/`zip_pairs`. Implementation decides.

Public output `fastq_paired` = `zip_pairs` output (`list:paired`, identifiers `test`, `test2`).

### F. Post-conversion QC
| Node | Source | In → Out | Gate |
|---|---|---|---|
| `fastqc_post_paired` | FASTQC_POST_CONVERSION on paired reads | list:paired → list:paired html/zip | `when: run_read_qc` |
| `fastqc_post_single` | same on single-end reads | list → list html/zip | `when: run_read_qc` |
| `fastq_info_paired` | FASTQUTILS_INFO (fastq_info R1 R2) | list:paired → list txt | none |
| `fastq_info_single` | FASTQUTILS_INFO single | list → list txt | none |

The source `mix`es single and paired reads into one channel; Galaxy keeps two parallel branches (different collection shapes). Outputs from the single branch are empty collections in the default test.

### G. Dropped (ledger)
- MULTIQC, versions YAML (`multiqc-report-not-carried`, `versions-yml-not-carried`).
- SAMTOOLS_CHR / SAMTOOLS_CHR_INDEX (`chr-region-filter-not-carried`).

## Galaxy idioms used

- Map-over of `list` for every per-sample process.
- Membership split by identifier file (classifier → table → id list → filter collection) instead of per-element `when` (avoids null-element cleanup on every output).
- Per-element bundle into `list:list` then reduction into a multi-input merge.
- Zip two lists into `list:paired`.
- Workflow-level boolean `when:` for QC/stat gates (scalar, not per element).

## Unresolved tool needs (for discovery)

samtools flagstat, idxstats, stats, view (flag filters, BAM out, optional reference), merge (multi-input), collate+fastq (paired R1/R2/other/singleton, `-N`, optional reference, fast mode), FastQC, fastq_info (fastq_utils), concatenate datasets, collapse collection with identifiers, tabular row filter / awk, built-in collection ops (filter from file, build list, zip). Paired/single classifier with samtools (probably authored).

## Expected test shape (default test: test, test2 both paired BAM)

- `alignments_paired` = {test, test2}; `alignments_single` = {}.
- `fastq_paired`: 2 pairs; `samtools_*`: 2 elements each; `fastqc_pre_*`: 2; `fastqc_post_paired_*`: 2 pairs; `fastq_info_paired`: 2 (`test.txt`, `test2.txt` md5 in snapshot — note source runs fastq_info on the pair).

## Open questions

- Empty-collection outputs (`fastq_single_end`, single-branch QC) in the default test: planemo assertions should check `element_count`-free or skip them.
- `run_read_qc`/`run_stats` gating of mapped steps whose outputs are public: skipped outputs become null datasets; acceptable since defaults are `true`.
