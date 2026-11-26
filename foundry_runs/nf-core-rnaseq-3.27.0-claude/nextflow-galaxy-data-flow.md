# nextflow-galaxy-data-flow — nf-core/rnaseq 3.27.0

Run: rnaseq-to-galaxy (phase 4). Cast: `nextflow-summary-to-galaxy-data-flow`.
Inputs: `summary-nextflow.json` (phase 1), `nextflow-galaxy-reference-data.md`
(phase 2), `nextflow-galaxy-interface.md` (phase 3),
`open-requirements.ledger.yml` (phases 2–3).

This brief is a data-flow draft, not gxformat2. It names abstract operations,
collection map/reduce choices, shape-changing placeholder steps, and what each
step needs a tool to *do*; it does not resolve Tool Shed tools, does not rule
any tool in or out, and leaves availability adjudication to
advance-galaxy-draft-step. Workflow inputs, outputs, and labels are pinned by
the phase-3 interface and are not re-derived here.

## How to read this brief

- Every per-sample collection is keyed on the **sample id** (the source
  `sample` column; see identifier discipline below). "Map-over" means a Galaxy
  step with a collection input producing a same-keyed collection;
  "reduction" means a step consuming a whole collection into one dataset.
- Branches are described as `when:`-gated subgraphs per the conditional note's
  heuristics (source subworkflow boundary, tool-swap character, narrow
  interface). This rests on param enums and the source's own subworkflow
  boundaries, NOT on `workflow.conditionals[]` — that array carries exactly 1
  of ~26 source guards (ledger discovery `branch-evidence-partial`), so guard
  text for every branch below is reconstructed from subworkflow take-blocks,
  call lists, and param enums. This is stated once here and applies to every
  branch disposition in the document.
- Tool needs are capabilities, never tool ids. Where a Galaxy built-in
  collection operation suffices, the gxformat2 opcode name is used
  (`__BUILD_LIST__`, `__FILTER_FAILED__`, …) — those are workflow language
  primitives, not Tool Shed tools.

## Element identifier discipline (checked against the source test)

Source's own names for the per-sample axis come from `samplesheetToList`
rows (`meta.id` = `sample` column) and from process output prefixes
(`"${prefix}"` = `meta.id` in CAT_FASTQ, TRIMGALORE, STAR_ALIGN, SALMON_QUANT,
…). They are unique per dataset in the fixture used for checking: the
"Params: default" test snapshot's `stable_paths` reveal five samples —
`RAP1_IAA_30M_REP1`, `RAP1_UNINDUCED_REP1`, `RAP1_UNINDUCED_REP2`, `WT_REP1`,
`WT_REP2` — each appearing exactly once per artifact family
(`fastqc/raw/{sample}_raw_{1,2}_fastqc.html`). Paired status:
`RAP1_IAA_30M_REP1`, `WT_REP1`, `WT_REP2` carry `_1` and `_2` reads;
`RAP1_UNINDUCED_REP1`/`_REP2` carry `_1` only. Therefore `_1`/`_2` are mates
in this fixture (every row they number is paired), matching the
`sample_sheet:paired_or_unpaired` input the interface pinned: element
identifier = `sample` value, forward/reverse roles inside the element.

Caveat carried forward, not silently dropped: the source's `sample` column CAN
repeat when one sample has several runs — `checkSamplesAfterGrouping` +
`CAT_FASTQ` (groupTuple on `meta.id`, then odd/even `reads` split into merged
`_1`/`_2` fastq.gz). `sample_sheet:paired_or_unpaired` requires one element
per sample id, so multi-run rows have no Galaxy carrier in v1. Recorded as
new ledger entry `multi-run-sample-merge-no-collection-carrier`; the abstract
DAG below maps one samplesheet row per sample and drops the merge tier.

## Abstract DAG

Granularity follows the source's own subworkflow boundaries (33 calls in
`RNASEQ`), not the 78-process granularity — the plumbing-to-science ratio
inside each boundary is low, and the boundaries already match the enum-driven
branch points.

