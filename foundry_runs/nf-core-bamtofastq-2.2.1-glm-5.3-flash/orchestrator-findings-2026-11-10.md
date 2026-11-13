# Orchestrator findings — nf-core-bamtofastq-glm (2026-11-10)

Observed by the orchestrating session when importing `galaxy-workflow.gxwf.yml` (unchanged) into Galaxy.
These are observations, not instructions: decide what to change, if anything, using the Foundry skills.

## 1. "Issues loading this workflow" (Galaxy's editor shows these on open)

Galaxy reports these parameters as missing from the step's `state` and substitutes a default.
`RuntimeValue` means Galaxy turned an unconnected optional dataset input into a value asked for at run time.

- step `samtools_chr_view` (tool `samtools_view`):
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: 'RuntimeValue'.
- step `fastqc_pre_conversion` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: 'RuntimeValue'.
  - `contaminants`: No value found for 'Contaminant list'. Using default: 'RuntimeValue'.
  - `kmers`: No value found for 'Length of Kmer to look for'. Using default: '7'.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: 'RuntimeValue'.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.
  - `nogroup`: No value found for 'Disable grouping of bases for reads >50bp'. Using default: 'False'.
- step `pairedness_split` (tool `pairedness_split`):
  - `lines_to_check`: No value found for 'Number of alignment records to sample'. Using default: '1000'.
- step `multiqc` (tool `multiqc`):
  - `comment`: No value found for 'Custom comment'. Using default: ''.
  - `image_content_input`: No value found for 'Image content'. Using default: 'RuntimeValue'.
  - `title`: No value found for 'Report title'. Using default: ''.
- step `samtools_view_map_map` (tool `samtools_view`):
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: 'RuntimeValue'.
- step `samtools_view_unmap_unmap` (tool `samtools_view`):
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: 'RuntimeValue'.
- step `samtools_view_unmap_map` (tool `samtools_view`):
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: 'RuntimeValue'.
- step `samtools_view_map_unmap` (tool `samtools_view`):
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: 'RuntimeValue'.
- step `samtools_merge_unmapped` (tool `samtools_merge`):
  - `bed_file`: No value found for 'Merge only reads overlapping the specified regions in the BED file'. Using default: 'RuntimeValue'.
  - `headerbam`: No value found for 'File to take @headers from'. Using default: 'RuntimeValue'.
  - `region`: No value found for 'Merge files in a region'.
- step `fastqutils_info_paired` (tool `fastq_info`):
  - `q`: No value found for 'Determine quality scoring'. Using default: 'True'.
  - `r`: No value found for 'Skip check for duplicated readnames'. Using default: 'False'.
- step `fastqutils_info_single` (tool `fastq_info`):
  - `q`: No value found for 'Determine quality scoring'. Using default: 'True'.
  - `r`: No value found for 'Skip check for duplicated readnames'. Using default: 'False'.
- step `fastqc_post_conversion` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: 'RuntimeValue'.
  - `contaminants`: No value found for 'Contaminant list'. Using default: 'RuntimeValue'.
  - `kmers`: No value found for 'Length of Kmer to look for'. Using default: '7'.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: 'RuntimeValue'.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.
  - `nogroup`: No value found for 'Disable grouping of bases for reads >50bp'. Using default: 'False'.

## 2. Frames

- No frame problems found.
