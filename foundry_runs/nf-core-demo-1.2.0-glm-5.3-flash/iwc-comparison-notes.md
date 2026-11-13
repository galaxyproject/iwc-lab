# IWC comparison notes — nf-core/demo (1.2.0)

Corpus: `~/.foundry/iwc` (fresh shallow clone, updated 2026-11-09).

## Candidate search

Feature hierarchy applied to the briefs (reads-in / FastQC + trim + MultiQC-out; sample-sheet collection input; FastQC/seqtk/MultiQC tool families):

| Candidate | Domain | Input topology | Tools | Verdict |
|---|---|---|---|---|
| `read-preprocessing/short-read-qc-trimming` (short-read-quality-control-and-trimming) | read QC + trimming | `list:paired` collection input | fastp, MultiQC | **nearest — Medium confidence** |
| `amplicon/amplicon-mgnify/…quality-control-single-end` | amplicon QC | `list` collection input | FastQC (×4), trimmomatic, MultiQC with multiple `results_N` entries | secondary reference for FastQC + MultiQC-multi-input idiom |
| `transcriptomics/rnaseq-pe` | RNA-seq | `list:paired` | fastp, MultiQC ×2 with `when:` gating | secondary reference for MultiQC `when` + multiple software inputs |

No IWC workflow uses FastQC + seqtk together, none uses a `sample_sheet*` collection input (the corpus still uses plain `list:paired`/`list`), and none embeds a toy "cow" tool. Exemplar confidence is **Medium**, not High: same domain (read QC/trimming/reporting), same topology family (collection input → mapped QC → reduced report), partial tool-family overlap (fastp instead of FastQC+seqtk; no cowpy).

## Structural diff against the briefs

1. **Input collection shape.** Exemplar: `list:paired` with no column metadata. Brief: `sample_sheet:paired_or_unpaired`. The corpus has no sample_sheet exemplar; the brief's shape stands as a deliberate choice (mixed paired/single test data), flagged for the template phase as corpus-novel. IWC precedent is `list:paired` — if the wrapper-acceptance question (ledger `wrapper-sample-sheet-variant-acceptance`) fails, the corpus-consistent fallback is `list:paired` + separate single-end handling, which IWC itself doesn't demonstrate.
2. **QC-tool → MultiQC wiring.** Exemplar: MultiQC `results_N|software_cond` repeated entries, one per tool, each a *single dataset or collection* input (`__current_case__` select). mgnify-single-end shows the pattern for multiple FastQC outputs: `results_0|software_cond|output_0..3|input` — several entries under one software block. For nf-core/demo: FASTQC mapped html collection + cowpy txt + (fixed) multiqc config → multiple `results` entries on the MultiQC step. The mapped-collection → multi-input connection is corpus-idiomatic.
3. **Map-over vs reduction.** Exemplar feeds one collection into fastp (single invocation, internal map). Brief: FastQC mapped over collection elements (one job per element) — IWC's FastQC steps are single-input (mapped) too (`in: input_file <- 0:output`). No diff.
4. **Output promotion.** Exemplar promotes `fastp trimmed reads` (collection), `fastp JSON report`, `MultiQC HTML report` via named `outputs:` with `outputSource: <step>/<out>`. Brief's five outputs match this idiom directly. Exemplar uses `hide: true` on internal outputs and `rename:` on promoted ones — copy that.
5. **Conditional gating.** Exemplar has none. rnaseq-pe gates MultiQC variants with `when:` (`in: when <- 3:output`). Brief's skip-trim gate is a single step; inline `when: $(inputs['Skip trimming'] == false)` on the seqtk step is corpus-consistent.
6. **Step granularity.** Exemplar has 2 tool steps; brief has 4 (fastqc, seqtk, cowpy, multiqc). No structural conflict.

## Nearest exemplar (gxformat2) view

Sibling file: `iwc-exemplar.gxwf.yml` — full converted `read-preprocessing/short-read-qc-trimming` (6 steps; whole workflow is already the relevant subgraph). Abstract IWC ID: `read-preprocessing/short-read-qc-trimming`. Covered labels: `fastp` (map-over QC/trim), `MultiQC` (reduction), promoted outputs `fastp JSON report`, `fastp trimmed reads`, `MultiQC HTML report`.

Inline excerpt — the MultiQC reduction idiom (one software entry per input family):

```yaml
  - id: MultiQC
    label: MultiQC
    doc: Aggregation of the quality controls for all samples
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy5
    tool_shed_repository:
      changeset_revision: 94b6bea727ae
      name: multiqc
      owner: iuc
      tool_shed: toolshed.g2.bx.psu.edu
    in:
      - id: results_0|software_cond|input
        source: fastp/report_json
    out:
      - id: stats
        hide: true
      - id: html_report
        rename: MultiQC report
```

## Findings routed forward

- **Template/data-flow:** use `outputs:` + `outputSource` promotion with `rename:`; `hide: true` for non-promoted step outputs. MultiQC input assembly = multiple `results_N` entries (corpus-idiomatic), not `__BUILD_LIST__` — the data-flow brief's placeholder #1 resolves to this idiom.
- **Pattern issue:** no corpus exemplar for `sample_sheet*` workflow inputs — the brief's choice is corpus-novel; if it fails wrapper validation the template should not improvise beyond `list:paired` fallback. Recorded in ledger.
- **Tool-step issue:** FastQC wrapper (devteam/fastqc 0.74+galaxy1 in corpus) takes a single `input_file`; confirm it accepts collections/multiple inputs during the per-step loop (ledger entry open).
- **Test issue:** none carried; test plan handled by its own phase.

## Ledger updates

No entries closed (wrapper acceptance still unverified — corpus inspection here shows only that IWC itself uses list:paired, which strengthens the fallback but doesn't verify the wrappers). No new obligations: the sample_sheet corpus-gap is already ledgered via `wrapper-sample-sheet-variant-acceptance`.