### Tier 0 — inputs (pinned by phase 3; not re-derived)

- `samplesheet`: `sample_sheet:paired_or_unpaired`, required. The only
  per-sample axis origin.
- 23 optional reference inputs (FASTA/GTF/GFF core, derived annotations, 9
  index inputs, kraken_db, rrna_fastas / bbsplit_ref_fastas as list
  collections of FASTA, multiqc config/logo, …) and ~50 scalar controls.
- Scalar controls that act as branch selectors down here: `aligner`
  (`star_salmon` | `star_rsem` | `hisat2`), `pseudo_aligner`
  (`salmon` | `kallisto`, optional alongside alignment), `trimmer`
  (`trimgalore` | `fastp`), `remove_ribo_rna`, `with_umi`, `skip_*` flags.

### Tier 1 — reference preparation (mirrors PREPARE_GENOME_REFERENCES + PREPARE_GENOME_INDICES)

`fasta` (workflow input, singleton) fans out to two abstract subgraphs:

1. **Derived annotations** (phase-2 decision: cheap assets keep in-tool
   rebuild; workflow-level shape is "optional explicit input, else derived"):
   `fai` (faidx), `gene_bed` (from GTF), `transcript_fasta` (from GTF, or
   GENCODE-aware parsing when `gencode` set), `additional_fasta` concat,
   `splicesites` (hisat2 extract-splice-sites), `chrom_sizes` (from fai).
   Each is: optional input OR small derive step OR in-tool derive by the
   first consumer; all singleton datasets broadcast to per-sample
   map-overs (Galaxy runs map-over steps once per sample against one shared
   input — the Nextflow value-channel broadcast).
2. **Heavy indexes** (phase-2 decision `workflow-tier-build-for-heavy-indexes`
   — workflow-tier build-on-absence for star, hisat2, salmon, kallisto,
   bowtie2, rsem, bbsplit, sortmerna, bowtie2_rrna): for each index I:
   `build_I` step (`when: <selector selects consumer branch AND index input
   empty>`) producing the index dataset, then fan-in
   `pick_value(first_non_null(index_input, build_I.out))` feeding the
   consumer map-over. rrna_fastas / bbsplit_ref_fastas list collections feed
   the sortmerna / bbsplit / bowtie2_rrna build steps directly (this is the
   wiring the resolved entry `path-list-inputs-not-portable` left open).
   Build-step `when:` plus `pick_value` is the
   conditional-route-between-alternative-outputs pattern; per
   `rebuild-unverified-positive-form` (still open), whether the chosen
   wrapper can build is NOT verified here — the build step is an abstract
   "build index I from FASTA (+GTF)" capability.

Confidence: **High** for the reference fan-in shape (source take-blocks show
every index entering `RNASEQ` as a resolved channel; phase-2 decisions pin
the posture); **Medium** that every cheap derived asset can stay in-tool
(wrapper rebuild capability unverified, carried).

### Tier 2 — reads QC / trim / filter / strandedness (FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS)

Map-over on `samplesheet`. Sequence within the branch:

1. **Raw FastQC** — per-read-pair QC. Over a `paired_or_unpaired` element a
   single-input QC tool maps per mate, yielding a `list:list` (sample →
   mate) of html/zip. Keep nesting; flatten only at MultiQC fan-in.
