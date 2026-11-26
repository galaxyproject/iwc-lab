# Galaxy interface brief — OceanOmics-amplicon-nf

Produced by `nextflow-summary-to-galaxy-interface` from `summary-nextflow.json`, `nextflow-galaxy-reference-data.md` and `open-requirements.ledger.yml`. Consumers: data-flow, template, test-plan Molds.

## Scope decision
The Galaxy workflow starts from **already-demultiplexed per-sample paired reads**, which is the source's `--skip_demux` entry. It then carries primer trimming, then ASV (DADA2) and ZOTU (vsearch) inference, LULU curation, BLAST against a user-supplied DB, LCA, phyloseq and proportional filtering, plus FastQC/MultiQC.
Why: the demux plane (CREATE_DEMUX_DEPENDENCIES → cutadapt combinatorial/UDI → mmv RENAME → CONCAT → POSTDEMUX_SAMPSHEET → SAMPLESHEET_CHECK) rebuilds the samplesheet mid-run and reshapes per-sample channels from file names. Its test inputs are also not runnable: `raw_data` is one R1 file given to `Channel.fromFilePairs`, and the test samplesheet uses `sample` where SAMPLESHEET_CHECK requires `samp_name` (summary warnings). The test samplesheet does carry per-sample paired FASTQ URLs (12S, 16S simulated reads), and those are exactly the skip_demux input. Recorded as `kind: dropped` in the ledger.

## Workflow inputs

| Label | gxformat2 type | collection_type / format | optional | default | Source | Confidence |
|---|---|---|---|---|---|---|
| `reads` | collection | `list:paired`, `fastqsanger.gz` | no | — | `params.input` rows `fastq_1`/`fastq_2` (skip_demux branch of `create_fastq_channel`); element id = `samp_name` | high (shape), medium (sample-sheet vs list) |
| `sample_metadata` | data | `csv` | no | — | `params.input` consumed literally by PHYLOSEQ (`ch_input.first()`) as sample metadata | high |
| `blast_db` | data | `blastdbn` | no | — | `params.dbfiles` (required; ref-data brief) | medium (OQ-1 v5 volumes) |
| `taxonomy_lineage` | data | `tabular` | no | — | **new**: NCBI `rankedlineage.dmp` that LCA wgets at run time (ref-data OQ-2) | medium |
| `filter_table` | data | `csv` | yes | — | `params.filter_table` → PHYLOSEQ | high |
| `fw_primer` | string | — | no | `GACCCTATGGAGCTTTAGAC` | `params.fw_primer` (`;`-separated allowed) | high |
| `rv_primer` | string | — | no | `CGCTGTTATCCCTADRGTAACT` | `params.rv_primer` | high |
| `read_minlen` | int | — | no | 40 | DADA2_FILTERANDTRIM minLen | high |
| `read_maxlen` | int | — | no | 1000 | DADA2_FILTERANDTRIM maxLen | high |
| `asv_pooled` | string | restrictions `true`/`false`/`pseudo` | no | `true` | DADA2 sample inference `pool` | medium (source type is string) |
| `asv_min_overlap` | int | — | no | 12 | DADA2_MERGE minOverlap | high |
| `asv_max_mismatch` | int | — | no | 0 | DADA2_MERGE maxMismatch | high |
| `asv_min_length` | int | — | no | 0 | FLAG_OTUS_OUTSIDERANGE | high |
| `asv_max_length` | int | — | no | 1000 | FLAG_OTUS_OUTSIDERANGE | high |
| `zotu_min_size` | int | — | no | 8 | vsearch cluster_unoise --minsize | high |
| `zotu_id` | float | — | no | 0.97 | vsearch usearch_global --id | high |
| `lulu_min_match` | int | — | no | 84 | LULU minimum_match | high |
| `blast_pid` | int | — | no | 90 | blastn -perc_identity | high |
| `blast_qcov` | int | — | no | 90 | blastn -qcov_hsp_perc | high |
| `blast_evalue` | float | — | no | 0.001 | blastn -evalue | high |
| `lca_pid` | int | — | no | 90 | LCA pid threshold | high |
| `lca_qcov` | int | — | no | 90 | LCA qcov threshold | high |
| `lca_diff` | int | — | no | 1 | LCA %id diff | high |

Test profile overrides to record for the test plan: `fw_primer=AAAACCCCTTTTGGGG`, `asv_min_overlap=0`, `asv_max_mismatch=12`, `asv_pooled=false`, `blast_qcov=50`, `lca_qcov=50`, `zotu_min_size=1`, `rv_primer` empty in samplesheet (see OQ-I2).

## Workflow outputs (labels)

