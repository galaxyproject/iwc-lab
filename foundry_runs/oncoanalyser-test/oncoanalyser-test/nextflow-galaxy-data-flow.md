# Galaxy data-flow brief — nf-core/oncoanalyser 3.0.0 (WGTS core DNA spine)

Inputs: `summary-nextflow.json` (workflow `WGTS`), `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`, `open-requirements.ledger.yml`. Scope is fixed by ledger decision `core-dna-spine-scope`.

This is an abstract DAG: no gxformat2, no Tool Shed resolution. "Tool need" says what a step must *do*. Phase 7 decides what exists.

## 1. Shape summary

- One subject per invocation (`one-subject-parallel-tumor-normal-inputs`). The only collections are the two lane-level `list:paired` read inputs and the per-lane BAM lists that alignment maps out. Everything after REDUX is a single dataset per role.
- **Tumor and normal run as twin branches** for alignment and REDUX. The source handles them in one channel, branched by `fastq_info.sample_type` (`READ_ALIGNMENT_DNA` `.branch { runnable: sample_type == 'tumor' … }`). Galaxy keeps them as two parallel chains because each needs its own sample-name parameter (`tumor_sample_id` / `normal_sample_id`) and downstream steps take tumor and normal in distinct, named slots. Confidence: high.
- **Directory currency.** The source passes whole tool output directories between stages (`topic: amber_dir`, `cobalt_dir`, `esvee_dir`, `redux_dir`, `purple_dir`). Galaxy carries each as one archive dataset (`tar`, fallback `data`), per ledger `hmftools-directory-outputs-as-archives`. Single VCFs that the source re-wraps as directories (PAVE outputs into PURPLE) travel as plain `vcf_bgzip` datasets. The consuming step rebuilds the directory layout it needs.
- **HMF bundle.** `hmf_pipeline_resources` fans into every hmftools step as one archive. Each step needs the members listed in its row (§3), at the `hmf_data_paths['38']` relative paths (decision `hmf-resources-as-single-archive-input`).

## 2. Abstract DAG

```
tumor_dna_reads (list:paired) ──► [A1 align_tumor_lanes] ─list:bam─► [R1 redux_tumor] ─┬─ tumor_redux_bam
normal_dna_reads (list:paired) ─► [A2 align_normal_lanes] ─list:bam─► [R2 redux_normal] ┼─ normal_redux_bam
                                                                                        └─ {tumor,normal}_redux_dir
reference_genome ─► [P1 build_fai?] ─► fai*        [P2 build_dict?] ─► dict*
tumor/normal BAM ─► [C1 amber] ─ amber_dir ─┐
tumor/normal BAM ─► [C2 cobalt] ─ cobalt_dir ┤
tumor/normal BAM + img ─► [S1 esvee] ─ esvee_dir ┤
tumor/normal BAM + redux_dirs ─► [V1 sage_somatic] ─► [V3 pave_somatic] ─ pave_somatic_vcf ┤
tumor/normal BAM + redux_dirs ─► [V2 sage_germline] ─► [V4 pave_germline] ─ pave_germline_vcf ┤
                                                                         [K1 purple] ◄────┘
                                                                            │ purple_dir, purple_sv_germline_vcf
                                                    [L1 linx_somatic] ◄──────┤
                                                    [L2 linx_germline] ◄─────┘
```

## 3. Nodes

