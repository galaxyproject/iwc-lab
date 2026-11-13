# Changelog

All notable changes to this workflow will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1] - 2026-11-10

### Added
- Initial translation of the core `nf-core/sarek` germline variant calling workflow to Galaxy `gxformat2` and native `.ga`.
- Quality control step using FastQC (version 0.72+galaxy1).
- Short-read alignment using BWA-MEM (version 0.7.17.1).
- Duplicate marking using Picard MarkDuplicates (version 2.18.2.2).
- Germline variant calling using Strelka Germline (version 2.9.10+galaxy0).
- QC report aggregation using MultiQC (version 1.9+galaxy1).
- Workflow tests defined in `galaxy-workflow.gxwf-tests.yml` with remote test fixtures from `nf-core/test-datasets`.
- Remote testing validation on `usegalaxy.org` with Planemo test framework.
- Auto-layout non-overlapping 2D coordinates for all inputs and tool steps.
- IWC metadata compliance including creators (nf-core, IWC, Rand Zoabi), license, annotations, and Dockstore configuration.
