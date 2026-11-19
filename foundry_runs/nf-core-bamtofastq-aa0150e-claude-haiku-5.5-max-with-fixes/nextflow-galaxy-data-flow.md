# Data-flow brief: nf-core/bamtofastq (aa0150e)

**Status:** draft for review. Abstract, not gxformat2. Tools are described by what they must do, not resolved.
**Produced by:** nextflow-summary-to-galaxy-data-flow (mold revision 8).
**Inputs:** `summary-nextflow.json` (phase 1, hand-corrected; sha256 `42bb9975…0624`), `nextflow-galaxy-reference-data.md` (phase 2), `nextflow-galaxy-interface.md` (phase 3), and the pinned source (nf-core/bamtofastq aa0150e).
**Ledger:** `open-requirements.ledger.yml` (carried from phases 2-3; this step's entries appended in section 12).

## 1. Summary

- The flow runs one sample list (identifier `sample_id`) through: reference preparation, a QC branch, an optional chromosome extraction, a per-element single-end or paired conversion, a rejoin into one `reads` collection, post-conversion QC, and one MultiQC run.
- Per-element branches use per-element `when` gates and a `pick_value` rejoin. The paired chain is the largest branch (about eight nodes). It stays inside its source boundary, `ALIGNMENT_TO_FASTQ`, with inline per-element gates.
- Confidence: high for topology and gates (read from source), medium for tool needs, low for seven placeholders (section 6).
- Tests cover most branches. The QC-off branch is not covered, because the source's no-QC test sets a misspelled parameter (section 9).

## 2. Source facts used

- Topology: `workflows/bamtofastq.nf` (the primary workflow, including the `if (params.chr)` block and the rebinding of `ch_input_new`), and the subworkflows `prepare_indices`, `pre_conversion_qc` and `alignment_to_fastq`.
- Flags, prefixes and gates: `conf/modules.config`. The four view selections use `-b -f1 -F12`, `-b -f8 -F260`, `-b -f4 -F264` and `-b -f12 -F256`. Collate uses `-f -r <reads_in_memory>` when fast mode is on, and `-N`. SAMTOOLS_CHR uses `-hb`, the region, and the prefix `<id>.<region>`.
- Single or paired classification: `modules/local/checkpairedend/main.nf`, lines 26-35. It samples the first 1000 records and marks a sample paired only if every sampled record has flag 1.
- Published outputs and identifiers: `tests/default.nf.test.snap`, `tests/chr.nf.test.snap` and `tests/cram.nf.test.snap`.

## 3. Abstract nodes

Mode is `map` (one job per sample element), `single` (one job), `reduce` (collected), `filter` or `pick`. Gate is the condition under which the node runs.

| Node | Source step | What it must do | Input → output | Mode | Gate | Confidence |
|---|---|---|---|---|---|---|
| N1 | PREPARE_INDICES, fasta branch | Index the reference FASTA | fasta → fai | single | fasta given and fai absent | high (topology); medium (tool) |
| N2 | PREPARE_INDICES, `.mix().first()` | Choose the user FAI, else the built one | user fai, N1 → fai_effective | single | always | high |
| N3 | PREPARE_INDICES, to_index branch | Build a BAI or CRAI for an alignment | alignment → index | map | index slot absent (per element) | medium (carrier, decision D2) |
| N4 | PREPARE_INDICES, `mix` | Keep the user index if given, else the built one | user index, N3 → sample_indexed | map | always | medium |
| N5 | sample sheet (placeholder P2) | Split the record into a mapped list and an index list, keeping identifiers | sample_sheet:record → mapped_list, index_list | single | always | low |
| N6 | PRE_CONVERSION_QC, idxstats | Per-reference read counts | sample_indexed → idxstats | map | `!no_stats` | high |
| N7 | PRE_CONVERSION_QC, flagstat | Flag counts | sample → flagstat | map | `!no_stats` | high |
| N8 | PRE_CONVERSION_QC, stats | Alignment statistics; uses the reference when given | sample, fai → stats | map | `!no_stats` | high |
| N9 | PRE_CONVERSION_QC, branch | Keep BAM rows only (CRAM rows skip this QC) | sample_indexed → bam_rows | filter | always | medium (P4) |
| N10 | PRE_CONVERSION_QC, FASTQC_PRE | FastQC on the BAM alignments | bam_rows → html, zip | map | `!no_read_QC` | high |
| N11 | CHECKPAIREDEND | Classify each sample single or paired from the first 1000 records | sample, fasta (CRAM) → single_end (boolean per element) | map | always | high (rule); medium (tool) |
| N12 | SAMTOOLS_CHR (conditional) | Extract a region, keeping the header; BAM output | sample_indexed, fai → region alignment | map | chr set | high |
| N13 | SAMTOOLS_CHR_INDEX | Index the region alignment | region alignment → region index | map | chr set | high |
| N14 | source rebinding of `ch_input_new` (placeholder P6) | Relabel identifiers to `<sample>.<region>` and re-key single_end | region tuple, single_end → relabelled sample | map | chr set | rule high; carrier low |
| N15 | source `ch_input_new` reassignment | Use the relabelled input when chr is set, else the original | N14 or sample_indexed → conv_input | map (pick) | always | high (verified mapped pick pattern) |
| N16 | SAMTOOLS_COLLATEFASTQ_SINGLE_END | Name-collate and export single-end reads (`other`) | single-end sample → fastq (single) | map | single_end is true | high (source); medium (tool) |
| N17 | SAMTOOLS_VIEW_MAP_MAP | Select both-mapped pairs (`-f1 -F12`) | paired sample → alignment | map | single_end is false | high |
| N18 | SAMTOOLS_VIEW_MAP_UNMAP | Select mapped reads with an unmapped mate (`-f8 -F260`) | paired sample → alignment | map | single_end is false | high |
| N19 | SAMTOOLS_VIEW_UNMAP_MAP | Select unmapped reads with a mapped mate (`-f4 -F264`) | paired sample → alignment | map | single_end is false | high |
| N20 | SAMTOOLS_VIEW_UNMAP_UNMAP | Select both-unmapped pairs (`-f12 -F256`) | paired sample → alignment | map | single_end is false | high |
| N21 | SAMTOOLS_MERGE_UNMAP, after a join with remainder | Merge the present unmapped selections into one alignment per sample | N18, N19, N20 (0 to 3 parts) → merged unmapped | map | single_end is false | low (P8) |
| N22 | COLLATE_FASTQ_MAP | Collate and export mapped pairs (`mapped`, `-N`) | N17 → paired FASTQ | map | single_end is false | high (source); medium (tool) |
| N23 | COLLATE_FASTQ_UNMAP | Collate and export merged unmapped reads (`unmapped`, `-N`) | N21 → paired FASTQ | map | single_end is false | high (source); medium (tool) |
| N24 | CAT_FASTQ, after join | Join mapped and unmapped pairs per sample; concatenate R1 parts and R2 parts | N22, N23 → paired FASTQ | multi-input map by identifier | single_end is false | medium (P9) |
| N25 | `ch_reads_post_qc` mix (placeholder P10) | One reads collection for single and paired samples | N16 or N24 per element → reads | map (pick) | per element | low (mixed types) |
| N26 | FASTQC_POST and FASTQUTILS_INFO, input (placeholder P11) | One list entry per read file, with identifiers per decision D7 | reads → read_files | flatten | always | medium |
| N27 | FASTQC_POST_CONVERSION | FastQC on each read file | read_files → html, zip | map | `!no_read_QC` | high (source); medium (tool) |
| N28 | FASTQUTILS_INFO | fastq_info check (source: one text per sample) | reads → info text | map | always | medium (granularity, see section 9) |
| N29 | topic `versions` (placeholder P12) | Collate tool versions for the report | tool versions → versions text | reduce | always | low (no recipe) |
| N30 | `methodsDescriptionText` (placeholder P12) | Methods text from the template and versions | template, N29 → methods text | single | always | low |
| N31 | MULTIQC | One report from config, logo, title and the collated text. No sample QC (source behaviour). | config, logo, title, N29, N30 → multiqc_report | reduce (one job) | always | high (faithful); medium (tools) |

## 4. Edges and broadcasts

- **Sample chain:** `samplesheet` → N5 → mapped_list, index_list. Both feed N3 and N4 (sync by identifier, P3) → sample_indexed.
- **Reference broadcast:** `fasta` (and fai_effective from N2) is one dataset per run. It is connected once to N1 and N2, and to every mapped step that uses it: N8, N11 (CRAM), N12, N16, N17-N20, N21, N22, N23. It is not per sample.
- **Mapped chain:** sample_indexed → N6, N7, N8, N9 → N10 (BAM rows), N11 → N12 (chr) → N13, N14 → N15.
- **Per-element branch:** N15 → N16 (gate single) and N17-N20 (gate paired) → N21 → N23; N17 → N22; N22 and N23 → N24 → N25.
- **Post-conversion:** N25 → N26 → N27, N28. N27 and N28 are the report collections. N29 and N30 → N31 → `multiqc_report`.
- **Reads:** N25 → `reads` (interface output).

## 5. Collection map and reduce choices

- One axis: the sample list, keyed on `sample_id`. Every mapped node keeps it.
- The source splits the list in two per element (single or paired) with per-element gates, not by making two sub-lists. This keeps identifiers aligned. The two branches rejoin once (N25) into one `list:paired_or_unpaired`.
- The paired chain runs on all samples, with `when` false for the single-end ones (per-element gates). It is not run on a filtered sub-list. Reason: a sub-list would need a split step that is not verified (see section 6).
- FastQC and fastq_info run on a flat list of read files (N26), not on paired elements. A paired element as one input needs a multi-input tool that is not verified.
- Reductions: MultiQC is one job (N31) over the collected text inputs. The QC tables are not reduced.

## 6. Placeholder transformations

| ID | Where | What | Carrier or recipe | Confidence |
|---|---|---|---|---|
| P1 | N2 | Choose user FAI else built FAI | `pick_value` `first_non_null`, user input first | high |
| P2 | N5 | Split sample_sheet:record into slot lists keeping identifiers | none verified | low |
| P3 | N3, N4 | Align index list to mapped list by identifier (missing indexes allowed) | identifier sync pattern (corpus) | medium |
| P4 | N9 | Keep BAM rows by the `file_type` column | column filter not verified | low |
| P5 | N11 → gates | Per-element single_end boolean from the classifier | `param_value_from_file`, boolean output (verified route) | medium-high |
| P6 | N14 | Relabel to `<sample>.<region>` and re-key single_end | relabel recipe not verified; rule from `ext.prefix` | low |
| P7 | N15 | Per-element choice between relabelled and original input | `pick_value` on mapped outputs (verified pattern) | high |
| P8 | N21 | Join the three unmapped selections with remainder; merge the present parts | no recipe | low |
| P9 | N24 | Join mapped and unmapped pairs; concatenate R1 and R2 parts | multi-input map by identifier; inner join | medium |
| P10 | N25 | One collection from single and paired per-element results | mixed-type `pick_value` not verified | low |
| P11 | N26 | Flatten to read files with identifiers per D7 | flatten recipe with identifier rule | medium |
| P12 | N29, N30 | Collate tool versions; build methods text | no recipe | low |
| P13 | N31 | Collect text inputs into one MultiQC call | `collect`, multiple-input tool | high |

## 7. Conditional disposition

| Source conditional | Galaxy disposition | Reason |
|---|---|---|
| `params.chr` (`if` block: SAMTOOLS_CHR, SAMTOOLS_CHR_INDEX) | inline `when` on N12, N13; per-element `pick` at N15 | Two steps in the main body, no source subworkflow. One rejoin point, so no twin cascade. |
| `!params.no_read_QC` (FASTQC_PRE, FASTQC_POST) | inline `when` on N10, N27 | Two steps. PRE_CONVERSION_QC keeps its own boundary. |
| `!params.no_stats` (FLAGSTAT, IDXSTATS, STATS) | inline `when` on N6, N7, N8 | Three report steps. Outputs are reports, so no fan-in. |
| Index present or absent (PREPARE_INDICES) | per-element gate (N3) and pick (N4), decision D2 | Data-driven and per element. A subworkflow `when` gates a whole run, not one element. |
| BAM or CRAM (PRE_CONVERSION_QC branch) | filter (N9) | Per element, from metadata. |
| Single or paired (CHECKPAIREDEND, branch) | per-element gates (N16-N24), pick at N25 | Per element, data-driven. A subworkflow `when` cannot express it. |
| Fasta index present or absent (fasta branch) | N1 and N2 | Global, single dataset. |

## 8. Subworkflow boundaries and granularity

- **PREPARE_INDICES:** keep as a boundary. The source boundary has a narrow interface (samplesheet and fasta in, indexed sample and fai out).
- **PRE_CONVERSION_QC:** keep as a boundary, ungated. Its three stats steps and FastQC carry the gates inside it.
- **ALIGNMENT_TO_FASTQ (paired chain, N17-N24):** keep as a boundary with a typed interface: a sample collection and a fai in, paired reads out. The per-element gates sit inside it. The subworkflow-level `when` is not used, because it cannot gate one element.
- **Chromosome extraction (N12-N15):** inline. The source has no subworkflow for it, and it has two steps.
- **Single-end conversion (N16):** one inline step.
- **MultiQC (N31):** one step.

## 9. Element identifiers

- **Base:** `sample_id` from the sample sheet. It must be unique per row. The source writes every output from `meta.id`, so duplicates would also collide there (interface ledger entry `samplesheet-duplicate-sample-ids`).
- **chr path:** `<sample_id>.<region>`, with region tokens joined by `_`. Derivation: `ext.prefix` in `conf/modules.config` for SAMTOOLS_CHR. Observed in `tests/chr.nf.test.snap`: `test3.chrX_chrY_X_Y`. Element identifiers change here, so the per-element single_end flag must be re-keyed (P6).
- **Mates:** `_1` and `_2` appear only for paired samples. Observed: `reads/test_1.merged.fastq.gz` for a paired sample, and `reads/test3.chrX_chrY_X_Y_other.fq.gz` for a single-end sample, which has no mate suffix. FastQC follows the same rule: `fastqc/test.post_conversion_1_fastqc.html` (paired) against `fastqc/test3.chrX_chrY_X_Y.post_conversion_fastqc.html` (single).
- **Flat QC list (D7):** paired → `<sample_id>_1` and `<sample_id>_2`. Single → `<sample_id>`.
- **Checked against test rows:** the default and CRAM snapshots show `test` and `test2`. The chr snapshot shows `test3`, single-end. Remote samplesheets were not fetched, so other rows are not checked.
- **Duplicate-id risk:** none is observed in the test rows, and none can be seen in the sample sheet schema (pattern only).

## 10. Galaxy tool needs (what each must do)

| ID | Needed for | What the tool must do |
|---|---|---|
| T1 | N1 | Index a FASTA (write .fai) |
| T2 | N3 | Index a BAM or CRAM (write BAI or CRAI) |
| T3 | N6 | Count reads per reference, from an index |
| T4 | N7 | Count flags |
| T5 | N8 | Alignment statistics; reference optional |
| T6 | N10, N27 | FastQC on alignments (BAM) and on FASTQ |
| T7 | N28 | fastq_info check on one read file |
| T8 | N12 | Extract a region with the header; BAM output; reference optional |
| T9 | N17-N20 | Select alignments by SAM flag masks; BAM or CRAM output; reference optional |
| T10 | N21 | Merge several alignments of one sample; reference optional |
| T11 | N16, N22, N23 | Name-collate and export FASTQ (single-end and paired); `-N`; optional fast mode with a memory setting; reference optional |
| T12 | N24 | Concatenate FASTQ files (two inputs per read end) |
| T13 | N11 | Classify single or paired from sampled records; boolean output. The source uses inline shell here, so a custom tool may be needed. Discovery decides. |
| T14 | N31 | MultiQC from config, logo, title and collated text inputs |
| T15 | N29, N30 | Collate tool versions; build methods text. None known. |

Built-in collection operations used by the design: `pick_value`, Apply Rules identifier derivation, flatten, collect, and the verified per-element `when` route.

## 11. Branch coverage by nf-tests (for the test plan)

| Branch | Covered by | Note |
|---|---|---|
| BAM, index provided, paired | default; collate_fast; fai; no_stats | Baseline. |
| BAM, no index (index built) | no_bai | Its snapshot also contains a single-end output (`other.fq`). |
| CRAM, index provided | cram | Paired. |
| CRAM, no index | no_crai | |
| User fasta_fai | fai | |
| No fasta at all | none | Every test passes a fasta (`d-suite-never-omits-fasta`). |
| chr extraction (single-end input) | chr | Covers the identifier relabel. |
| Fast collate | collate_fast | |
| `no_stats = true` | no_stats | The parameter name is correct. |
| `no_read_QC = true` | none | `no_qc.nf.test` sets `no_read_qc`, not `no_read_QC`. Its snapshot lists the same 12 FastQC files as the default. |
| Single and paired rows in one run | not confirmed | Not read from the snapshots. |

## 12. Confidence and rationale

- **Topology and gates:** high. Each gate is read from source.
- **Tool needs:** medium. What each must do is clear; whether a tool exists is not checked here.
- **Placeholders:** high for P1, P7 and P13; medium for P3, P4, P5, P9 and P11; low for P2, P6, P8, P10 and P12 (no verified recipe or carrier).
- **Overall:** medium. The main uncertainty is the per-element and mixed-type plumbing.

## 13. Open questions

1. **Index presence per element (N3, N4).** Can a Galaxy record slot's presence drive a per-element `when`? If not, the decision D2 fallback runs the indexing on every row, with the same outputs and extra work.
2. **Mixed-type rejoin (N25).** Can one `list:paired_or_unpaired` come from paired and single branches? If not, expose two outputs. That changes the interface, so it needs the expert's review.
3. **Unmapped join (N21).** Which recipe merges 0 to 3 parts per sample? Until one is found, the paired chain cannot be built.
4. **Versions and methods (N29, N30).** Drop them, or build them from the tool wrappers? The source puts both into the MultiQC report.
5. **Sample QC in MultiQC (N31).** Keep the faithful metadata-only report, or mix in FastQC and samtools QC? The second is a divergence from the source.
6. **Chromosome index (N13).** The chr snapshot publishes the region BAM but not its index. Should `chr_alignments_index` stay in the interface?
7. **Map-over subworkflow.** Can the paired chain run as a subworkflow mapped over elements? If not, use the inline per-element gates (decision D6).
8. **Inner joins (N24, N23).** Does Galaxy drop a sample silently when one side of a join is missing? The source may do the same. Verify with a test.
9. **fastq_info granularity (N28).** The source writes one text per sample. The flat design writes one per read file. The output count differs for paired samples.

## 14. Ledger and feedback record

- **Ledger:** 12 gaps (P2, P4, P6, P8, P9, P10, P12, the paired-element route, the per-element subworkflow gate, the fastq_info granularity, the QC-off test gap, and the chr index publication), 9 decisions and 4 discoveries. Entry IDs are in the ledger file.
- **Feedback:** 2 entries. `no-qc-test-sets-misspelled-parameter` (related project: nf-core/bamtofastq test) and `params-delta-undeclared-key-not-flagged` (summarize-nextflow).