| id | Source (summary) | Abstract operation | Inputs → outputs (shape) | Galaxy idiom | Confidence |
|---|---|---|---|---|---|
| P1 `build_fai` | `reference_rebuilds[ref_data_genome_fai]` → `SAMTOOLS_FAIDX` | index FASTA | `reference_genome` → `fai`; runs only when `reference_genome_fai` is null | step `when:` on the optional input, then **pick_value** (first non-null of supplied and built) → `genome_fai` | medium (conditional pattern; see §5) |
| P2 `build_dict` | `reference_rebuilds[ref_data_genome_dict]` → `SAMTOOLS_DICT` | sequence dictionary from FASTA | `reference_genome` → dict; when `reference_genome_dict` is null | `when:` + pick_value → `genome_dict` | medium |
| A1 `align_tumor_lanes` | `READ_ALIGNMENT_DNA` → `BWAMEM2_ALIGN` (`bwa-mem2 mem -Y -K 100000000 -R <rg>` → `sambamba sort`) | paired-end short-read alignment, coordinate-sorted BAM, read group per lane | `tumor_dna_reads` `list:paired` → `list` of `bam`, identifiers preserved (`library_1_001`) | **map-over** lane elements | high |
| A2 `align_normal_lanes` | same | same | `normal_dna_reads` → `list` of `bam` | map-over | high |
| R1 `redux_tumor` | `REDUX_PROCESSING` → `REDUX` (`tuple val(meta), path(alns), path(idxs)`, multi-BAM) | merge lane BAMs, mark duplicates, unmap problem regions, compute MS jitter/BQR tables | `list` of `bam` (**reduction**: one job consuming the whole list) + fasta, fai, dict, bundle[`common/unmap_regions.38.tsv`, `dna/variants/msi_jitter_sites.38.tsv.gz`], `genome_version`, `sequencing_platform`, `tumor_sample_id` → `tumor_redux_bam` (`bam`), `tumor_redux_dir` (archive of `redux_<id>/` tsvs), `tumor_redux_duplicate_freq` (`tabular`) | reduce list → dataset (`multiple: true` input) | high |
| R2 `redux_normal` | same | same | normal side → `normal_redux_bam`, `normal_redux_dir` | reduce | high |
| C1 `amber` | `AMBER_PROFILING` → `AMBER` | B-allele frequency at het sites | tumor+normal redux BAM, fasta, fai, bundle[`dna/copy_number/AmberGermlineSites.38.tsv.gz`], version, platform, ids → `amber_dir`, `amber_qc` (`<tumor>.amber.qc`) | plain step | high |
| C2 `cobalt` | `COBALT_PROFILING` → `COBALT` | GC-normalised read-depth ratios | tumor+normal BAM, fasta, fai, bundle[`dna/copy_number/GC_profile.1000bp.38.cnp`, `DiploidRegions.38.bed.gz`], ids → `cobalt_dir` | plain step | high |
| S1 `esvee` | `ESVEE_CALLING` → `ESVEE` (prep → assemble → depth → call) | structural-variant calling | tumor+normal BAM, fasta, fai, dict, `reference_genome_bwa_img`, bundle[`dna/sv/sgl_pon.38.bed.gz`, `sv_pon.38.bedpe.gz` (platform-selected), `known_fusions.38.bedpe`, `repeat_mask_data.38.fa.gz`, `common/unmap_regions.38.tsv`], version, platform, ids → `esvee_dir`, `esvee_somatic_vcf` | plain step (four ESVEE sub-commands in one source process, kept as one step) | high |
| V1 `sage_somatic` | `SAGE_CALLING` → `SAGE_SOMATIC` (`… path(redux_tsvs)`) | somatic SNV/MNV/indel calling | tumor+normal BAM, tumor+normal `redux_dir` (jitter/ms tsvs), fasta, fai, dict, bundle[`hmf_wgs_sage_pon_1000.38.tsv.gz` (platform-selected), `KnownHotspots.somatic.38.vcf.gz`, highconf bed, `DriverGenePanel` (or `driver_gene_panel` input), `common/ensembl_data/`, `dna/variants/gnomad/`], version, platform → `sage_somatic_vcf` (`vcf_bgzip` + tbi) | plain step | high |
| V2 `sage_germline` | `SAGE_CALLING` → `SAGE_GERMLINE` | germline calling at panel/hotspot regions | tumor+normal BAM, `redux_dir`s, bundle[`KnownHotspots.germline.38.vcf.gz`, highconf, driver panel, ensembl] → `sage_germline_vcf` | plain step | high |
| V3 `pave_somatic` | `PAVE_ANNOTATION` → `PAVE_SOMATIC` | annotate somatic variants (gene impact, PON, mappability, ClinVar, gnomAD) | `sage_somatic_vcf`, fasta, fai, bundle[sage PON, `clinvar.38.vcf.gz`, `mappability_150.38.bed.gz`, driver panel, ensembl, gnomad], version, platform → `pave_somatic_vcf` | plain step | high |
| V4 `pave_germline` | `PAVE_ANNOTATION` → `PAVE_GERMLINE` | annotate germline variants (blocklists, ClinVar) | `sage_germline_vcf`, bundle[`KnownBlacklist.germline.38.bed`/`.vcf.gz`, clinvar, mappability, driver panel, ensembl] → `pave_germline_vcf` | plain step | high |
| K1 `purple` | `PURPLE_CALLING` → `PURPLE` (`path(amber_dir), path(cobalt_dir), path(esvee_dir), path(pave_somatic_dir), path(pave_germline_dir), path(redux_tumor_tsvs)`; WGTS passes `[]` for redux) | purity/ploidy fit, copy number, SV/SNV finalisation, driver catalogue | **fan-in** of `amber_dir`, `cobalt_dir`, `esvee_dir`, `pave_somatic_vcf`, `pave_germline_vcf` + fasta, fai, dict, bundle[`GC_profile`, hotspots somatic+germline, driver panel, ensembl, `cohort_germline_amp_del_freq.38.csv`], version, optional `purple_{min,max}_{purity,ploidy}` → `purple_dir` plus named `purple_purity`, `purple_qc`, `purple_somatic_vcf`, `purple_germline_vcf`, `purple_sv_vcf`, `purple_cnv_somatic`, `purple_driver_catalog_somatic`, internal `purple_sv_germline_vcf` | multi-input fan-in step (distinct named slots, not a collection) | high |
| L1 `linx_somatic` | `LINX_ANNOTATION` → `LINX_SOMATIC` (`tuple val(meta), path(purple_dir)`) | SV clustering, fusions, drivers | `purple_dir`, version, bundle[ensembl, `known_fusion_data.38.csv`, driver panel], `tumor_sample_id` → `linx_somatic_dir`, `linx_driver_catalog`, `linx_fusions`, `linx_svs` | plain step | high |
| L2 `linx_germline` | `LINX_ANNOTATION` → `LINX_GERMLINE` (input `purple_dir.resolve("<tumor>.purple.sv.germline.vcf.gz")`) | germline SV disruption annotation | `purple_sv_germline_vcf`, version, bundle[ensembl, driver panel] → `linx_germline_driver_catalog` | plain step. The source runs it only when tumor+normal exist and the germline SV VCF exists; always true here (matched pair) | medium (must tolerate an empty germline SV VCF) |

