# IWC exemplar comparison: nf-core/bamtofastq (Galaxy target)

- **Pipeline:** nf-core/bamtofastq at `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`
- **Inputs:** `nextflow-galaxy-interface.md` (phase 3), `nextflow-galaxy-data-flow.md` (phase 4), the carried `open-requirements.ledger.yml`
- **Corpus:** IWC at `~/.foundry/iwc`, HEAD `c07557f` (2026-11-12; `git pull --ff-only` up to date). 133 `.ga` workflows, 0 gxformat2 files in the working tree. Workflows were converted with `gxwf convert --to format2 --compact` before comparison.

## Result

**No High or Medium nearest exemplar.** No IWC workflow converts BAM or CRAM to FASTQ. Searching all 133 `.ga` workflows for `collatefastq`, `samtools_fastq`, `bam2fastq`, `bamtofastq`, `bam_to_fastq`, `samtools_collate` and `collate_fastq` found zero matches. Samtools appears in 27 workflows (variant calling, ChIP/ATAC, virology, assembly); none converts alignments back to reads.

The best **Low-confidence pattern match** is `data-fetching/sra-manifest-to-concatenated-fastqs`. It shares the topology this pipeline needs for its per-sample paired and single read outputs, but its analysis is read acquisition, not conversion. It is used below for pattern comparison only. Per the procedure, no domain exemplar is claimed, so the sibling file `iwc-exemplar.gxwf.yml` is **not written**.

## Candidates ranked by the feature hierarchy

| Rank | Workflow | Domain | Topology | Tool families | Confidence | Why |
|---|---|---|---|---|---|---|
| 1 | `data-fetching/sra-manifest-to-concatenated-fastqs` | read acquisition (partial match) | manifest → per-sample `list:paired` and `list`, concatenation per sample | none shared | **Low** (cross-domain structural match) | Per-sample paired/single split with separate outputs; concatenate per element; identifier relabelling from a table. |
| 2 | `read-preprocessing/short-read-qc-trimming` | read QC | `list:paired` in, MultiQC out | fastp (not used here), MultiQC | **No nearest** | Shares only MultiQC (a generic tool) with this pipeline, which the procedure names as no-match. |
| 3 | `transcriptomics/rnaseq-pe/rnaseq-pe` | RNA-seq | paired FASTQ collection in, BAM out, MultiQC report | fastp, STAR, MultiQC | **Low** (cross-domain) | Pattern reference only, no excerpt: MultiQC with and without extra QC switched by `pick_value`; per-element strandedness parameter via `map_param_value`. |
| — | samtools-based variant-calling and ChIP/ATAC workflows | — | BAM inputs for calling, not conversion | samtools generic | **No nearest** | Shares generic samtools only. |

## Labeled excerpt (Low-confidence pattern comparison, not a domain exemplar)

Workflow: `data-fetching/sra-manifest-to-concatenated-fastqs/sra-manifest-to-concatenated-fastqs.ga` (IWC `c07557f`), converted with `gxwf convert --to format2 --compact`. The conversion wrote 391 lines; 7 of 13 steps fell back to non-stateful conversion (tool cache empty). Tool IDs in the excerpt are the converter's output.

Steps covered: `relabel pair collec to get SRA+sample`, `relabel single collec to get SRA+sample`, the two `__APPLY_RULES__` steps, and the two `cat_multi_datasets` concatenation steps. The full converted file is not written here (no sibling).

```yaml
outputs:
  - id: paired_output
    outputSource: _unlabeled_step_14/paired_output
  - id: single_output
    outputSource: _unlabeled_step_15/out_file1
steps:
  # ... split file to collection, fasterq-dump (fetch) omitted ...
  - id: relabel pair collec to get SRA+sample
    label: relabel pair collec to get SRA+sample
    tool_id: __RELABEL_FROM_FILE__
    tool_version: 1.1.0
    in:
      - id: how|labels
        source: generate table for relabelling/outfile
      - id: input
        source: get Fastqs from SRA IDs/list_paired
  # ... relabel single collec, apply rules (x2), concatenate (x2) follow the same pattern ...
  - id: _unlabeled_step_14            # concatenate multiple datasets (paired)
    tool_id: toolshed.g2.bx.psu.edu/repos/artbio/concatenate_multiple_datasets/cat_multi_datasets/1.4.3
    tool_version: 1.4.3
    in:
      - id: global_condition|inputs
        source: _unlabeled_step_12  # apply rules output
```

Cross-reference: this excerpt is the pattern for the concatenate-per-end and the separate paired and single outputs. It is not the converted subgraph of this pipeline and not a resolution of any tool need.

## Structural diff (exemplar versus the phase-4 data-flow draft)

