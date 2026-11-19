# Galaxy data flow — nf-core/bamtofastq 2.2.1

Source: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`, `open-requirements.ledger.yml`.

## Workflow inputs (from interface brief)

`alignments` (list, bam/cram, ids = samplesheet `sample_id`), `reference_fasta` (optional fasta), `chr` (optional string), `skip_read_qc` (bool, false), `skip_stats` (bool, false), `collate_fast` (bool, false), `reads_in_memory` (int, 100000).

## Abstract DAG

Granularity follows the source's subworkflow boundaries (`PREPARE_INDICES`, `PRE_CONVERSION_QC`, `ALIGNMENT_TO_FASTQ`) and keeps every source process that does scientific work as its own node.

| # | Node | Source | In shape | Out shape | Galaxy idiom | Tool need | Confidence |
|---|---|---|---|---|---|---|---|
| 0 | *(subsumed)* index BAM/CRAM, faidx FASTA | `PREPARE_INDICES` (`SAMTOOLS_INDEX`, `SAMTOOLS_FAIDX`) | — | — | Galaxy `bam`/`cram` metadata index; in-tool faidx | none | high (bam), medium (cram, fai — ledger `fasta-fai-rebuild-in-wrapper-unverified`) |
| 1 | `idxstats` | `SAMTOOLS_IDXSTATS` | list bam | list tabular | map-over; `when: !skip_stats` | samtools idxstats | high |
| 2 | `flagstat` | `SAMTOOLS_FLAGSTAT` | list bam | list txt | map-over; `when: !skip_stats` | samtools flagstat | high |
| 3 | `stats` | `SAMTOOLS_STATS` | list bam + optional fasta | list txt | map-over; `when: !skip_stats` | samtools stats (reference optional) | high |
| 4 | `fastqc_pre` | `FASTQC_PRE_CONVERSION` | list bam | list html + list zip | map-over; `when: !skip_read_qc` | FastQC on BAM | high |
| 5 | `chr_extract` | `SAMTOOLS_CHR` (+ `SAMTOOLS_CHR_INDEX`) | list bam | list bam | map-over; `when: chr != null` | samtools view, `-h -b`, region list from `chr` | medium |
| 6 | `pick_alignments` | `ch_input_new` reassignment in `if (params.chr)` | (5) or `alignments` | list bam | `pick_value` first_non_null | built-in | medium |
| 7 | `check_paired_end` | `CHECKPAIREDEND` (local module) | list bam (+ fasta) | list txt (`paired`/`single`) | map-over | classifier: sample ≤1000 records, "paired" iff every sampled record has FLAG 0x1 | medium |
| 8 | `pairing_table` | `ch_input.join(CHECKPAIREDEND.out.*)` | list txt | tabular `id<TAB>class` | collection → tabular bridge (collapse with element identifiers) | collapse collection | medium |
| 9 | `paired_ids` | branch predicate `meta.single_end == false` | tabular | txt (ids) | tabular filter + cut | filter rows `class == paired`, keep id | medium |
| 10 | `split_by_pairing` | `ch_input_new.branch { ch_single / ch_paired }` | list bam + ids | 2 × list bam (paired = filtered, single = discarded) | `__FILTER_FROM_FILE__` | built-in | high |
| 11 | `view_map_map` | `SAMTOOLS_VIEW_MAP_MAP` `-b -f1 -F12` | list bam (paired) | list bam | map-over | samtools view with flag filters | high |
| 12 | `view_unmap_unmap` | `SAMTOOLS_VIEW_UNMAP_UNMAP` `-b -f12 -F256` | list bam | list bam | map-over | samtools view | high |
| 13 | `view_unmap_map` | `SAMTOOLS_VIEW_UNMAP_MAP` `-b -f4 -F264` | list bam | list bam | map-over | samtools view | high |
| 14 | `view_map_unmap` | `SAMTOOLS_VIEW_MAP_UNMAP` `-b -f8 -F260` | list bam | list bam | map-over | samtools view | high |
| 15 | `merge_unmapped` | `SAMTOOLS_MERGE_UNMAP` over `join(…, remainder:true)` of 12–14 | 3 × list bam | list bam | multi-input map-over (identifiers match by construction) | samtools merge (multiple inputs per job) | high |
| 16 | `collate_fastq_mapped` | `COLLATE_FASTQ_MAP` (`-N`; `-f -r N` when collate_fast) | list bam | R1 list + R2 list (+ other/singleton unused) | map-over | samtools collate \| samtools fastq, separate R1/R2, `-N` read-name suffixes | medium |
| 17 | `collate_fastq_unmapped` | `COLLATE_FASTQ_UNMAP` | list bam | R1 list + R2 list | map-over | same as 16 | medium |
| 18 | `cat_r1`, `cat_r2` | `CAT_FASTQ` (join map/unmap, `[m1,m2,u1,u2]` → `_1`, `_2`) | 2 × list fastqsanger.gz | list fastqsanger.gz | multi-input map-over, ordered (mapped then unmapped) | concatenate datasets (gz-safe) | high |
| 19 | `zip_paired_reads` | CAT_FASTQ `reads` tuple(meta,[R1,R2]) | 2 × list | list:paired | `__ZIP_COLLECTION__` | built-in | high |
| 20 | `collate_fastq_single` | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`fastq_other` kept) | list bam (single) | list fastqsanger.gz | map-over | same as 16, keep the "other" (no 0x40/0x80) stream | medium |
| 21 | `fastqc_post` | `FASTQC_POST_CONVERSION` over `mix(single, paired)` | list:paired + list | per-file html/zip | two map-over steps (paired & single), `when: !skip_read_qc` | FastQC | high |
| 22 | `fastq_info` | `FASTQUTILS_INFO` over `mix(single, paired)` | list:paired + list | list txt | map-over per branch | fastq_utils `fastq_info` (paired: both files in one job) | low — ledger `fastq-info-tool-unverified` |

Edges are the "In shape" column's producers; workflow inputs fan out (broadcast) to every mapped step: `reference_fasta` → 3, 5, 7, 11–17, 20; `alignments` → 1–4 and 6.

### Element identifiers

Sample ids flow unchanged from `alignments` element identifiers (default test: `test`, `test2`, each a unique samplesheet row). `__ZIP_COLLECTION__` gives `paired_reads` elements `test`/`test2` with `forward`/`reverse` — the NF `_1`/`_2` suffixes are mate positions because every row in the paired branch is paired by construction (node 10). NF renames ids to `<id>.<chr_joined>` under `--chr`; Galaxy keeps the sample id (identifier loss is cosmetic, recorded in open questions).

## Conditionals

| Source guard | Disposition | Rationale |
|---|---|---|
| `params.chr` | inline `when` on node 5 + `pick_value` (6) | one-step cascade; transform-or-pass-through. |
| `!params.no_read_QC` (ext.when) | inline `when` on 4, 21 | gates leaf QC steps only. |
| `!params.no_stats` (ext.when) | inline `when` on 1–3 | leaf steps. |
| `meta.index == false` / fasta `meta.index == false` | subsumed (Galaxy metadata / in-tool faidx) | — |
| `meta.single_end` (per element) | data-driven split (7–10) | per-element routing cannot use `when`; filter-from-file splits the list, both branches map over possibly empty lists. Closes ledger `per-element-single-paired-routing`. |
| `filetype == 'bam'` for FastQC pre | open | see ledger `cram-elements-fastqc-pre`. |

## Dropped

- **MultiQC** (`MULTIQC`): in 2.2.1 its only inputs are the collated software-versions YAML, the params summary and the methods description (`workflows/bamtofastq.nf`: the `ALIGNMENT_TO_FASTQ.out.zip` mix is commented out "TEMPORARILY DISABLED"); no QC output reaches it. Galaxy records tool versions and parameters per job, so the report carries no information the Galaxy run lacks. Dropped; recorded as ledger `multiqc-versions-report-dropped`.
- **Software-versions collation** (`topic: versions` → `collectFile`): Galaxy job provenance replaces it.

## Placeholder transformations

- Node 8–9: collection-to-table bridge and row filter. Shape: list txt → tabular → txt. Implementation picks collapse + filter/cut tools.
- Node 6: `pick_value` over two list bam sources.
- Node 18: ordered two-input concatenation per element.

## Handoff notes

- Every samtools step takes the optional `reference_fasta` (CRAM decoding); for BAM the reference is inert in NF (`--reference` only when `meta.filetype == 'cram'` in CHECKPAIREDEND; samtools view/stats/collate modules pass it through).
- Read-name suffix `-N` (`ext.args2`) matters for content equality with the nf-test snapshot.
- `collate_fast` maps to collate `-f -r reads_in_memory` only if the chosen tool exposes fast mode.

## Open questions

- Is there a Galaxy samtools wrapper that collates and emits separate R1/R2 + other streams in one step, or does collate need a separate step?
- `pick_value` with collection inputs — confirm module support at implementation time.
- Classification is computed on the chr-filtered alignments in Galaxy (NF classifies the full input, then filters). Same answer unless a region subset changes pairing.