Step granularity follows the source process boundaries: one Galaxy step per kept nf-core process, with somatic/germline SAGE, PAVE and LINX as separate processes as in the source. Subworkflow wrappers (`*_PROFILING`, `*_CALLING`) hold only channel plumbing (`Utils.selectCurrentOrExisting`, branch on existing inputs), so they collapse.

## 4. Edges and identifier handling

| Edge | Shape before → after | Notes | Confidence |
|---|---|---|---|
| `tumor_dna_reads` → A1 | `list:paired` → map over `paired` | element identifier = lane key `<library_id>_<lane>`; unique per lane within a sample. The source keys lanes by `sample_id.library_id.lane[.flowcell]` (`rg_id`), and flowcell is part of the key when present | high |
| A1 → R1 | `list` of `bam` → reduced into one `multiple: true` BAM input | REDUX merges lanes (source `path(alns)` is a list). Order-independent | high |
| R1/R2 BAM → C1, C2, S1, V1, V2 | `bam` (+bai via Galaxy metadata) | tumor slot and normal slot named explicitly; never zipped | high |
| R1/R2 `redux_dir` → V1, V2 | archive | SAGE needs the REDUX jitter/ms tsvs (`path(redux_tsvs)`) | high |
| C1, C2, S1, V3, V4 → K1 | 3 archives + 2 VCFs → one step | fan-in by named slot | high |
| K1 `purple_dir` → L1; K1 `purple_sv_germline_vcf` → L2 | archive / vcf_bgzip | — | high |
| `hmf_pipeline_resources` → every hmftools step | archive | member extraction per §3 | medium (ledger `hmf-bundle-member-extraction-unverified`) |
| P1/P2 → all fai/dict consumers | pick_value result | — | medium |

**Read-group / sample naming.** The source sets `@RG ID:<sample_id>.<library_id>.<lane> SM:<sample_id> LB:<library_id>`, and hmftools match `-tumor`/`-reference` names against BAM `SM`. Galaxy A1/A2 must set `SM = tumor_sample_id` / `normal_sample_id` and `ID = <sample_id>.<element_identifier>`. The RG `ID` then uses `library_1_001` where the source has `library_1.001`. That difference is header-only and doesn't affect hmftools results. Confidence: medium; recorded in the ledger.

