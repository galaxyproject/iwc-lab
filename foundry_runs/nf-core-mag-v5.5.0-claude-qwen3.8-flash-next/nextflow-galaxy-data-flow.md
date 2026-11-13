# Galaxy data-flow brief — nf-core/mag → Galaxy

Abstract target-shaped DAG per the draft contract: no gxformat2, no Tool Shed ids.
Granularity justified by the source's own structure: MAG's 94 processes sit inside 22
local subworkflows that are genuine phase units → Galaxy **subworkflow steps** with
`when:` gates; tool swaps inside them → **inline `when:` + `pick_value`**. Operator
classes per the recipes note (`wiring` / `collection semantics` / `explicit step` /
`review`).

Inputs/outputs/labels: `nextflow-galaxy-interface.md` (fixed; not re-decided here).

## Identifier scheme (load-bearing)

- Reads elements: samples are **not unique** (multirun test samplesheet; `sample` may
  repeat with distinct `run`). Key reads elements `sample_run` (unique per row);
  paired inner names `forward`/`reverse` (R1/R2 columns — every row with R2 is paired,
  rows may be single-end when `single_end` or LR-only).
- Coassembly groups: `group` metadata; group-level collections keyed by `group`.
- Contigs/bins: bins arrive as per-group multi-FASTA → split step yields element ids
  `${group}_${binN}`; every per-bin tabular (QUAST report.tsv, gtdbtk_summary, CAT
  summary, BUSCO, checkm(2), pydamage medians) keys on this bin id → the
  `bin_summary` merge joins on it. Preserve bin ids through all map-overs
  (testability: addressable rows).
- Assemblies per sample×assembler: ids `${sample}_${assembler}` (source meta carries
  `assembler`; from assembly_input sheet too).

## Stage 1 — sheet materialization (`input_mode == reads`)

| # | abstract node | shape in → out | recipe / class | conf |
|---|---|---|---|---|
| 1.1 | reads_samplesheet → fastq collections | `sample_sheet:record` → `list:paired` fastqsanger.gz, ids `sample_run` | tabular bridge + Apply Rules (record slots → paired, identifier from sample+run columns) | Medium (record-slot nullability pending ledger check) |
| 1.2 | platform/group metadata table | sample_sheet → tabular (sample, run, group, platforms) | `__SAMPLE_SHEET_TO_TABULAR__` | High |
| 1.3 | LR-only rows → `list` fastq | record.long_reads slot | collection filter/flatten | Medium |

Metadata columns must be re-attached after map-overs that lose them (sample-sheet
note): every stage reads `group`/platform from the 1.2 table via identifier-keyed
lookups, not parallel inputs.

### 1x. `input_mode == assemblies` branch (subworkflow, `when: input_mode == 'assemblies'`)

assembly_samplesheet (`sample_sheet`, fasta elements) → gunzip-as-needed (in-tool
decompress) → **filter by `assembler` column** (tabular bridge) → two routed lists:
short-read assemblers {MEGAHIT,SPAdes,SPAdesHybrid} and long-read {Flye,MetaMDBG}
(`explicit tabular-filtered split`; Medium). These lists enter at 3.4/4 exactly where
the ASSEMBLY subworkflow's outputs would, under a twin-cascade joined by **merge
collections** (both modes never run: `input_mode` gates both producers; consumer uses
`first_or_skip`-style tolerance via merge-collections).

## Stage 2 — preprocessing (source: SHORTREAD/LONGREAD_PREPROCESSING; subworkflows, `when: input_mode == 'reads'` (+ LR steps: list non-empty))

