# Nanopore DNA variant calling

This workflow calls small variants and structural variants from Oxford Nanopore DNA reads against a reference genome, with read-level and alignment-level QC. For each sample it maps reads with minimap2, calls diploid SNVs and indels with Clair3, calls structural variants with Sniffles2 and builds a bigWig coverage track. One MultiQC report covers all samples.

It is adapted from the DNA variant-calling path of [nf-core/nanoseq](https://github.com/nf-core/nanoseq) 3.1.0. Unlike nanoseq, it calls small variants with Clair3 rather than medaka (see [Why Clair3 instead of medaka](#why-clair3-instead-of-medaka)).

## Inputs

| Input | Type | Description |
|---|---|---|
| `Nanopore reads` | List collection of `fastqsanger.gz` | Basecalled ONT DNA reads from R9.4.1 flow cells, one gzipped FASTQ per sample. The element identifiers become the sample names in every per-sample output. |
| `Reference genome` | `fasta` | One reference genome FASTA shared by all samples. Its sequence names are carried into the BAM, VCF and bigWig outputs. |

The workflow has no runtime parameters. The tools run with these fixed settings:
- minimap2 uses the `map-ont` preset.
- Clair3 uses the built-in `r941_prom_hac_g360+g422` model and calls diploid genotypes over all contigs, without phasing or GVCF output.
- Sniffles2 runs with its defaults (minimum SV length 50 bp, minimum MAPQ 20).
- bedtools genomecov writes split-read coverage (`-split -bg`), which wigToBigWig turns into a bigWig file.

### Limitation: R9.4.1 data only

The Clair3 Galaxy wrapper offers only R9.4.1 ONT models, so results on R10.4.1 or newer chemistry will be unreliable. Supporting newer chemistry needs a newer Clair3 model in the wrapper. The workflow can't fix that on its own.

## Outputs

All per-sample outputs are list collections keyed by the input element identifiers.

| Output | Format | Content |
|---|---|---|
| `Sorted alignments` | `bam` | Coordinate-sorted minimap2 alignments (indexed by Galaxy) |
| `Alignment flagstat` | text | `samtools flagstat` report |
| `Alignment stats` | tabular | `samtools stats` report, computed with the reference |
| `Small variants` | `vcf_bgzip` | Clair3 SNVs and indels, diploid genotypes, `PASS`/`LowQual` filter |
| `Structural variants` | `vcf_bgzip` | Sniffles2 structural variants, bgzipped |
| `Coverage bigWig` | `bigwig` | Read coverage track for genome browsers |
| `NanoPlot reports` | `html` | NanoPlot read QC |
| `FastQC reports` | `html` | FastQC read QC |
| `MultiQC report` | `html` | One report across all samples, with FastQC and samtools stats, flagstat and idxstats sections |

## Relation to nf-core/nanoseq

The workflow follows the nanoseq 3.1.0 DNA path with demultiplexing skipped (profile `test_nodx_vc`). It leaves out these parts of nanoseq:
- barcode demultiplexing (qcat) and NanoLyse;
- all cDNA and direct-RNA analyses;
- the alternative variant callers;
- the per-read bigBed alignment track, because the sorted BAM already serves that purpose.

Tool versions are current Galaxy wrappers rather than nanoseq's pins. The changes that matter most are minimap2 2.17 → 2.31 and Sniffles 1.0.12 → 2.5.2.

### Why Clair3 instead of medaka

nanoseq calls small variants with medaka 1.4.4's diploid `medaka_variant` pipeline. That pipeline isn't usable in Galaxy:
- Current Galaxy medaka wrappers (2.1.1) make **haploid** calls. That design suits viral and bacterial genomes, not human samples.
- The legacy 1.4.4 diploid-pipeline wrapper fails on usegalaxy.org.

Clair3 is maintained and designed for diploid ONT calling. Upstream medaka itself recommends it.

| Call set (vs GIAB HG001, nanoseq test region) | SNV F1 | Indel F1 | Overall F1 |
|---|---|---|---|
| This workflow, Clair3 `PASS` | **0.95** | **0.56** | **0.90** |
| nf-core/nanoseq, medaka 1.4.4 `PASS` | 0.61 | 0.16 | 0.49 |
| Galaxy medaka 2.1.1 (haploid) | 0.72 | 0.12 | 0.50 |

On a larger 30x HG002 benchmark, Clair3 reaches SNV F1 0.997 and indel F1 0.70. See [Testing and validation](#testing-and-validation) for both runs.

## How this differs from related IWC workflows

The closest IWC workflow is [SARS-CoV-2 ONT ARTIC variant calling](https://github.com/galaxyproject/iwc/tree/main/workflows/sars-cov-2-variant-calling/sars-cov-2-ont-artic-variant-calling). It also maps ONT reads with minimap2, but it is built for SARS-CoV-2 ARTIC amplicon data and calls **haploid** variants with medaka.

Use this workflow for whole-genome or targeted ONT DNA from **diploid** organisms, such as human samples. It produces diploid small-variant genotypes, structural variants and coverage tracks, and it has no amplicon or primer handling.

## Testing and validation

### A. Bundled Planemo test

This is the test in `nanopore-dna-variant-calling.gxwf-tests.yml`, run by CI.

| Input | Location | SHA-1 | Notes |
|---|---|---|---|
| `Nanopore reads`, element `NA12878_R1` | https://raw.githubusercontent.com/nf-core/test-datasets/nanoseq/fastq/demultiplexed/NA12878_DNA.fastq.gz | `a4921703e623c048bb455cf8b2099730adc57b75` | 334 ONT reads, NA12878 |
| `Reference genome` | https://raw.githubusercontent.com/nf-core/test-datasets/nanoseq/reference/GRCh38_EDIL3.fa | `f5e587811949ab7b696430d3875915830108d20f` | Exact copy of GRCh38 chr5:83,940,555–84,384,880, sequence named `chr5` |

These are the nf-core/nanoseq 3.1.0 `test_nodx_vc` fixtures.

What was run on these inputs:
- **Planemo test:** the test file as submitted passed on usegalaxy.org (Galaxy 26.2rc1), invocation `4ae2da923366f120`. An earlier version of the workflow had also passed there (invocation `fbf1b200b6a8b01c`). The test checks:
  - read and mapping counts: 334 primary reads, 333 primary mapped (99.70%);
  - the structure of the VCF, BAM, bigWig and HTML outputs.
- **Comparison with nf-core/nanoseq 3.1.0:** nanoseq was run unmodified (`-profile test_nodx_vc,docker --skip_bigbed`, Nextflow 22.10.3) on the same inputs.
  - Alignment is equivalent: 333 of 334 primary reads mapped on both sides.
  - Both find the well-supported 348 bp deletion, with breakpoints 6 bp apart.
  - Sniffles2 additionally reports two insertions, one of which rests on a single read.
- **Accuracy against GIAB HG001 (NA12878) v4.2.1**, in high-confidence regions: 521 truth variants, matched by exact allele after `bcftools norm`.

| Call set | SNV F1 | Indel F1 | Overall F1 | Genotype correct (of true positives) |
|---|---|---|---|---|
| This workflow, Clair3 `PASS` | 0.95 | 0.56 | 0.90 | 439/443 |
| nf-core/nanoseq medaka 1.4.4 `PASS` | 0.61 | 0.16 | 0.49 | 347/374 |
| Galaxy medaka 2.1.1 (haploid) | 0.72 | 0.12 | 0.50 | 0/303 |

This fixture is small: one sample, about 12x coverage over 444 kb.

### B. Larger accuracy benchmark

This run is external evidence. CI doesn't run it.

| Input | Source | SHA-1 |
|---|---|---|
| `Nanopore reads`: `HG002_chr20_10M_30x.fastq.gz` (14,041 reads, 313 Mb, mean length 22 kb) | ONT open data `gm24385_2020.11` (HG002, R9.4.1, guppy 4.0.11 hac, PromethION), BAM [`calls2ref.bam`](https://ont-open-data.s3.amazonaws.com/gm24385_2020.11/analysis/r9.4.1/20201026_1644_2-E5-H5_PAG07162_d7f262d5/guppy_v4.0.11_r9.4.1_hac_prom/align_unfiltered/chr20/calls2ref.bam) | `00f204f8192d852477af37eb94e081f797021f35` |
| `Reference genome`: GRCh38 chr20:10,000,000–20,000,000, sequence named `chr20_10M_20M` | UCSC hg38 sequence API | `371e37de0d2136a49320604f0ee270fdea08318e` |
| Truth set (not a workflow input) | [GIAB HG002 v4.2.1 GRCh38](https://ftp-trace.ncbi.nlm.nih.gov/ReferenceSamples/giab/release/AshkenazimTrio/HG002_NA24385_son/NISTv4.2.1/GRCh38/) benchmark VCF and `noinconsistent` BED | |

The reads were derived with samtools 1.21:
1. `samtools view -b -F 0x904 -q 1 <bam> chr20:10000000-20000000` extracted the region at 67x coverage.
2. `samtools view -s 42.45` downsampled it to 30.0x.
3. `samtools fastq` wrote the reads file.

chr20 is held out of Clair3's training. The workflow ran on usegalaxy.org (invocation `2fff7c5c42acbf11`), and all 13 jobs finished ok. A rerun with the final tool state, launched through the API without tool-state corrections (invocation `5d0f5d607a6ecc43`), produced byte-identical small-variant records. Calls were scored with RTG `vcfeval` 3.13 (genotype-aware, `PASS` calls) on the 15,372 truth variants in the high-confidence regions, which cover 98% of the slice.

| Class | Precision | Recall | F1 |
|---|---|---|---|
| SNV | 0.9987 | 0.9959 | 0.9973 |
| Indel | 0.8087 | 0.6217 | 0.7030 |
| All | 0.9784 | 0.9456 | 0.9617 |

Indels are the known weak point of R9.4.1 data, and most errors are homopolymer lengths.

### C. Earlier runs during the translation

<details>
<summary>History</summary>

- **Local Planemo on arm64 macOS:** NanoPlot failed when its amd64 container ran under emulation. This is an environment-only limitation, and NanoPlot passes on usegalaxy.org.
- **medaka 2.1.1 version:** the Planemo test passed on usegalaxy.org (invocation `3bc6626d240d663e`), but every genotype was haploid. That led to the comparison above.
- **Legacy medaka 1.4.4 diploid-pipeline wrapper:** failed on usegalaxy.org (invocation `cf5318de2072ffe4`). The wrapper indexes the reference in place on read-only storage, and `| tee` hides the error. This failure is why the workflow switched to Clair3.

</details>

## Notes for reviewers

- The test inputs are GitHub raw URLs from nf-core/test-datasets rather than Zenodo records. The reads file is larger than 100 KB.
- The workflow keeps Galaxy's own export encoding: `null` for unconnected optional data inputs in FastQC and MultiQC. `gxwf validate` reports these as tool-state errors, which is a known validator false positive.