**Output naming.** hmftools name outputs `<sample_id>.<tool>.<…>`, so named-file extraction from each step's directory keys on `tumor_sample_id` / `normal_sample_id`.

## 5. Conditionals disposition

| Source guard (`workflow.conditionals[]`) | Disposition |
|---|---|
| `run_config.stages.{alignment,redux,amber,cobalt,esvee,sage,pave,purple,linx}` | **always on**: the spine fixes them true. No Galaxy `when:` |
| `run_config.stages.*` for every dropped stage | not built (ledger `*-not-built` drops) |
| `params.fastp_umi_enabled ∥ fastq_tools_umi_enabled` | always off (ledger `umi-processing-not-carried`) |
| `max_fastq_records > 0` → `FASTP_SPLIT` | default `-1` (no split, `nextflow.config` line 25). Not built; Galaxy maps over lanes instead |
| `prep_config.require_fai && !params.ref_data_genome_fai` (and dict) | Galaxy step `when:` on the null optional input + `pick_value`. Only two conditional steps, under the mapping note's "DAG explodes" concern. Fallback if `when:` is unsupported on the target: make fai/dict required inputs |
| bwa-mem2 / STAR / GRIDSS / img rebuilds | bwa-mem2 is in-tool (wrapper builds from history FASTA); STAR/GRIDSS are out of scope; img is a required input (no builder) |
| `run_mode == …` dispatch | fixed `wgts` |

## 6. Unresolved tool needs (for phase 7 routing)

| Node | Needs a tool that… | I/O shape |
|---|---|---|
| P1 | indexes a FASTA (`.fai`) | fasta → fai |
| P2 | writes a sequence dictionary for a FASTA | fasta → dict |
| A1/A2 | aligns paired FASTQ with bwa-mem2 (`-Y`, custom `-R` read group, coordinate-sorted BAM output), indexing the history FASTA when no index is supplied | paired fastqsanger.gz + fasta → bam |
| R1/R2 | runs hmftools REDUX 2.0.5 on ≥1 BAMs | bam (multiple) + refs + bundle → bam, archive, tabular |
| C1 | runs hmftools AMBER 4.3 (tumor+reference) | 2 bam + refs + bundle → archive, txt |
| C2 | runs hmftools COBALT 3.0 | 2 bam + refs + bundle → archive |
| S1 | runs hmftools ESVEE 2.0.1 (prep/assemble/depth-annotate/call) | 2 bam + refs + img + bundle → archive, vcf_bgzip |
| V1/V2 | runs hmftools SAGE 5.0.2 somatic / germline | 2 bam + 2 archives + refs + bundle → vcf_bgzip |
| V3/V4 | runs hmftools PAVE 1.9 somatic / germline | vcf_bgzip + refs + bundle → vcf_bgzip |
| K1 | runs hmftools PURPLE 4.4 from AMBER/COBALT/ESVEE/PAVE outputs | 3 archives + 2 vcf + refs + bundle + floats → archive + 7 named files |
| L1/L2 | runs hmftools LINX 2.3.1 somatic / germline | archive or vcf_bgzip + bundle → archive + tabular |

Versions come from `summary.tools[]` (bioconda `hmftools-*`, biocontainers images listed there).

## 7. Placeholder transformations

- **Archive ↔ directory** at every hmftools boundary (pack on output, unpack on input). This lives inside each step, not as separate collection operations (ledger `hmftools-directory-outputs-as-archives`).
- **Named-file extraction** from each step's directory into the public outputs in the interface brief. Also inside each step (extra declared outputs), with no separate extract steps.
- **No Apply Rules / collection cleanup is needed.** Collections exist only at the lane level and are reduced by REDUX.

## 8. Handoff notes

- Template: 16 tool steps (P1, P2, A1, A2, R1, R2, C1, C2, S1, V1, V2, V3, V4, K1, L1, L2) plus one `pick_value` each for fai and dict. Inputs and outputs exactly as labelled in the interface brief, plus internal `purple_sv_germline_vcf`.
- Exemplar comparison: look for IWC somatic-variant workflows (tumor/normal parallel inputs, bwa-mem2 map-over then merge) to check the twin-branch and reduction shape.
- Per-step: hmftools take `-ref_genome_version`, `-tumor`, `-reference`, and resource paths as CLI flags. The source `script_excerpt` in `summary-nextflow.json` `processes[]` holds the exact argument sets.
