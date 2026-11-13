# Nextflow → Galaxy data-flow brief: nf-core/bamtofastq

- **Pipeline:** nf-core/bamtofastq at `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78` (`source/`)
- **Inputs:** `summary-nextflow.json` (phase 1, reconciled); `nextflow-galaxy-reference-data.md` (phase 2); `nextflow-galaxy-interface.md` (phase 3, binding for inputs, outputs, labels and collection shapes); `open-requirements.ledger.yml` (carried)
- **Scope:** an abstract, target-shaped DAG. No gxformat2, no Tool Shed resolution. Each tool need states what the step must *do*, not which tool does it.

## Summary

The Galaxy draft is a per-sample map-over pipeline with one data-dependent split. Each sample is either single-end or paired-end, decided by a classifier that the source runs on the input file. Each sample then takes one of two conversion paths, and the two results are gathered into the `single_reads` and `paired_reads` outputs. The abstract DAG has 20 nodes. Two decisions in this brief change placements the earlier briefs fixed:

1. **Index building moves to workflow tier.** The FASTA index and the per-sample BAM/CRAM indexes are built once, as upstream steps. The phase-2 choice to build the `.fai` inside each consuming tool (`fai-rebuild-in-tool`) is superseded. The source already structures both as workflow-level steps (`PREPARE_INDICES`), and each index feeds several consumers, which the mapping note's threshold (rebuild more than about three times, use a workflow-tier step) rules against in-tool building.
2. **Per-element routing uses boolean `when` gates on mapped steps,** followed by null cleanup. The source's branch on sample layout is a data-driven channel split, not a parameter guard.

The chromosome branch (`chr`) is the weakest part of the draft. It changes element identifiers, so the per-sample layout flag no longer keys onto the data. That join is an open obligation, and a `chr` run should not be claimed correct until it is resolved.

## Evidence used

