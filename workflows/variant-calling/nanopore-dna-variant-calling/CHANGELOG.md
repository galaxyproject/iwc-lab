# Changelog

## [0.1] - 2026-11-10

First release. Covers the DNA variant-calling path of nf-core/nanoseq 3.1.0:
- read QC with NanoPlot and FastQC;
- minimap2 alignment and samtools statistics;
- diploid small-variant calling with Clair3, replacing nanoseq's medaka;
- structural-variant calling with Sniffles2;
- a bigWig coverage track;
- a MultiQC report.
