# Reference data brief — nf-core/oncoanalyser 3.0.0 → Galaxy

Source: `summary-nextflow.json` (`reference_assets[]` 13 entries, `reference_rebuilds[]` 6 entries, `params[]`), primary workflow **WGTS**. Galaxy target: test.galaxyproject.org. Posture: v1 (explicit optional inputs, in-tool rebuild, no data tables).

## 1. Classification (Nextflow side)

| Classification | Applies? | Evidence |
|---|---|---|
| None | no | — |
| Reference-producing | only in `mode=prepare_reference` (out of WGTS scope) | `PREPARE_REFERENCE` workflow, `WRITE_REFERENCE_DATA` aliases |
| Single asset | no | — |
| **Key-expanded bundle** | **yes** | `params.genome = 'GRCh38_hmf'` → 7 `getGenomeAttribute()` params (`ref_data_genome_fasta/fai/dict/img/bwamem2_index/gridss_index/star_index`) from `conf/hmf_genomes.config`; only `GRCh37_hmf` / `GRCh38_hmf` keys are supported (`force_genome` to bypass) |
| **Compute-if-missing** | **yes** | 6 `reference_rebuilds[]` (`SAMTOOLS_FAIDX`, `SAMTOOLS_DICT`, `GATK4_BWA_INDEX_IMAGE`, `BWAMEM2_INDEX`, `GRIDSS_INDEX`, `STAR_GENOMEGENERATE`), each guarded by `prep_config.require_<x> && !params.ref_data_genome_<x>`. Index params may also be `.tar.gz` (decompressed by `CUSTOM_EXTRACTTARBALL`) |
| **Coordinated bundle (directory)** | **yes** | `ref_data_hmf_data_path` → one HMF resource directory/tarball (`hmf_pipeline_resources.38_v3.0.0--8.tar.gz`); ~55 members resolved through `params.hmf_data_paths['38']` relative paths, including subdirectories (`common/ensembl_data/`, `misc/lilac/`, `misc/neo/binding/`, `misc/virusbreakend/`, `dna/variants/gnomad/`) |
| Multi-DB pick-list | partial | panel-of-normals chosen per `params.sequencing_platform` (illumina / sbx / ultima) by `Utils.getSequencingPlatformPons` — selects among files *inside* the HMF bundle, not separate user DBs |
| **Parallel bundles plus cohort data** | **yes** | cohort data that can't be rebuilt, all inside the HMF bundle: SAGE/ESVEE PONs, gnomAD, ClinVar, Isofox cohort distributions, Neo TPM medians, Qsee cohort percentiles, CUPPA classifier, germline amp/del frequencies |

Measured sizes (HTTP `content-length`, 2026-11-11): FASTA 3.25 GB, HMF bundle 5.91 GB, bwa-mem2 index tar 8.91 GB, GRIDSS index tar 7.71 GB, STAR index tar 27.4 GB, BWA image 5.63 GB. **About 59 GB in total.** The source nf-test (`profile_test.nf.test`) uses these full-size references; there is no test-scale reference bundle.

## 2. Per-asset Galaxy shape

### Genome bundle (key-expanded → per-asset inputs)

The `genome` key is **not carried** as a selector (no data table, per v1). The workflow surface starts at the resolved assets.

| NF param | Galaxy input | `format` | Optional | Rebuild-on-absence (Galaxy) | Consumers (WGTS) |
|---|---|---|---|---|---|
| `ref_data_genome_fasta` | `reference_genome` | `fasta` | **required** | — | alignment, REDUX, AMBER, COBALT, ESVEE, SAGE, PAVE, PURPLE, LILAC, CIDER, CHORD, VIRUSBreakend, Isofox |
| `ref_data_genome_fai` | `reference_genome_fai` | `fai` | optional | in-tool (`samtools faidx`) — every hmftools step needs it, so a **workflow-tier `samtools faidx` step** fed to all consumers is cheaper than per-tool rebuild (>3 consumers rule) | same as FASTA |
| `ref_data_genome_dict` | `reference_genome_dict` | `data` (no `picard_dict` guaranteed; verify on target) | optional | workflow-tier `samtools dict` / Picard CreateSequenceDictionary step (>3 consumers) | REDUX, ESVEE, SAGE, PURPLE, CHORD, CIDER, VIRUSBreakend |
| `ref_data_genome_img` | `reference_genome_bwa_img` | `data` | optional | workflow-tier GATK `BwaMemIndexImageCreator` (no Galaxy wrapper known; rebuild-unverified) | ESVEE, CIDER |
| `ref_data_genome_bwamem2_index` | `bwamem2_index` | `bwa_mem2_index` (directory) or none | optional | **in-tool**: the Galaxy bwa-mem2 wrapper builds an index from a history FASTA. Run once per lane chunk → heavy for a 3.2 GB genome (≈64 GB RAM); prefer a server-cached index on large instances (v2) | READ_ALIGNMENT_DNA |
| `ref_data_genome_star_index` | `star_index` | none (STAR wrapper builds from history FASTA + GTF) | optional | **in-tool** STAR genomeGenerate (needs GTF `ref_data_genome_gtf`; ≈32 GB RAM) | READ_ALIGNMENT_RNA |
| `ref_data_genome_gridss_index` | `gridss_index` | `data` (tar.gz) | optional | rebuild-unverified (no GRIDSS index wrapper known) | VIRUSBREAKEND_CALLING |
| `ref_data_genome_gtf` | `reference_gtf` | `gtf` | optional (needed only to build a STAR index) | — | STAR_GENOMEGENERATE |
| `genome_version` (derived 37/38) | workflow parameter `genome_version` | text, restricted `38` / `37` | required, default `38` | — | almost every hmftools step (`-ref_genome_version`) |

