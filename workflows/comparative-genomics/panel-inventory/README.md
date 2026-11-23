# Comparative Panel Inventory and Completeness QC

This workflow profiles a multi-genome comparative panel before launching expensive whole-genome alignments, combining k-mer similarity screening, annotation completeness QC, and panel bookkeeping:

- **Assembly similarity (`sourmash`)**: Sketches every assembly (`sourmash_sketch`) and computes both an `N x N` Jaccard similarity matrix and a size-robust symmetric `--max-containment` matrix (`sourmash_compare`).
- **Annotation completeness (`BUSCO` + `MultiQC`)**: Runs `BUSCO -m prot` on available annotated proteomes (which may be a subset of the assemblies) and aggregates summaries in MultiQC.
- **Alignment bookkeeping**: Builds `samtools faidx` indexes, two-column `chrom.sizes` tables (`Cut1`), and an ordered list of panel member identifiers (`collection_element_identifiers`).

## Inputs

- **Genome assemblies** (`list` of `fasta`): Panel assemblies keyed by member name.
- **Annotated proteomes** (`list` of `fasta`): Protein FASTAs (one protein per gene) for annotated members of the panel.
- **BUSCO lineage** (`string`): Cached BUSCO lineage dataset name available on the target Galaxy instance (e.g. `apicomplexa_odb12`, `saccharomycetes_odb10`, `eukaryota_odb10`).

## Outputs

- **Sourmash signatures**, **Jaccard similarity matrix CSV**, **Jaccard similarity labels**, and **Max-containment similarity matrix CSV**
- **BUSCO summaries** and **BUSCO MultiQC report**
- **FASTA indexes**, **Chromosome sizes**, and **Panel member identifiers**

## Notes

- BUSCO requires a cached `busco_database` data table on the target Galaxy instance matching the chosen **BUSCO lineage**.
- Additional BRC helper tools for all-vs-all self-pair diagonal filtering (`collection_self_pairs`), strict ordered-pair relabelling (`collection_relabel_map`), and TOGA2 anchor preparation (`anchor_prep`) are submitted separately to `galaxyproject/tools-iwc-lab`.
