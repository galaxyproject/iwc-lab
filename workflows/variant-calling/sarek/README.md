# nf-core/sarek Galaxy Workflow Suite (IWC-Ready)

This directory contains the complete modular Galaxy workflow suite ported from **nf-core/sarek** (v3.11.0).
The suite faithfully maps the 128 modules and 76 subworkflows of Sarek into idiomatic Galaxy workflows and unprivileged User-Defined Tools (UDTs).

## Architecture

The suite consists of a master orchestrator workflow and 6 specialized subworkflows:

1. **`sarek-master`** (`.ga` / `.gxwf.yml`):
   End-to-end genomic variant calling pipeline connecting raw FASTQ reads directly to aligned BAMs, calibrated variants, annotations, and aggregate MultiQC reports.
2. **`sarek-preprocessing`**:
   Read quality filtering and adapter trimming (`fastp`), reference genome alignment (`bwa_mem2`), duplicate marking (`picard_MarkDuplicates`), base quality score recalibration (`gatk4_base_recalibrator`, `gatk4_apply_bqsr`), and depth coverage calculation (`samtools_stats`, `mosdepth`).
3. **`sarek-germline-suite`**:
   Germline short variant calling using `strelka_germline`, `gatk4_haplotype_caller`, and `freebayes`, followed by `bcftools_norm` normalization.
4. **`sarek-somatic-suite`**:
   Somatic and tumor-only variant calling using `gatk4_mutect2`, `strelka_somatic`, and `lofreq_call`.
5. **`sarek-structural-suite`**:
   Structural variant and CNV calling using `manta` and candidate inspection via `bcftools_view`.
6. **`sarek-annotation-suite`**:
   Functional variant effect prediction via `snpeff` and caller tag enrichment via `add_info_to_vcf`.
7. **`sarek-qc-reporting`**:
   Aggregate MultiQC report generation over alignment, duplicate, and coverage metrics.

## Custom Tools (UDTs)

Custom formatting and provenance scripts from Sarek that do not have standalone Tool Shed equivalents are wrapped as Galaxy User-Defined Tools (`class: GalaxyUserTool`) in `local_udts/`:
- `add_info_to_vcf`: Inserts custom caller and tool tags into VCF records (`biocontainers/gawk:5.3.0`).
- `consensus_from_sites`: Merges and indexes multi-caller variant sites (`biocontainers/bcftools:1.20`).

## Inputs

- **`reads_paired`**: Paired-end sequencing reads in FASTQ format (`fastqsanger.gz`).
- **`reference_fasta`**: Reference genome FASTA sequence.
- **`known_sites`**: VCF of known polymorphic sites (dbSNP or 1000 Genomes indels) for base recalibration.
- **`germline_resource`** *(optional)*: Population germline allele frequencies (gnomAD) for somatic filtering.
- **`target_intervals`** *(optional)*: Exome or targeted sequencing capture regions in BED format.

## Outputs

- **`recalibrated_bam`**: Recalibrated and duplicate-marked BAM alignment.
- **`strelka_vcf`**: Strelka germline variant calls.
- **`haplotypecaller_vcf`**: GATK HaplotypeCaller variant calls.
- **`freebayes_vcf`**: FreeBayes variant calls.
- **`mutect2_vcf`**: GATK Mutect2 somatic variant calls.
- **`manta_sv_vcf`**: Manta structural variant calls.
- **`annotated_vcf`**: Fully annotated VCF with predicted consequences and caller provenance.
- **`multiqc_report`**: Interactive HTML summary report aggregating metrics across all pipeline stages.

## Testing

Automated tests are declared in `sarek-master.gxwf-tests.yml` utilizing standard test fixtures from `nf-core/test-datasets`:
```bash
planemo test --galaxy_url http://localhost:8088 --galaxy_user_key fakekey sarek-master.ga
```
