# Nextflow → Galaxy interface brief: nf-core/rnaseq 3.27.0

Produced by `nextflow-summary-to-galaxy-interface` from `summary-nextflow.json`
(phase 1; source revision `95dbcd977a74a4d1b2a3954abb90df3851014afa`), the
reference-data brief `nextflow-galaxy-reference-data.md` (phase 2), and the
carried `open-requirements.ledger.yml`. Consumed by
`nextflow-summary-to-galaxy-data-flow`, `nextflow-summary-to-galaxy-template`,
and later test-plan work.

This is a design handoff, not a gxformat2 skeleton and not a workflow schema.
All interface claims cite the summary artifact, the phase-2 brief, or the
packaged reference notes; nothing is re-derived from the source tree.

Evidence limits inherited from phase 1 (summary `warnings[]`): "workflow graph
extraction is intentionally partial in resolver v1" — `workflow.conditionals[]`
carries 1 guard while the source has ~26, and every `processes[].publish_dir`
is `null`. Output-intent evidence below therefore rests on process output
patterns (`path "*.ext"`) and `meta.yml`/test-snapshot corroboration, not on
`publishDir` patterns (evidence rank 5 in the datatype note is unavailable for
this pipeline). The single `workflow.channels[]` entry (`ch_samplesheet`,
`construct: value`, `from_param: null`) references `params.input` verbatim in
its `source`, so the params note's substring-matching fallback binds it to the
`input` param; the `samplesheetToList` materialization itself lives inside the
`RNASEQ` subworkflow body and is not carried as a channel.

## Translation order used

1. Read `params[]`, `sample_sheets[]`, `workflow.channels[]`,
   `workflow.conditionals[]`, `processes[].inputs/outputs`, `subworkflows[]`,
   `warnings[]`.
2. Classify each launch param (data-bearing / sample sheet / scalar /
   workflow-shape control / runtime-publish control / reference selector).
3. For data-bearing params, join `workflow.channels[]` by `from_param`
   (direct join empty here except via substring fallback for `input`);
   process inputs (`tuple val(meta), path(reads)`) refine shape.
4. Inherit reference-asset interface decisions from the phase-2 brief
   (its per-asset table is the runtime contract for this brief).
5. Decide gxformat2 `type`, then `format`/`collection_type`, `optional`,
   `default`, and confidence per input.

## Workflow inputs

### 1. Sample sheet — `samplesheet`

Primary biological input. `params.input` is the only required launch param
(nf-schema `required: true`, `format: file-path`, `mimetype: text/csv`,
`schema: assets/schema_input.json` per `sample_sheets[0]`, `discovered_via:
nf-schema`, `format: csv`, `header: true`).

**Decision: `type: collection`, `collection_type: sample_sheet:paired_or_unpaired`, `optional: false`.**

- Row shape: required `fastq_1` plus optional `fastq_2` path columns
  (`kind: data`, `format: file-path`, `exists: true`, pattern
  `^([\S\s]*\/)?[^\s\/]+\.f(ast)?q(\.gz)?$`) — the params note's
  "optional second mate" row is exactly the `sample_sheet:paired_or_unpaired`
  case. Galaxy maps unpaired rows to single datasets and paired rows to inner
  `paired` collections.
- `sample` column → **element identifier** per row (mirrors the source's
  `meta.id`; pattern `^\S+$` is a valid Galaxy `regex` validator on the
  identifier). Confidence medium: Galaxy could alternatively carry it as a
  `string` column; identifier is preferred so downstream per-sample outputs
  inherit it.
- Meta columns → `column_definitions`:

| Galaxy column | type | optional | restrictions / validators | Source column |
|---|---|---|---|---|
| `strandedness` | `string` | `false` | `restrictions: [forward, reverse, unstranded, auto]` (from nf-schema `enum`) | `strandedness` (required) |
| `seq_platform` | `string` | `true` | — | `seq_platform` |
| `seq_center` | `string` | `true` | — | `seq_center` |
| `percent_mapped` | `float` | `true` | — | `percent_mapped` (number) |

