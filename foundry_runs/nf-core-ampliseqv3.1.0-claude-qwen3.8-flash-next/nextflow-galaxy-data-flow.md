# Nextflow → Galaxy data-flow brief — nf-core/ampliseq 3.1.0

Inputs: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`, `open-requirements.ledger.yml` (5 open, 1 resolved entries inherited — none re-derived). Shapes per `nextflow-to-galaxy-channel-shape-mapping`; operators per `nextflow-operators-to-galaxy-collection-recipes`; conditionals per `nextflow-conditional-to-galaxy-subworkflow-when`; separation from template per `galaxy-data-flow-draft-contract` (abstract nodes below; no tool ids).

**v1 scope** (inherited decisions + drops): illumina_pe/se only, `asv_calling` auto→dada2, selectors/catalog not exposed, multiregion fan-out dropped (see ledger `multiregion-fanout-no-recipe`), ~55 tuning scalars fixed. The default scenario: sample sheet → trim/filter → DADA2 ASVs → optional taxonomy branches → QIIME2 summaries/reports.

## Element identifiers (load-bearing)

- Per-sample elements keyed by `sample[__run]` (interface decision): unique per dataset — test fixture Samplesheet_v3.tsv rows are sample-unique; the `run` fold guards multi-run sheets. All per-sample map-overs below preserve this identifier.
- **Group-unit hazard**: `workflows/ampliseq.nf` subworkflows/local/dada2_preprocessing/main.nf:146-158 groupTuple-by-(run,region) **strips `id`/`sample` from the grouping meta and re-adds them as sorted lists**. So error-model/denoising/rmchimera elements are keyed by (run, region)-equivalent meta, carrying a *list* of member samples. In Galaxy the group element identifier must be a deterministic join of the grouping fields (e.g. `run__region`); the member-sample list must ride as tabular side data (per-group stats), not inside the identifier. Recorded as discovery `group-unit-identifier-carries-sample-list`.
- sample_sheet `column_definitions` are **not propagated** through map-overs (galaxy-sample-sheet-collections §mapping rules): wherever a downstream step needs `control`/`quant_reading`/`run` per element, re-attach via `__SAMPLE_SHEET_TO_TABULAR__` + identifier-keyed tabular join, not parallel parameter inputs.

## Abstract DAG, by stage

| # | Abstract nodes (source) | Shape in → out | Galaxy idiom | Tool need (verb) | Conf |
|---|---|---|---|---|---|
| 1 | RENAME_RAW_DATA_FILES | sample_sheet:paired_or_unpaired → list:paired (or list) | channel-only wiring; identifier-preserving map-over | rename/copy datasets | High |
| 2 | FASTQC (`when !skip_fastqc`) | list:paired → list (html per element) | map-over over flattened elements | per-element FASTQ QC html | High |
| 3 | CUTADAPT_* + CUTADAPT_SUMMARY (+MERGE_STATS) | list:paired/list → list:paired + tsv | map-over; per-element args come from *fixed* primers (v1: params, same for all elements → scalar, no per-element parameterization needed) | primer-trim paired reads; emit per-element trim stats tsv | High (v1 single-region; multiregion dropped) |
| 4 | DADA2_QUALITY1/2, TRUNCLEN | pool all trimmed reads per direction → per-direction plot+profile; optional TRUNCLEN | **collection reduction**: `collect()` per FW/RV axis = unzip → per-direction reduce steps (2 jobs each) | pool reads per direction, run DADA2 profile plot; parse profile table to truncation values | Medium |
| 5 | DADA2_FILTNTRIM + passed/failed branch | list → list (per sample) | map-over + **filter non-empty** on the pass branch; fail list collected to a log dataset | per-sample quality filter, drop elements below read threshold | Medium — error-instead-of-drop semantics lost (ledger `sample-failure-error-semantics`) |
| 6 | groupTuple by (run, region) | list (per sample) → list (per group), reads as nested lists | **group by identifier derivation** (identifier-transform: sample→group key; member list to tabular sidecar); Apply Rules / relabel+find-replace class | regroup elements by run+region key | Medium |
| 7 | DADA2_ERR | per group → err.rds (+pdf/svg/convergence) | map-over over group collection | learn error model from pooled group reads | High |
| 8 | DADA2_DENOISING (join err) | per group (reads+err) → seqtab.rds, denoised, mergers | map-over with identifier-matched 2-collection input (join ⇒ multi-input map-over, identifiers match) | denoise/merge reads → per-group sequence table | High |
| 9 | DADA2_RMCHIMERA | per group seqtab → ASVtable.rds | map-over | remove chimeras per group table | High |
| 10 | DADA2_STATS (3-way join) + MERGE_STATS_* | joins of group streams; stats tsv merges | identifier-keyed multi-input map-over + **tabular concatenate-collection** for stats merge | row-merge per-group stats tsvs (header once) | Medium |
| 11 | DADA2_MERGE | **collect() ×2 → one table + fasta** (ASV_table.tsv, ASV_seqs.fasta, DADA2_table.tsv, stats) | collection reduction (one job, N inputs via `multiple`/list input) | merge per-group ASV tables + seqs into one | High — this is the pipeline's primary gather point |
| 12 | SUMMARY_TABLE_COUNTS / TAXONOMY, DUCKDB_TABLE2PARQUET | table → long tsv → parquet | single-dataset tabular steps | melt counts to long table; tsv→parquet copy | High |
| 13 | Taxonomy branches (DADA2_TAXONOMY_WF, SINTAX_TAXONOMY_WF, VSEARCH_LCA_TAXONOMY_WF, KRAKEN2_TAXONOMY_WF, QIIME2_TAXONOMY, SIDLE_WF, ADDSH) | ASV fasta + optional ref input(s) → per-(branch,db) tax tsv | **subworkflow `when:` per branch** (source already groups them; small typed interface: ASV fasta + reference in, tax tsv out) — each gated on its custom-input + skip flags (discovery `taxonomy-custom-overrides-selector`) | classify ASVs per tool against supplied reference | High shape / per-branch tool availability deferred to loop |
| 14 | CONSOLIDATE_TAXONOMY + _TOOLS | N tax tsv (per db, then per tool) → one | **multi-present tabular fan-in**: materialize present branch tables into a list collection (collection construction tolerates skipped-branch sentinels), one reduce step with `multiple` input + strategy scalar (`consolidate_taxonomies`) | merge N taxonomy tables by ASV id with pick strategy | Medium (ledger `consolidate-taxonomy-optional-fanin`) |
| 15 | QIIME2 core: FILTER_SAMPLES (metadata-when), taxonomy→feature-classifier import, EXPORT, diversity (skip-gated), barplots, ANCOM/ANCOMBC/ADONIS, METADATA_ALL/PAIRWISE | single feature table + taxonomy tsv + optional metadata tsv → tables + qzv-class visualizations | mostly single-dataset tabular/plot steps; metadata joins = tabular-join-on-key bridges; `when:` on metadata-dependent steps (`$(inputs.metadata)`) | import table+taxonomy; filter/sample-meta join; alpha/beta diversity; barplot; differential abundance | Medium |
| 16 | BARRNAP + FILTER_SSU / FILTER_LEN_ASV / FILTER_CODONS / DECONTAM | ASV fasta (+metadata for decontam) → filtered fasta/table | map-over (barrnap per element) + tabular filters keyed on ASV id | annotate SSU; filter ASV sets by kingdom/length/codon/decontam-likelihood | Medium |
| 17 | EXPECTED_SEQUENCES / ABUNDANCES / PROFILE (comparison_wf) | outputs + expected_* inputs → comparison tables | single-dataset tabular comparison steps, `when:` on each optional expected input | compare observed vs expected sequences/abundances/profiles | High |
| 18 | MULTIQC (`when !skip_multiqc`), SUMMARY_REPORT (`when !skip_report`) | collected logs/plots/tables → html | **collection fan-in** of report inputs (merge-collection of present outputs; skipped branches tolerated) | aggregate QC report; render parameter-echo summary report | Medium |
| 19 | ROBJECT: PHYLOSEQ / TSE exports | table+tree+taxonomy → rds | single-dataset steps, skip-gated | export phyloseq/TSE objects | Medium |

**Dropped plumbing**: versions.yml topic aggregation (report-only), `dump`/log-only branches, `RENAME` soft-link logic, ONT/SAVONT stage (platform drop), DADA2_SPLITREGIONS + multiregion cross-product (drop entry).

## Collection map/reduce decisions

- **Map-overs (identifier-preserving)**: stages 1–3, 5, 7–9, 16(barrnap). Input sample_sheet drives everything; element identifier `sample[__run]` preserved per the identifier section.
- **Reductions**: per-direction read pools (stage 4), stats merges (10), DADA2_MERGE (11), consolidate fan-in (14), report aggregation (18). All are *explicit reduce steps* with list/`multiple` inputs, not wiring.
- **The one reshape**: per-sample → per-(run,region) grouping (stage 6). Everything downstream of DADA2_ERR is group-keyed, then collapses to a single table at stage 11. No `list:list` needed: grouping produces a flat list over group keys (Galaxy rule: use list:list only when the nesting axis matters — here denoising consumes a flat group element with its member list).
- **Paired axis**: pairedness lives only in stages 1–3 (reads); after FILTNTRIM elements are unpaired fastq lists per sample; DADA2 merges internally. Unzip between stage 3 and 4 if tools demand separate mates.

## Conditional dispositions (15 source conditionals + skip surface)

| Source guard | Disposition | Notes |
|---|---|---|
| `skip_fastqc`, `skip_barrnap`, `skip_abundance_tables`, `skip_barplot`, `skip_diversity_indices`, `skip_alpha_rarefaction`, `skip_phyloseq`, `skip_tse`, `skip_multiqc`, `skip_report`, `skip_parquet_summary`, `skip_cutadapt`, `skip_dada_quality` | inline tool-step `when:` (1–2 steps each) | cascade short, no source subworkflow boundary |
| `skip_taxonomy` / `skip_dada_taxonomy` / taxonomy custom-input presence | **subworkflow `when:` per taxonomy branch** | source boundary already exists (`*_TAXONOMY_WF`), wide gated cascade inside, narrow interface (ASV fasta + ref → tsv) |
| `params.metadata` and metadata-dependent analyses | inline `when: $(inputs.metadata)` on FILTER_SAMPLES / METADATA_* / DECONTAM / diversity-when-metadata | value-channel carrier: optional data input presence |
| pplace branch (`run_pplace` + refs) | subworkflow `when:` | **re-keyed off supplied inputs** (`pplace_tree && pplace_aln`) per inherited obligation `pplace-enablement-keyed-on-selector` — obligation discharged here; hmmer-row limitation stays open as `pplace-sheet-file-refs` |
| expected_* presence | inline `when:` per comparison step | |
| `consolidate` gating | run consolidate reduce only when ≥2 branch tables present: gate on `!skip_taxonomy && (any custom ref present)`; single-branch case passes its table through directly (twin-input wiring, not pick_value) | |
| asv_calling swap (dada2 vs savont) | not carried (savont dropped with ONT) — auto resolves to dada2 for illumina | `restrict` handles it; no runtime swap needed |

Fan-in primitives: **no pick_value needed anywhere** — branch outputs are concatenated/joined (multi-present semantics), not selected-one. Skipped-step sentinel tolerance of collection construction (per the when-note) is assumed at stages 14/18; flag for phase-11 validation.

## Unresolved tool needs (verbs for the loop; no adjudication here)

primer trimmer w/ per-call stats; DADA2 pool-profile plotter; truncation-value calculator; per-sample filter+truncate; error-model learner (rds I/O); per-group denoiser (rds in/out); chimera remover (rds); group-table merger (rds list → tsv+fasta); stats tsv row-merger; taxonomy classifiers ×5 (dada2/sintax/vsearch-LCA/kraken2/qiime2/sidle each) with user-supplied refs; multi-table taxonomy consolidator w/ strategy; QIIME2 table/taxonomy importers, diversity suite, barplotter, ANCOM(BC), metadata joins; SSU annotator; sequence filter suite; decontam; expected-comparators ×3; tsv→parquet; phyloseq/TSE exporters; MultiQC; report renderer. Each lands in template at the evidence tier template Mold chooses; availability claims belong to `advance-galaxy-draft-step`.

## Confidence & open questions

- High: stages 1–3, 7–9, 11–12, 17; branch/subworkflow routing; identifier scheme (fixture-checked unique).
- Medium: stage 4 pooling semantics (FW/RV per-direction jobs — verify tool arg shapes in template), stage 6 grouping (identifier derivation + sidecar), 14 fan-in sentinel tolerance, 15 breadth (many QIIME2 steps; granularity follows source subworkflows, justified by their boundaries not tool guesses), 18 report fan-in.
- Open (ledger): multiregion fan-out dropped; consolidate N-optional fan-in wrapper shape; sample-failure error semantics; hmmer-row refs in pplace_sheet; whether QIIME2 `qzv` visualizations convert to html in-tool (affects output datatypes — template/loop question).
