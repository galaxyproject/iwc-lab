# Galaxy data-flow brief — nf-core/bamtofastq

Sources: `summary-nextflow.json` (reconciled `workflow.edges`, `conditionals`, `processes[].resolved_args`), `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`.

This is an abstract DAG. It names what each step must do, not which Galaxy tool does it.

## Scope decisions made here

| Decision | Effect on the DAG |
|---|---|
| **BAM only.** CRAM input and the FASTA reference are dropped together (ledger `cram-and-reference-not-carried`). | No reference input. No `SAMTOOLS_FAIDX`. No per-element filetype branch before FastQC. |
| **`chr` region extraction not carried** (ledger `chr-region-filter-not-carried`). | No `SAMTOOLS_CHR` / `SAMTOOLS_CHR_INDEX` nodes, no `Regions to extract` input. |
| **Index building subsumed.** | No `SAMTOOLS_INDEX` node: a Galaxy `bam` dataset has its index. |
| **Per-sample single/paired routing is kept**, as classifier + collection split (below). | Two conversion branches, each over its own sub-list. |
| **Three unmapped-category filters + merge become one filter** (subsumption, verified). | One node instead of four (`SAMTOOLS_VIEW_UNMAP_UNMAP`, `_UNMAP_MAP`, `_MAP_UNMAP`, `SAMTOOLS_MERGE_UNMAP`). |

The interface brief's inputs 2 (`Reference genome FASTA`) and 3 (`Regions to extract`) are therefore **removed**. The workflow has one input.

## Workflow input

| Label | Shape | Format | Identifiers |
|---|---|---|---|
| `Alignments` | `list` | `bam` | `sample_id` from the sample sheet. Unique per row in every source test sheet (`test`, `test2`, `test3`); one row = one file, no multi-run samples. |

## Nodes

Shapes: `L` = list keyed by sample id. `L[paired]` / `L[single]` = the sub-list of samples classified paired-end / single-end.

