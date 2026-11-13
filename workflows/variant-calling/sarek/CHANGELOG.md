# Changelog

## [0.1.0] - 2026-11-11

### Added
- Initial release of the comprehensive Galaxy port of nf-core/sarek (v3.11.0).
- Modular workflow architecture comprising 6 functional subworkflows:
  - `sarek-preprocessing`: FASTQ quality trimming (fastp), alignment (BWA-MEM2), duplicate marking (Picard MarkDuplicates), and base recalibration (GATK BaseRecalibrator, ApplyBQSR).
  - `sarek-germline-suite`: Strelka germline calling, GATK HaplotypeCaller, FreeBayes, and BCFtools norm.
  - `sarek-somatic-suite`: Somatic and tumor-only variant calling using GATK Mutect2, Strelka Somatic, and LoFreq.
  - `sarek-structural-suite`: Structural variant calling with Manta and BCFtools view filtering.
  - `sarek-annotation-suite`: Functional annotation with SnpEff and provenance tag injection.
  - `sarek-qc-reporting`: MultiQC aggregation of alignment, duplicate, and coverage statistics.
- End-to-end master orchestrator workflow: `sarek-master` (.ga and .gxwf.yml).
- Unprivileged User-Defined Tools (UDTs) for Sarek custom operations:
  - `add_info_to_vcf`: Injects caller metadata and provenance INFO tags into VCF headers and records.
  - `consensus_from_sites`: Merges and indexes multi-caller variant sites.
- Automated test definitions (`sarek-master.gxwf-tests.yml`) backed by official nf-core remote fixtures.
- Creator attribution: nf-core, Rand Zoabi, and Intergalactic Workflow Commission (IWC).