| Label | Shape / format | Source producer | Why exposed |
|---|---|---|---|
| `fastqc_html` | list, html | FASTQC | QC |
| `multiqc_report` | html | MULTIQC | QC summary |
| `asv_fasta` | fasta | DADA2_FINALOUTPUTS.asv_fasta | checkpoint |
| `asv_table` | tabular | DADA2_FINALOUTPUTS.asv_tsv | checkpoint, testable |
| `asv_track_reads` | tabular | DADA2_TRACKREADS.txt | read-retention checkpoint |
| `zotu_fasta` | fasta | VSEARCH_UCHIME3DENOVO | checkpoint |
| `zotu_table` | tabular | VSEARCH_USEARCHGLOBAL.zotu_tsv | checkpoint, testable |
| `lulu_curated_table` | collection list (asv, zotu) or two datasets, tabular | LULU | curated table |
| `blast_results` | tabular (per prefix) | CONCAT_BLASTN_RESULTS | checkpoint |
| `lca_table` | tabular (per prefix) | REMOVE_DUPS.tsv | primary taxonomy result |
| `phyloseq_object` | rdata | PHYLOSEQ / FLAG_OTUS_OUTSIDERANGE | primary product |
| `final_taxa` | tabular | PROPORTIONAL_FILTER.final_taxa | primary product |
| `filtered_otu_table` | tabular | PROPORTIONAL_FILTER.final_otu | primary product |

Prefix semantics: the source runs every downstream step once per string prefix (`asv_db1`, `zotu_db1`, plus `_lulucurated` variants). In Galaxy those prefixes are best modelled as **element identifiers of a list collection** that downstream steps map over. The data-flow Mold owns that choice.

## Excluded params

| Param(s) | Class | Effect | Assessment |
|---|---|---|---|
| `outdir`, `publish_dir_mode`, `tracedir`, `email*`, `plaintext_email`, `hook_url`, `monochrome_logs`, `help`, `version`, `validate_params`, `show_hidden_params`, `schema_ignore_params`, `max_*`, `config_profile_*`, `custom_config_*`, `binddir`, `max_multiqc_email_size` | publish / notification / CLI / site | runtime only | safe |
| `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`, `multiqc_title` | report config | cosmetic | safe (fixed default) |
| `project_id`, `assay`, `seq_run_id`, `readlength` | naming / metadata | output-name prefix; `assay` also selects primer/length presets from `conf/assay_params.config` | `assay`: **problematic → resolved as fixed explicit scalars** (primers and length inputs exposed directly) |
| `ulimit` | runtime | process fd limit | safe |
| `raw_data`, `skip_demux`, `alt_demux`, `demux_udi`, `cutadapt_error`, `cutadapt_min_len` | demux plane | scope | **dropped** (ledger) |
| `skip_primer_trim`, `skip_primer_leftover_trim`, `skip_asvs`, `skip_zotus`, `skip_lulu`, `skip_lulu_comparison`, `skip_classification`, `skip_filter` | skip flags | gate branches | fixed to source defaults (all steps run); not exposed in v1 |
| `seqtk_trim`, `seqtk_length`, `fastp_trim`, `fastp_*` | optional trimming (default off) | gate SEQTK_TRIM / FASTP | fixed off; dropped (ledger) |
| `zotu_mode`, `usearch64`, `zotu_min_quality`, `zotu_min_align_leng` | ZOTU engine | default `vsearch`; usearch is proprietary | fixed `vsearch`; `zotu_min_quality`/`zotu_min_align_leng` feed ADAPTERREMOVAL args, fixed to defaults (10, 6) |
| `start_from_blast`, `start_from_lca`, `fasta`, `otu_table`, `blast_results`, `partial_run_prefix` | partial-run entry points | alternate entry | dropped (ledger) |
| `dbfiles2`, `blast_twice`, `db2name` | second DB | — | dropped (ref-data ledger) |
| `dbname` | naming | prefix suffix only | safe (fixed `db1`) |
| `blast_task`, `blast_max_tar_seq`, `blast_best_hit_*`, `blast_taxids`, `blast_negative_*` | BLAST tuning | tool args | fixed to defaults (`blastn`, 99999, unset) |
| `masterlist`, `aquamaps_db`, `faire_mode`, `faire_metadata`, `lca_with_fishbase`, `normalise_pid`, `use_bitwise`, `primertrim_error`, `obi3_*`, `mitodbfiles`, `caabmap` | optional branches / unused | — | dropped or fixed default (ledger) |

## Open questions
- **OQ-I1:** `sample_sheet:paired` vs `list:paired` + `sample_metadata` csv. The source consumes the samplesheet file literally (PHYLOSEQ metadata, extra columns such as lat/long), so the brief keeps a flat csv beside a `list:paired`. A sample_sheet collection would duplicate it.
- **OQ-I2:** In the test samplesheet, `rv_primer` is empty while the profile sets only `fw_primer`. The source's `params.rv_primer` keeps its default `CGCTGTTATCCCTADRGTAACT`, so the test plan should use the default unless the reads lack it.
- **OQ-I3:** The test samplesheet's `fastq_1`/`fastq_2` reads are 12S and 16S simulations under one primer pair. Expected outputs are unknown (no assertions in the source).
