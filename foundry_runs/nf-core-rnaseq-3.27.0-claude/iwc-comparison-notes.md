# IWC exemplar comparison — nf-core/rnaseq 3.27.0 → Galaxy

Produced by `compare-against-iwc-exemplar` (phase 5, run `rnaseq-to-galaxy`). Inputs: `nextflow-galaxy-interface.md`, `nextflow-galaxy-data-flow.md`, `open-requirements.ledger.yml`. Corpus: `galaxyproject/iwc` cloned to `~/.foundry/iwc` (main @ 2026-11-11).

## Nearest exemplar selection

| Rank | Candidate | Domain | Input topology | Tool-family overlap | Verdict |
|---|---|---|---|---|---|
| 1 | `transcriptomics/rnaseq-pe/rnaseq-pe` | RNA-seq PE quantification | `list:paired` collection + GTF + genome | fastp, rna_star, featurecounts, multiqc, pick_value, map_param_value (4/6 primary) | **nearest — Medium confidence** |
| 2 | `transcriptomics/rnaseq-sr/rnaseq-sr` | RNA-seq SE | `list` collection | same minus pairedness | same subgraph, single-end — rejected on topology (hierarchy tier 2) |
| 3 | `transcriptomics/rnaseq-de/rnaseq-de-filtering-plotting` | DE analysis | collection inputs | DESeq2-side only | rejected on tier 1 (analysis intent: post-quantification) |

Confidence is **Medium**, not High, per the rubric ("same domain and topology, but partial tool-family or output match"): quantification in the exemplar is STAR-counts + StringTie/Cufflinks FPKM — the Salmon pseudo-aligner path, UMI, rRNA-removal, trim-galore/other aligner branches, and per-sample strandedness of nf-core/rnaseq have **no corpus counterpart**. No candidate lacks domain alignment, so the result is not "no nearest exemplar."

## Structural diff against the briefs

### Where the exemplar validates our design (carry through to template)

| Brief decision | IWC precedent (`rnaseq-pe`) |
|---|---|
| Sample-sheet paired input → paired collection driving per-sample map-over (`data-flow` §element-identifier) | `Collection paired FASTQ files` (`list:paired`) feeds fastp directly; collection element identifiers carry sample identity end-to-end |
| Enum branches → gated subgraphs with `pick_value` fan-in (`data-flow` §enum-branches) | `Use featureCounts for generating count tables` boolean gates featureCounts via `when:`; `_unlabeled_step_25`'s `pick_value` (Counts table) selects between STAR counts and featureCounts output; two MultiQC branches + `pick_value` at both outputs |
| Flatten-at-MultiQC disposition (`data-flow` §MultiQC, flagged user-review) | MultiQC consumes fastp/STAR/featureCounts outputs directly from collections — the corpus precedent supports collection-native consumption rather than transpose reconstruction |
| Checkpoint outputs for testability (`interface` §outputs: gene_counts, salmon_quant, star_alignment_log, bam_stats) | `Mapped Reads`, `Counts Table` promoted as named workflow outputs; content-bearing, per `iwc-shortcuts-anti-patterns` (weak smoke checks alone are an anti-pattern) |
| Tests sibling to workflow (`iwc-test-data-conventions`) | `rnaseq-pe-tests.yml` + `test-data/` sibling directory — matches the layout `implement-galaxy-workflow-test` will emit |

### Where the exemplar diverges from our design (route to template + user review)