2. **Trim** — `trimmer` enum branch: two `when:`-gated subgraph variants
   (trimgalore-flavored vs fastp-flavored: same abstract op "adapter + quality
   trim, paired-aware, optional UMI extraction"), fan-in via
   `pick_value(first_or_skip)` on the trimmed collection. Outputs per
   sample: trimmed `_1`/`_2` fastq.gz plus (trimgalore route) optional
   3'/5'-trimmed and unpaired artifacts.
3. **UMI extract** — `when: with_umi`; capability "barcode-pattern UMI
   extraction to fastq headers" (umitools-extract-like, or fastp UMI mode).
   Consumes `umitools_bc_pattern[_2]` scalars (conditional requiredness stays
   an open ledger entry — not closable in v1 gxformat2).
4. **Contaminant filtering** — `when: remove_ribo_rna` (rRNA: sortmerna-like
   or ribodetector-like per `ribo_removal_tool` enum — nested enum branch,
   `when:` + fan-in) and `when: bbsplit_fasta_list/bbsplit_index supplied`
   (BBSplit-like binning, optional). Each consumes the Tier-1 index from the
   pick_value fan-in.
5. **Strandedness resolution** — per-row `strandedness` column if set;
   otherwise the source runs FASTQ_SUBSAMPLE_FQ_SALMON (subsample → salmon
   quant on the subset → infer library type → rewrite `meta.strandedness`).
   Galaxy cannot mutate collection metadata mid-flight (sample-sheet note:
   metadata does not survive map-over), so the auto-detect route is an
   abstract step "infer strandedness per sample" whose output joins the
   per-sample table used for metadata re-attachment (below). Capability
   need, **Medium** confidence — no corpus exemplar cited by the bundle for
   strandedness inference as a Galaxy step.
6. **MultiQC artifact fan-out** — source builds `ch_multiqc_files` per
   subworkflow then `multiqc_files.transpose()`. `transpose` is a
   user-review trigger in the operators note (no recipe). Disposition chosen
   here: keep per-family collections (fastqc list:list, trimming list, …),
   flatten each family to a flat `list` (`__FLATTEN__`-equivalent) at the
   MultiQC fan-in. The transpose's positional-pairing semantics are NOT
   reproduced; since every artifact family is keyed by sample id and MultiQC
   consumes the flat union, the transpose is representation-only. Flagged
   for user review in Open questions.

Outputs of Tier 2: trimmed reads collection (keyed by sample id, pairedness
preserved), QC artifact collections, and the per-sample metadata table
(strandedness).

### Tier 3 — alignment (ALIGN_STAR | FASTQ_ALIGN_HISAT2, selected by `aligner` enum)

Two `when:`-gated subgraphs at subworkflow granularity (source boundary
aligns 1:1 with the enum; tool-swap character; interface is narrow:
reads-in, BAM+stats+QC-files out):

- **star branch**: per-sample STAR alignment against the Tier-1 star index
  (pick_value fan-in) + splicesites/gtf; outputs per sample: sorted BAM,
  `*Log.final.out`, bedgraph. Then per-sample sort/stats
  (samtools-stats-like producing `*.stats`), then markdup branch:
  `when: with_umi` → UMI-aware dedup (umitools/umicollapse-like) else
  Picard-MarkDuplicates-like; both produce dedup BAM + metrics. Sentieon /
  Parabricks backends are dropped per ledger
  `sentieon-parabricks-accelerators-dropped` (open, uncited debt).
- **hisat2 branch**: per-sample HISAT2 alignment + samtools sort/stats.
  Output shapes identical to the star branch (BAM + stats + QC artifacts).

Fan-in after the branches: `pick_value(first_non_null(star_bams,
hisat2_bams))` for the BAM collection and the stats collection — the two
branches emit compatible shapes, so one merge point serves all downstream
BAM consumers. Skipped branches emit the expression.json sentinel; downstream
steps that must not see sentinels are wired from the fan-in output only.
`when: skip_alignment` drops Tier 3+5 entirely in the source; in the target,
the same gate nulls the fan-in (no BAM consumers run) — with
`branch-evidence-partial`, this gate is enum-reconstructed, **Medium**.

`aligned_bams`, `bam_stats`, `star_alignment_log` (interface outputs) are the
post-fan-in collections. Coverage bedgraphs flow on the star branch only.

### Tier 4 — quantification

Three mutually compatible routes (source call graph: rsem only with
star_rsem; pseudo-aligner optional alongside either aligner, or standalone
when `skip_alignment`):

- **QUANTIFY_RSEM** (`when: aligner == star_rsem`): per-sample RSEM
  expression quantification on sorted BAMs against the rsem index (Tier-1
  fan-in); per-sample gene/isoform count tables, then a **reduction**:
  merge-counts step consuming the whole per-sample collection into the
  `gene_counts` matrix (rsem route) — collection-to-one-table reduction.
- **QUANTIFY_PSEUDO_ALIGNMENT** (`when: pseudo_aligner`): per-sample salmon
  (or kallisto, nested enum branch) quantification against the Tier-1
  salmon/kallisto index; `salmon_quant_libtype` scalar and the per-sample
  strandedness table feed the lib-type argument (metadata re-attachment
  below). **Shape-changing placeholder (resolves interface open question
  4):** SALMON_QUANT emits `path("${prefix}")` — a per-sample *directory*.
  Galaxy list collections hold datasets, not directories. Disposition: the
  quantification step's tool need is phrased as "expose `quant.sf` and
  `quant.genes.sf` as named outputs" (wrapper-level file selection), so the
  workflow sees two per-sample `list` collections (`salmon_quant`,
  `salmon_quant_genes`). Fallback if no such wrapper exists: a placeholder
  extract step (composite/directory input → two file outputs) between
  quantification and consumers. `salmon_quant` interface output confidence
  lifts from Low to **Medium** once the named-outputs capability is
  confirmed; it stays Low if the fallback placeholder must carry it.
- **QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT** (pseudo-aligner route): a
  **reduction** — tximport-like merge over the whole per-sample
  `salmon_quant` collection (+ transcriptome GTF) producing
  `gene_counts`, `gene_tpm`, `transcript_counts` (interface outputs) and a
  merged SummarizedExperiment (internal).

Fan-in: `gene_counts` = `pick_value(first_non_null(tximport_counts,
rsem_merge_counts))` (both routes emit a same-shape count matrix).

### Tier 5 — BAM QC + coverage (BAM_QC_RNASEQ, BAM_RSEQC, BAM_STRINGTIE_MERGE, BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG)

Map-over on the post-fan-in BAM collection:

- Per-sample samtools stats (already produced in Tier 3 on the star branch;
  hisat2 branch produces it in-subworkflow; the fan-in is on identical
  shapes).
- **RSeQC-like module suite** per sample (`rseqc_modules` string control;
  whether it becomes one multi-select or several toggles is a tool-step
  decision — interface open question 7 carried).
- **featureCounts-like summarization** per sample (or as a single
  collection-consuming step; source is per-sample + later merge). Requires
  the per-sample **strandedness** for the `-s` argument — this is the
  primary metadata re-attachment point (below).
- **Coverage** (star branch): per-sample STAR bedgraph → bedclip-style
  chromosome-length clip (needs `chrom_sizes` from Tier 1) →
  bedGraphToBigWig-style conversion; `coverage_bigwigs` interface output.
  Interval semantics only (coverage + coordinate clip); no overlap/masking
  operations appear in this pipeline.
- **Stringtie merge** (optional per `stringtie` flags): reduction over
  per-sample stringtie outputs.

### Tier 6 — reporting

- **MULTIQC_RNASEQ → MULTIQC**: a single **reduction** consuming the union
  of all QC artifact collections (each family flattened, Tier 2 item 6),
  plus multiqc_config/logo inputs; produces the `multiqc_report` File
  output. The source's second input — `ch_per_sample_bundle_raw`
  (`[id, meta, f1, f2, ...]` grown by successive `.join(..., remainder:
  true)`) — is a **user-review trigger** (loose join, unkeyed heterogeneity).
  Disposition: do not reproduce the join; MultiQC consumes the flattened
  union keyed by sample id, which preserves what the report needs (per-file
  sections). Flagged for user review in Open questions.
- **DESEQ2_QC**: singleton over the merged count matrix (+ pca/clustering
  header files produced by the merge step): `deseq2_qc_plots` (pdf — no
  registry `pdf` datatype, interface already omits format),
  `deseq2_pca_values`.
- **Versions**: per-process version outputs are emitted as a topic channel
  in the source; target: versions text outputs collect into one
  softwareVersionsToYAML-like reduction producing `pipeline_versions`.
  Capability need; the per-step version capture is a tool-step concern, so
  this reduction is **Medium** confidence.

## Metadata re-attachment (sample-sheet discipline)

Per the sample-sheet note, `column_definitions` metadata (strandedness,
seq_platform, seq_center, percent_mapped) does NOT propagate through Galaxy
map-over steps. Points where the target must re-attach it:

- featureCounts `-s` (strandedness) and salmon lib type (Tier 4): re-attach
  via the sample-sheet → tabular bridge (`__SAMPLE_SHEET_TO_TABULAR__` or
  rules-DSL add_column_from_sample_sheet_index) keyed on element
  identifier, then join per-sample rows to the mapped outputs by identifier
  (sync-collections-by-identifier filtering where membership varies).
- `percent_mapped` (checkSamplesAfterGrouping threshold filtering): same
  bridge; the filter step is `when:`-gated on the column being present.
- `dbkey`: if a user sets dbkey on the samplesheet elements, map-over steps
  must not strip it (mapping note gap: no corpus exemplar yet — carried as
  an open question, and as a handoff note to the template Mold).

## Collection map/reduce choices (summary table)

| Seam | Source shape | Galaxy shape | Operation |
|---|---|---|---|
| samplesheet rows | `tuple val(meta), path(reads)` from samplesheetToList | `sample_sheet:paired_or_unpaired` | input collection |
| raw/trimmed reads | per-sample `_1`/`_2` fastq.gz | `list` (keyed by sample id), paired elements | map-over |
| FastQC artifacts | per-mate html/zip | `list:list` (sample → mate) | map-over, keep nesting |
| QC artifacts → MultiQC | `transpose()` + flat channel | per-family `list` → flatten → union `list` | `__FLATTEN__`-equivalent + reduction |
| per-sample BAMs/stats/logs | repeated `tuple val(meta), path(...)` | `list` keyed by sample id | map-over |
| salmon results | per-sample **directory** | two `list` collections (`quant.sf`, `quant.genes.sf`) | wrapper named outputs (placeholder extract fallback) |
| tximport / rsem merge / MultiQC / versions / DESEQ2 | singleton consumers of merged channels | whole-collection step input | reduction |
| index inputs | value-channel broadcast | single dataset input to map-over | broadcast |
| branch outputs (aligner, trimmer, ribo tool, markdup) | if/else channel selection | `when:`-gated subgraph + `pick_value(first_non_null/first_or_skip)` | conditional route |
| skipped-branch sentinels | missing values | expression.json sentinel from `when:`-skipped steps | filter before consumers |

## Shape-changing placeholder steps (explicit list)

1. **Salmon directory → named files** (Tier 4): wrapper-exposes-outputs
   preferred; placeholder extract step fallback.
2. **Metadata re-attachment bridge** (above): sample-sheet → tabular →
   identifier-keyed join; needed before featureCounts and salmon lib type.
3. **QC artifact flatten** (Tier 2/6): per-family `list:list` → flat `list`
   before MultiQC (replaces the source's `transpose`).
4. **Sentinel filtering**: after `pick_value` fan-ins and after optional
   branches (contaminant filtering, UMI), filter
   empty/failed/null elements before reductions so MultiQC/tximport see
   only live datasets; where a later step needs the original shape, use
   identifier-synced filtering of siblings (collection-cleanup pattern
   family).

## Galaxy tool needs (capabilities; NOT availability claims)

Per-step, phrased as what a tool must do — discovery and any "must be
authored" adjudication belong to advance-galaxy-draft-step:

1. Per-mate FASTQ QC producing html + data zip (FastQC-like).
2. Paired-aware adapter/quality trimming, two flavors (cutadapt/trim-galore
   -like; fastp-like with UMI-extract mode) emitting trimmed `_1`/`_2`
   fastq.gz and optional 3'/5'-trim artifacts.
3. UMI barcode extraction by pattern to read headers (umitools-extract-like).
4. rRNA filtering from an index built from a FASTA collection
   (sortmerna-like; ribodetector-like alternate for `ribo_removal_tool`).
5. Reference binning of reads against a multi-FASTA-derived index
   (BBSplit-like).
6. Strandedness inference from a read subsample (salmon-quant-on-subset
   like) — Medium confidence, no cited corpus exemplar.
7. STAR alignment: genome index (+GTF/splicesites) in; sorted BAM,
   `Log.final.out`, per-sample bedgraph out.
8. HISAT2 alignment with splicesites; sorted BAM + stats out.
9. Index builders from FASTA(+GTF) for: star, hisat2, salmon, kallisto,
   bowtie2, rsem, bbsplit, sortmerna (workflow-tier build steps; build
   capability unverified per open ledger entry).
10. SAMtools-style sort/stats/flagstat; Picard-style markdup;
    UMI-aware dedup (umitools/umicollapse-like).
11. Salmon and kallisto quantification exposing `quant.sf`/`quant.genes.sf`
    (or per-file) named outputs; lib-type argument.
12. RSEM quantification on BAMs + merge-counts aggregation over a
    collection.
13. tximport/SummarizedExperiment merge over a per-sample quant collection
    + transcriptome GTF → gene/transcript counts and TPM matrices.
14. featureCounts-like strandedness-aware gene counting.
15. RSeQC-like QC module suite (per `rseqc_modules`).
16. StringTie assembly + merge over a collection.
17. bedclip-style length-clip + bedGraphToBigWig conversion (chrom_sizes
    input).
18. MultiQC aggregation over a flat collection with config/logo inputs.
19. DESeq2 QC on a count matrix (+header files) → pdf + pca values table.
20. Version-collection → YAML reduction.
21. Sample-sheet → tabular bridge / rules-DSL metadata re-attachment
    (gxformat2 built-ins; no discovery needed).

## Confidence

| Unit | Confidence | Rationale |
|---|---|---|
| Per-sample axis = sample id; pairedness inside elements | High | Fixture-checked (5 samples, unique; `_1`/`_2` mates only on paired rows) |
| Multi-run merge drop | High (that it is dropped) | No `sample_sheet*` carrier; ledger entry opened |
| Reference tier (fan-in + workflow-tier builds) | High shape / Medium rebuild | Source take-blocks + phase-2 decisions / rebuild unverified |
| Tier 2 map-over chain | High | `FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS` take/emit verified in summary |
| Trim/ribo/markdup branch gating | Medium | Guard text absent (1 of ~26 extracted); enums + call lists only |
| Alignment branches + pick_value fan-in | High shape / Medium gating | Subworkflow boundaries align with enum; same evidence caveat |
| Salmon directory resolution | Medium | Named-outputs capability assumed; placeholder fallback declared |
| MultiQC flatten-vs-transpose | Medium | `transpose` has no Galaxy recipe (user-review trigger); flatten keyed by id is representation-equivalent for the consumer |
| MultiQC loose-join bundle dropped | Medium | Same trigger family; user review requested |
| Strandedness inference step | Medium/Low | Capability with no cited exemplar |
| Versions reduction | Medium | Topic-channel aggregation is plumbing, not summarized |
| Branch wiring overall | Medium | `branch-evidence-partial` discovery (inherited) |

## Open questions

1. **Multi-run FASTQ merge** (new ledger entry
   `multi-run-sample-merge-no-collection-carrier`): v1 drops it; a future
   manifest + per-group concatenation tier could restore it, anchored by no
   corpus exemplar.
2. **`transpose()` and the `join(remainder: true)` bundle** (user review):
   the dispositions chosen here (flatten by identifier; drop the loose join)
   are the operators note's review triggers — a reviewer should confirm
   MultiQC's report completeness does not depend on the per-sample bundle.
3. **Strandedness auto-detect**: confirm a Galaxy tool can infer library
   type per sample; otherwise the interface's `strandedness` column becomes
   effectively required.
4. **Salmon wrapper named outputs** (interface open question 4, resolved
   here pending discovery): verify `quant.sf`/`quant.genes.sf` exposure, or
   accept the placeholder extract step.
5. **dbkey propagation through map-overs** (mapping-note gap): the template
   Mold must not strip dbkey set by users on samplesheet elements.
6. **`rseqc_modules` string vs repeatable** (interface open question 7
   carried): tool-step decision.
7. Carried open ledger entries (no closure this phase — see ledger actions):
   `rebuild-unverified-positive-form`,
   `contaminant-db-conditional-requiredness`, `bam-start-rows-unrepresented`
   (data flow does not wire BAM rows into the FASTQ path, per its note),
   `umi-bc-pattern-conditional-requiredness`,
   `rrna-default-db-no-portable-equivalent`,
   `sentieon-parabricks-accelerators-dropped`.

## Ledger actions taken (open-requirements.ledger.yml re-emitted)

- **Appended** entry `multi-run-sample-merge-no-collection-carrier` (open,
  gap).
- **No entries closed**: every open entry is either a v1 gxformat2
  validation loss (conditional requiredness ×2), a wrapper-verification
  obligation owned by implement-galaxy-tool-step (rebuild), a deferred
  interface addition (BAM-start), a default-bundle sourcing question
  (rrna), or an uncited drop (accelerators) — none is settled by wiring
  choices alone, and partial resolutions are exactly the undefined case
  FOUNDRY-ISSUES #17 records.
- **Appended** discoveries: `per-sample-axis-fixture-verified`,
  `multiqc-bundle-loose-join-and-transpose`, `versions-topic-channel`.
- **Appended** decisions: `per-sample-collections-keyed-by-sample-id`,
  `enum-branches-as-when-gated-subworkflows`,
  `index-fan-in-first-non-null`,
  `salmon-quant-extracted-named-outputs`,
  `metadata-reattachment-bridge`,
  `multiqc-consumes-flattened-union`.

## Provenance summary

- Source: nf-core/rnaseq 3.27.0, revision `95dbcd9…`; summary by phase 1
  (`summarize-nextflow`).
- Structural evidence: `subworkflows[]` (RNASEQ take/calls; FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS,
  ALIGN_STAR, FASTQ_ALIGN_HISAT2, QUANTIFY_RSEM, QUANTIFY_PSEUDO_ALIGNMENT,
  QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT, BAM_QC_RNASEQ, BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG,
  MULTIQC_RNASEQ take/emit blocks), `processes[]` input/output ChannelIO
  shapes (CAT_FASTQ, TRIMGALORE, STAR_ALIGN, SALMON_QUANT, MULTIQC,
  SUBREAD_FEATURECOUNTS, DESEQ2_QC), `workflow.edges[]`, the single
  `workflow.channels[]` entry, `sample_sheets[0]`, and the "Params:
  default" test snapshot `stable_paths` (sample identifiers and mate rule).
- Prior-brief contracts honored: interface (inputs/outputs/labels pinned;
  salmon_quant hazard resolved as above), reference-data (index posture,
  list-collection path-list inputs wired into Tier 1 builds).
- Reference skip recorded: `nextflow-reference-data-classification.md` was
  not loaded — its trigger (reference-data/interface brief silent,
  low-confidence, or conflicting with source evidence) does not fire: the
  phase-2 brief is explicit, evidence-cited, and consistent with the
  summary on every reference asset this data flow touches.
- Environment note: Bash auto-mode was unavailable, so python3/jq/node
  could not run; the 5.8 MB summary JSON was explored with grep + Read
  pagination only (same workaround as phases 1–3; see FOUNDRY-ISSUES
  "Non-Foundry friction").