- `summary-nextflow.json`: `workflow.edges[]` (24, reconciled), `workflow.channels[]` (17), `workflow.conditionals[]` (3, all parameter guards), subworkflow `calls` and `invocations`, process `script_summary`.
- `source/workflows/bamtofastq.nf`: the main dataflow, including the `conversion_input` branch on `meta.single_end`, the `params.chr` branch, the `join(..., remainder: true)` merges in `ALIGNMENT_TO_FASTQ`, the `ch_multiqc_files` assembly.
- `source/subworkflows/local/prepare_indices`, `pre_conversion_qc`, `alignment_to_fastq`; `source/modules/local/checkpairedend`; `source/conf/modules.config` (ext.when gates, ext.args, the `SAMTOOLS_CHR` prefix).
- Test rows (fetched from the test-dataset URLs the summary's `test_candidates[].inputs` name): `test_bam_samplesheet.csv`, `test_bam_samplesheet_no_bai.csv`, `test_cram_samplesheet.csv`, `test_cram_samplesheet_no_crai.csv`, `test_chr_samplesheet.csv`.
- Packaged notes: operators-to-recipes (operator classes), conditional-to-subworkflow-when (inline versus subworkflow `when`, `pick_value`), collection and conditional patterns, sample-sheet collections.

## Test rows (identifier check)

| Sheet | Rows (`sample_id`, layout as the source will classify) | Identifier check |
|---|---|---|
| `test_bam_samplesheet` | `test` (paired), `test2` (paired) | unique |
| `test_bam_samplesheet_no_bai` | `test` (paired), `test2` (paired), `test3` (single-end BAM) | unique; **mixed layout** |
| `test_cram_samplesheet` | `test`, `test2` (paired CRAM) | unique; no single-end rows |
| `test_cram_samplesheet_no_crai` | `test`, `test2` (paired CRAM) | unique; no index column values |
| `test_chr_samplesheet` | `test3` (single-end BAM) | unique |

Element identifiers are `sample_id`. The source does not enforce uniqueness; the test rows are all unique (see open questions).

## Abstract operations

Scope: **S** = one job per sample (map-over), **R** = reduction over the whole collection, **1** = single job, **F** = fan-in merge within a sample or across siblings.

| ID | Operation | Scope | Inputs → outputs (shape) | Source provenance | Galaxy idiom | Tool need (what it must do) | Confidence |
|---|---|---|---|---|---|---|---|
| N1 | Sample input | — | `input` (sample_sheet) → per-sample BAM/CRAM element | `--input`, `ch_samplesheet` | sample_sheet collection | — | High |
| N2 | Reference broadcast | 1 | `fasta` (optional) → `(fasta)` broadcast; `fasta_fai` (optional) → `(fai)` broadcast | `fasta_fai` channel, `PREPARE_INDICES` | broadcast File | — | Medium (reference brief) |
| N3 | Build FASTA index if absent | 1 | `fasta` → `fai` | `SAMTOOLS_FAIDX` on `index == false` branch | workflow-tier step, gated on `fasta` present and `fasta_fai` absent | build a FASTA index (`.fai`) from a FASTA | High placement; tool unresolved |
| N4 | Build BAM/CRAM index | S | element → element + index | `SAMTOOLS_INDEX` in `PREPARE_INDICES` (every sample, since the index column is not carried) | workflow-tier map-over | build an index (`.bai`/`.crai`) for a BAM or CRAM | High placement; tool unresolved |
| N5 | Alignment summaries | S | element + index → flagstat, idxstats, stats (lists) | `SAMTOOLS_FLAGSTAT`, `_IDXSTATS`, `_STATS` in `PRE_CONVERSION_QC` | map-over, inline `when` on `!no_stats` (three independent steps) | summarise counts (total, mapped, paired), per-reference counts, and full statistics for an indexed BAM/CRAM | High |
| N6 | Layout classifier | S | element + index + fasta → per-sample boolean `is_single` | `CHECKPAIREDEND` (outputs `single_end` / `paired_end` markers) | map-over; emits a boolean file readable by mapped `param_value_from_file` | sample records and decide whether the file's reads are paired (paired flag on the sampled first 1000 records); emit a boolean | Medium (logic is in a shell body, not a standard summary) |
| N7 | Per-element gate values | S | `is_single` → `gate_single`, `gate_paired` (boolean collections) | the branch on `meta.single_end` (`conversion_input`) | mapped `param_value_from_file` (`param_type: boolean`); `gate_paired` = negation | derive a boolean per element; negate it | High (verified pattern in collection note) |
| N8a | Region extract (only with `chr`) | S | element + index → region BAM/CRAM | `SAMTOOLS_CHR` (`ext.args -hb`, `ext.args2 = chr`) | map-over, inline `when: chr` | extract records overlapping a region from an indexed BAM/CRAM | High |
| N8b | Region index (only with `chr`) | S | region BAM → region index | `SAMTOOLS_CHR_INDEX` | map-over, inline `when: chr` | index a BAM/CRAM | High |
| N8c | Chromosome fan-in (only with `chr`) | 1-collection | original collection *or* region collection → one collection | `ch_input_new` (`if (params.chr)`) | `pick_value`, mode `the_only_non_null` (see open questions) | — (gather only) | Low (collection support of `pick_value` unverified) |
| N9a | Flag selection (paired path) | S | element + index → four flag-selected BAM sets (map/map, unmap/unmap, unmap/map, map/unmap) | `SAMTOOLS_VIEW_*` in `ALIGNMENT_TO_FASTQ` (`ext.args` flags) | map-over, four sibling collections, gated by `gate_paired` | select records by SAM flag and output BAM/CRAM in the input's format | High (flags from `modules.config`) |
| N9b | Unmapped merge (paired path) | S (F) | three unmapped sets per sample → one unmapped BAM/CRAM | `SAMTOOLS_MERGE_UNMAP`, fed by `join(..., remainder: true)` | fan-in merge within each sample, **synchronised by identifier** across three sibling collections | merge several BAM/CRAM files into one | Medium: `remainder` joins can give null members (review trigger) |
| N9c | Collate and convert, mapped | S | mapped BAM/CRAM → paired FASTQ (R1, R2) | `COLLATE_FASTQ_MAP` | map-over, gated by `gate_paired` | name-collate records and write paired FASTQ (read 1 and read 2 streams) | High |
| N9d | Collate and convert, unmapped | S | merged unmapped BAM/CRAM → paired FASTQ (R1, R2) | `COLLATE_FASTQ_UNMAP` | map-over, gated by `gate_paired` | same as N9c | High |
| N9e | Join mapped and unmapped pairs | S (F) | N9c pairs + N9d pairs → one keyed pair per sample | `join` of `COLLATE_FASTQ_MAP.out.fastq` and `COLLATE_FASTQ_UNMAP.out.fastq` | identifier-synchronised join (inner) | match two collections by sample identifier | High (inner join on meta) |
| N9f | Concatenate reads per end | S | joined pairs → R1 (mapped R1 + unmapped R1), R2 (mapped R2 + unmapped R2) | `CAT_FASTQ` | unzip pair collection → per-end concatenation → zip back to pair | concatenate two FASTQ files, one per read end | High |
| N10 | Single-end collate and convert | S | element → single FASTQ stream | `SAMTOOLS_COLLATEFASTQ_SINGLE_END` (`fastq_other`) | map-over, gated by `gate_single` | name-collate records and write a single (unpaired) FASTQ stream | High |
| N11a | Null cleanup, paired | R | paired elements with nulls → `paired_reads` | the same elements are null where `gate_paired` is false | drop null elements | filter null/empty elements from a collection | High (pattern cited in collection note) |
| N11b | Null cleanup, single | R | single elements with nulls → `single_reads` | same | drop null elements | same | High |
| N12 | MultiQC | 1 (R) | `multiqc_config`, logo, title, methods description, versions (see gaps) → `multiqc_report` | `MULTIQC`, `ch_multiqc_files` assembly | single job over collected inputs | aggregate reports and metadata into one HTML report | High for shape; versions unresolved |

## Edges

Producers → consumers, with the operator the source applies (`via`).

- `input` → N4 (map over samples) → N5, N6, N8a, N9a, N10 (with the indexed element) and N9c/N9d through N9a outputs.
- `fasta` → N3 (only when `fasta_fai` is absent) → `fai` broadcast → N5, N6, N8a, N9a, N9b, N9c/N9d (as the reference argument).
- `fasta_fai` → broadcast directly when supplied; otherwise N3's `fai`.
- N6 → N7 (boolean per element) → `when` of N9a–N9f (paired) and N10 (single).
- N8a/N8b (chr only) → N8c → downstream of N4 for N5, N6, N9a, N10. **Re-keying gap:** N6 and N7 are keyed by source `sample_id`; after N8c the identifiers are `<sample>.<chr>` (see open questions).
- N9a outputs → N9b (merge of three siblings, synchronised by identifier) → N9d.
- N9a (map/map) → N9c.
- N9c + N9d → N9e (join by identifier) → N9f (unzip → concatenate → zip) → `paired_reads` through N11a.
- N10 → `single_reads` through N11b.
- N5 outputs → `samtools_flagstat`, `samtools_idxstats`, `samtools_stats` (checkpoints, unchanged).
- N12 → `multiqc_report`. No per-sample QC feeds N12 (see open questions).

## Collection map and reduce choices

- **Map-over:** every per-sample node (N4, N5, N6, N7, N8a, N8b, N9a, N9c, N9d, N10, N9f) runs once per sample element. Elements are paired with siblings **by identifier**, not by position. Galaxy pairs multi-input mapped steps by position, so each multi-input node that consumes sibling collections needs an identifier synchronisation (N9b, N9e). This is the review trigger the operator recipes name for `join`.
- **Gated map-over:** N9a–N9f are gated per element by `gate_paired`, and N10 by `gate_single`. A skipped element is null in the output.
- **Reduction:** N11a and N11b drop null elements, so the outputs are lists of the samples that ran that path. N12 is a single reduction over the collected report inputs.
- **Pair handling:** N9f unzips the joined pair collection into R1 and R2 collections, concatenates per end, and zips back to `list:paired`. This is the only place pairing changes shape.

## Conditionals and routing

- **Per-sample layout routing (data-driven, not in `workflow.conditionals[]`).** The source branches each sample on `meta.single_end`, which `CHECKPAIREDEND` decides. In Galaxy, the decision becomes a per-element boolean (N6, N7) read by mapped `when` gates on both paths. This is the per-element `when` the collection note reports as verified. The alternative, running both paths for every sample and filtering afterwards, is wasteful and would run paired conversion on single-end data, so it is not used.
- **`chr` (`params.chr`).** Two steps and a rebinding. The cascade is short, so the source's guard maps to inline `when` on N8a and N8b, not a subworkflow boundary (the conditional-note heuristic). The fan-in is N8c.
- **`no_stats` (`!params.no_stats`).** Three independent steps (N5 flagstat, idxstats, stats) with the same guard. Inline `when` on each. No subworkflow boundary, since the three steps do not chain.
- **`no_read_QC` (`!params.no_read_QC`).** Not carried: the FastQC steps it gates are dropped (interface, dropped entry `fastqc-and-fastq-utils-outputs-not-exposed`).

## Index and reference placement

- **N3 (FASTA index) and N4 (BAM/CRAM index) are workflow-tier steps.** The source structures both as workflow-level steps in `PREPARE_INDICES`. Each index feeds several consumers: the FASTA index feeds about ten steps per sample (stats, the layout check, the region extraction, the single-end collate, the four flag selections, the merge and the two paired collates), so an in-tool build would repeat the work per consumer per sample. The mapping note's threshold (more than about three rebuilds, workflow-tier) applies directly.
- **This supersedes** the phase-2 decision `fai-rebuild-in-tool` (recorded as decision `fai-and-sample-index-workflow-tier` in the ledger, with `supersedes` set). The phase-2 entry `fasta-fai-rebuild-in-tool-unverified` and the phase-3 entry `sample-index-in-tool-build-unverified` are resolved on placement; their tool-availability question moves to the new tool needs for N3 and N4.
- **Reference absence.** When `fasta` is absent, N3 must not run. Gating on the absence of a FASTA is the open reference-free question carried from phase 2; the data-flow only fixes the placement.

## Element identifiers

- **Default key:** `sample_id` on every per-sample collection. The source's own output names use `meta.id` (`sample_id`) in `publishDir` paths and in output file prefixes (`${meta.id}`), so `sample_id` is the source's per-sample identifier.
- **What makes an element unique.** One row of the sample sheet is one element, and the element is unique when its `sample_id` is unique across rows. The five test sheets satisfy this. The source does not enforce it, and the join in `ALIGNMENT_TO_FASTQ` keys on the whole `meta` map (`id`, `filetype`, `single_end`), which only behaves as a sample key when `sample_id` is unique. A sheet with a repeated `sample_id` (one sample with several runs) would give an ambiguous join and a Galaxy identifier collision. The brief records a constraint for the interface and template: either the input sheet must have unique `sample_id` values (stated as a requirement), or the element key must be `sample_id` plus the row number. The source does not choose between these.
- **After `chr`.** `SAMTOOLS_CHR`'s prefix is `${meta.id}.${chr}` (for example `test.chr1`), and the source rebinds `meta.id` to the file basename. The identifier then carries the sample id plus a dot-separated suffix. Splitting on the first dot is ambiguous when `sample_id` contains dots. The data-flow records the rule that the chromosome-named element is keyed by the full basename, and that the sample id must be recovered for the flag join.

## Shape-changing placeholder steps

- Boolean gate values (N7): `param_value_from_file` mapped over the N6 output.
- Unzip, concatenate per end, zip (N9f): explicit collection operations.
- Identifier synchronisation for N9b and N9e: explicit collection operations (identifier extraction, sort, filter).
- Null cleanup (N11a, N11b).
- The chr fan-in (N8c): `pick_value` (see open questions).

## Galaxy tool needs (what each must do)

These are needs, not resolutions. They state what each step must accomplish; discovery reports what exists.

1. Build a FASTA index (N3).
2. Build a BAM/CRAM index (N4).
3. Summarise counts, per-reference counts and full statistics for an indexed BAM/CRAM (N5, three outputs).
4. Classify a BAM/CRAM as single-end or paired-end and emit a boolean (N6). The source does this with a shell check over sampled records.
5. Extract records overlapping a region from an indexed BAM/CRAM (N8a), and index the result (N8b).
6. Select records by SAM flag and output BAM/CRAM in the input's format (N9a, four selections).
7. Merge several BAM/CRAM files into one (N9b).
8. Name-collate BAM/CRAM records and write paired FASTQ (N9c, N9d).
9. Name-collate BAM/CRAM records and write a single FASTQ stream (N10).
10. Concatenate two FASTQ files (N9f).
11. Aggregate reports into one HTML report (N12).

## Dropped and unexposed nodes

- FastQC pre- and post-conversion, and fastq_utils (unpublished, unconsumed in the source). Not in this draft. The gated `no_read_QC` path goes with them.
- The collated software-versions YAML **as a published output** is dropped (interface). Its data still feeds N12 (see open questions), so the versions node stays internal.
- The Nextflow workflow-summary YAML (`paramsSummaryMap`, the parameter dump that MultiQC also consumes). Not produced. Galaxy's invocation record replaces it.

## Granularity

- **Source subworkflow boundaries** set the grouping: `PREPARE_INDICES` (N3, N4), `PRE_CONVERSION_QC` (N5), the layout check (N6, N7), `ALIGNMENT_TO_FASTQ` (N9a–N9f), and the single-end module (N10). Each is kept as one group of nodes in this brief.
- **Plumbing versus scientific work** inside `ALIGNMENT_TO_FASTQ`: the four flag selections, the collate-and-convert steps and the merge are the scientific work; the joins, the unzip/concatenate/zip and the identifier synchronisation are plumbing. The plumbing is kept as explicit nodes because each one changes collection shape, and the template must see those changes.
- The merge of N9b and the concatenation of N9f are separate nodes, because they are different operations: one merges records, the other concatenates files.

## Confidence

- **High:** the node structure, the workflow-tier index placement, the per-element `when` routing, the collection shapes and the identifier key (`sample_id`), each checked against the source and the test rows.
- **Medium:** the layout classifier (N6), which depends on a shell-level rule the Galaxy side must reproduce; the identifier-synchronised merge (N9b), where `remainder` joins can produce nulls; the empty-collection behaviour when all rows share one layout (for example the CRAM sheets have no single-end rows).
- **Low:** the chr fan-in (N8c). `pick_value` for collections is not verified, and the chr path needs the re-keying rule before its correctness can be claimed.

## Open questions and unverified assumptions

1. **Chr re-keying (open obligation).** After N8c, the layout flag (keyed by `sample_id`) no longer matches the chromosome-named elements, so the per-element gates in N9 and N10 would apply to the wrong elements. Options for the template: (a) an identifier rule that recovers the sample id from the chromosome-named element; (b) classify layout on the region BAMs, which changes the classifier's input (mates can leave the region, so the result can differ from the source); (c) keep the chromosome branch out of this draft. This brief does not choose. Ledger entry `chr-layout-flag-rekeying`.
2. **Chr fan-in.** `pick_value` on collections is not verified; the alternative is a twin downstream cascade (each branch carries its own N9 and N10 steps), which roughly doubles the DAG width.
3. **Empty collections.** When all samples are one layout, the other path's cleaned collection is empty. Galaxy's handling of an empty mapped collection downstream is unverified.
4. **Null members from `remainder` joins** (N9b). The source passes nulls into the merge; the design needs the nulls removed before N9b, or N9b must accept them. Unverified.
5. **MultiQC content.** The source's MultiQC receives only the versions file, the workflow-summary YAML and the methods description; it does not receive the samtools reports or FastQC (the FastQC line is commented out). The faithful Galaxy draft therefore produces a report with little QC content. Keeping it faithful is the default; including the samtools reports would be a deliberate deviation, for the expert to decide.
6. **Versions for MultiQC.** The versions file has no Galaxy source: Galaxy records tool versions per job, not as a workflow file. N12 needs a versions input or it runs without one. Unresolved.
7. **Layout classifier output.** The classifier's boolean must be readable by mapped `param_value_from_file`. The output format must be settled with the tool need in item 4.
