# Galaxy data-flow brief — nf-core/demo (1.2.0)

Consumes: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md` (no reference surface), `nextflow-galaxy-interface.md`.

## Galaxy-facing inputs

- `Input samplesheet` — `sample_sheet:paired_or_unpaired` collection. Forward slot = `fastq_1` (fastqsanger.gz), optional reverse slot = `fastq_2`; element identifier = `sample` column value. Elements: SAMPLE1_PE (paired), SAMPLE2_PE (paired), SAMPLE3_SE (two unpaired rows — samplesheetToList groups them into one sample entry with 2 unpaired elements? **No**: `groupTuple` groups by `meta.id`; SAMPLE3_SE has two rows with the same id, so the group holds two single-end fastq lists. Galaxy `sample_sheet:paired_or_unpaired` cannot model a row with *two* unpaired elements — this is a shape mismatch. See **Open questions**).
- `Skip trimming` — boolean, default false.

## Node list (abstract)

| Node | Galaxy idiom | Needs a tool that… | Confidence |
|---|---|---|---|
| N1 `fastqc` | map-over: sample_sheet → per-element QC | runs FastQC over a dataset (paired and unpaired members), emitting html + zip per element | high |
| N2 `trim reads` | map-over: sample_sheet → per-element trimmed fastq | runs seqtk trimfq per fastq element, gzipped output | high |
| N3 `cowpy` | no data in/out | prints an ASCII cow to a text file | high (likely UDT — nf-core's cowpy is a toy; expect author-galaxy-tool-wrapper or an existing embedded UDT) |
| N4 `multiqc` | reduction: N files → 1 report | runs MultiQC over a set of files with a fixed config, emitting html (+ data dir) | high |

## Edges (with shape before/after)

- `Input samplesheet` → N1 (map-over): sample_sheet:paired_or_unpaired → list of (html, zip) per element.
- `Input samplesheet` → N2 (map-over): sample_sheet:paired_or_unpaired → list of trimmed fastqsanger.gz. Edge gated by `Skip trimming` (see conditional).
- N2 → `trimmed_reads` output (collection passthrough).
- N1 (zip/html members) → N4: FastQC reports feed MultiQC. The materialized MultiQC input is a flat list of files. `zip` elements cannot be scanned by MultiQC — in the source, the FastQC *zip* is mixed into ch_multiqc_files but MultiQC reads extracted fastqc report files from the publish tree; **Galaxy target: connect FASTQC html outputs (the actual report files) to MultiQC.** The zip channel mixing is Nextflow publish plumbing, not data flow. (Operator classification: `mix` over report files = wiring; the interface brief promotes both html and zip as outputs, but only html feeds MultiQC.)
- N3 (cowpy.txt) → N4: direct edge, single dataset input. (`mix` of report inputs = wiring.)
- N4 → `multiqc_report` output.

## Conditional disposition

`params.skip_trim` gates SEQTK_TRIM only.

- **Inline `when:`** on the N2 step (`when: $(Skip trimming == false)`) — heuristic evidence: cascade is short (SEQTK_TRIM's outputs are only the promoted `trimmed_reads` output; nothing downstream consumes them), no source subworkflow boundary exists for it (bare `if` in the DEMO workflow body), pure phase-swap not tool-swap.
- No `pick_value` needed: nothing downstream consumes the trimmed reads, so a skipped step simply yields the typed null output which the output promotion tolerates (or, if that breaks output binding, gate the output promotion itself — template phase to verify).
- COWPY has a `when: task.ext.when == null || task.ext.when` guard in the source — always true; no Galaxy conditional needed.

## Operator translations

- `map { _meta, file -> file }` (FASTQC zip→file): channel-only rewiring (metadata projection); no materialized reshape needed since html feeds MultiQC directly.
- `mix` (ch_multiqc_files): channel-only rewiring into MultiQC's multi-file input. If MultiQC's wrapper takes multiple datasets, connect FASTQC html (mapped) + cowpy txt; if it takes a single collection, insert `__BUILD_LIST__`/merge step. Data-flow records both; template picks based on the resolved wrapper.
- `groupTuple` + `validateInputSamplesheet` (PIPELINE_INITIALISATION): collection semantics inside the input materialization. On the Galaxy side the sample_sheet collection *is* the grouped channel — this is folded into the input shape, no step needed. The single_end-consistency validation is runtime-only (recorded as validation loss in the interface brief).
- `collectFile` (versions.yml, workflow summary, methods description): Nextflow reporting plumbing; not carried. No Galaxy node.
- `channel.topic("versions")` aggregation: Nextflow reporting plumbing; not carried.

## Placeholder transformations

1. **MultiQC input assembly** — merge N mapped dataset streams (FASTQC html list + cowpy.txt) into whatever the MultiQC wrapper accepts (multi-dataset input or a collection). Shape-changing; resolved at template/implementation once the wrapper is known.
2. **(Conditional) skip-gated output promotion** — if a skipped N2's null output breaks `trimmed_reads` promotion, gate the output with the same expression.

## Unresolved tool needs

| Need | Shape in / out | Note |
|---|---|---|
| `fastqc` tool | sample_sheet (or paired_or_unpaired) collection → list of html+zip | existing Galaxy FastQC wrapper expected; wrapper's declared collection_type allowlist must be checked (ledger entry `wrapper-sample-sheet-variant-acceptance`) |
| `seqtk trim` tool | collection of fastqsanger.gz → collection of fastqsanger.gz | existing wrapper expected |
| `cowpy` tool | no input → txt | expect UDT (toy nf-core tool); author-galaxy-tool-wrapper likely |
| `multiqc` tool | many files/collection → html report | existing wrapper expected; check whether its inputs accept multiple mapped datasets + one static dataset |

## Open questions (carried)

1. **SAMPLE3_SE two-row grouping** — the source groups the two SAMPLE3_SE single-end rows into one sample with two fastqs; Galaxy `sample_sheet:paired_or_unpaired` models one optional reverse per row, not two rows merged. Options: (a) model SAMPLE3_SE as two distinct rows (SAMPLE3_SE_R1, SAMPLE3_SE_R2) — deviation from source naming; (b) input as `list:paired` + separate list, splitting by endedness; (c) accept sample_sheet:paired_or_unpaired with each row standalone and let seqtk trim both rows independently (semantically equivalent to source: seqtk trimfq is per-file; FastQC is per-file too; only the *meta.id* grouping is lost, which affects nothing downstream — MultiQC consumes files, not sample groups). **Recommended: (c)** — the grouping affects only publish-directory layout, not scientific output. Recorded as a decision below.
2. Whether FastQC/seqtk wrappers accept the collection type (ledger entry `wrapper-sample-sheet-variant-acceptance`).
3. Element-identifier derivation for `trimmed_reads` (ledger entry `trimmed-reads-element-identifiers`) — seqtk writes `<prefix>_<basename>`; wrapper naming will decide.

## Ledger updates

- Closed: `wrapper-sample-sheet-variant-acceptance` → **not closable here**; stays open (this Mold cannot inspect wrappers without discovery tools; routing belongs to advance-galaxy-draft-step).
- Appended decision: `sample-sheet-row-grouping-flattened` (see below).
