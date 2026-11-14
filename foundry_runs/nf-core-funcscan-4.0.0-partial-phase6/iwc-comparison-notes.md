# IWC exemplar comparison — nf-core/funcscan 4.0.0

Artifact `iwc-comparison-notes`. Produced by `compare-against-iwc-exemplar` (phase 5 of
`pipeline-nextflow-to-galaxy`, run `funcscan-run1`). Consumes `nextflow-galaxy-interface.md`
and `nextflow-galaxy-data-flow.md`; sibling artifact `iwc-exemplar.gxwf.yml`; re-emits
`open-requirements.ledger.yml`. Every count below is machine-measured (appendix A lists the
commands and what each produced); nothing here is estimated by eye.

## 0. Scope and method

- **Corpus actually used:** `~/Desktop/bioHackthon/iwc/workflows` — the local IWC
  fixtures the operator named. `~/.foundry/iwc` does not exist on this machine, so the
  procedure's "clone or pull to `~/.foundry/iwc`" step was **not** executed: nothing was
  cloned, fetched or installed, and no file was written outside the run directory and
  `/tmp/gxy-scratch/`.
- **Corpus size:** 133 `.ga` workflow files, 135 `*-tests.yml` test-definition files,
  157 test documents, 342 input fixtures. Structural ranking parsed 130 of 133; three
  `VGP-assembly-v2` files (`Assembly-Hifi-HiC-phasing-VGP4`, `Assembly-Hifi-Trio-phasing-VGP5`,
  `Assembly-Hifi-only-VGP3`) carry step entries that are not objects and were skipped. They are
  genome-assembly workflows, outside funcscan's domain, so the ranking is over 130 candidates.
- **Normalisation:** `gxwf` 1.15.0, `convert --to format2 --compact`, on the chosen exemplar only
  (converting all 133 was unnecessary once the ranking was settled on step/input/tool/gate
  counts, which the native format carries).
- **Reading boundary honoured:** reads were confined to the run directory, `funcscan-test/`, the
  IWC fixtures, and the funcscan clone the run record points at
  (`~/Desktop/bioHackthon/nf-core-funcscan`, read-only, unmodified). Two extra reads
  outside that set were needed to fill the feedback ledger's required identity fields: the phase-5
  mold's `_provenance.json` and a `shasum` of its cast `SKILL.md`. No Foundry *source* content was
  consulted for design decisions, and the packaged reference notes were not re-opened this phase.
- **Phase 3 was not amended and phase 6 was not started.** Two corpus findings bear on the four
  `held-for-operator-decision` recommendations and are reported in §7 as inputs to that decision
  only.

## 1. Exemplar chosen, and confidence

**`microbiome/metagenomic-genes-catalogue/metagenomic-genes-catalogue` — confidence: Medium.**

Ranking was a deterministic score over every workflow (3 × matched funcscan tool families + domain
weight + collection inputs + distinct collection-op families + MultiQC + Tooldistillator + gated
steps + multi-valued inputs + test documents), then hand-verification of the leaders against the
two briefs. Funcscan tool ids were canonicalised first (`ncbi-amrfinderplus` → `amrfinderplus`,
`r-ampir` → `ampir`), which matters: matching raw names against Tool Shed ids under-counts.

| score | workflow | domain | steps | collection inputs | gated steps | promoted | tests | funcscan families |
|---|---|---|---|---|---|---|---|---|
| **28** | **metagenomic-genes-catalogue** | microbiome | 43 | 1 | 4 | 23 | 1 | abricate, amrfinderplus, argnorm, mmseqs2, prodigal, seqkit |
| 18 | MAGs-generation (`mags-building`) | microbiome | 69 | 5 | 3 | 8 | 2 | — none — |
| 16 | metagenomic-assembly | microbiome | 32 | 4 | 2 | 9 | 5 | — none — |
| 16 | single-sample-binning | microbiome | 53 | 2 | 11 | 12 | 2 | seqkit |
| 15 | functional-annotation-of-sequences | genome_annotation | 18 | 1 | 4 | 19 | 4 | interproscan |
| 15 | metagenomic-raw-reads-amr-analysis | microbiome | 29 | 1 | 0 | 17 | 1 | argnorm, deeparg |
| 13 | amr_gene_detection | bacterial_genomics | 13 | 0 | 0 | 16 | 1 | abricate, amrfinderplus |
| 12 | bacterial_genome_annotation | bacterial_genomics | 14 | 0 | 3 | 31 | 1 | bakta |