| Aspect | IWC exemplar | Draft | Divergence | Routed to |
|---|---|---|---|---|
| Input | manifest table (`data`) plus column-number parameters | typed `sample_sheet` collection (`input`) | No IWC precedent for the sample-sheet input: no `.ga` in the corpus uses a `sample_sheet` input | template (keep the interface decision; do not claim corpus support) |
| Per-sample split | `split_file_to_collection` makes one element per accession | elements already per sample | No split node needed | template |
| Read production | `fasterq_dump` per element | per-sample BAM→FASTQ: N9c, N9d, N10, plus the flag selections N9a and the merge N9b | No precedent for BAM→FASTQ conversion | template and tool loop (authored from the brief) |
| Layout | fetch tool already splits pair and single per accession; relabel each collection separately | per-sample boolean from N6 gates both paths (N7, mapped `when`) | No precedent for per-element layout routing in this exemplar | template; keep the open entry `per-element-layout-routing-unverified` |
| Identifier relabelling | `__RELABEL_FROM_FILE__` with a generated identifier table (SRA plus sample) | chr re-keying (open entry `chr-layout-flag-rekeying`); identifier synchronisation in N9b and N9e | Candidate mechanism, not a resolution | template and data-flow review |
| Reshape before concatenation | `__APPLY_RULES__` then `cat_multi_datasets` with `global_condition\|inputs` | N9f unzip, concatenate per end, zip | Same operation class; the exemplar applies rules first | template (placeholder steps) |
| Concatenation | per-element, multiple runs per sample | per-end, two inputs (mapped and unmapped) | Same class of operation, different inputs | template |
| Outputs | `paired_output` (list:paired) and `single_output` (list) as separate outputs | `paired_reads` and `single_reads` | **Matches** the layout-split decision | none (corroborates `reads-split-by-layout`) |
| Samtools QC and indices | none | N3 to N5 workflow-tier indexes and summaries | No precedent in this exemplar | template and tool loop |
| MultiQC | none in this exemplar | N12 with no QC content (faithful) | See the rnaseq-pe precedent below | expert decision (open entry `multiqc-report-without-qc-content`) |
| Test style | `element_tests` with `has_size` (delta) per FASTQ element | interface checkpoints `samtools_flagstat` (counts) | Size-only assertions are a weaker check than the counts the testability note prefers | test-plan skill |

## Pattern evidence from the rnaseq-pe exemplar (Low, no excerpt)

- MultiQC report selection: `pick_value` chooses between a MultiQC variant with extra QC and one without (`style_cond`, `pick_from_0`, `pick_from_1`). The MultiQC inputs are the workflow's own trimming, alignment and counting outputs. Corpus precedent for a QC-gated report that aggregates the workflow's QC, which bears on the open MultiQC decision.
- Per-element strandedness: `map_param_value` mapped over the sample sheet's strandedness value, feeding each tool's parameter. Consistent with the per-element parameter route in the collection notes.
- `pick_value` in these workflows is applied to dataset outputs (MultiQC HTML and stats), not to collections. This is not evidence that `pick_value` works over collections.

## Routing of findings

- **Template and data-flow:** the sample-sheet input (no precedent), the per-element layout routing (no precedent), the concatenate-per-end placeholders (apply-rules first), the chromosome fan-in (dataset-level `pick_value` only in the corpus).
- **Pattern:** the concatenate-after-apply-rules and the relabel-from-table patterns are recurring Galaxy idioms that the pattern pages could describe (not updated here).
- **Tool step:** every wrapper choice (samtools collate, fastq, flag view, merge; the layout classifier; the index builds) is owned by the per-step loop. The exemplar's `fasterq_dump` and `cat_multi_datasets` are not adopted by this note.
- **Test:** the size-only `has_size` style and the counts preference route to the test-plan skill.

## Open entries and what this comparison settled

- **Closed:** none. No exemplar fully answers an open entry.
- **Partly informed (kept open, evidence recorded as discoveries):** `chr-layout-flag-rekeying` (relabel-from-table is a candidate mechanism); `chr-fan-in-pick-value-collections` (corpus `pick_value` is dataset-level only); `multiqc-report-without-qc-content` (corpus precedent for a QC-fed MultiQC report); `per-element-layout-routing-unverified` (no corpus precedent for per-element routing).
- **Corroborated:** the layout-split output decision (`reads-split-by-layout`) has IWC precedent in the concatenation exemplar.
- **New obligations with no corpus precedent:** `no-iwc-exemplar-bam-to-fastq-conversion` and `no-iwc-precedent-sample-sheet-input` (both appended to the ledger).

## Limits

- The corpus has no BAM-to-FASTQ workflow, so no pattern-level comparison of the core conversion is possible.
- Matches are by hand, against the feature hierarchy. No automatic ranking was run.
- Excerpt lines are the converter's output, trimmed to the covered steps; `tool_state` and UUIDs are omitted.
