# Reference data brief — nf-core/atacseq 2.1.2 → Galaxy

Produced by `nextflow-summary-to-galaxy-reference-data` from `summary-nextflow.json`.
Galaxy target: test.galaxyproject.org (datatypes checked 2026-11-12 via `GET /api/datatypes`).

## Evidence note

`summary-nextflow.json` carries **no `reference_assets[]` and no `reference_rebuilds[]`** (the
summarizer emitted neither for this pipeline). The classification below uses `params[]`
(`source_kind: getGenomeAttribute` on 11 params, `schema_group: Reference genome options`) plus the
`PREPARE_GENOME` subworkflow body in `subworkflows/local/prepare_genome.nf`, read directly because
the summary did not carry the rebuild branches. Every rebuild claimed below is cited to that file.

## Classification

| Classification | Applies | Evidence |
|---|---|---|
| Key-expanded bundle (iGenomes) | yes | `main.nf` L20–31: `params.fasta/bwa_index/bowtie2_index/chromap_index/star_index/gtf/gff/gene_bed/tss_bed/blacklist/mito_name = WorkflowMain.getGenomeAttribute(params, …)`; `macs_gsize = WorkflowMain.getMacsGsize(params)` keyed by `genome` + `read_length` |
| Coordinated bundle | yes | FASTA + GTF (or GFF) + optional blacklist travel together; switching genome switches all |
| Compute-if-missing | yes (positive/negated mix) | aligner index, gene BED, TSS BED, macs_gsize, GTF-from-GFF (see table) — rebuild-unverified by the summary, verified by source read |
| Always-derived (not a param) | yes | fai + chrom sizes (`CUSTOM_GETCHROMSIZES`), autosomes (`GET_AUTOSOMES`), include-regions BED (`GENOME_BLACKLIST_REGIONS`) |
| Single asset / multi-DB / cohort | no | — |

The test profile supplies only `fasta` + `gtf` (+ `mito_name: MT`, `read_length: 50`); every other
asset is rebuilt. Test genome is small (yeast, `nf-core/test-datasets` atacseq branch).

## Per-asset decisions

Galaxy posture: explicit workflow inputs, no data tables, no `genome` key. Derived assets become
workflow-tier steps when no Galaxy wrapper rebuilds them internally.

| NF param / asset | NF behaviour | Galaxy shape | Format | Required | Notes |
|---|---|---|---|---|---|
| `fasta` | required; gunzip if `.gz` | workflow input `genome_fasta` | `fasta` | **yes** | `fasta` auto-decompresses gz uploads; no GUNZIP step |
| `gtf` | required unless `gff`; gunzip if `.gz` | workflow input `genome_gtf` | `gtf` | **yes** | consumed by GTF2BED, HOMER annotatePeaks, featureCounts (via SAF/consensus), STAR (not carried) |
| `gff` | alternative to GTF → `GFFREAD` | **not exposed** (v1) | — | — | `kind: dropped` in ledger; either-or input needs a conditional |
| `blacklist` | optional BED; gunzip if `.gz` | optional input `blacklist_bed` | `bed` | no | feeds include-regions BED; absent → only mito removal |
| `gene_bed` | optional; else `GTF2BED(gtf)` | **derived step** from `genome_gtf` | `bed` | — | override input not exposed (ledger `dropped`); NF also rebuilds when `--gtf` overrides an iGenomes gene BED |
| `tss_bed` | optional; else `TSS_EXTRACT(gene_bed)` | **derived step** from gene BED | `bed` | — | override input not exposed (same ledger entry) |
| fai / chrom sizes | always `CUSTOM_GETCHROMSIZES(fasta)` | derived step (samtools faidx → cut cols 1–2) | `fai`, `len`/`tabular` | — | single build, fans out to filter / bigWig / IGV / picard |
| autosomes | always `GET_AUTOSOMES(fai)` | derived step (text filter over fai) | `txt` | — | used only by ataqv |
| include-regions BED | always `GENOME_BLACKLIST_REGIONS(sizes, blacklist, mito_name, keep_mito)` | derived step (bedtools complement/subtract over sizes) | `bed` | — | drives BAMTOOLS filter `-L` region restriction |
| `bwa_index` | optional (`.tar.gz` untar); else `BWA_INDEX(fasta)` | **in-tool rebuild**: `devteam/bwa/bwa_mem` "use a genome from history" | — | — | test.galaxyproject.org has `bwa_mem/0.7.19+galaxy2`; uploaded pre-built index is not consumable by that wrapper outside data tables → param `kind: dropped` |
| `bowtie2_index` / `chromap_index` / `star_index` | per `aligner`; else build | follow interface aligner scope | — | — | default aligner is `bwa`; non-default aligners are an interface scope decision. Bowtie2 wrapper also builds in-tool from history FASTA |
| `macs_gsize` | iGenomes lookup by `genome`+`read_length`, else `KHMER_UNIQUEKMERS(fasta, read_length)` | integer workflow parameter `macs_gsize` | `integer` | **yes** (v1) | no khmer unique-kmers wrapper confirmed; test value must be computed or chosen → ledger gap |
| `read_length` | used only to compute/lookup macs_gsize | not exposed once `macs_gsize` is a direct parameter | — | — | |
| `mito_name` | string (iGenomes attr; test `MT`) | text parameter `mito_name` | `text` | no | used by blacklist filter and ataqv mito reference |
| `keep_mito` | boolean | boolean parameter | — | no | default false |
| `ataqv_mito_reference` | string, defaults to `mito_name` | not exposed (uses `mito_name`) | — | — | |
| `genome`, `igenomes_base`, `igenomes_ignore`, `save_reference` | iGenomes plumbing | **not exposed** | — | — | Galaxy surface starts at resolved per-asset paths |

### Rebuild cost

BWA in-tool indexing runs once per alignment job. The test sheet has 8 runs (4 PE, 4 SE), so the
yeast index is built 8 times — above the ~3× workflow-tier threshold, but Galaxy on the target
has no standalone BWA index tool whose output `bwa_mem` accepts (index building is a data
manager). Accepted for test scale; flagged for real genomes.

### Non-genome pipeline assets

`bamtools_filter_pe_config` / `bamtools_filter_se_config` (`assets/bamtools_filter_*.json`) and
the MultiQC header files are pipeline-bundled config, not reference data. Interface/data-flow
decide whether they become inputs or inline tool parameters.

## Open questions (carried in ledger)

1. `macs_gsize` test value — no khmer wrapper; compute from the test FASTA (unique 50-mers) at test-data time or use a documented approximation.
2. GFF-only inputs unsupported in v1.
3. BWA index rebuild per job is acceptable only at small genome scale.