Why Medium and not High, stated precisely: same domain (microbiome functional characterisation),
the largest tool-family overlap in the corpus, the same output shape (many promoted per-tool
tables plus one MultiQC report), and the DAG motifs funcscan needs most — step-level `when:`
gates, `pick_value` cascades, a *gated* lane subworkflow, and a variable-membership table fan-in —
all present. It is not High because **input collection topology, the #2 feature, diverges**: the
exemplar takes one `list:paired` read collection, funcscan takes four parallel per-sample
`sample_sheet` collections (§3.2), and 16 of funcscan's 26 tool families appear nowhere in the
corpus (§3.3). The confidence table's rows do not describe this combination (§8, feedback entry).

Secondary exemplars, named for the template Mold but **not** emitted as artifacts:

| workflow | what it is the exemplar for | confidence |
|---|---|---|
| `genome_annotation/functional-annotation/functional-annotation-of-sequences` | the PROTEIN_ANNOTATION lane: InterProScan as an optional step behind a `Run InterProScan` boolean + a mode select, and the only shortlist member whose **4 test docs flip gate arms** | Medium (single-tool lane) |
| `bacterial_genomics/bacterial_genome_annotation` | the ANNOTATION lane: `bakta` behind `Run Bakta`, `pick_value` labelled "Pick the main bakta file if the tool is run.", and twin `tooldistillator` / `tooldistillator without bakta` branches | Medium |
| `microbiome/metagenomic-raw-reads-amr-analysis` | the only DeepARG user in the corpus, plus argNorm harmonisation → Tooldistillator → MultiQC; note its wrapper is `deeparg_short_reads` (reads), funcscan runs DeepARG on proteins | Low–Medium |
| `microbiome/multi-sample-binning` | the **only** `__CROSS_PRODUCT_NESTED__` in 133 workflows, and 10 gated steps: pattern comparison for funcscan's cross-product axes only | Low (cross-domain) |
| `microbiome/metagenomic-assembly` | the only `__HARMONIZELISTS__`, plus `__FILTER_EMPTY_DATASETS__`: pattern comparison for the emptiness filters | Low (cross-domain) |

**No exemplar exists for the AMP, BGC or CAZYME lanes** — see §3.3.

## 2. What the exemplar is

43 native steps → 36 non-input steps + 7 workflow inputs; 24 distinct tools; 23 promoted outputs;
one embedded subworkflow (5 inputs / 22 steps / 4 outputs); 7 `pick_value` steps; 7 gated steps
carry `when:` (4 distinct in the converted view); 1 MultiQC step with **seven** numbered
`results_N|software_cond|input` slots; one test document.

The shape that matters for this run: reads → MEGAHIT → rename contigs → Prodigal → **two mutually
exclusive clustering arms** (full gene catalogue vs ARG-specific) → **AMRFinderPlus + ABRicate +
starAMR fanning off one sequence set** → per-tool `Collapse Collection` → argNorm → a **gated
subworkflow** that joins five differently-shaped tables → `pick_value` fallbacks → MultiQC. That is
funcscan's trunk → gated annotation → parallel screening lanes → per-lane table shape, in one
workflow, with six of funcscan's tools.

## 3. Structural diff, in feature-hierarchy order

### 3.1 Domain / analysis intent — match
Microbiome functional characterisation of assembled sequence, ending in per-tool tables plus a
MultiQC report. funcscan's intent minus assembly-from-reads, minus AMP/BGC/CAZyme. No competing
candidate is closer on intent; the next domain-matched candidates are either genome-annotation
single-lane workflows or binning pipelines.

### 3.2 Input collection topology — **the central divergence**
- Corpus, all 133 workflows: collection-typed workflow inputs occur in exactly two shapes —
  `list` (87) and `list:paired` (37). `nested_collection_type` is unset on every one. There is
  **no `folder` input, no `list:list` input, and no nested collection at the input boundary**
  (46 test fixtures *do* supply nested collections, so nesting is exercised internally).
- Workflow input declarations corpus-wide: `parameter_input` text 225 / integer 176 / boolean 63 /
  float 43, `data_input` 97 untyped + typed sets, `data_collection_input` 88 + 7 + 7.
  Across 45 distinct declared formats, **zero `sample_sheet` inputs anywhere in the corpus**; the
  closest are `tabular` (16 + 1 with a leading space), `csv` (4), `tsv` (2), `qiime2.tabular` (1).
  The exemplar's one collection input carries `column_definitions: null`.
