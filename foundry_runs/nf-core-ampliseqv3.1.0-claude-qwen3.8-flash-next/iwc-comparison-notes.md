# IWC comparison notes — nf-core/ampliseq 3.1.0 → Galaxy

Corpus: `~/.foundry/iwc` @ ed48e2f (2026-11-10, pulled). Candidates normalized with `gxwf convert --to format2 --compact --no-stateful` into `<run>/iwc-converted/` (IWC amplicon workflows are all legacy `.ga`; `--no-stateful` avoids tool-cache dependency for structural comparison).

## Ranking (feature hierarchy: domain → topology → tool families → DAG motifs → outputs → tests)

| Candidate | Domain | Topology | Tool families | DAG motifs | Verdict |
|---|---|---|---|---|---|
| `amplicon/dada2/dada2_paired` | 16S amplicon DADA2 — exact | `list:paired` collection input ≈ our sample_sheet→flattened spine | IUC `dada2_*` R wrappers = our DADA2_* modules | filterAndTrim map-over → per-direction pooled learnErrors → dada → mergePairs → makeSequenceTable → removeBimera → assignTaxonomy + seqCounts stats fan-in | **Nearest — Medium** (stops before primer trimming, diversity, reports; fixture is raw collection, not a sheet) |
| `amplicon/qiime2/qiime2-IIb-…paired-end` | amplicon denoising | single dataset-collection step | q2d2 `qiime2__dada2__denoise_paired` | whole-collection denoise in one job (contrasting idiom to our per-group chain) | Secondary, Medium — covers stage-15-adjacent QIIME2 import/table idioms |
| `amplicon/qiime2/qiime2-III-V…`, `…VI-diversity…` | amplicon downstream | table+metadata | q2d2 diversity suite (`core_metrics_phylogenetic`, alpha/beta_group_significance), `__BUILD_LIST__` | our stage 15 (diversity, group significance) | Secondary, Medium — stage-level exemplar for the diversity fan-out |
| `amplicon/amplicon-mgnify/mgnify-amplicon-pipeline-v5-complete` | amplicon full pipeline (SRA→summary) | SRA-accession driven, no sheet | fastp/trimmomatic, dada2/mapseq, SSU, krona, multiqc | heavy plumbing corpus: `__FILTER_EMPTY_DATASETS__` ×20, `collection_element_identifiers` ×15, `collection_column_join`, `__FILTER_FROM_FILE__`, `param_value_from_file` | Secondary, Medium — not a shape exemplar (input topology wrong), but the corpus's richest collection-hygiene / drop-semantics idiom bank |
| `amplicon/multivariable-association-analysis` | association stats on ASV tables | — | — | — | Rejected: wrong intent |

No High exists: IWC has no sample-sheet-driven amplicon pipeline with diversity+reports in one workflow. `iwc-exemplar.gxwf.yml` = full `dada2_paired` (its whole 15-step body is the relevant spine subgraph; trimming would break in-references).

## Structural diff vs the design briefs

**Confirmed by corpus (raise confidence):**
- Stage 4 pooling idiom resolved: exemplar `__UNZIP_COLLECTION__` (out tagged `#forward`/`#reverse`) → one `dada2_learnErrors` job per direction over the whole list (`fls: <list>`) — matches the brief's "pool per direction, reduce steps"; single job per direction, not per group. `dada2_plotQualityProfile` with `batch_select: joint, aggregate: true` collapses both directions into one QC-plot job — cheaper than the brief's 2-job-per-direction guess (template may use it for `dada2_quality_plots`).
- Stages 7–11 chain exists end-to-end as IUC wrappers (learnErrors/dada/mergePairs/makeSequenceTable/removeBimeraDenovo), map-over by identifier on collections; `makeSequenceTable(samples: <collection>)` is exactly stage 11's single-gather job.
- Stage-10/11 stats reduce idiom: `dada2_seqCounts` named repeat port (`inrep_0..5` + `inrep` state list) = compile-time-N multi-input tabular fan-in — the corpus primitive for `per_sample_stats`/`MERGE_STATS_*`.
- Optional reference input idiom: `assignTaxonomyAddspecies` `reference_cond` conditional (`reference_select: builtin | <custom refFasta ConnectedValue>`) — the wrapper-side alternative to a workflow `when:` for "reference supplied?" (relevant to the dada2 taxonomy branch; sintax/kraken/sidle have no builtin, so branch-level subworkflow `when:` stays).
- Drop-not-error (stage 5): `__FILTER_EMPTY_DATASETS__` is the corpus-wide drop idiom (mgnify uses it 20×); no corpus workflow fails the run on a bad fan element — corroborates ledger `sample-failure-error-semantics` v1 posture.
- Identifier hygiene: `__APPLY_RULES__` over `list_identifiers`/`paired_identifier` columns (exemplar "Sort samples") and `iuc/collection_element_identifiers` + `iuc/collection_column_join` (mgnify) are worked tools for stage 6 group-key derivation and identifier-keyed metadata re-attachment.
- Tool families for loop `_plan_context` (corpus evidence, not availability adjudication): IUC dada2_* (9 wrappers), q2d2 qiime2__* (denoise_paired, feature_table summarize/tabulate_seqs, diversity suite, metadata tabulate), iuc/cutadapt (absent from these exemplars but standard), iuc/multiqc.

