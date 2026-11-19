# Nextflow → Galaxy interface brief — nf-core/ampliseq 3.1.0

Inputs to this brief: `<run>/summary-nextflow.json` (source b9bd579), `<run>/nextflow-galaxy-reference-data.md`, `<run>/open-requirements.ledger.yml`. Per `nextflow-params-to-galaxy-inputs`: classification from launch params + materialization evidence; per `nextflow-to-galaxy-channel-shape-mapping` and `galaxy-sample-sheet-collections` for shapes.

**Source fact**: nf-schema declares only `outdir` as required; `--input`/`--input_fasta` either-or is enforced at runtime (`workflows/ampliseq.nf:205`). All requiredness below is therefore semantic, not schema-required.

## Workflow labels

- Name: `nf-core/ampliseq (ASV/OTU amplicon analysis) 3.1.0`; tags: `amplicon`, `16S`, `ITS`, `ASV`, `DADA2`, `taxonomy`, `microbiome`; source: https://github.com/nf-core/ampliseq @ b9bd579.

## Primary data inputs

| Input | gxformat2 shape | Details | Confidence |
|---|---|---|---|
| `input` | collection `sample_sheet:paired_or_unpaired` | from `input` tsv via `samplesheetToList` (`assets/schema_input.json`); `fastq_2` optional ⇒ paired_or_unpaired. Element datatypes `fastqsanger.gz` (fastq patterns are gz-only). Columns: `sample` (string, req), `run` (string, opt), `control` (string, opt, restrictions `[control, sample]`), `quant_reading` (string, opt). nf-schema `pattern` validators on sample/run downgrade to prose (regex allowlist OK but sample pattern `^[a-zA-Z][a-zA-Z0-9_]+$` is expressible — apply as regex validator). **Element identifier**: `sample` alone is NOT unique (multi-run sheets repeat it; summary data-flow rule); identifier = `sample` + `__` + `run` when `run` set — derivation owned by data-flow. | High |
| `input_fasta` | data `fasta`, optional | Alternate entry (ASV/OTU fasta → FORMAT_FASTAINPUT bypass, `workflows/ampliseq.nf:202,746`). Exactly-one-of with `input` inexpressible in gxformat2 → obligation `either-of-input-interface-loss`; v1 treats `input` as primary required and `input_fasta` optional alt with doc note. | High |
| `multiregion` | data `tsv`, optional | `assets/schema_multiregion.json` sheet has **no path columns** (region, region_length int, primer_fwd, primer_rev) → flat tabular input, not sample_sheet. | High |
| `pplace_sheet` | data `tsv`, optional | `assets/schema_pplace_sheet.json`; rows reference HMM/reference **file names** (`hmm`, `refseqfile`, `refphylogeny`) that the source resolves from the reference-download tier — no carrier in v1 (obligation `pplace-sheet-file-refs`). `alignmethod` enum `[hmmer, clustalo, mafft]` row-wise. | Medium |
| `metadata` | data `tsv`, optional | Sample metadata; gates FILTER_SAMPLES / METADATA_* analyses (`params.metadata &&` guards). Without it most downstream stats are skipped — keep optional with doc. | High |

## Reference / database inputs (from reference-data brief; all optional `data`)

| Input | format | Group |
|---|---|---|
| `dada_ref_tax_custom` | `data` | DADA2 pair (mate below) |
| `dada_ref_tax_custom_sp` | `data` | DADA2 species mate |
| `qiime_ref_tax_custom` | `data` | tarball/qza — **split affordance**: pair form = second optional input (resolves `qiime-ref-tax-custom-two-path-affordance`) |
| `qiime_ref_tax_custom_2` | `data`, optional | second qza of the pair |
| `qiime_classifier` | `data` | trained-classifier qza |
| `kraken2_ref_tax_custom` | `data` (tgz) | |
| `sintax_ref_tax_custom` | `fasta` | |
| `vsearch_lca_ref_tax_custom` | `fasta` | |
| `sidle_ref_tax_custom` | `data` (txt) | SIDLE quartet |
| `sidle_ref_seq_custom` | `fasta` | |
| `sidle_ref_aln_custom` | `fasta` | |
| `sidle_ref_tree_custom` | `data` (qza) | |
| `pplace_tree` | `newick` | pplace set; enablement keyed on these inputs, not the DADA2 catalog key (obligation `pplace-enablement-keyed-on-selector`) |
| `pplace_aln` | `fasta` | |
| `pplace_taxonomy` | `tsv`, optional | |
| `expected_sequences` | `fasta`, optional | validation truth |
| `expected_abundances` | `tsv`, optional | |
| `expected_profile` | `tsv`, optional | |
| `multiqc_config` | `data` (yaml), optional | real MultiQC tool input |
| `multiqc_logo` | `data` (png), optional | |
| `multiqc_methods_description` | `data` (yaml), optional | |
| `report_abstract` | `data` (md), optional | |