| # | Node | Source process (alias) | In | Out | Galaxy idiom | Tool need | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Flagstat | `SAMTOOLS_FLAGSTAT` | `Alignments` L(bam) | L(txt) | map-over | samtools flagstat, plain text output | high |
| 2 | Idxstats | `SAMTOOLS_IDXSTATS` | L(bam) | L(tabular) | map-over | samtools idxstats | high |
| 3 | Stats | `SAMTOOLS_STATS` | L(bam) | L(txt) | map-over | samtools stats, no reference, no extra args | high |
| 4 | FastQC pre-conversion | `FASTQC` (`FASTQC_PRE_CONVERSION`) | L(bam) | L(html), L(txt raw data) | map-over | FastQC accepting BAM | high |
| 5 | Classify pairedness | `CHECKPAIREDEND` (local module) | L(bam) | L(txt): one line per sample, `paired` or `single` | map-over | per BAM: look at the first up to 1000 alignment records; `paired` if every one has flag 0x1, else `single`. The source writes `<id>.paired.txt` or `<id>.single.txt`; one output with the class as content carries the same information. | medium (needs a tool that does exactly this) |
| 6 | Table of classes | (operators `join` on meta) | L(txt) | File(tabular): `sample_id <tab> class` | collection → table, carrying element identifiers into rows | concatenate a collection of one-line files into one table with the identifier as a column | high |
| 7 | Paired sample ids | (operator `branch { meta.single_end }`) | File(tabular) | File(txt): one sample id per line, only rows with class `paired` | tabular filter + column cut | keep rows where column 2 is `paired`, print column 1 | high |
| 8 | Split alignments | (operator `branch`) | `Alignments` L(bam) + ids file | L[paired](bam), L[single](bam) | filter a collection by identifiers from a file, keeping both the matching and the non-matching part | built-in collection filter with "filtered" and "discarded" outputs | medium (an empty side must be tolerated) |
| 9 | Mapped pairs | `SAMTOOLS_VIEW` (`SAMTOOLS_VIEW_MAP_MAP`) | L[paired](bam) | L[paired](bam) | map-over | samtools view, BAM out, require flag 1, exclude flag 12 (`-b -f1 -F12`) | high |
| 10 | Pairs with an unmapped mate | `SAMTOOLS_VIEW` ×3 + `SAMTOOLS_MERGE` (`_UNMAP_UNMAP`, `_UNMAP_MAP`, `_MAP_UNMAP`, `SAMTOOLS_MERGE_UNMAP`) | L[paired](bam) | L[paired](bam) | map-over | samtools view, BAM out, exclude flag 256, require **any** of flags 12 (`-F 256 --rf 12`) | high for equivalence (see evidence), medium for the wrapper exposing "any of these flags" |
| 11 | Mapped pairs → FASTQ | `SAMTOOLS_COLLATEFASTQ` (`COLLATE_FASTQ_MAP`) | L[paired](bam) | L[paired](fastqsanger.gz) forward, same for reverse | map-over | `samtools collate` (default mode, not `sort -n`) piped to `samtools fastq -N`; READ1 and READ2 outputs, gzip | high for need; order-sensitive |
| 12 | Unmapped-mate pairs → FASTQ | `SAMTOOLS_COLLATEFASTQ` (`COLLATE_FASTQ_UNMAP`) | L[paired](bam) from 10 | forward + reverse lists | map-over | same as 11 | high |
| 13 | Concatenate forward | `CAT_FASTQ` | 11.forward, 12.forward | L[paired](fastqsanger.gz) | two lists with the same identifiers, mapped pairwise | concatenate two gzip FASTQ files, **mapped first, unmapped second** | high |
| 14 | Concatenate reverse | `CAT_FASTQ` | 11.reverse, 12.reverse | L[paired](fastqsanger.gz) | as 13 | as 13 | high |
| 15 | Pair up | (tuple `[r1, r2]`) | 13, 14 | `list:paired` | zip two lists into paired | built-in zip | high |
| 16 | Single-end → FASTQ | `SAMTOOLS_COLLATEFASTQ` (`SAMTOOLS_COLLATEFASTQ_SINGLE_END`) | L[single](bam) | L[single](fastqsanger.gz) | map-over | collate + `samtools fastq -N`; the published file is the **`-0` "other" output** (reads with neither or both of READ1/READ2), not the READ1 output | high (the source comment says `fastq_other` was chosen on purpose) |
| 17 | Flatten paired reads | (channel `mix` into `ch_reads_post_qc`) | 15 `list:paired` | list, ids `<sample>_forward`, `<sample>_reverse` | flatten | built-in flatten | high |
| 18 | All converted reads | (`mix`) | 17 + 16 | list | merge two collections (identifiers cannot collide: flattened ones carry a suffix) | built-in merge | medium (one side is empty when all samples are of one kind) |
| 19 | FastQC post-conversion | `FASTQC` (`FASTQC_POST_CONVERSION`) | 18 list(fastqsanger.gz) | list(html), list(txt) | map-over | FastQC on FASTQ | high |
| 20 | Validate paired FASTQ | `FASTQUTILS_INFO` | 15 `list:paired` | L[paired](txt) | map-over the outer list; both mates go to one invocation | `fastq_info <r1> <r2>` (fastq_utils): fail the job on invalid or unpaired reads; write a short text on success | medium |
| 21 | Validate single-end FASTQ | `FASTQUTILS_INFO` | 16 L[single] | L[single](txt) | map-over | `fastq_info <reads>` | medium |
| 22 | MultiQC | `MULTIQC` | 4.txt, 19.txt, 1, 2, 3 | File(html) (+ stats table) | reduce: each collection is consumed whole | MultiQC with FastQC and samtools (stats, flagstat, idxstats) modules | medium (deviation, below) |

### Source structure vs. step granularity

The source has three local subworkflows: `PREPARE_INDICES` (2 processes, both subsumed), `PRE_CONVERSION_QC` (4 processes → nodes 1–4), `ALIGNMENT_TO_FASTQ` (8 process calls → nodes 9–15, with 4 calls folded into node 10), plus 6 processes in the main workflow (nodes 5, 16, 19, 20/21, 22; `SAMTOOLS_CHR*` not carried). Nodes 6–8, 15, 17, 18 are plumbing that Nextflow does with channel operators (`join`, `branch`, `mix`, tuple building); Galaxy needs them as explicit collection steps. That is 16 scientific/QC nodes and 6 plumbing nodes. No Galaxy subworkflow is planned: the source subworkflows are not parameter-gated, so nothing would be gained by nesting.

## Edges and operator translations

| Source construct | Translation | Class |
|---|---|---|
| `ch_input.join(CHECKPAIREDEND.out.paired_end)` / `.single_end`, then `map` adding `meta.single_end`, then `branch` on it | nodes 5 → 6 → 7 → 8: classifier output becomes an identifier file that splits the input list. The operator note says per-element `branch` "usually needs explicit filters/classifiers"; the collection-patterns note's *sync-collections-by-identifier* is the same filter. | explicit Galaxy steps |
| `SAMTOOLS_VIEW_*.out.bam.join(..., remainder: true)...map` → `SAMTOOLS_MERGE_UNMAP` | folded into node 10 (one filter, same read set, same order) | subsumption |
| `.out.cram.mix(.out.bam)` (several places) | BAM only → plain wiring | channel-only |
| `COLLATE_FASTQ_MAP.out.fastq.join(COLLATE_FASTQ_UNMAP.out.fastq).map { [m1, m2, u1, u2] }` → `CAT_FASTQ` | nodes 13 and 14: forward and reverse concatenated separately, each mapped over two identifier-aligned lists | Galaxy collection semantics |
| `channel.empty().mix(SE.out.fastq_other, ALIGNMENT_TO_FASTQ.out.reads)` | nodes 17 + 18 (materialised, because FastQC must map over it) | explicit collection assembly |
| `ch_multiqc_files...collect()` | node 22 reduces each QC collection | reduction |
| `channel.topic('versions')`, `softwareVersionsToYAML`, `paramsSummaryMultiqc`, `methodsDescriptionText` | not carried (ledger `software-versions-file-not-produced`) | dropped |
| `ext.when` on QC processes (`no_read_QC`, `no_stats`) | always run (ledger `qc-skip-flags-fixed-default`) | fixed default |

