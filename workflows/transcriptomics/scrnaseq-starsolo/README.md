# Single-Cell RNA-Seq Fastq to Gene Matrix (STARsolo and MultiQC)

This workflow performs end-to-end single-cell RNA-seq alignment, demultiplexing, barcode error correction, and gene-level quantification using **STARsolo**, followed by interactive quality report aggregation using **MultiQC**.

## Provenance & Attribution

- **Original Pipeline**: Translated from the **[nf-core/scrnaseq](https://nf-co.re/scrnaseq)** pipeline (v4.2.0 / `aligner: star`).
  - nf-core citation: Ewels, P. A., et al. (2020). *The nf-core framework for community-curated bioinformatics pipelines.* Nature Biotechnology, 38(3), 276-278. [doi:10.1038/s41587-020-0439-x](https://doi.org/10.1038/s41587-020-0439-x).
  - Pipeline DOI: [10.5281/zenodo.3568187](https://doi.org/10.5281/zenodo.3568187).
- **Creators**:
  - **[nf-core](https://nf-co.re/scrnaseq)** (Original pipeline authors)
  - **Rand Zoabi** (<rand.zoabi@rz.uni-freiburg.de>)
  - **[Intergalactic Workflow Commission](https://github.com/galaxyproject/iwc)** (Galaxy workflow maturation and packaging)
- **License**: MIT

## Inputs

1. **Paired-end single-cell RNA-seq reads** (`list:paired` collection of `fastqsanger.gz`):
   - **Forward read (Read 1)**: Cell barcode and Unique Molecular Identifier (UMI) sequences.
   - **Reverse read (Read 2)**: cDNA sequence reads.
2. **Reference genome FASTA** (`fasta`):
   - Genomic reference FASTA file used for STAR index generation and mapping.
3. **Reference gene annotation GTF** (`gtf`):
   - Transcript and gene annotations matching the reference genome.
4. **Cell barcode whitelist** (`txt`, optional):
   - Whitelist of known barcode sequences corresponding to the single-cell library chemistry (e.g., 10x Genomics 737K-august-2016 for V2 chemistry).

## Parameters & Processing Details

- **Single-cell Chemistry**: Default configured for 10x Genomics Single Cell 3' v2 (16 bp cell barcode, 10 bp UMI).
- **Cell Calling & Filtering**: Integrated STARsolo CellRanger 2.2 knee-filtering algorithm (`--soloCellFilter CellRanger2.2 5000 0.99 10`) producing both raw (unfiltered) and filtered gene expression matrices.
- **UMI Deduplication**: Directional/1MM_CR matching Cell Ranger specifications.

## Outputs

1. **Raw Gene Expression Matrix** (`matrixmarket`): Complete UMI count sparse matrix across all detected barcodes.
2. **Cell Barcodes** (`tsv`): Barcode list corresponding to matrix columns.
3. **Gene Features** (`tsv`): Gene identifiers and symbols corresponding to matrix rows.
4. **Filtered Gene Expression Matrix** (`matrixmarket`): Filtered sparse matrix containing only high-confidence cell barcodes.
5. **Filtered Cell Barcodes** (`tsv`): Filtered list of genuine cell barcodes.
6. **Filtered Gene Features** (`tsv`): Gene metadata for filtered matrix.
7. **STARsolo Summary** (`txt` / `tsv`): Comprehensive barcode, feature, and mapping statistics.
8. **MultiQC Quality Report** (`html`): Interactive HTML report aggregating STAR mapping statistics and gene count distributions.

## Relations to Existing IWC Workflows

This workflow provides a direct, drop-in Galaxy implementation of `nf-core/scrnaseq`, leveraging STARsolo's native cell calling to output Cell Ranger-compatible 10x matrices and MultiQC dashboards without requiring separate downstream DropletUtils runs.