1. **Strandedness is workflow-level in IWC; per-sample in our brief.** `Strandedness` is a single enum input fanned into featureCounts/StringTie/Cufflinks via three `map_param_value` steps (from→to value mapping). Our interface carries per-sample `strandedness` from the sample sheet, re-attached via a sample-sheet→tabular bridge (`data-flow`). The corpus has **no per-sample strandedness idiom** — every IWC RNA-seq workflow inspected parameterizes it workflow-wide. Our design is richer (matches nf-core's per-sample capability) but is *without corpus precedent*: keep the bridge, mark it as a review point, and expect the per-sample tabular join machinery to be the least-proven part of the draft. A `map_param_value` step remains the right corpus-idiomatic tool when strandedness collapses to one value.
2. **Reference handling: cached built-in genome vs workflow-tier build-on-absence.** The exemplar passes `Reference genome` (a restricted string input naming a Galaxy-cached genome) into `rna_star`'s `genomeDir` and `compose_text_param` — indexes come from Galaxy's data-manager world. Our phase-2 brief chose workflow-tier build-on-absence with `pick_value(first_non_null(index_input, build_output))` because the source pipeline supports custom non-iGenomes references. Both are defensible; the corpus route requires a cached genome to exist, ours costs runtime when it doesn't. Route: template should wire STAR against a *conditional* reference source (cached-genome param as the happy path, build-on-absence subgraph as fallback), which neither brief currently states explicitly.
3. **Quantification family absent.** No Salmon, kallisto, or pseudo-aligner step exists in the exemplar; featureCounts+StringTie is the corpus's quantification idiom. The Salmon `quant.sf`/`quant.genes.sf` named-wrapper-outputs resolution (data-flow) and the `salmon_quant` interface output are *design inventions with no corpus backing* — they must not be pattern-matched away during template authoring; keep them as explicit draft steps.
4. **No UMI / rRNA-removal / contaminant-screening / BAM-start rows** in any inspected RNA-seq exemplar — consistent with the still-open ledger entries; the corpus does not discharge them.
5. **fastp adapter params as workflow inputs** (`Forward adapter`/`Reverse adapter` strings) — our interface exposes the full trimmer block; the exemplar shows the corpus norm is a minimal adapter surface. Not a conflict; noted for output-expansion discipline.

## Inline excerpt (nearest exemplar subgraph)

From `iwc-exemplar.gxwf.yml` (bounded subgraph of `transcriptomics/rnaseq-pe/rnaseq-pe`; steps `Collection paired FASTQ files` input, `remove adapters + bad quality bases`, `STAR: map and count and coverage splitted`, `Get featureCounts strandedness parameter`, `_unlabeled_step_21` (featureCounts), `_unlabeled_step_25` (Process Count files), `MultiQC without extra QC`, `MultiQC HTML report`/`MultiQC stats`). The two load-bearing idioms:

```yaml
- id: Get featureCounts strandedness parameter
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/map_param_value/map_param_value/0.2.0
  in:
  - id: input_param_type|input_param
    source: Strandedness
  tool_state:
    input_param_type:
      type: text
      mappings:
      - { from: 'stranded - forward', to: '1' }
      - { from: 'stranded - reverse', to: '2' }
      - { from: unstranded, to: '0' }
```

```yaml
- id: _unlabeled_step_21          # featureCounts
  in:
  - id: alignment
    source: 'STAR: map and count and coverage splitted/map'
  - id: strand_specificity
    source: Get featureCounts strandedness parameter/output_param_text
  - id: when
    source: Use featureCounts for generating count tables   # boolean gate
```

The full validated subgraph (`gxwf validate` → 13 tool-states OK, 0 skipped) is in the sibling `iwc-exemplar.gxwf.yml`.

## Routing findings forward

- **Template issues** (owned by `nextflow-summary-to-galaxy-template`): wire STAR's reference source conditionally (cached-genome happy path + build-on-absence fallback); keep per-sample strandedness bridge despite no corpus precedent, flagged; keep Salmon quant steps explicit; reuse `pick_value` fan-in shape for the counts table and MultiQC outputs verbatim.
- **Pattern issues**: per-sample metadata re-attachment (sample-sheet tabular join into collection flow) deserves a pattern page once proven in this run; `map_param_value` enum remapping is the corpus idiom for enum→tool-param translation.
- **Tool-step issues** (defer to `advance-galaxy-draft-step`/`discover-shed-tool`): all tool IDs remain symbolic until the loop; exemplar pins (iuc/fastp 1.4.0+galaxy0, iuc/rgrnastar rna_star 2.7.11b+galaxy1, iuc/featurecounts 2.1.1+galaxy1, iuc/multiqc 1.35+galaxy5) are *hints*, not decisions.
- **Test issues** (defer to `nextflow-test-to-galaxy-test-plan`/`implement-galaxy-workflow-test`): follow the `rnaseq-pe-tests.yml` sibling convention; checkpoint outputs named in the interface give content-bearing assertions, not just size checks.

## Ledger actions

Appended discoveries (none of the 7 open entries is closed — the corpus exemplar does not discharge any open obligation; it adds evidence, not resolution):

- `iwc-strandedness-workflow-level-precedent` — corpus precedent is workflow-level strandedness; our per-sample bridge is a deliberate divergence to preserve.
- `iwc-cached-genome-precedent` — corpus precedent is data-manager-cached genomes; supports an optional conditional reference source in the template beyond our build-on-absence posture.

## Confidence and provenance

Exemplar ranking and diff: **Medium confidence** overall (domain+topology exact, tool family partial). Corpus state: galaxyproject/iwc main, cloned 2026-11-11, unpinned (the skill prescribes clone-or-pull, not a revision pin; re-ranking on a later corpus state may differ). Comparison notes authored from the converted gxformat2 view (`gxwf convert --to format2 --compact`), not the raw `.ga`. Briefs consumed: interface rev phase-3, data-flow rev phase-4.