## Empty-branch behaviour

The selected source test (`tests/default.nf.test`) has two paired-end samples and no single-end sample, so `L[single]` is empty there. Places where an empty list arrives:

1. Node 8 output `L[single]`, then nodes 16 and 21 map over nothing → empty outputs. Workflow outputs `Single-end reads` and `FASTQ validation (single-end)` are empty collections in that test.
2. Node 18 merges a non-empty and an empty list. The merged list is never empty as long as there is at least one sample, so nodes 19 and 22 always have input.
3. With only single-end samples the mirror case holds: node 7 writes an empty ids file, nodes 9–15, 17, 20 see empty lists.

The only source test with a single-end sample alongside paired ones is `tests/no_bai.nf.test` (`test`, `test2`, `test3`; the missing index is irrelevant in Galaxy). The test plan should use it to cover the single-end branch if a second case is allowed.

## Workflow outputs

| Label | From node | Shape | Format |
|---|---|---|---|
| `Paired-end reads` | 15 | `list:paired` | fastqsanger.gz |
| `Single-end reads` | 16 | `list` | fastqsanger.gz |
| `Samtools flagstat` | 1 | list | txt |
| `Samtools idxstats` | 2 | list | tabular |
| `Samtools stats` | 3 | list | txt |
| `FastQC pre-conversion report` / `FastQC pre-conversion data` | 4 | list / list | html / txt |
| `FastQC post-conversion report` / `FastQC post-conversion data` | 19 | list / list (ids `<sample>_forward`, `<sample>_reverse`, or `<sample>` for single-end) | html / txt |
| `FASTQ validation (paired-end)` | 20 | list | txt |
| `FASTQ validation (single-end)` | 21 | list | txt |
| `MultiQC report` | 22 | File | html |
| `Pairedness per sample` | 6 | File | tabular — promoted checkpoint: shows how each sample was routed |

Change against the interface brief: `FASTQ validation` is two outputs (one per branch) instead of one; post-conversion FastQC is one flat list (interface open question 3); `Pairedness per sample` is added as a test checkpoint.

## Evidence for the subsumption in node 10 and for order sensitivity

Hand run of the source commands on `test.paired_end.sorted.bam` with samtools 1.17, 1.22 and 1.23.1 (logged in `model-test-log.md`):

- literal method (3 filters + `samtools merge`) and the single filter `-F 256 --rf 12` give byte-identical decompressed forward and reverse FASTQ;
- both equal the md5s in `tests/default.nf.test.snap` for `test_1.merged.fastq.gz` / `test_2.merged.fastq.gz` (nf-test hashes the decompressed content of `.gz` files);
- `samtools sort -n` in place of `samtools collate` changes the read order, so the md5 no longer matches.

Constraints this puts on implementation: nodes 11, 12, 16 must use collate in default mode and `-N`; nodes 13/14 must put mapped reads first.

## Deviations from the source

1. **MultiQC inputs.** Source `MULTIQC` gets only versions/summary/methods YAML. Node 22 gets FastQC and samtools outputs (decision `multiqc-fed-with-fastqc-and-samtools`). This adds behaviour the source revision does not have.
2. **Classifier output form.** One text per sample with the class as content, instead of two optional flag files.
3. **Pre-conversion FastQC for all inputs** — same as the source for BAM (the source skips it only for CRAM).

## Open questions carried to template / step loop

1. Node 5: is there an existing tool that classifies the first 1000 records, or must one be authored? (routing decision belongs to the step loop)
2. Node 10: does the samtools view wrapper expose "require any of these flags" (`--rf`)? If not, the literal 3 filters + per-sample merge must be restored, which needs a nested collection per sample.
3. Nodes 11/12/16: does the BAM→FASTQ wrapper run collate (not name-sort), accept `-N`, and expose the `-0` output?
4. Collate fast mode (`samtools_collate_fast`, `reads_in_memory`): not an input; close ledger entry `collate-fast-mode-unverified` with wrapper evidence when nodes 11/12/16 are implemented.
