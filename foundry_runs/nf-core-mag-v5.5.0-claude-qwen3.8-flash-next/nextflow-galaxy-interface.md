# Galaxy interface brief — nf-core/mag → Galaxy

Consumes `summary-nextflow.json` (source of truth) and `nextflow-galaxy-reference-data.md`
(reference posture). Rules applied: params→inputs translation order, sample-sheet
variants, channel-shape mapping, datatype evidence precedence, testability design.

Source provenance: nf-core/mag 5.5.0 @ db7772f (`source.ecosystem nf-core`, URL
https://github.com/nf-core/mag, MIT). Primary workflow MAG; input materializations
`samplesheetToList(params.input, assets/schema_input.json)` and
`samplesheetToList(params.assembly_input, assets/schema_assembly_input.json)` inside
PIPELINE_INITIALISATION.

## Interface posture

Two input modalities (reads vs pre-assemblies) are mutually exclusive in the source
(`anyOf` between `input` / `assembly_input`; assembly_input bypasses QC+assembly).
Galaxy cannot express "required unless the other is set", so: a scalar **`input_mode`**
plus two optional sample-sheet inputs (branch-required pattern from the params note).
Analysis databases are optional inputs whose presence gates their branch (reference
brief; replaces `run_*`/`skip_*`-paired DB params).

## Workflow inputs

### Mode

| input | gxformat2 | default | optional | source | conf |
|---|---|---|---|---|---|
| `input_mode` | string, restrictions `[reads, assemblies]` | `reads` | no | derived (schema anyOf input↔assembly_input; `assembly_input` branch in mag.nf) | Medium (design inference; fills a branch-required gap) |

### Samplesheets

**`reads_samplesheet`** ← `params.input` (`samplesheetToList`, High materialization).
`type: collection`, `collection_type: sample_sheet:record` — row carries heterogeneous
data (optional SR pair AND optional LR). Inner record slots: `short_reads`
(paired_or_unpaired), `long_reads` (dataset).
`column_definitions`:

| column | type | optional | validators / restrictions | nf-schema origin |
|---|---|---|---|---|
| sample | string | false | regex `^\S+$` | required, pattern |
| run | string | true | regex `^\S+$` | pattern |
| group | string | false | regex `^\S+$` | required |
| short_reads_platform | string | true | restrictions enum (ILLUMINA, BGISEQ, LS454, ION_TORRENT, DNBSEQ, ELEMENT, ULTIMA, VELA_DIAGNOSTICS, GENAPSYS, GENEMIND, TAPESTRI) | enum |
| long_reads_platform | string | true | restrictions enum (OXFORD_NANOPORE, OXFORD_NANOPORE_HQ, PACBIO_CLR, PACBIO_HIFI) | enum |

Elements: FASTQ files → `fastqsanger.gz` (High, pattern `^\S+\.f(ast)?q\.gz$`).
Optional (`input_mode == reads`). Confidence **Medium**: nf-schema `anyOf`
(SR or LR per row), `dependentRequired` (R2⇒R1, platform⇒reads) and
cross-column rules exceed the Galaxy validator allowlist (regex/in_range/length) —
downgraded to column `description` prose (validation loss, see open questions).
Nullability of record slots for LR-only / SR-only rows is **unverified** — fallback:
split into `short_reads_samplesheet` (`sample_sheet:paired_or_unpaired`) +
`long_reads_samplesheet` (`sample_sheet`) (ledger entry).

**`assembly_samplesheet`** ← `params.assembly_input`.
`type: collection`, `collection_type: sample_sheet` (one path column per row).
Elements `fasta` (pattern `.fasta|.fas|.fa|.fna(.gz)`, High).
`column_definitions`: id (string, false, regex `^\S+$`), group (string, false,
regex `^\S+$`), assembler (string, false, restrictions `[MEGAHIT, SPAdes,
SPAdesHybrid, Flye, MetaMDBG]`, High — enum). Optional (`input_mode == assemblies`).

### Reference data (all optional `data` inputs, per reference brief)

| input | source_param | format | note |
|---|---|---|---|
| `phix_reference` | phix_reference | fasta | absent ⇒ no phiX removal (= keep_phix); bundled copy documented in help |
| `lambda_reference` | lambda_reference | fasta | absent ⇒ no NANOLYSE/chopper lambda step |
| `host_genome` | host_fasta | fasta | host removal gated on presence; bowtie2 index built in-tool (not surfaced) |
| `busco_db` + `busco_db_lineage` (string, optional) | busco_db, busco_db_lineage | tar.gz | presence ⇒ BUSCO QC (run_busco merged) |
| `checkm_db` | checkm_db | tar.gz | presence ⇒ CheckM QC (run_checkm merged) |
| `checkm2_db` | checkm2_db | tar.gz | presence ⇒ CheckM2 QC (run_checkm2 merged) |
| `gunc_db` | gunc_db | data | presence ⇒ GUNC (run_gunc merged) |
| `gtdbtk_db` | gtdb_db | tar.gz | plus `skip_gtdbtk` switch |
| `cat_db` | cat_db | tar.gz | presence ⇒ CATPACK; `cat_db_generate` not carried |
| `genomad_db` | genomad_db | tar.gz/data | plus `run_virus_identification` |
| `metaeuk_db` | metaeuk_db ∪ metaeuk_mmseqs_db | data | presence ⇒ MetaEuk branch |

### Scientific switches kept (branch/tool/mode effects; defaults from params[])

Booleans (default false unless noted): `single_end`, `skip_clipping`,
`skip_shortread_qc`, `skip_fastqc`, `skip_longread_qc`, `skip_longread_filtering`,
`filtlong_filtering_by_shortreads`, `bbnorm`, `coassemble_group`, `skip_spades`,
`skip_spadeshybrid`, `skip_megahit`, `skip_flye`, `skip_metamdbg`, `run_pypolca`,
`skip_binning`, `skip_metabat2`, `skip_maxbin2`, `skip_concoct`, `skip_comebin`,
`skip_metabinner`, `skip_semibin`, `refine_bins_dastool`,
`exclude_unbins_from_postbinning`, `bin_domain_classification`, `ancient_dna`,
`skip_ancient_damagecorrection`, `skip_quast`, `skip_prodigal`, `skip_prokka`,
`skip_binqc`, `skip_gtdbtk`, `cat_classify_unbinned`, `run_virus_identification`,
`generate_bigmag_file`.

String/enum selectors (restrictions from schema enums):
`clip_tool` `[trimmomatic, adapterremoval, fastp]`; `longread_adaptertrimming_tool`
`[porechop_abi, porechop, none]`; `longread_filtering_tool` `[chopper, filtlong,
nanoq, none]`; `binning_map_mode` `[own, group, all]`; `postbinning_input`
`[raw_bins_only, raw_bins_and_unbinned, refined_bins_only]`.

Numbers: `min_length_unbinned_contigs` (int), `max_unbinned_contigs` (int),
`refine_bins_dastool_threshold` (float), `gtdbtk_min_completeness` (float),
`gtdbtk_max_contamination` (float). `multiqc_title` (string, optional).

Confidence: High for schema-backed enums/booleans (nf-schema + conditional guards
agree); Medium where default interacts with a branch (e.g. `skip_spadeshybrid` also
implies `single_end`).

## Excluded params (consolidated warning + assessment)

| class | params | assessment |
|---|---|---|
| output location/publishing | `outdir`, `keep_phix`, `keep_lambda` | **promoted**: branch presence of the bundled-DB inputs now gates removal; flags redundant (safe) |
| publication-only save flags | `save_filtered_longreads` (+ other `save_*`) | safe — Galaxy output exposure is design choice, not flag; note: Galaxy may publish filtered reads always or never, fixed default = don't publish |
| notification/CLI plumbing | `email`, `plaintext_email`, `validate_params`, `help`, `version`, `monochrome_logs` | safe (runtime UX) |
| site/profile config | `config_profile_*`, `pipelines_testdata_base_path`, `custom_config_version`, `igenomes_base`, `igenomes_ignore` | safe (site config) |
| reference resolution magic | `host_genome`, `genomes` map, `checkm_download_url`, `checkm2_db_version`, `gunc_database_type`, `cat_db_generate`, `metaeuk_mmseqs_db` (name form) | **problematic→handled**: recorded in reference brief + ledger (`host-genome-key-not-carried`, `cat-db-generate-chain-not-carried`, `db-download-fallbacks-not-carried`, `metaeuk-remote-db-name-gap`) — user uploads datasets instead |
| merged into input-presence | `run_busco`, `run_checkm`, `run_checkm2`, `run_gunc` | **promoted** per reference decision; residual loss: cannot supply a DB yet keep branch off (ledger) |
| resource/cpU pins | `*_fix_cpus`, `*_fix_cpu_1`, process resource caps | safe (Galaxy schedules resources) |

## Workflow outputs (promoted)

| output | source publish evidence | Galaxy format | shape | role |
|---|---|---|---|---|
| `multiqc_report` | `multiqc/multiqc_report.html` | html | file | user report; smoke-checkable |
| `bin_summary` | `GenomeBinning/bin_summary.tsv` | tabular | file | **checkpoint**: stable tabular per-bin table — the content-checkpoint equivalent of the nf-test content/tsv-rows snapshots (completeness/contamination/taxonomy/size per bin) |
| `software_versions` | `pipeline_info/nf_core_mag_software_mqc_versions.yml` | (omit; yml not registry-backed) | file | **checkpoint**: version yml, matches the versions snapshot after nextflow-version stripping |
| `bins` | `GenomeBinning/**/fasta/*.fa.gz` (per coassembly group) | fasta.gz | `list:list` (group → bins) | primary product |
| `unbinned_contigs` | `GenomeBinning/**/unbinned/*.fa.gz` | fasta.gz | list | split-fasta output |
| `assemblies` | `Assembly/**` (`*.fa.gz` per assembler) | fasta.gz | list:list (sample → assembler) | pre-binning product |
| `quast_assembly_summary` | QUAST `*_report.tsv`/summary | tabular | list | assembly QC checkpoint |
| `taxonomy_tables` | `Taxonomy/**/*_summary.tsv` (gtdbtk/cat) | tabular | list | taxonomy checkpoint (bin_summary already merges them) |

Element identifiers must carry group/sample labels through the map-overs (testability:
addressable members; identifiers from the samplesheet `sample`/`group` values).

## Labels

`mag`, `metagenome-assembled-genomes`, `metagenomics`, `assembly`, `binning`,
`taxonomy`, `annotation`, `multiqc`.

## Open questions

1. `sample_sheet:record` nullability for rows missing one modality (ledger
   `mixed-modality-samplesheet-record-slots`); fallback split-sheet design defined.
2. Conditional requiredness (`input` ⟺ `input_mode==reads`) expressed only by
   convention + help text (ledger `either-input-required-unexpressible`).
3. `anyOf`/`dependentRequired` nf-schema rules → prose (recorded validation loss).
4. DB-presence gating cannot express "supplied but disabled" (ledger
   `run-flags-merged-into-db-presence`).