- Briefs: four parallel `sample_sheet` inputs (`input_fasta` required, `input_protein`, `input_gbk`,
  `input_gff` with a `gff_type` column), element id = sample id, `sample` → `element_identifier`.
- **Delta:** funcscan's input shape has no precedent in this corpus, and the corpus's alternative
  is one nested collection instead of four aligned flat ones. Per-element metadata through
  map-over (the `gff_type` column) has no corpus precedent to copy either, since no corpus input
  declares `column_definitions`. → *ledger:* new gap `no-sample-sheet-input-precedent-in-corpus`;
  *routing:* template/data-flow + pattern.

### 3.3 Primary tool families — partial, and lopsided
Of 26 canonical funcscan tools, **10 appear somewhere in the corpus and 16 appear nowhere**:
`ampcombi, ampir, amplify, antismash, bigslice, dbcan, deepbgc, diamond, fargene, gecco,
hamronization, hmmer, macrel, prokka, pyrodigal, rgi`. The 10 that do appear are rare in it:
`seqkit` 4 files, `abricate` 3, `amrfinderplus` 2, `argnorm` 2, and `bakta`, `interproscan`,
`deeparg`, `prodigal`, `mmseqs2`, `tabix` 1 each.
- **Delta:** the exemplar legitimately informs the ARG lane and the annotation/protein-annotation
  trunk. It says nothing about AMP (amplify/ampir/macrel/ampcombi), BGC (antismash/deepbgc/gecco)
  or CAZYME (dbcan), which are 3 of the 4 screening lanes and 58 of the 82 abstract nodes
  (AMP 17 + ARG 24 + BGC 19 + CAZYME 5 — only ARG has corpus support). Also note `rgi`, `hmmer`
  and `prokka` are absent even though their wrappers are the most conventional in the pipeline: a
  per-step loop for those cannot pattern-match against any IWC workflow.
  → *ledger:* new gap `sixteen-funcscan-tool-families-absent-from-iwc`; *routing:* tool-step tier.

### 3.4 DAG motifs and structural recipes — where the exemplar pays
Corpus census: **125 gated steps across 29 of 133 workflows.** Idiome prevalence (workflow file
counts): `pick_value` 30, `map_param_value` 26, collapse-collections 29,
`collection_element_identifiers` 25, `collection_column_join` 15, `__APPLY_RULES__` 15,
`__RELABEL*` 14, `__FLATTEN__` 11, `__FILTER_EMPTY_DATASETS__` 8, `__BUILD_LIST__` 7,
`__MERGE_COLLECTION*` 6, `__CROSS_PRODUCT*` **1**, `__HARMONIZELISTS__` **1**, `sync_collections`
**0**, legacy `type: conditional` steps **0**, embedded/nested subworkflow steps 34,
`tooldistillator` 7 (24 files contain the step *and* at least one gate).

1. **Gates are real and they are step-level.** Every one of the 125 carries the literal
   `when: $(inputs.when)`; the value's provenance is the step's `input_connections.when` →
   `{id, output_name}`. Resolved: **42 gates are fed directly by a workflow input** ("Run Bakta",
   "Full genes catalogue", "Generate additional QC reports") and **83 by a computed step** —
   `map_param_value` 47, a nested subworkflow's `when` 32, `param_value_from_file` 2,
   `pick_value` 2.
2. **…but not one gate tests data.** All 125 booleans are computed in *parameter space* (a param
   transform, or another gate). There is **no corpus workflow that gates a step on a dataset
   property** — non-emptiness, size, or format. The mechanism phase 4 needed (`when:` fed by a
   step output) is attested; the predicate it needs is not. 18 per-element emptiness filters and 5
   data-inspecting gates still have no corpus construction. → *ledger:* confirms
   `data-derived-gate-needs-nonemptiness-threshold` and `input-datatype-cannot-gate-a-step`;
   new discovery `corpus-gates-live-in-parameter-space`; *routing:* pattern.