**Not exposed**: the six `*_ref_taxonomy` selector strings, the 144-key download catalog, `ref_taxonomy_storage` (inherited obligations, confirmed here). `branch enablement = custom input supplied` (ledger discovery `taxonomy-custom-overrides-selector`).

## Scalar workflow inputs (v1 exposed set)

Enums from `nextflow_schema.json` verbatim unless noted.

### Mode / branch switches
| Input | type | default | notes |
|---|---|---|---|
| `sequencing_type` | string, restrictions `[illumina_pe, illumina_se]` | `illumina_pe` | full enum also has iontorrent/pacbio/nanopore — **restricted; platforms not carried** (obligation `non-illumina-platforms-not-carried`) |
| `asv_calling` | string, restrictions `[auto, dada2]` | `auto` | `savont` is ONT-only → dropped with platform |
| `sample_inference` | string enum `[independent, pooled, pseudo]` | `pooled` | |
| `mergepairs_strategy` | string enum `[merge, concatenate, consensus]` | `merge` | |
| `quality_type` | string enum `[Auto, FastqQuality, SFastqQuality]` | `Auto` | |
| `binned_quality` | string, optional | | DADA2 binned-quality bins |
| `decontam` | string enum `[none, decontaminate, notcontaminant]` | `none` | |
| `decontam_decontaminate_method` | string enum `[auto, frequency, prevalence, combined, minimum, either, both]` | `auto` | |
| `its_extractor` | string enum `[itsx, itsxrust]` | `itsx` | |
| `cut_its` | string enum `[none, full, its1, its2]` | `none` | |
| `filter_ssu` | string, restrictions = 15 kingdom-combo enum | — | |
| `consolidate_taxonomies` | string enum `[first, most-specific, score]` | `first` | |
| `expected_sequences_region` | enum `[alignment, observed, expected]` | `observed` | |
| `expected_sequences_merge` | enum `[all, observed, expected, none]` | `all` | |
| `pplace_alnmethod` | string enum `[hmmer, clustalo, mafft]` | `clustalo` | hmmer rows need `hmm` files (see obligation) |
| `run_pplace` | boolean | `false` | |

### Primers / trimming
`primer_fwd` (string), `primer_rev` (string) — runtime-required for illumina; `trunclenf`/`trunclenr` (int), `truncq` (int 2), `trunc_qmin` (int 25), `trunc_rmin` (float 0.75), `cutadapt_min_overlap` (int 3), `cutadapt_max_error_rate` (float 0.1), `double_primer` (bool), `retain_untrimmed` (bool), `illumina_pe_readthrough` (bool).