Short reads, per element `sample_run`:
2.1 FASTQC raw (optional `!skip_fastqc`; wiring into MultiQC, `wiring`).
2.2 **clip-tool swap** — three `when:`-gated parallel steps Trimmomatic /
AdapterRemoval (PE+SE variants) / fastp, merged with `pick_value(the_only_non_null)`
(`explicit steps`; pure tool-swap, source has no boundary → inline, per the
subworkflow-when note; default `clip_tool`). `skip_clipping` → identity path
(3-way + passthrough → `first_or_skip`). Confidence Medium (4-way fan-in).
2.3 **host removal** (`when: host_genome != null`): bowtie2 align (index built
in-tool) + *extract unmapped* (tool need: "unmapped reads from BAM as fastq"
— samtools -f4) → fastq; per sample. LR analog: same when, minimap2/bowtie2 per
source.
2.4 **phiX removal** (`when: phix_reference != null`): same 2-step pattern, second
`when:`; sequential after host.
2.5 FASTQC trimmed (optional).
2.6 **coassembly pooling** (`when: coassemble_group`): group reads by `group` —
`groupTuple` → concat fastq per group (`explicit steps`: group-relabel via Apply
Rules + "concatenate datasets" ×fastq; class: collection semantics + explicit).
2.7 BBnorm (`when: bbnorm`, short-read pre-assembly; explicit step, Medium).

Long reads: nanoplot QC; adapter-trim swap porechop_abi|porechop (`pick_value`);
filter swap chopper|filtlong|nanoq + none (`first_or_skip`; filtlong `combine`s SR
by id — keyed pairing, collection semantics; `filtlong_filtering_by_shortreads`
flag); lambda removal (`when: lambda_reference != null`, nanolyse-or-chopper
embedded — source branches on filtering tool: **per-element branch with non-trivial
predicate → review trigger**; design decision: nanolyse step gated
`when: lambda_reference != null && longread_filtering_tool != 'chopper'`, chopper
gets the lambda fasta as optional input — Medium).

**Versions files**: every module emits `versions.yml`; Galaxy has no equivalent
convention. Placeholder need: "collect tool versions metadata from all steps into
one YAML" — recorded as `versions-yml-aggregation-gap` (ledger), checkpoint output
`software_versions` depends on it. Low confidence; template must leave TODO.

## Stage 3 — assembly (source ASSEMBLY; subworkflow `when: input_mode == 'reads'`)

Five independent `when:`-gated assemblers over `list:paired`/`list` fastq, each →
`list` fasta.gz (`${sample}_${assembler}`), megahit pigz in-tool:
metaspades (`!skip_spades`), hybrid-spades (`!skip_spadeshybrid && !single_end` —
needs both SR+LR lists as paired-with-optional inputs; Medium), megahit
(`!skip_megahit`; when `coassemble_group`, input keyed by group then fan-out copy to
samples — **broadcast/duplicate collection by identifier map**, explicit, Medium),
flye (`!skip_flye`), metaMDBG (`!skip_metamdbg`). Outputs **merge collections** (not
pick_value: branches are additive, not exclusive) → `assemblies` (list).
3.4 QUAST (`when: !skip_quast`; one metaquast job over the whole list; reduces list
→ report dir + summary tsv; `explicit reduction` tool need).
3.5 Prodigal (`!skip_prodigal`); virus ID subworkflow (`when:
run_virus_identification`; genomad with optional db input, unpack in-tool).
3.6 PyPolca (`when: run_pypolca`): `combine` assemblies×reads keyed by sample →
polish; unpolished branch mixed back (`branch` w/ predicate → review; modeled as
two routed inputs to merge-collections, Medium-Low).

## Stage 4 — binning preparation (source BINNING_PREPARATION; subworkflow `when: !skip_binning || ancient_dna || !skip_ale`)

4.1 build bowtie2 index per short-read assembly (`!skip_binning`-ish; in-tool or
workflow-tier: reused by ≥1 sample per assembly — in-tool).
4.2 **bins-of-reads mapping**: map each sample's reads to its group's assembly —
source joins SR-by-group ↔ assembly-by-group. Galaxy: multi-input map-over needs
collections harmonized on a *group* key while reads ids are `sample_run` →
**explicit relabel/derive-group step from the 1.2 tabular** (Apply Rules + tabular
join) then map-over pairs (`sample_run` reads, `group` assembly) → BAM
(`list`, ids `sample_run`). Medium.
4.3 LR alignment: minimap2 index + align per assembly (same keyed pattern).
4.4 ALE (`when: !skip_ale`), per group bam+contigs.
4.5 ancient DNA subworkflow (`when: ancient_dna`): pydamage analyze (+MAPD filter),
freebayes/bcftools consensus recall producing *recalled contigs* that **replace** the
mapping input into BINNING when `!skip_ancient_damagecorrection` — twin-cascade with
`pick_value(first_or_skip)` at the consumer (Medium).

