# Sarek Germline Variant Calling Galaxy Workflow

## Evidenced Purpose

This workflow performs quality control, short-read mapping with BWA-MEM, duplicate marking with Picard, and germline variant calling with Strelka to analyze genomic variation in paired-end sequencing data. It translates the core germline small-variant discovery path of the [nf-core/sarek](https://github.com/nf-core/sarek) analysis pipeline into a native, sample-agnostic Galaxy workflow.

## Valid Inputs

1. **Paired-end sequencing reads** (`reads`):
   - Type: `list:paired` collection of paired-end FASTQ datasets.
   - Formats: `fastqsanger.gz`, `fastqsanger`.
   - Description: Paired forward and reverse Illumina sequencing reads.

2. **Reference genome** (`reference_genome`):
   - Type: Data input.
   - Format: `fasta`.
   - Description: Reference genome assembly FASTA against which reads are aligned and variants are called.

## Expected Outputs

1. **FastQC quality report** (`FastQC quality report`):
   - Formats: HTML report and raw summary metrics per sample.
2. **Deduplicated aligned reads** (`Deduplicated aligned reads`):
   - Format: `bam`.
   - Description: Coordinate-sorted, deduplicated read alignments.
3. **Germline variants** (`Germline variants`):
   - Format: `vcf`.
   - Description: Small genomic variants (single nucleotide variants and indels) called by Strelka Germline.
4. **MultiQC report** (`MultiQC report`):
   - Format: `html`.
   - Description: Aggregated quality control report compiling statistics from FastQC and Picard MarkDuplicates.

## Pipeline Steps

1. **FastQC**: Evaluates sequencing read quality, base distribution, and duplication rates.
2. **BWA-MEM**: Maps paired-end sequencing reads against the reference FASTA genome.
3. **Picard MarkDuplicates**: Locates and tags duplicate reads in the aligned BAM file.
4. **Strelka Germline**: Detects germline single nucleotide variants and insertions/deletions.
5. **MultiQC**: Aggregates quality control metrics across all preprocessing stages into an interactive HTML summary.

## Creators & Attribution

- **Original Pipeline**: [nf-core/sarek](https://nf-co.re/sarek) by the [nf-core community](https://nf-co.re)
- **Workflow Creators**:
  - `nf-core` (Organization: https://nf-co.re)
  - `IWC` (Intergalactic Workflow Commission: https://github.com/iwc-workflows)
  - `Rand Zoabi` (<rand.zoabi@rz.uni-freiburg.de>)
- **License**: MIT


- **nf-core/sarek**: A comprehensive workflow offering extensive options across multiple mappers (BWA-MEM, BWA-MEM2, DragMap), callers (Strelka, GATK HaplotypeCaller, DeepVariant, FreeBayes, Mutect2, LoFreq), somatic analysis modes, and annotation engines (VEP, SnpEff).
- **Galaxy Sarek Germline Workflow**: A lean, standard-compliant, portable workflow tailored for standard germline variant calling with verified execution on public Galaxy servers (e.g., `usegalaxy.org`).