**Divergences the template must decide:**
1. **Chimera removal position**: exemplar gathers first (makeSequenceTable → removeBimeraDenovo on the one table); ampliseq removes chimeras per (run,region) group *before* merging tables. Not interchangeable when groups differ. Recommendation: keep per-group only if the wrapper accepts a collection-of-tables; else follow the exemplar order and record as a fidelity divergence in the draft's comment. (Template/data-flow issue.)
2. **Grouping vs pooling**: exemplar pools all samples into one error model; ampliseq learns per (run,region) group. With multiregion dropped, v1 groups per `run` — for the single-run test fixture that collapses to the exemplar's shape, so the test cannot distinguish them; keep grouping for fidelity. (Data-flow note, no action.)
3. **Fan-in family choice** (consolidate stage 14): repeat ports are fixed-N — they cannot track a variable number of present optional branches. Confirms the ledger choice: variable N rides a list collection into a `multiple=true` input; repeat ports only for the named per-stage stats table (stage 10). Pattern issue: neither corpus fan-in family covers "N-way present-only" cleanly — already filed to feedback (`conditional-when-note-lacks-multi-present-fanin`).
4. **No cutadapt/QC/multiqc/report steps in the nearest exemplar** — stages 1–3, 18 stay exemplar-less; fall back to mgnify (fastqc/fastp/multiqc presence) and standard wrapper knowledge at the loop. (Tool-step issue.)

**Antipatterns — do not pattern-match these:**
- Dead state residue in the exemplar: `dadaF|__identifier__: pool.feces.fastq` pins (contradict even its own F3D0/F3D5 fixture — residue from the author's scratch run) and `chromInfo: /gpfs1/...` absolute server paths. Strip on copy.
- `type: string` + `restrictOnConnections` for a "Cached reference database" (legacy .loc-style select) — conflicts with the interface brief's explicit-optional-data posture; keep our `*_ref_tax_custom` data inputs.
- Fixture style: raw `list:paired` of zenodo URLs — our tests should use the sample_sheet input (per interface brief); keep the *assertion* style though (see below).

## Nearest exemplar (gxformat2) view

Abstract id: `amplicon/dada2/dada2_paired`. Full converted spine in the sibling artifact `iwc-exemplar.gxwf.yml`. Covers steps *Sort samples → QualityProfile → filterAndTrim → UNZIP → learnErrors×2 → dada×2 → mergePairs → makeSequenceTable → removeBimeraDenovo → seqCounts → assignTaxonomy*. Relevant excerpt (the unzip→pooled-error-model idiom, condensed):

```yaml
  - id: _unlabeled_step_9
    tool_id: __UNZIP_COLLECTION__
    in: [{ id: input, source: _unlabeled_step_7/paired_output }]
    out:
      - { id: forward, add_tags: ["#forward"] }
      - { id: reverse, add_tags: ["#reverse"] }
  - id: _unlabeled_step_10           # one pooled error model per direction
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/dada2_learnerrors/dada2_learnErrors/1.38.0+galaxy1
    in: [{ id: fls, source: _unlabeled_step_9/forward }]
  - id: _unlabeled_step_12           # dada consumes the whole direction list
    tool_id: .../dada2_dada/dada2_dada/1.38.0+galaxy1
    in:
      - { id: batch_cond|derep, source: _unlabeled_step_9/forward }
      - { id: batch_cond|pool, source: Pool samples }
      - { id: err, source: _unlabeled_step_10/errors }
```

## Test-style signal (defer to phase 9)

`dada2_paired-tests.yml`: inline `job:` with remote-URL File elements + named expected outputs `Counts.tabular`, `Sequence Table.dada2_sequencetable` — note the **custom datatype `dada2_sequencetable`** on makeSequenceTable/removeBimera outputs: our ASV-table edges should expect that datatype when these wrappers are chosen, not plain `tsv` (datatype evidence for template + test plan).

## Confidence

Medium-high overall: same domain, overlapping tool families, same gather topology for the DADA2 spine; partial coverage of ampliseq's tail (taxonomy fan-in, diversity, reports) and no sheet-driven exemplar — no single IWC workflow is High.