3. **Negation happens in step space.** The exemplar expresses "run the ARG-specific sub-part only
   when the full catalogue is off" as a two-step chain: a *gated* `pick_value` (`when:` ← the form
   boolean, state `pick_style: first_or_default`, `pick_from: [false]`, `default_value: true`)
   feeding a second ungated `pick_value` whose `default_value: true` fires when the first was
   skipped, and that boolean feeds two downstream gates plus the gated subworkflow. No gate in the
   corpus is written as a negated expression. funcscan's `*_skip_*` params are exactly this
   inverted shape, so the idiom transfers — at two extra steps per inverted gate, i.e. on top of
   the 11 gates the data-flow brief counts. → *ledger:* new discovery
   `corpus-inverts-gates-in-step-space-with-two-pick-values`; *routing:* template + pattern.
4. **Twin cascade is the corpus's `if/else pass-through`.** `_unlabeled_step_35` is
   `pick_value` with `pick_style: first` over two connected sources — the gated arm's output and
   the ungated fallback — promoted as "MMseqs2 representative sequences". The exemplar carries four
   such two-source cascades; 30 corpus workflows use `pick_value`. This is the concrete shape for
   funcscan's else-branches (§10's 13→11 table), replacing prose. → *routing:* template.
5. **Fan-in of a variable number of things has three attested recipes** where phase 4 recorded
   none: (a) `Collapse Collection` (`collapse_dataset`) over a collection whose membership varies
   because gated producers emit nothing — 29 workflows; (b) `collection_column_join` for
   per-identifier table merges — 15 workflows; (c) a consuming step with **fixed named optional
   inputs** — the exemplar's MultiQC has exactly seven `results_N|software_cond|input` slots, and
   its gated subworkflow takes five named inputs of three different shapes.
   → *ledger:* resolves `variable-arity-fan-in-has-no-attested-galaxy-recipe` (scope-limited, see
   §7); new discovery `multiqc-wrapper-offers-fixed-numbered-result-slots`; *routing:* template.
6. **Gated lane subworkflow.** The exemplar's lane body is embedded in the step, gated by
   `when:`, taking 5 named inputs and emitting 4 promoted outputs, and its consumers paper over
   its absence with `pick_value` fallbacks. That is funcscan's AMP/ARG/BGC/CAZYME call shape
   (3–5 positional args, outputs consumed by a summary step) and it supports phase 4's
   medium-confidence call that a subworkflow can be instantiated as two steps — as a *pattern*,
   not as proof: the exemplar instantiates one subworkflow once.
7. **Empty elements.** `__FILTER_EMPTY_DATASETS__` (8 workflows) drops empty elements from a
   collection without branching. That covers the *filter* half of funcscan's 18 emptiness filters;
   routing one element to a different arm per element is still unattested.
8. **Cross product.** Exactly one corpus workflow uses `__CROSS_PRODUCT_NESTED__`, in an unrelated
   domain, and none uses `sync_collections_by_id`. funcscan's `nested-collection-dot-product`
   question is therefore still open; `gxwf draft-validate` on a draft remains the check, which
   phase 5 cannot perform (no draft exists yet, and authoring one is phase 6/7 work).