### DADA2 core tuning (exposed — scientifically load-bearing)
`max_ee` (int 2), `max_ee_r` (int), `min_len` (int 50), `max_len` (int), `min_read_counts` (int 1), `ignore_failed_filtering` / `ignore_failed_trimming` / `ignore_empty_input_files` / `ignore_binned_quality` (bool — these change which samples survive; promote, don't drop).

### ASV post-processing / filtering
`vsearch_cluster` (bool), `vsearch_cluster_id` (float 0.97), `min_len_asv` / `max_len_asv` (int), `filter_codons` (bool), `orf_start` (int 1), `orf_end` (int), `stop_codons` (string `TAA,TAG`), `min_frequency` (int 1), `min_samples` (int 1), `exclude_taxa` (string `mitochondria,chloroplast`), `decontam_decontaminate_threshold` (float 0.1), `decontam_notcontaminant_threshold` (float 0.5), `its_partial` (int 0).

### Taxonomy controls
`dada_min_boot` (int 50), `dada_assign_taxlevels` (string), `dada_addspecies_allowmultiple` (bool), `dada_taxonomy_rc` (bool), `addsh` (bool), `sintax_cutoff` (float 0.8), `sintax_assign_taxlevels`, `kraken2_confidence` (float 0.0), `kraken2_assign_taxlevels`.

### Downstream analyses
`metadata_category` (string), `metadata_category_barplot` (string), `qiime_adonis_formula` (string), `diversity_rarefaction_depth` (int 500), `tax_agglom_min` (int 2), `tax_agglom_max` (int 6), `picrust` (bool), `ancom` (bool), `ancom_sample_min_count` (int 1), `ancombc` (bool), `ancombc_formula` (string), `ancombc2` (bool), `ancombc2_formula` (string), `seed` (int 100), `pplace_model` (string).

### Skip flags (boolean, default false — all keep, each gates processes/outputs)
`skip_fastqc`, `skip_cutadapt`, `skip_dada_quality`, `skip_barrnap`, `skip_taxonomy`, `skip_dada_taxonomy`, `skip_dada_addspecies`, `skip_barplot`, `skip_abundance_tables`, `skip_alpha_rarefaction`, `skip_diversity_indices`, `skip_phyloseq`, `skip_tse`, `skip_multiqc`, `skip_report`, `skip_parquet_summary`. (`skip_porechop_abi`, `skip_chopper` dropped with ONT.)

### Report customization
`multiqc_title` (string), `report_title` (string `Summary of analysis results`).

## Excluded control params (consolidated notice)

| Group | Params | Effect | Assessment |
|---|---|---|---|
| Output location/publishing | `outdir`, `publish_dir_mode`, `save_intermediates` | Galaxy owns histories/exposure | `save_intermediates` **problematic→promoted as design default**: qza/qzv intermediates are NOT promoted as workflow outputs in v1 (recorded drop); everything else safe |
| Email/notification | `email`, `email_on_fail`, `plaintext_email`, `max_multiqc_email_size` | runtime reporting | safe |
| CLI/UX/profile | `help`, `help_full`, `show_hidden`, `version`, `monochrome_logs`, `validate_params`, `trace_report_suffix`, `config_profile_*` (4), `custom_config_*` (2) | CLI/site config | safe |
| Test infra | `pipelines_testdata_base_path` | test-data base URL (used by fixtures, not runtime input) | safe (phase-8 note: fixtures resolve against it) |
| Bundled assets | `report_template`, `report_css`, `report_logo`, `pplace_name` | paths into the pipeline's own `assets/`; cosmetic run name | safe if Galaxy report step is authored without them; medium if summary report is kept verbatim — carry as authoring note |

## Fixed-at-source-defaults (long-tail tuning; see ledger `param-surface-tuning-scalars`)

~55 per-tool fine-tuning scalars stay at their source defaults as workflow design constants (not user inputs): `mergepairs_consensus_*` (6), `vsearch_lca_*` tuning (5), `ancombc*_formula_reflvl/effect_size/significance` (6), `dada_assign_chunksize`, `savont_options` (dropped w/ ONT), `sidle_ref_degenerates` (5), `sidle_ref_cleaning`, `kraken2_*`/`sintax_*` remaining tuning, `raise_filter_stacksize`, `expected_sequences_mismatches` (0), `orf_*` residuals, `multiqc_email`-adjacent. Sanctioned by params-note: "keep as scalar input **or resolve to a fixed Galaxy design default**".

## Workflow outputs (public, stable labels)

Publishing evidence from `conf/modules.config` (centralized `process.withName` publishDir — the per-process artifact field is empty; see feedback). `*` = promoted test checkpoint (per galaxy-workflow-testability-design: stable, content-checkable):

| Output label | datatype | source (publish evidence) |
|---|---|---|
| `asv_sequences` * | `fasta` | final ASV fasta (dada2 export; `_final_asvs.fasta` analogue) |
| `counts_table` * | `tsv` | `SUMMARY_TABLE_COUNTS` (`ampliseq.counts`) |
| `taxonomy_table` * | `tsv` | `SUMMARY_TABLE_TAXONOMY` (`ampliseq.taxonomy`) |
| `per_sample_stats` | `tsv` | `MERGE_STATS_*` merged stats tables |
| `dada2_quality_plots` | pdf/svg collection | DADA2_QUALITY1/2 publishes |
| `tool_taxonomy_tables` | tsv collection | FORMAT_TAXRESULTS_* (sintax/kraken2/vsearch/qiime per enabled branch) |
| `diversity_results` | svg/html collection | alpha/beta plots, skip-gated |
| `barplots` | pdf/svg collection | QIIME2_BARPLOT/AVG, skip-gated |
| `phyloseq_objects`, `tse_objects` | rds | skip-gated exports |
| `summary_parquet` | parquet collection | `DUCKDB_TABLE2PARQUET` → `summary_tables/` |
| `multiqc_report` * | `html` | MULTIQC publish (smoke-check value) |
| `summary_report` | md/html | SUMMARY_REPORT |

qza/qzv intermediates not promoted (v1; drop recorded). Element identifiers must stay sample-keyed through map-overs (data-flow owns derivation; see identifier note above).

## Confidence & open questions

- High: input sheet shape, reference inputs (inherited), skip-flag set, output groups.
- Medium: `either-of` input validation (obligation), pplace sheet row-refs (obligation), tuning-surface cut (judgment, sanctioned but first worked instance).
- Open: whether `input_fasta` entry scenario is carried at all in v1 (interface keeps the input; template may scope FORMAT_FASTAINPUT path out — flag to data-flow/template); multiregion multi-region fan-in shape (data-flow).