## Stage 5 — binning (source BINNING; subworkflow `when: !skip_binning`)

5.1 depth prep: jgi_summarize_bam_contig_depths (group of BAMs per assembly,
`groupTuple`-by-group → **group + reduce**: explicit); CONVERT_DEPTHS (bioawk tabular
transform BAM-depths→MaxBin2 profile — tool need "depth-table format conversion").
5.2 six binner swaps, each `when:`-gated, additive → **merge collections** of per-bin
FASTAs: metabat2 (`!skip_metabat2`), maxbin2 (`!skip_maxbin2`), concoct
(`!skip_concoct`: cutup→coveragetable→clustering→merge→extract = 5 internal steps,
cohesive — inner sub-assembly), comebin (`!skip_comebin`), metabinner
(`!skip_metabinner`: kmer/tooshort/bins/inner = sub-assembly), semibin2
(`!skip_semibin`).
5.3 unbinned handling: split FASTA above `min_length_unbinned_contigs`, keep ≤
`max_unbinned_contigs` — tool need "split multi-FASTA into per-sequence collection
with length cutoff" (Low confidence on availability — discovery decides).
5.4 DAS Tool refinement (source BINNING_REFINEMENT; subworkflow `when:
refine_bins_dastool`): rename→scaffold2bin→das_tool→rename-post; inputs: bins +
group BAM contigs; output refined bins (+unbinned) routed by `postbinning_input`
(enum → tabular/select filter) and `exclude_unbins_from_postbinning`.
5.5 domain classification (source DOMAIN_CLASSIFICATION; subworkflow `when:
bin_domain_classification`): tiara per contig + classify-R rollup → adds `domain`
metadata to bins (re-attach via tabular bridge).
5.6 final bins/unbinned collections: `list:list` group→bins(ids `${group}_${binN}`);
`meta.domain` filter for PROKKA (bacteria/archaea/unclassified) vs METAEUK
(eukarya/unclassified) via tabular-filter-by-column-value (`explicit tabular step`).

## Stage 6 — per-bin QC & annotation (parallel gated subworkflows over `bins`)

| subworkflow | gate | abstract content | conf |
|---|---|---|---|
| DEPTHS | `!skip_binning` | bins × per-group BAMs cross-product (source `combine` **unkeyed** → review trigger; Galaxy: cross-product build + filter to same group — `bins-x-bams-cross-product` ledger), depth tabulars → summary table | Low-Medium |
| BIN_QC | `!skip_binqc` | BUSCO (`when: busco_db != null`, untar in-tool, lineage from `busco_db_lineage`); CheckM lineage+qa (`when: checkm_db != null`); CheckM2 (`when: checkm2_db != null`); GUNC run+merge_checkm (`when: gunc_db != null`); seqkit bin-size stats | Medium |
| GTDBTK | `!skip_gtdbtk && gtdbtk_db != null && any QC ran` | **tabular filter of bins by QC table** (completeness/contamination bounds) → classify_wf → gtdbtk_summary.py rollup (custom-script tool need) | Medium; gate is compound — Medium |
| CATPACK | `cat_db != null` | cat_bins (+cat_contigs for unbinned `when: cat_classify_unbinned`) + bat add_names + summarise; db tar unpack in-tool | Medium |
| PYDAMAGE bins | `ancient_dna` | summarise_pydamagebins.py (custom script; joins contig→bin map) | Low-Medium |
| PROKKA | `!skip_prokka` | map bins filtered domain≠eukarya | High |
| METAEUK | `metaeuk_db != null` | eukarya/unclassified bins vs mmseqs db | Medium |
| QUAST_BINS | `!skip_quast` | metaquast over bins → per-bin report rows | Medium |

## Stage 7 — merge + reports (root workflow tail)