- Element datatypes: `fastqsanger` / `fastqsanger.gz` (high confidence —
  nf-schema pattern pins `.fq/.fastq(.gz)`, per the datatype note's rnaseq
  corpus entry). The compressed/uncompressed choice must stay per-dataset
  (Galaxy sniffing), not pinned in `format`.
- **Validation loss**: the nf-schema `pattern` on the path columns and
  `exists: true` checks have no Galaxy sample-sheet expression at slot level
  (the safe validator allowlist is `regex`/`in_range`/`length` on columns
  only); recorded, not worked around.
- **Loss / open obligation (ledger `bam-start-rows-unrepresented`)**: the row
  schema also has optional `genome_bam` / `transcriptome_bam` path columns
  (`.bam` patterns) for BAM-start runs. No single Galaxy `sample_sheet*`
  variant expresses "paired FASTQ *or* optional BAMs" in one row set
  (`sample_sheet:record` slots are single datasets, not pairs). v1 interface
  models FASTQ rows only; BAM-start is a deferred interface tier, not a
  silent drop.

Confidence: **high** (nf-schema row schema + `sample_sheets[]` + the one
substring-matched materialization channel agree).

### 2. Reference bundle (from the phase-2 brief, pinned here as inputs)

Phase-2 decisions inherited: explicit optional `data` inputs, no data tables,
iGenomes key dropped, heavy indexes get workflow-tier build-on-absence, cheap
derived assets get in-tool rebuild (all rebuild-unverified). This brief pins
the input ids, `format`, and optionality:

| Galaxy input id | Source param | gxformat2 | `format` | `optional` | Confidence |
|---|---|---|---|---|---|
| `reference_fasta` | `fasta` | `data` | `fasta` | true* | High |
| `annotation_gtf` | `gtf` | `data` | `gtf` | true* | High |
| `annotation_gff` | `gff` | `data` | `gff3` | true* | High |
| `gene_bed` | `gene_bed` | `data` | `bed` | true | High |
| `transcriptome_fasta` | `transcript_fasta` | `data` | `fasta` | true | High |
| `additional_fasta` | `additional_fasta` | `data` | `fasta` | true | High |
| `hisat2_splicesites` | `splicesites` | `data` | (omit — HISAT2 extract text file, no registry datatype) | true | Medium |
| `star_index` | `star_index` | `data` | (omit; directory/tarball — no STAR index datatype) | true | Medium |
| `hisat2_index` | `hisat2_index` | `data` | (omit; directory) | true | Medium |
| `rsem_index` | `rsem_index` | `data` | (omit; directory) | true | Medium |
| `salmon_index` | `salmon_index` | `data` | (omit; directory) | true | Medium |
| `kallisto_index` | `kallisto_index` | `data` | (omit; source expects directory, Galaxy's `kallisto.idx` is single-file — do not use it) | true | Medium |
| `bowtie2_index` | `bowtie2_index` | `data` | `bowtie_base_index` | true | Medium |
| `bbsplit_index` | `bbsplit_index` | `data` | (omit; no BBMap datatype) | true | Medium |
| `sortmerna_index` | `sortmerna_index` | `data` | (omit; directory) | true | Medium |
| `bowtie2_rrna_index` | `bowtie2_rrna_index` | `data` | `bowtie_base_index` | true | Medium |
| `kraken_db` | `kraken_db` | `data` | (omit; directory/tarball) | true† | Medium |
| `rrna_fastas` | `ribo_database_manifest` | `collection`, `list` | `fasta` | true† | Medium |
| `bbsplit_ref_fastas` | `bbsplit_fasta_list` | `collection`, `list` | `fasta` | true† | Medium |
| `sylph_dbs` | `sylph_db` | `collection`, `list` | (omit; `.syf` files, no registry datatype) | true† | Low |
| `sylph_taxonomies` | `sylph_taxonomy` | `collection`, `list` | `tabular` | true† | Low |
| `multiqc_config` | `multiqc_config` | `data` | (omit; YAML config) | true | Medium |
| `multiqc_logo` | `multiqc_logo` | `data` | (omit; image) | true | Medium |
| `multiqc_methods_description` | `multiqc_methods_description` | `data` | (omit; YAML/text) | true | Medium |

\* Practically-required core per the phase-2 carried assumption: `reference_fasta`
+ (`annotation_gtf` or `annotation_gff`) for alignment-based runs;
`transcriptome_fasta` or GTF/GFF for pseudo-alignment-only runs. gxformat2
cannot express "gtf or gff, at least one" — both stay `optional: true` with the
disjunction stated in `doc`; the launch-time gate is invisible to the summary
(ledger discovery `all-reference-assets-optional-in-summary`). Treat as the
documented core, not as 7 interchangeable optionals.

† Required-when-conditional: `kraken_db` when `contaminant_screening` ∈
{`kraken2`, `kraken2_bracken`}; `sylph_dbs`/`sylph_taxonomies` when
`contaminant_screening == sylph`; `rrna_fastas` when `remove_ribo_rna` (note:
the source's default manifest `assets/rrna-db-defaults.txt` has no portable
equivalent — ledger `rrna-default-db-no-portable-equivalent`);
`bbsplit_ref_fastas` when `skip_bbsplit` is false. All surface as optional with
gated `doc` (ledger `contaminant-db-conditional-requiredness` stays open).

`rrna_fastas` / `bbsplit_ref_fastas` close ledger `path-list-inputs-not-portable`:
the source params are path-list files whose contents are local filesystem
paths; the Galaxy representation is a `list` collection of user-supplied FASTA
datasets whose element identifiers carry the reference names the source took
from the manifest/list file.

### 3. Scalar workflow-shape controls (kept)

Tool/mode switches that select the subgraph — kept as gxformat2 scalars with
`restrictions` from the nf-schema enums. `optional: false` only where the
source default is a real mode choice carried into the interface; the default is
the source default.

| Galaxy input id | Source param | Type | Default | Restrictions |
|---|---|---|---|---|
| `aligner` | `aligner` | `string` | `star_salmon` | star_salmon, star_rsem, hisat2, bowtie2_salmon |
| `pseudo_aligner` | `pseudo_aligner` | `string` | (none) | salmon, kallisto |
| `trimmer` | `trimmer` | `string` | `trimgalore` | trimgalore, fastp |
| `remove_ribo_rna` | `remove_ribo_rna` | `boolean` | (none) | — |
| `ribo_removal_tool` | `ribo_removal_tool` | `string` | `sortmerna` | sortmerna, ribodetector, bowtie2 |
| `contaminant_screening` | `contaminant_screening` | `string` | (none) | kraken2, kraken2_bracken, sylph |
| `contaminant_screening_input` | `contaminant_screening_input` | `string` | `unmapped` | trimmed, unmapped, trim_only, raw |
| `bracken_precision` | `bracken_precision` | `string` | `S` | D, P, C, O, F, G, S |
| `with_umi` | `with_umi` | `boolean` | (none) | — |
| `umi_dedup_tool` | `umi_dedup_tool` | `string` | `umitools` | umitools, umicollapse |
| `umitools_bc_pattern` | `umitools_bc_pattern` | `string` | (none) | — (required when `with_umi`; ledger `umi-bc-pattern-conditional-requiredness`) |
| `umitools_bc_pattern2` | `umitools_bc_pattern2` | `string` | (none) | — |
| `umitools_extract_method` | `umitools_extract_method` | `string` | `string` | string, regex |
| `umitools_grouping_method` | `umitools_grouping_method` | `string` | `directional` | unique, percentile, cluster, adjacency, directional |
| `umitools_umi_separator` | `umitools_umi_separator` | `string` | (none) | — |
| `umi_discard_read` | `umi_discard_read` | `int` | (none) | — |
| `umitools_dedup_stats` | `umitools_dedup_stats` | `boolean` | (none) | — |
| `umitools_dedup_primary_only` | `umitools_dedup_primary_only` | `boolean` | (none) | — |
| `skip_umi_extract` | `skip_umi_extract` | `boolean` | (none) | — |
| `use_rustqc` | `use_rustqc` | `boolean` | `false` | — |
| `prokaryotic` | `prokaryotic` | `boolean` | (none) | — |

Notes:

- `prokaryotic` is `hidden: true` in nf-schema (normally an exclusion signal)
  but is referenced outside `publishDir` — the edge
  `params.prokaryotic ?: false → PREPARE_GENOME_REFERENCES` — and changes
  alignment parameters (scientific output). Per the control-param note's
  "promote, don't drop, when problematic" rule it is **promoted** to a public
  boolean despite the hidden flag (ledger decision
  `prokaryotic-promoted-to-input`). Same reasoning does not rescue
  `multiqc_config`/`multiqc_logo` (report customization only) or
  `gpu_container_options` (hardware).
- Skip flags gating analysis steps (kept as booleans, source defaults where
  declared): `skip_alignment`, `skip_trimming`, `skip_pseudo_alignment`,
  `skip_quantification_merge`, `skip_markduplicates`, `skip_bigwig`,
  `skip_stringtie`, `skip_fastqc`, `skip_preseq` (default `true`),
  `skip_dupradar` (default `false`), `skip_qualimap` (`false`),
  `skip_rseqc` (`false`), `skip_biotype_qc` (`false`), `skip_deseq2_qc`
  (`false`), `skip_multiqc`, `skip_qc`, `skip_bbsplit` (default `true`),
  `skip_gtf_filter`, `skip_gtf_transcript_filter`, `skip_linting`.
  **Caveat**: these keep decisions rest on param descriptions + enum values,
  not on guard evidence — `workflow.conditionals[]` extracted 1 of ~26 source
  guards (summary warning "workflow graph extraction is intentionally partial
  in resolver v1"; ledger discovery `branch-evidence-partial`). Confidence
  medium, not high.

### 4. Per-tool tunables (kept as optional scalars)

Kept because they alter tool commands/output sets, not just `publishDir`.
`optional: true` with the source default where one exists.

`gtf_extra_attributes` (string, `gene_name`), `gtf_group_features` (string,
`gene_id`), `featurecounts_group_type` (string, `gene_biotype`),
`featurecounts_feature_type` (string, `exon`), `gencode` (boolean),
`gffread_transcript_fasta` (boolean), `min_trimmed_reads` (int, `10000`),
`min_mapped_reads` (float, `5`), `deseq2_vst` (boolean, `true`),
`rseqc_modules` (string, comma list — consider `[string]` if the Galaxy
consumer takes repeats), `pseudo_aligner_kmer_size` (int, `31`),
`salmon_quant_libtype` (string with 16-value restrictions), 
`kallisto_quant_fraglen` (int, `200`), `kallisto_quant_fraglen_sd` (int,
`200`), `stranded_threshold` (float, `0.8`), `unstranded_threshold` (float,
`0.1`), `stringtie_ignore_gtf` (boolean), `star_ignore_sjdbgtf` (boolean),
`seq_center` (string), `seq_platform` (string), `multiqc_title` (string),
`hisat2_build_memory` (string, `200.GB`), and the pass-through
extra-argument strings `extra_trimgalore_args`, `extra_fastp_args`,
`extra_star_align_args`, `extra_hisat2_align_args`,
`extra_bowtie2_align_args`, `extra_salmon_index_args`,
`extra_salmon_quant_args`, `extra_kallisto_quant_args`, `extra_fqlint_args`
(default `--disable-validator P001`). The extra-args strings are free-text
tool CLI fragments; in Galaxy they should collapse into the selected wrapper's
own parameters at implement-galaxy-tool-step time rather than surviving as
raw strings — flagged for the data-flow/template Molds, not decided here.

**Interface-size strain**: ~50 scalar controls survive exclusion. That is the
faithful translation of the source surface; a curated-subset v2 would be a
brief change, not this Mold's call.

### 5. Excluded params (recorded, not silently dropped)

Per the cast's warning-and-impact posture. Tracing caveat: reference tracing
used `workflow.edges[]` + `workflow.conditionals[]`, and the conditional
evidence is near-empty (see above), so `assessment` below is name- and
description-based with enum/edge corroboration — medium confidence, recorded
per the note's own rule that a name match alone is not assessment.

| source_param | class | effect | assessment | reason |
|---|---|---|---|---|
| `outdir`, `publish_dir_mode` | Output location/publishing | History layout only | safe | Galaxy owns histories and workflow outputs |
| `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | Notification | Report delivery | safe | Runtime reporting, not scientific input |
| `validate_params`, `monochrome_logs`, `trace_report_suffix`, `help`, `help_full`, `show_hidden`, `version` | Runtime UX / CLI plumbing | Execution UX | safe | Nextflow CLI behavior |
| `config_profile_*` (4), `custom_config_version`, `custom_config_base` | Institutional config | Site environment | safe | Not user science |
| `save_merged_fastq`, `save_umi_intermeds`, `save_non_ribo_reads`, `save_bbsplit_reads`, `save_reference`, `save_trimmed`, `save_align_intermeds`, `save_unaligned`, `save_kraken_assignments`, `save_kraken_unassigned` | Publish toggles | Which intermediates land in results | safe (with caveat) | Galaxy output exposure is a workflow-design choice — replaced by the explicit output set below (ledger decision `save-flags-become-explicit-outputs`); caveat: cannot fully trace whether any also add tool arguments, conditional evidence is partial |
| `genome`, `igenomes_base`, `igenomes_ignore`, `arm`, `pipelines_testdata_base_path` | Hidden reference/CLI plumbing | iGenomes key resolution, container arch, test data base | safe | Dropped by phase-2 decision `igenomes-key-dropped-from-surface` / CLI plumbing; `pipelines_testdata_base_path` is the known `reference_assets[]` false positive |
| `gpu_container_options`, `use_gpu_ribodetector` | Hardware/runtime | GPU flags | safe | No GPU scheduling surface in a stock Galaxy; ribodetector falls back to CPU |
| `use_sentieon_star`, `use_parabricks_star` | Proprietary accelerators | Replace STAR/MarkDuplicates with licensed tools | **problematic (dropped)** | No freely installable Galaxy wrapper exists for Sentieon or Parabricks; recorded as ledger drop `sentieon-parabricks-accelerators-dropped`, reason uncited (no tool search performed in this phase) |

## Workflow outputs

Labels are stable public names (test keys address these, per the testability
note; treat any rename as a test-interface change). Collection element
identifiers inherit the sample sheet's `sample` values.

| Galaxy output id | Producing source (summary evidence) | Shape | `format` | Checkpoint | Confidence |
|---|---|---|---|---|---|
| `multiqc_report` | `MULTIQC.out.report` `path("*.html")`; `RNASEQ.out.multiqc_report` | File | `html` | smoke | High |
| `gene_counts` | `TXIMETA_TXIMPORT.out.counts_gene_scaled` `path("*gene_counts_scaled.tsv")` (salmon route); `CUSTOM_RSEMMERGECOUNTS` (rsem route) | File | `tsv` | **yes — content** | High |
| `gene_tpm` | `TXIMETA_TXIMPORT.out.tpm_gene` `path("*gene_tpm.tsv")` | File | `tsv` | no | High |
| `transcript_counts` | `TXIMETA_TXIMPORT.out.counts_transcript` | File | `tsv` | no | High |
| `aligned_bams` | `STAR_ALIGN.out.bam_sorted_aligned` / `BAM_SORT_STATS_SAMTOOLS` / markdup output `*.bam` | `list` | `bam` | no | High |
| `bam_stats` | `SAMTOOLS_STATS.out.stats` `path("*.stats")` | `list` | `tabular` | **yes — per-sample content** | High |
| `star_alignment_log` | `STAR_ALIGN.out.log_final` `path('*Log.final.out')` | `list` | `tabular` | **yes — per-sample content** | High |
| `salmon_quant` | `SALMON_QUANT.out.results` `path("${prefix}")` (a **directory** per sample) | `list` | `tabular` (quant.sf / quant.genes.sf after extraction) | **yes — per-sample content** | Low (shape hazard: source emits a per-sample directory; Galaxy list collections hold datasets, so the data-flow Mold must extract `quant.sf`/`quant.genes.sf` or expose a different shape) |
| `coverage_bigwigs` | `UCSC_BEDGRAPHTOBIGWIG` output `*.bw` via `BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG` | `list` | `bigwig` | no | Medium |
| `deseq2_qc_plots` | `DESEQ2_QC.out.pdf` `path("*.pdf")` | File | (omit — no `pdf` in the registry) | no | Medium |
| `deseq2_pca_values` | `DESEQ2_QC.out.pca_txt` `path("*pca.vals.txt")` | File | `tabular` | **yes — stable summary** | High |
| `pipeline_versions` | `MULTIQC` software-versions / `softwareVersionsToYAML` | File | `txt` | no | Medium |

Checkpoint rationale (testability note): `gene_counts` gives a cross-sample
content assertion; `bam_stats` / `star_alignment_log` / `salmon_quant` give
per-sample element assertions addressable through the sample identifiers;
`multiqc_report` is a smoke check only; `deseq2_pca_values` is a stable
structured summary that an image cannot replace. Outputs deliberately *not*
exposed: every intermediate FASTQ/BAM variant the `save_*` flags gated —
their exposure is now an explicit design choice (this table), not a flag.

Version-pin note: the summary shows `tools[].versions` divergence for shared
dependencies (e.g. samtools pinned at multiple versions across modules); the
interface does not pin tool versions — that belongs to the template/tool-step
Molds reading `tools[]`.

## Collection shapes summary (channel-shape note)

| Source shape (summary evidence) | Galaxy shape |
|---|---|
| `samplesheetToList` rows: `tuple val(meta), path(reads)` with `fastq_1`+optional `fastq_2` | `sample_sheet:paired_or_unpaired` (input side) |
| Repeated `tuple val(meta), path("*.bam")` per sample | `list` (`aligned_bams`) |
| Repeated `tuple val(meta), path("*.stats")` / `path('*Log.final.out')` | `list` (`bam_stats`, `star_alignment_log`) |
| Global singletons: MultiQC report, merged counts | File outputs |
| `SALMON_QUANT` per-sample directory | unresolved — see `salmon_quant` hazard above |
| Reference index directories (star, salmon, …) | single optional `data` inputs, not collections (one index per run, broadcast to the per-sample map-over) |

## Provenance summary

- Source: nf-core/rnaseq 3.27.0, revision `95dbcd9…`, summary produced by
  phase 1 (`summarize-nextflow`).
- Input-side evidence: `params[]` (130 entries), `sample_sheets[0]`
  (nf-schema, `assets/schema_input.json`), `workflow.channels[0]`
  (`ch_samplesheet`, substring-bound to `params.input`),
  `workflow.edges[]` (params → `PREPARE_GENOME_REFERENCES` /
  `PREPARE_GENOME_INDICES` / `RNASEQ`), `subworkflows[]` `RNASEQ` take block.
- Output-side evidence: `processes[].outputs[]` patterns for `MULTIQC`,
  `SALMON_QUANT`, `STAR_ALIGN`, `TRIMGALORE`, `SAMTOOLS_STATS`,
  `DESEQ2_QC`, `TXIMETA_TXIMPORT`; `test_candidates[]` "Params: default"
  fixtures (samplesheet v3.10 CSV + reference FASTAs) confirm the FASTQ-first
  interface is fixture-compatible.
- Reference inputs: pinned from `nextflow-galaxy-reference-data.md` (phase 2),
  which cites `reference_assets[]` (22 entries) and `reference_rebuilds[]`
  (empty — positive-form detector gap).

## Open questions

1. **BAM-start rows** (ledger `bam-start-rows-unrepresented`): no Galaxy
   sample-sheet variant mixes paired FASTQ and optional BAM slots; v1 defers
   BAM-start support.
2. **Conditional requiredness** (ledger `contaminant-db-conditional-requiredness`,
   `umi-bc-pattern-conditional-requiredness`): gxformat2 has no clean
   required-when-conditional; affected inputs stay optional with gated `doc`.
3. **FASTA+GTF/GFF core requiredness** is an assumption from phase 2, not
   summary evidence; the interface documents rather than enforces it.
4. **`salmon_quant` directory shape** needs a data-flow decision (extract
   `quant.sf` per sample, or restructure).
5. **Rebuild verification** (ledger `rebuild-unverified-positive-form`) stays
   open; the workflow-tier index-build steps this interface assumes for the
   heavy indexes are unverified against actual wrapper capabilities.
6. **Interface surface scale**: ~50 scalar controls is faithful but heavy;
   a curated subset would need an explicit brief change.
7. **`rseqc_modules`** is a comma-separated string in the source; whether the
   Galaxy consumer takes a repeatable param or a single string is a
   tool-step decision.