### HMF resource bundle (coordinated directory bundle → one archive input)

Exposing ~55 HMF files as separate inputs is impractical, and several members are directories. **Decision: a single workflow input `hmf_pipeline_resources`** holding the HMF tarball, passed whole to each hmftools step. Each step's wrapper extracts the members it needs using the same relative paths as `conf/hmf_data.config` `hmf_data_paths['38']`.

- `format`: `tar` if the target registers it (with `.tar.gz` upload), otherwise `data`. Unverified on test.galaxyproject.org; see the ledger.
- Required for WGTS.
- No rebuild: this is cohort/curated data.
- Consumers: AMBER (heterozygous_sites), COBALT (gc_profile, diploid_bed), REDUX (unmap_regions, msi_jitter_sites), ESVEE (PON, known_fusions, repeatmasker, unmap_regions), SAGE (hotspots, highconf, PON, mappability, ensembl, gnomad), PAVE (blocklists, clinvar, PON, mappability, ensembl, gnomad), PURPLE (gc_profile, hotspots, ensembl, germline_amp_del_freq), LINX (ensembl, known_fusion_data), Isofox (ensembl, known_fusion_data, cohort distributions), LILAC (lilac resources), Neo (neo binding, tpm medians), CUPPA (classifier, alt_sj), SIGS (signatures), PEACH (haplotypes, functions, drugs), Qsee (cohort percentiles), VIRUSBreakend/Virus Interpreter (virusbreakend_db and the three virus TSVs), ORANGE (doid.json), bam-tools/Qsee (driver panel, ensembl).
- The sequencing-platform PON pick (`sage_pon_<platform>`, `esvee_pon_*_<platform>`) becomes per-step wrapper logic driven by a workflow parameter `sequencing_platform` (restricted `illumina` / `sbx` / `ultima`, default `illumina`). It is not a separate input.

### Individually overridable bundle members (optional explicit inputs)

The WGTS body lets four bundle members be replaced by a user file (`params.X != null ? file(params.X) : hmf_data.X`). These are exposed as optional `data` inputs. When unset, the step reads the bundle member.

| NF param | Galaxy input | `format` | Default when unset |
|---|---|---|---|
| `driver_gene_panel` | `driver_gene_panel` | `tabular` | `common/DriverGenePanel.38.tsv` from bundle |
| `gridss_config` | `gridss_config` | `txt` | `dna/sv/gridss.properties` |
| `isofox_counts` | `isofox_counts` | `csv` | `rna/read_151_exp_counts.38.csv` |
| `isofox_gc_ratios` | `isofox_gc_ratios` | `csv` | `rna/read_100_exp_gc_ratios.38.csv` |

Optional data inputs whose default is "a member of another input" can't be expressed in gxformat2. Each consuming step needs a `when`/conditional or wrapper-level fallback. Recorded in the ledger.

### Not carried

- `genome`, `force_genome`, `ref_data_base`, `ref_data_genomes_base`, `igenomes_base`, `igenomes_ignore`, `genome_type`, `ref_data_types`, `prepare_reference_only`: remote-location and key-resolution plumbing. They don't apply when the user uploads per-asset inputs.
- `ref_data_panel_data_path`, `target_regions_bed`, `isofox_tpm_norm`, `isofox_gene_ids`: TARGETED / panel-resource-creation modes only.
- `PREPARE_REFERENCE` staging (`CUSTOM_EXTRACTTARBALL` for index tarballs, `WRITE_REFERENCE_DATA`): Galaxy inputs arrive already materialized. Archive inputs are extracted inside the consuming wrapper.

## 3. Open questions / risks for downstream phases

1. **Test-scale reference data does not exist.** The selected nf-test needs about 59 GB of references. Uploading that to test.galaxyproject.org is impractical, and the in-tool bwa-mem2/STAR rebuilds need ≥32–64 GB RAM. Phase 8 must find or build a reduced reference set (e.g. a chromosome subset plus a matching HMF subset), or phases 12–13 can't run on the target.
2. **hmftools wrappers are unverified.** The archive-input decision assumes wrappers (Tool Shed or user-defined) that accept the bundle and extract members. Phase 7 discovery decides whether any hmftools wrapper exists. If wrappers instead take individual files, the bundle needs an "extract member" step per file (e.g. an archive-extract tool), and the input surface changes.
3. **The `tar` / `bwa_mem2_index` / sequence-dictionary datatypes are unverified on test.galaxyproject.org.** Fall back to `data` with descriptions.
4. **The GRIDSS index and BWA image have no known Galaxy builder.** Treat them as required uploads if the steps that use them (VIRUSBreakend, ESVEE, CIDER) are kept.
5. **`dbkey`.** Set `hg38` on inputs if the user uploads with a dbkey. The data-flow brief must not strip it across map-overs.
