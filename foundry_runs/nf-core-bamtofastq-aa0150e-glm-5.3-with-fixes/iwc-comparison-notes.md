# IWC exemplar comparison — nf-core/bamtofastq → Galaxy

Inputs: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`. Corpus: galaxyproject/iwc @ c07557f (2026-11-12), searched for domain and structure.

## Retrieval result: no nearest domain exemplar

IWC contains **no BAM/CRAM → FASTQ conversion workflow**. Domain-intent search (bamtofastq, bam-to-fastq, collatefastq, samtools fastq, extract reads from bam) returns only FASTQ→BAM pipelines in the opposite direction (rnaseq-pe/sr, atacseq, cutandrun) and unrelated samtools consumers. Per the feature hierarchy, a structurally similar workflow in the wrong direction is not a domain exemplar. Result level: **No nearest exemplar (High confidence in the negative)**, with one **Low-confidence cross-domain pattern reference** surfaced below for the conditional-gating idiom our design depends on.

## Cross-domain pattern reference: `epigenetics/atacseq` (Low confidence, pattern comparison only)

The single highest-value corpus match for our design's riskiest mechanism — step-level `when:` gating fed by a boolean — is IWC `epigenetics/atacseq/atacseq` (label "ATAC-seq Analysis: Chromatin Accessibility Profiling"). It is not a domain exemplar (different science, opposite data direction) and must not be treated as one; it is cited purely for the `when` + boolean-inversion idiom, which it exercises in CI (`atacseq-tests.yml` sets both boolean inputs).

Converted view: `iwc-exemplar.gxwf.yml` (sliced subgraph, `gxwf convert --to format2 --compact --no-stateful`). Inline excerpt of the idiom (from that file):

```yaml
inputs:
  - id: Compute TSS enrichment Genome-wide
    type: boolean
    optional: false
    default: false
steps:
  - id: Compute TSSE on specified chromosome     # boolean inversion
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/map_param_value/map_param_value/0.2.0
    in:
      - id: input_param_type|input_param
        source: Compute TSS enrichment Genome-wide
    out:
      - id: output_param_boolean
    tool_state:
      input_param_type:
        type: boolean
        mappings:
          - {from: false, to: 'true'}
          - {from: true, to: 'false'}
      output_param_type: boolean
  - id: ATACseqQC TSSE GW                        # gated step
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/atacseqqc/atacseqqc_tsse/1.34.0+galaxy0
    in:
      - id: gtf
        source: Gene annotation file
      - id: inputbam
        source: remove PCR duplicates/outFile
      - id: when
        source: Compute TSS enrichment Genome-wide
    when: $(inputs.when)
```

What this settles for our template:

1. **`when:` reads a connected step input named `when`** (`$(inputs.when)` refers to the step's own connected inputs, confirmed against `lib/galaxy/workflow/modules.py` `evaluate_value_from_expressions` in the local Galaxy dev checkout). The boolean source may be a workflow-level boolean parameter input directly, or a tool output.
2. **Boolean negation is done with `map_param_value`, not with a negated expression** — the corpus maps `false→'true'` and `true→'false'`. For our `no_stats`/`no_read_qc` gates (run when the flag is false), the template should insert a `map_param_value` inversion step per flag, or rename the interface booleans. Preference: keep the source-faithful `no_stats`/`no_read_qc` names and add inversion steps.
3. Workflow-level boolean inputs are plain `type: boolean` gxformat2 inputs with `default` — matches our interface brief.

## Structural diff against our design briefs

| Our design element | Corpus precedent | Divergence / guidance |
|---|---|---|
| `list` collection of BAMs mapped over samtools steps | Common (atacseq, consensus-peaks, cutandrun map tools over collections) | None — idiomatic. |
| Identifier-synced parallel index list (`join` recipe) | Sibling-collection map-over with matching identifiers appears in consensus-peaks | Our wrappers may instead accept/derive the index internally; per-step implementation decides. Record. |
| Workflow boolean gates (`no_stats`, `no_read_qc`) | atacseq `when` + `map_param_value` inversion (excerpt above) | **Corpus-proven; adopt verbatim.** |
| String gate on non-empty `chr` (`pick_value` pass-through) | `pick_value` steps exist in several IWC workflows (bacterial-quality-control, VGP series); the transform-or-pass-through variant is pattern-documented but not yet corpus-dense | Low risk; keep open question 3 (chr identifier rename) — untested by selected test either way. |
| **Per-element `when` gating from mapped boolean files** (`is_paired`/`is_single` endedness routing) | **No IWC corpus use.** Galaxy's own test suite verifies it (`test_run_workflow_conditional_step_map_over_expression_tool`), and `lib/galaxy/workflow/modules.py` computes `when_values` per map-over iteration element (line ~1016-1046) | **Beyond IWC practice; rely on engine behavior, not corpus.** Template must keep this mechanism prominent for review; the planemo test is the real gate. Fallback if it fails: drop per-element routing and split the workflow by endedness (ledger escalation, not silent). |
| `param_value_from_file` mapped booleans | Used in IWC (consensus-peaks, mgnify amplicon) but not connected to `when` | Combination is upstream-verified only; same caveat as above. |
| FastQC mapped over collection → html/zip lists | Common (atacseq etc.) | None. |
| Flat `list` reads output assembled from null-filtered branches | Collection assembly via built-ins (`__MERGE_COLLECTION__`, filter null) appears in Galaxy tool set; corpus use of filter-null after when-skips is thin | Keep as placeholder transformation; the planemo test verifies. |
| MultiQC final report | Common in IWC | **N/A — dropped at this commit** (see data-flow brief; MultiQC receives only boilerplate). |

## Routing findings forward

- **Template/data-flow (next phase)**: use `map_param_value` inversion steps for `no_stats`/`no_read_qc` gates; wire `when` inputs per the excerpt; keep per-element endedness gating on the upstream-verified mechanism and mark it for test-driven confirmation.
- **Pattern issue**: the per-element-when + mapped-boolean-files combination has no IWC exemplar despite being engine-verified — a pattern-page candidate after this run's planemo result (not filed here; run is no-posting).
- **Tool-step issues** (samtools wrapper surfaces, fastq_utils UDT, check_endedness UDT) — deferred to the per-step loop per this skill's non-goals.
- **Test issues** — deferred to the test-plan phase; note that endedness routing and the reads assembly are the two mechanisms the test must actually exercise.

## Confidence

High (negative): no same-domain exemplar exists. Low (pattern): atacseq excerpt is cross-domain, used only for the `when` idiom. The per-element gating mechanism carries engine-verified but corpus-unproven status.