7.1 **`bin_summary` merge**: QSV_CAT 'rowskey' = join-up-to-8 per-bin tables
(depths_summary, QUAST, GTDBTK, CATPACK, BUSCO, CheckM(2), GUNC, pydamage), each
`.ifEmpty` — a **tolerant key-join** over optionally-skipped branches
(`collection_column_join`/join-data-tables with missing-table tolerance →
`bin-summary-tolerant-join` ledger; design: each branch emits an empty-but-typed
table when skipped — how is template's problem). Central tabular bridge;
High-need/Medium-mechanism.
7.2 BigMag (`when: generate_bigmag_file`): bin_summary + gunc summary join.
7.3 **MultiQC**: fan-in collection of every QC dataset produced (fastqc html/zip,
nanplot, quast reports+summary, bbsplit stats, freebayes/pydamage txt, per-branch
tsvs) → one html. Reduction over many optional inputs — collection construction
tolerates skipped (engine sentinel). High confidence in mechanism; Medium on which
datasets to route (mirror source multiqc_config search patterns).
7.4 promoted outputs per interface brief; skipped-branch tolerance: everything
downstream of a skipped branch is itself gated or sentinel-tolerant (engine behavior
confirmed in the subworkflow-when note).

## Conditional disposition summary

- **subworkflow `when:`** (source boundary exists + wide + cohesive — all match the
  note's evidence list): SHORTREAD_PREPROCESSING, LONGREAD_PREPROCESSING, ASSEMBLY,
  assembly-input branch, VIRUS_IDENTIFICATION, BINNING_PREPARATION, BINNING,
  BINNING_REFINEMENT, DOMAIN_CLASSIFICATION, BIN_QC, GTDBTK, CATPACK, ANCIENT_DNA(+
  BINNING_PYDAMAGE), METAEUK.
- **inline `when:` + pick_value**: clip_tool (the_only_non_null), long-read
  adapter trim, long-read filter (first_or_skip), aDNA consensus-vs-original
  (first_or_skip), keep/absent removal steps.
- **inline `when:` + merge collections** (additive branches): 5 assemblers, 6
  binners, QC scanners (each contributes its own tables, never merged by pick).
- Tool-stack-selection via runtime `when:` has thin IWC precedent (note §corpus) —
  recorded as evidence for the reviewer, not a reason to split workflows.

## Unresolved tool needs (abstract; discovery adjudicates)

Read trimming: trimmomatic / adapterremoval(PE+SE) / fastp; fastqc; nanplot;
porechop_abi; porechop; chopper; filtlong; nanoq; nanolyse; bowtie2 index+align
with unmapped-fastq extraction; bbnorm (bbmap); seqtk mergepe/concat fastq-by-group;
megahit(+pigz out); spades (meta/hybrid); flye; **metaMDBG (python entry script)**;
**pypolca**; quast metaquast (dir + tsv out); prodigal; **genomad**; **metabat2 +
jgi depths**; maxbin2 (+depth-profile converter, bioawk logic); **concoct 5-step
chain**; **comebin**; **metabinner chain**; semibin2; **DAS Tool chain**;
**seqkit stats**; tiara (+**R rollup script**); busco; checkm (lineage_wf+qa);
checkm2; gunc (run+merge_checkm); gtdbtk classify_wf (+**summary.py**);
**cat/bat chain (unpack+cat_bins+add_names+summarise)**; **pydamage
(analyze/filter/summarise bins)**; freebayes+bcftools consensus; prokka; **metaeuk
+ mmseqs createdb**; **bin_summary aggregator (QSV-cat rowskey equivalent)**;
**bigmag prepare (R)**; **mag-depths scripts**; versions collection (see gap).
Bolded = custom scripts / niche tools where authoring is plausible; no
availability claims made either way.

## Open questions (ledger-carried)

1. record-slot nullability for mixed-modality rows (inherited
   `mixed-modality-samplesheet-record-slots`) — data-flow proceeds on it for
   Stage-1; fallback restructures only Stage 1.
2. versions.yml aggregation has no Galaxy idiom (`versions-yml-aggregation-gap`).
3. tolerant n-way tabular join for bin_summary over skipped branches
   (`bin-summary-tolerant-join`).
4. unkeyed bins×BAMs cross-product with same-group filter
   (`bins-x-bams-cross-product`).
5. lambda-removal per-element branch folded into two gated steps (design call,
   Medium) — reviewer check.
6. compound GTDBTK gate (`!skip_gtdbtk && db != null && any QC tool`) — expressible
   as ES5.1 `when:` over inputs incl. null-checks; confirm on import.
