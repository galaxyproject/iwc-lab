# IWC exemplar comparison — nf-core/bamtofastq → Galaxy

Corpus: `~/.foundry/iwc` @ `c07557f`.
Reads: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`,
`open-requirements.ledger.yml`.
Mold: `compare-against-iwc-exemplar`.

## Nearest exemplar

**`read-preprocessing/short-read-qc-trimming`** — "Short-read quality control and trimming"
(fastp 1.4.0 → MultiQC 1.35). Confidence: **medium**.

| Feature | Exemplar | This pipeline | Match |
|---|---|---|---|
| Domain | read QC / preprocessing of sequencing reads | convert alignments back to reads, then QC | partial (same QC family, different primary operation) |
| Input topology | one `list:paired` collection of FASTQ | one `list` of BAM/CRAM + workflow-level `layout` select | partial |
| Primary tool families | fastp, MultiQC | samtools (view/merge/collate/fastq/index/stats), FastQC, MultiQC, fastq_utils | partial — MultiQC shared |
| DAG motifs | flat map-over one tool, reduce to MultiQC | map-over with four-way split → merge → collate → concat → zip, plus gated branches | divergent |
| Outputs | trimmed reads (`list:paired`), fastp JSON, MultiQC HTML | converted reads (`list:paired`), FastQC/samtools QC collections, MultiQC HTML | partial |
| Test style | one `job:` with a paired collection, `has_text` asserts, `element_tests` per pair | snapshot md5s of merged FASTQ + task count | different, but complementary |

No IWC workflow performs alignment→FASTQ conversion (the corpus has no `samtools fastq` /
`bam2fq` workflow), so a high-confidence domain exemplar does not exist. The exemplar is
chosen for the **collection topology + QC reduction motif**, not for the science.

## Relevant subgraph (inline excerpt)

Exemplar steps covered: `Raw reads` input, `fastp`, `MultiQC`, output promotion. Full
converted view: `iwc-exemplar.gxwf.yml` (whole workflow — it is only two steps).

```yaml
inputs:
  - id: Raw reads
    type: collection
    collection_type: list:paired
    optional: false
    fields: null
    column_definitions: null
outputs:
  - id: fastp trimmed reads
    outputSource: fastp/output_paired_coll
  - id: MultiQC HTML report
    outputSource: MultiQC/html_report
steps:
  - id: fastp
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/fastp/fastp/1.4.0+galaxy0
    in:
      - id: single_paired|paired_input
        source: Raw reads
    out:
      - id: output_paired_coll
        rename: Trimmed reads
      - id: report_json
        rename: fastp JSON report
  - id: MultiQC
    in:
      - id: results_0|software_cond|input
        source: fastp/report_json
    out:
      - id: html_report
        rename: MultiQC report
```

## Structural diff and guidance for the template phase

1. **Collection input declaration** — the exemplar writes `optional: false`,
   `fields: null`, `column_definitions: null` explicitly. Mirror that verbose form for
   `input`, `fasta` and `fasta_fai`; do not rely on defaults.
2. **Output promotion** — the exemplar promotes with `outputSource: <step>/<out_id>` and a
   stable `id`. Do the same for `reads_paired`, `reads_single` and the QC collections.
   `reads_paired` will be produced by `__ZIP_COLLECTION__`; the zip step's output is the
   promotion source.
3. **Map-over is implicit** — neither the exemplar nor IWC generally inserts explicit
   `__APPLY_RULES__` or flattening steps for a plain map-over. In this translation
   `__APPLY_RULES__` is only needed for the BAM-only filter before pre-conversion FastQC;
   do not add collection-operation steps for the ordinary map-overs.
4. **`layout` select has no corpus precedent.** The exemplar commits to `list:paired` at
   authoring time. A workflow-level `when:` that swaps the entire conversion branch is
   supported by the engine but not represented in IWC; keep it, record it, and expect a
   reviewer to flag it.
5. **MultiQC input assembly diverges.** The exemplar feeds MultiQC one `report_json`
   collection through `results_0|software_cond|input` with
   `results: [{software_cond: {software: fastp}}]`. This translation has several
   differently-shaped QC collections; the template must build a single list (flatten the
   paired FastQC output, append the single-end and samtools lists) and use MultiQC's
   automatic file discovery (`results_0|input` style) rather than `software_cond`, if the
   wrapper supports it.
6. **Test style to follow** (`iwc-test-data-conventions` / this exemplar's tests.yml):
   `job:` keys are the public input ids, collections are declared with `class: Collection`
   + `collection_type`, and per-element assertions use `element_tests:`. The nextflow test
   plan will use `element_tests` for `reads_paired` (sample → `forward`/`reverse`) and
   `has_text` for text QC outputs.

## Findings routed forward

| Finding | Owner |
|---|---|
| `layout` select branch swap has no IWC precedent | template phase + human review (recorded in the ledger) |
| MultiQC input assembly across mixed collections | template phase |
| `__APPLY_RULES__` BAM filter | template phase |
| md5 assertions on `reads_paired` members | test-plan phase (`nextflow-test-to-galaxy-test-plan`) |
| `samtools collate | fastq` single wrapper | per-step tool discovery |