9. **Reference databases are pick-lists, not data.** Of inputs whose label contains
   db/database/index, **44 are `parameter_input` text, 12 are untyped `data_input`, and none is a
   collection**. In the exemplar the four DB inputs are declared `type: string` ("Select the
   database to identify AMR genes with AMRFinderPlus.") and its test fixture passes option-like
   values (`resfinder`, `amrfinderplus_V4.2_2026-05-15.1`,
   `staramr_downloaded_07042025_…`) — i.e. the database list is resolved *inside the tool*, not
   supplied by the user. That settles the multi-DB pick-list question and *raises* a posture
   conflict: this run's reference-data brief chose explicit optional inputs with in-tool rebuild,
   and 0 corpus workflows pass a database directory as data.
   → *ledger:* resolves `multi-db-pick-list-no-galaxy-exemplar`; keeps
   `db-directory-input-shape-unsettled` open with corpus evidence appended; *routing:* template +
   tool-step.

### 3.5 Output types and report shape — precedent in scale, divergence in content
- Promoted outputs per workflow: **median 8, p90 25, max 81**. funcscan promotes **61** result
  sets (from 61 `publishDir` sites) against one emitted MultiQC output in the source. So 61 is
  precedented but far off the norm — roughly the 95th percentile of this corpus — and the exemplar
  itself promotes 23.
- The exemplar's report content is the opposite of funcscan's. Its MultiQC is fed by seven
  `results_N` slots carrying **screening-table-derived** datasets (Quast tabular meta, staramR
  detailed summary with columns removed, collapse/argNorm outputs), and in
  `bacterial_genomics/amr_gene_detection` the chain is explicit: `tooldistillator` →
  `tooldistillator_summarize` → `multiqc`, with `tooldistillator_results_amr` and
  `tooldistillator_summarize_amr` both promoted. funcscan's `multiqc_report` contains versions, a
  parameter summary, a methods blurb and Prokka/Bakta stats — **nothing from any screening lane**
  (phase 4 discovery `multiqc-report-carries-no-screening-results`). The corpus shows the missing
  route and the tool that builds it. 36 of 133 workflows run MultiQC; 7 use Tooldistillator; 2 use
  both. → *ledger:* new gap `multiqc-receives-no-lane-results-unlike-corpus-idiom`; *routing:*
  template, and it is the operator's call because it changes the promoted-output list that the
  held phase-3 recommendations also touch.

### 3.6 Test style and fixture topology — the sharpest divergence
- Corpus test definitions are `- doc: / job: / outputs:` documents. **157 docs, 342 fixtures:
  146 `class: Collection`, 114 `class: File` by remote `location:` URL, 82 `class: File` by local
  `path:`, 46 of the collections nested.** Assertion spellings are mixed three ways: 258
  `{that: has_text, rule: …}`-style, 84 + 47 + 41 + 39 + … single-key `{has_text: {text: …}}` /
  `{has_archive_member: …}` shorthand, and **237 bare-string asserts**.
  Content assertions dominate: `has_text` 258, `has_line` 82, `has_n_lines` 79, `has_n_columns` 56,
  `has_size` 48, `has_text_matching` 27, `has_line_matching` 17, `not_has_text` 8.
- Gates and tests interact: of the 29 gated workflows, **16 ship a single test doc** (one arm), 7
  ship two, 5 ship more. `functional-annotation-of-sequences` — the closest lane analog — ships
  **four docs that flip `Run InterProScan` and `Run eggNOG + completeness calculation` across
  true/false and assert different output sets per doc (4 / 5 / 2 / 3 outputs)**. That is the corpus
  answer to "which gate arm does the first Galaxy test exercise": one doc per arm combination, and
  funcscan has 11 gates.
- The exemplar's own single test passes `Full genes catalogue: false`, i.e. it exercises the
  **false arm** of the catalogue gate and the true arm of the inverted ARG gate — and its asserted
  outputs include `MultiQC Report` with `has_text: AMRFinderPlus` / `ABRicate`, i.e. the report is
  asserted *by content* because the lane tables were fed into it.
- funcscan's side: `test_selection.status = selected`, candidate
  `tests/default.nf.test::-profile test` (of 14 candidates), 2 inputs (a remote CSV samplesheet and
  a remote HMM), and 12 expected outputs expressed as **publishDir paths**
  (`amp/ampir/sample_1/sample_1.ampir.faa`, …). Galaxy test docs address **promoted output
  labels**, not paths, and the corpus never uses a samplesheet-shaped fixture.
  → *ledger:* new gap `arm-coverage-needs-one-test-doc-per-gate-combination`; *routing:* test tier
  (phase 9/10). Also a note for phase 8: funcscan's remote CSV samplesheet must become four
  collections (or the interface's alternative), and its HMMs become text/option inputs or files
  depending on §3.4 item 9.

## 4. Nearest exemplar (gxformat2) — inline excerpt

Workflow id `microbiome/metagenomic-genes-catalogue/metagenomic-genes-catalogue`; steps covered:
the gate-value chain (`_unlabeled_step_8`, `_unlabeled_step_11`), a gated tool step
(`MMseqs2 ARGs Sequence Clustering`), and one twin cascade (`_unlabeled_step_35`). Verbatim from
`iwc-exemplar.gxwf.yml`, with two exceptions, both visible: `tool_state` blocks are elided where they
are not load-bearing (marked `# (tool_state elided)`), and any other `#` comment in the excerpt below is
this file's annotation, not corpus text — the YAML payload on those lines is unaltered. Line numbers
refer to that file.

```yaml
# lines 110-133 — a gate value: the step itself is gated on the form boolean,
# and when it is skipped its consumer's default takes over
- id: _unlabeled_step_8
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0
  in:
  - id: when
    source: Full genes catalogue          # a workflow input of type: boolean
  out: []
  tool_state:
    style_cond:
      pick_style: first_or_default
      type_cond:
        param_type: boolean
        pick_from:
        - __index__: 0
          value: false
        default_value: true
  when: $(inputs.when)

# lines 154-177 — the inversion/default step: picks the value above if it exists, else true
- id: _unlabeled_step_11
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0
  in:
  - id: style_cond|type_cond|pick_from_0|value
    source: _unlabeled_step_8/boolean_param
  out: []
  tool_state:
    style_cond:
      pick_style: first_or_default
      type_cond:
        param_type: boolean
        pick_from:
        - __index__: 0
          value:
            __class__: ConnectedValue
        default_value: true               # fires when step 8 was skipped

# lines 1203-1217 — the gated step: guard references its own connected input, not a literal
- id: MMseqs2 ARGs Sequence Clustering
  label: MMseqs2 ARGs Sequence Clustering
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/mmseqs2_easy_linclust_clustering/mmseqs2_easy_linclust_clustering/18-8cc5c+galaxy0
  in:
  - id: input_fasta
    source: _unlabeled_step_29/data_param
  - id: when
    source: _unlabeled_step_11/boolean_param
  when: $(inputs.when)
  # (tool_state elided)

# lines 1277-1307 — the twin cascade that replaces an if/else pass-through, and is promoted
- id: _unlabeled_step_35
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/pick_value/pick_value/0.2.0
  in:
  - id: style_cond|type_cond|pick_from_0|value
    source: MMseqs2 full catalogue Sequence Clustering/output_rep_seq
  - id: style_cond|type_cond|pick_from_1|value
    source: MMseqs2 ARGs Sequence Clustering/output_rep_seq
  out:
  - id: data_param
    rename: MMseqs2 representative sequences
  tool_state:
    style_cond:
      pick_style: first
      type_cond:
        param_type: data
        pick_from:
        - __index__: 0
          value: {__class__: ConnectedValue}
        - __index__: 1
          value: {__class__: ConnectedValue}
```

Outside the slice, the MultiQC fixed-slot wiring quoted in §3.4 item 5(c), verbatim from the same
conversion of the full workflow:

```yaml
- id: _unlabeled_step_42
  tool_id: toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc/1.35+galaxy4
  in:
  - id: results_0|software_cond|input
    source: _unlabeled_step_10/report_tabular_meta
  - id: results_1|software_cond|input
    source: _unlabeled_step_28/output_tabular
  # results_2 … results_6 follow the same shape
```

## 5. The sibling artifact `iwc-exemplar.gxwf.yml`

- Produced by `gxwf convert --to format2 --compact` on the exemplar `.ga` (43 native steps →
  36 non-input steps, `class: GalaxyWorkflow`, release `1.6`, original `uuid` preserved), then
  pruned to a **dependency-closed** subgraph: seed = every step with a `when:`, the embedded
  subworkflow, every `pick_value`, the three screening tools, the two `Collapse Collection` steps
  and argNorm; closure over `in[].source`; promoted outputs whose producer fell outside are
  dropped. **22 of 36 steps, 5 of 7 inputs, 15 of 23 promoted outputs, 1,338 lines / 39,436 bytes**
  (the embedded subworkflow's 22 inner steps are most of it — kept whole, because "a lane body you
  can gate" is the idiom being surfaced).
- `gxwf validate` on the emitted file (re-run after writing these notes, exit 0): **Structural
  validation: OK**, `Tool state: 43 validated, 0 skipped`. The 43 counts the 22 slice steps *and* the
  22 inner steps of the embedded subworkflow less the container — the same command on the unpruned
  36-step conversion reports 57, so the two numbers differ by the pruned branch, not by anything
  hand-edited. The file re-parses as YAML with 4 gated steps and no dangling `in:` source. Nothing was
  rewired or relabelled; the only edits are the header comment block and the `name:` field, both
  documenting the pruning.
- Deliberately outside the slice: the MultiQC tail and the taxonomy branch (Quast, eggNOG, MMseqs2
  taxonomy, CoverM, Krona) that exists only to feed it. Dropping them removed 12 steps that carried
  no motif this run needs; their MultiQC wiring is quoted in §4 instead.

## 6. Findings, routed

| # | finding | evidence | routed to | ledger |
|---|---|---|---|---|
| 1 | funcscan's four parallel `sample_sheet` inputs have zero precedent; the corpus alternative is one nested collection, and no corpus input declares `column_definitions` | 0 `sample_sheet` formats in 133 workflows; input shapes `list` 87 / `list:paired` 37 only | template/data-flow; pattern page needs corpus evidence it lacks | new gap |
| 2 | `when:` gates are attested (125 steps / 29 workflows) but every derived gate is parameter-space; no corpus gate tests data | 42 form-input gates, 83 derived (`map_param_value` 47, subworkflow 32, `param_value_from_file` 2, `pick_value` 2), 0 dataset-derived | pattern (the `when:` construction note) | 2 entries confirmed, 1 discovery |
| 3 | inverted gates are built with two `pick_value` steps, not a negated expression — add steps for every `*_skip_*` param | exemplar steps 8→11 feeding 2 gates + 1 gated subworkflow | template; pattern | 1 discovery |
| 4 | twin-cascade `pick_value` is the concrete shape for the 13→11 else-branches | 4 cascades in the exemplar; `pick_value` in 30 workflows | template | §10 note |
| 5 | variable-arity fan-in now has three candidate recipes (collapse over a variable collection; `collection_column_join`; fixed named optional slots) | collapse 29, column-join 15, MultiQC's 7 slots, gated subworkflow's 5 named inputs | template | 1 entry resolved, 1 decision, 1 discovery |
| 6 | multi-DB pick-lists are `type: string` selects resolved inside the tool — and 0 corpus workflows pass a DB directory as data, which conflicts with this run's in-tool-rebuild posture | 44 text vs 12 untyped data vs 0 collection db-labelled inputs; fixture values `resfinder`, `amrfinderplus_V4.2_2026-05-15.1` | template + tool-step; posture question for the operator | 1 resolved, 1 narrowed |
| 7 | no corpus support for 3 of 4 screening lanes: 16 of 26 tool families absent from all 133 workflows | §3.3 counts | tool-step tier (phase 7) | new gap |
| 8 | 61 promoted outputs is ~p95 of this corpus (median 8, p90 25, max 81); the exemplar promotes 23 | distribution over 133 | template + test tier (assert a subset) | new gap |
| 9 | the corpus feeds screening tables into MultiQC (often via Tooldistillator); funcscan's report carries no lane results at all | exemplar `results_0…6`; `tooldistillator`→`_summarize`→`multiqc` in `amr_gene_detection`; 36 MultiQC / 7 Tooldistillator | template — **and operator decision**, it touches the promoted-output list | new gap |
| 10 | test style: corpus fixtures are collections + `test-data/` or remote files with content asserts; funcscan's evidence is path-based nf-test expectations over a remote CSV samplesheet | §3.6 counts | test tier (phase 9/10), test-data branch (phase 8) | 1 new gap |
| 11 | gate-arm coverage is done by multiple test docs flipping booleans | `functional-annotation-of-sequences` 4 docs; 16 of 29 gated workflows ship only 1 doc | test tier | same gap as 10 |

## 7. Ledger deltas, and the two items that touch the held phase-3 decisions

`open-requirements.ledger.yml` after this phase: **19 discoveries (+3), 30 entries (28 open,
2 resolved; +5 gaps), 17 decisions (+1)**, 4 `brief_change_recommendations` untouched. 2 entries
resolved, 6 annotated, 5 gaps + 3 discoveries + 1 decision appended; nothing was surrendered and no
phase-3 or phase-4 text was edited. Counted, not assumed: all 25 entries this phase inherited carried
`status: open`, and the two entries that read as dropped do so through `kind: dropped` while staying
`status: open` — so `status: resolved` is the first status change this ledger has had, which is why the
two resolutions state their scope and reopen condition explicitly.

Relevant to the four `held-for-operator-decision` recommendations — reported, **not applied**:
- **`annotation-tool-override-belongs-on-the-form`.** The corpus precedent is a boolean form input
  plus a `pick_value` ("Pick the main bakta file if the tool is run." in
  `bacterial_genome_annotation`), and §3.4 item 3 shows the corpus pays two steps per inverted
  gate. Both the "hoist it to the form" option and the "repeat the expression" option now have a
  measured corpus cost attached; the corpus never encodes a *derived* tool-identity test in a gate.
- **`versions-output-has-no-producer` / `interproscan-table-binds-to-the-rewrite-step`.** Both are
  promoted-output questions, and finding 8 (61 promoted outputs ≈ p95) plus finding 9 (the corpus's
  report route) are the two places where the corpus has an opinion on that list.

## 8. What this comparison could not settle

- Whether `when:` *can* be fed a dataset-derived boolean. The corpus shows the connection shape and
  83 computed gates, and not one dataset-derived predicate. Absence of precedent, not proof of
  impossibility — and Galaxy's expression language is outside this run's readable source set, so no
  claim is made about it.
- Whether a dot-product/Apply-rules zip works over nested `list:list` collections with
  ragged inner axes. One `__CROSS_PRODUCT_NESTED__` use exists, cross-domain; verifying funcscan's
  use needs a draft to run `gxwf draft-validate` against, which does not exist before phase 6.
- Directory-shaped database inputs (antismash, dbcan, gecko): 0 corpus precedent, so the untar-
  versus-directory choice stays an authoring-time decision.
- Nested `list:list` and `folder` input semantics: 0 occurrences at any input boundary in 133
  workflows, so the corpus is silent rather than negative.
- The three unparseable VGP files (§0) were excluded from the ranking; they are genome-assembly
  workflows and would not have ranked above the leader on tool families in any case, but the
  exclusion is recorded rather than assumed harmless.
- Whether the exemplar's single embedded subworkflow generalises to phase 4's "one ANNOTATION
  subworkflow instantiated as two steps" (§5 of that brief). The corpus instantiates one
  subworkflow once; the two-instance recommendation is untested here and stays medium confidence.

## 9. Confidence statement

Medium confidence in the exemplar choice and in the corpus censuses (§3.2, §3.4, §3.5, §3.6),
which are direct measurements over 133 files. Low confidence in any inference of the form "Galaxy
cannot X because no IWC workflow does X" — §8 states the three places where that temptation was
declined. The single largest limit on this artifact's usefulness is that the corpus is 133 legacy
`.ga` files: the shape of a *modern* format2-native IWC workflow with `sample_sheet` inputs and
`when:` expressions written by hand is not observable here, so "no precedent" findings about
`sample_sheet` inputs in particular should be read as "no precedent in this fixture snapshot".

## Appendix A — how each number was measured

All scripts live in `/tmp/gxy-scratch/`, all run with `python3 -I`, all read-only on the corpus and
the run directory. Re-runnable, in the order used:

1. `iwcscan.py <iwc-workflows> <run>/summary-nextflow.json --full=3` — canonicalises funcscan tool
   names and IWC Tool Shed ids, scores and ranks all 133 `.ga`, prints the top table and full
   fingerprints (the numbers in §1 and §2). Reported `parsed=130 failed=3`,
   `promoted-output counts: max=81 median=8 … tests total=214`.
2. `iwcidioms.py <iwc-workflows> metagenomic-genes-catalogue` — per-input facts parsed from each
   step's `tool_state` JSON (not raw-text matching), giving the input-kind table, the db-labelled
   input split, collection-input shapes, the promoted-output distribution, the gate connection
   shapes and the fixture/assert counts (§3.2, §3.4 item 9, §3.5, §3.6).
3. `iwcgates.py <iwc-workflows> metagenomic-genes-catalogue` — resolves
   `input_connections.when.{id,output_name}` to the producing step and classifies it as
   form-input vs derived (§3.4 items 1–2), and dumps the exemplar's ordered step inventory.
4. `phase5facts.py <iwc-workflows> <run> <converted-full.yml>` — assert-spelling census, the
   exemplar's test document, funcscan's selected test candidate from `summary-nextflow.json`, the
   MultiQC slot wiring, the Tooldistillator chain in `amr_gene_detection`, the ledger inventory, and
   the brief-side counts re-read from the two briefs.
5. Corpus tool-coverage probe (§3.3) — union of matched funcscan tool families over all 133 files.
6. `gxwf convert --to format2 --compact` then `iwcprune.py <full.yml> <run>/iwc-exemplar.gxwf.yml`
   then `gxwf validate` on the result (§4, §5).

One caveat that changed results mid-phase, recorded because it produced three wrong numbers before
they were corrected: in this corpus `tool_state` is a **JSON string** inside the step, a step's
`when` is the literal string `"$(inputs.when)"` with provenance in `input_connections`, and
`inputs`/`outputs` are **lists** keyed by `id`, not maps. Raw-text or format2-shaped probes against
these files return zeros that look like corpus facts — the first pass reported "0 sample-sheet
inputs, 0 text DB params, 0 gates traceable", of which only the first happened to be true. The
figures above all come from parsed values.
