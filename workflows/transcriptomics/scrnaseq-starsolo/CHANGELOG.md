# Changelog

## [0.1] - 2026-11-11

### Added
- Initial release of the single-cell RNA-seq FASTQ to Gene Expression Matrix workflow.
- Translation of the `nf-core/scrnaseq` pipeline (v4.2.0, `aligner: star`).
- Creator attribution: `nf-core` (<https://nf-co.re/scrnaseq>), Rand Zoabi (<rand.zoabi@rz.uni-freiburg.de>), and `Intergalactic Workflow Commission` (<https://github.com/galaxyproject/iwc>).
- Demultiplexing, alignment, and knee filtering using `rna_starsolo` (`2.7.11b+galaxy3`).
- MultiQC quality metric aggregation (`multiqc` `1.35+galaxy4`).
- Non-overlapping layered layout (`COL_STRIDE: 220`, `ROW_STRIDE: 100`).
- Validated on [usegalaxy.org](https://usegalaxy.org) with 10-sample benchmark showing 100% numerical concordance against `nf-core/scrnaseq`.
