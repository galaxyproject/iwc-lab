# Galaxy data-flow brief — nf-core/bamtofastq

Consumes: summary-nextflow.json, nextflow-galaxy-reference-data.md, nextflow-galaxy-interface.md, open-requirements.ledger.yml.
Consumed by: compare-against-iwc-exemplar (phase 5), nextflow-summary-to-galaxy-template (phase 6), advance-galaxy-draft-step (phase 7).

## Input amendments (supersedes interface brief where noted)

1. **Alignment input is a plain `list` collection, not `sample_sheet:record`.** With
   `file_type` dropped (derivable from the Galaxy datatype) and the `index` slot dropped
   (indexes are rebuilt unconditionally, see N1), no per-row metadata remains to carry —
   `sample_sheet:record` would be ceremony with no payload, and its tool-side slot
   consumption was the interface brief's weakest-confidence decision (ledger
   `mixed-bam-cram-wrapper-support-unverified`). Element identifiers = `sample_id`
   (`test`, `test2` in the selected test's rows — unique per row, used as-is).
   Elements may be mixed `bam`/`cram` datatypes; wrapper support for CRAM remains the
   open tool-discovery risk.
2. **`fasta_fai` input dropped.** No Galaxy tool in the converted chain consumes a
   `.fai` dataset; samtools wrappers take the FASTA directly (in-tool rebuild posture).
   Resolves ledger `samtools-wrapper-fai-capability-unverified` as moot. Recorded as
   dropped work.
3. **`samtools_collate_fast` / `reads_in_memory` dropped.** Performance-only toggles
   (samtools collate buffering); converted FASTQ content is identical. Recorded as
   dropped.

Kept from the interface brief: `chr` (string), `no_read_qc`, `no_stats` (booleans),
`multiqc_title` (string), `multiqc_config` (optional data), reference `fasta`
(optional data).

## Conditional disposition (per nextflow-conditional-to-galaxy-subworkflow-when)

All source conditionals translate to **inline `when:` on tool steps** — no subworkflow
`when:` anywhere. Rationale: every gated unit is 1–2 steps, the source structures none
of them as a subworkflow boundary, and each rejoin is either a `pick_value`
(chr branch) or a null-tolerant output exposure (QC toggles). No twin-cascade needed.

| Source conditional | guard | disposition |
|---|---|---|
| chr region subsetting | `params.chr` (truthy) | Two parallel branches (original vs chr-subset BAMs) rejoin with `pick_value(first_or_skip)` — corpus pattern [[conditional-route-between-alternative-outputs]]. |
| FASTQC_PRE/POST | `!params.no_read_QC` | inline `when` on both FastQC steps; skipped steps emit typed nulls, exposed as null outputs (honest loss). |
| FLAGSTAT/IDXSTATS/STATS | `!params.no_stats` | inline `when` on the three stats steps, same null-output handling. |

## Abstract nodes

Element identifiers through the whole DAG: `sample_id` (`test`, `test2`); preserved by
map-over on every step. The chr branch renames elements to `<sample>.<region>` in the
source (`file.baseName`, e.g. `test.chrX_chrY_X_Y`); Galaxy pick_value keeps the
input-side identifiers (rename only lives in output filenames) — tests must not expect
renamed collection members.

| id | abstract operation | inputs → outputs | tool need (unresolved) | confidence |
|---|---|---|---|---|
| N1 | index each alignment (unconditional, replaces compute-if-missing `PREPARE_INDICES`) | alignments(list bam/cram) → index(list bai/crai) | samtools index | high |
| N2 | region subset (only when `chr` set) | alignments + index → subset bam(list) + subset index | samtools view with region + samtools index | high |
| N3 | pick conversion input | original alignments+index ↔ N2 outputs | `pick_value(first_or_skip)` ×2 (bam, index) | high |
| N4 | pre-conversion QC | alignments + index + fasta → flagstat/idxstats/stats(list tabular), fastqc_pre html+zip | samtools flagstat, samtools idxstats, samtools stats, fastqc | high |
| N5 | split by pair status ×4 | N3 bam (+index, +fasta) → 4 bam lists: mapped-pairs (`-b -f1 -F12`), unmap-unmap (`-b -f12 -F256`), unmap-map (`-b -f4 -F264`), map-unmap (`-b -f8 -F260`) | samtools view | high |
| N6 | merge the 3 unmapped bams per sample | 3 sibling lists → merged unmapped bam(list) | samtools merge (multiple input, dot-product over aligned siblings) | medium — multi-input map-over of 3 collections must stay linked |
| N7 | convert mapped-pair bam → fastq R1/R2 (+singletons/other tolerated) | N5 map_map → fastq R1/R2 lists | samtools fastq (collate+fastq semantics; grouping/order fidelity is the tool step's concern) | medium |
| N8 | convert merged-unmapped bam → fastq R1/R2 | N6 → fastq R1/R2 lists | samtools fastq | medium |
| N9 | concatenate mapped+unmapped per mate | N7 R1 + N8 R1 → sample_1.merged.fastq.gz(list); idem R2 | concatenate (gzip output) | high |
| N10 | build paired output collection | N9 R1,R2 sibling lists → `list:paired` reads | __ZIP_COLLECTION__ or Apply Rules [[collection-build-list-paired-with-apply-rules]] | medium |
| N11 | post-conversion FastQC (when !no_read_qc) | N9 fastqs → fastqc_post html+zip lists | fastqc | high |
| N12 | fastq sanity check (when !no_read_qc) | N9 fastqs → info(list txt) | fastq_info / fastq-utils (discovery may report absent → step dropped, see ledger) | low |
| N13 | MultiQC report | N11 zip + multiqc_config(optional) + `multiqc_title` → multiqc_report(File html) | multiqc | high |

## Edges / fan-in notes

- N5's four branches, N6, N7, N8 all map over the same sample axis — sibling collection
  alignment is preserved by construction (each is a map-over of the same input), so N6's
  merge needs no identifier synchronization.
- N9 pairs N7/N8 per mate — again same-axis siblings, direct wiring.
- N10 is the only shape-changing step (two lists → list:paired).
- N4 outputs are workflow outputs (list each), each step independently when-gated.
- fasta flows into N2, N4 (stats), N5 (view, needed for CRAM); when absent for BAM-only
  runs the connection is optional-input wiring.

## Workflow outputs

`paired_reads` (list:paired fastqsanger.gz), `fastqc_pre_html`, `fastqc_pre_zip`,
`fastqc_post_html`, `fastqc_post_zip`, `flagstat`, `idxstats`, `stats`,
`fastq_info` (if N12 survives discovery), `multiqc_report` (File).
**`single_reads` from the interface brief is withdrawn** — single-end path dropped (below).

## Dropped source features (ledger `kind: dropped`, cited)

| units | because |
|---|---|
| single-end conversion path (SAMTOOLS_COLLATEFASTQ_SINGLE_END + CHECKPAIREDEND routing) | Per-element computed branch routing (`CHECKPAIREDEND` → per-element when-gated rejoin) has no verified Galaxy pattern — per-element `when` mapping emits full-size null-bearing collections whose downstream alignment breaks conversion (channel-shape note marks per-element branch rejoin unresolved; `__FILTER_NULL__` weakly attested). All 9 nf-test candidates in the selected source are paired-end (samplesheets: test/test2/test3 paired_end sorted bam/cram), so no test coverage is lost. Cited: tests/*.nf.test `when` blocks; operators note user-review triggers. |
| CHECKPAIREDEND as a workflow step | Its only product is the paired/single routing flag consumed by the dropped path. |
| `fasta_fai` honoring (tests/fai.nf.test path) | No Galaxy consumer for a supplied `.fai`; in-tool rebuild posture. |
| provided-index honoring (`tests/no_bai`/`no_crai` "no index" semantics) | N1 indexes unconditionally; a supplied index would simply be overwritten in the work dir, not in the user's history. Outcome equivalent. |
| `samtools_collate_fast`, `reads_in_memory` | Performance toggles; converted content identical (nf-test collate_fast snapshot asserts same structure). |
| MultiQC input set fidelity | Source's MultiQC receives only versions/params/methods YAML (the line mixing conversion fastqs into MultiQC is commented out in workflows/bamtofastq.nf — an upstream bug note). Galaxy translation feeds the FastQC zips it actually produces, the standard IWC MultiQC pattern. Deviation recorded. |
| versions.yml / workflow-summary / methods-description YAML collection | nf-core boilerplate artifacts with no Galaxy counterpart; MultiQC's Galaxy wrapper does not consume them. |

## Open questions carried forward

1. CRAM wrapper support (ledger `mixed-bam-cram-wrapper-support-unverified`) — unresolved
   until tool discovery; if the samtools wrappers reject CRAM the workflow must either
   restrict input to bam or split by datatype.
2. N6 multi-input merge over 3 aligned sibling collections — dot-product map-over with a
   `multiple=true` merge input; implement-galaxy-tool-step must verify linked selection.
3. N12 fastq_info tool existence — discovery decides; absence drops the step, not the workflow.
