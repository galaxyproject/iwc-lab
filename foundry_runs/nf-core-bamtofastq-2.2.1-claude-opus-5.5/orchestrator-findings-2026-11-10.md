# Orchestrator findings — nf-core-bamtofastq-claude (2026-11-10)

Observed by the orchestrating session when importing `galaxy-workflow.gxwf.yml` (unchanged) into Galaxy.
These are observations, not instructions: decide what to change, if anything, using the Foundry skills.

## 1. "Issues loading this workflow" (Galaxy's editor shows these on open)

Galaxy reports these parameters as missing from the step's `state` and substitutes a default.
"a value set at runtime" means an unconnected optional dataset input; that is standard Galaxy state (87 of 133 IWC workflows have it), not a defect by itself.

- step `chr_extract` (tool `samtools_view`):
  - `mode|filter_config|cigarcons`: No value found for 'Filter by number of CIGAR bases consuming query sequence'.
  - `mode|filter_config|library`: No value found for 'Filter by library'.
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: a value set at runtime.
  - `mode|filter_config|quality`: No value found for 'Filter by quality'.
  - `mode|filter_config|tag`: No value found for 'Filter by tag'.
  - `mode|output_options|adv_output|collapsecigar`: No value found for 'Collapse backward CIGAR operation'. Using default: 'False'.
  - `mode|subsample_config|subsampling_mode|seed`: No value found for 'Seed for random number generator'.
- step `fastqc_pre` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: a value set at runtime.
  - `contaminants`: No value found for 'Contaminant list'. Using default: a value set at runtime.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: a value set at runtime.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.
- step `stats` (tool `samtools_stats`):
  - `cov_threshold`: No value found for 'Only bases with coverage above this value will be included in the target percentage computation'.
  - `gc_depth`: No value found for 'Size of GC-depth bins'.
  - `insert_size`: No value found for 'Maximum insert size'.
  - `most_inserts`: No value found for 'Report only the main part of inserts'.
  - `read_group`: No value found for 'Limit to a specific read group name'.
  - `read_length`: No value found for 'Minimum read length to generate statistics for'.
  - `remove_overlaps`: No value found for 'Remove overlaps of paired-end reads from coverage and base count computations'. Using default: 'False'.
  - `sparse`: No value found for 'Suppress absence of insertions'. Using default: 'False'.
  - `trim_quality`: No value found for 'BWA trim parameter'.
- step `view_map_map` (tool `samtools_view`):
  - `mode|filter_config|cigarcons`: No value found for 'Filter by number of CIGAR bases consuming query sequence'.
  - `mode|filter_config|library`: No value found for 'Filter by library'.
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: a value set at runtime.
  - `mode|filter_config|quality`: No value found for 'Filter by quality'.
  - `mode|filter_config|tag`: No value found for 'Filter by tag'.
  - `mode|output_options|adv_output|collapsecigar`: No value found for 'Collapse backward CIGAR operation'. Using default: 'False'.
  - `mode|subsample_config|subsampling_mode|seed`: No value found for 'Seed for random number generator'.
- step `view_unmap_unmap` (tool `samtools_view`):
  - `mode|filter_config|cigarcons`: No value found for 'Filter by number of CIGAR bases consuming query sequence'.
  - `mode|filter_config|library`: No value found for 'Filter by library'.
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: a value set at runtime.
  - `mode|filter_config|quality`: No value found for 'Filter by quality'.
  - `mode|filter_config|tag`: No value found for 'Filter by tag'.
  - `mode|output_options|adv_output|collapsecigar`: No value found for 'Collapse backward CIGAR operation'. Using default: 'False'.
  - `mode|subsample_config|subsampling_mode|seed`: No value found for 'Seed for random number generator'.
- step `view_unmap_map` (tool `samtools_view`):
  - `mode|filter_config|cigarcons`: No value found for 'Filter by number of CIGAR bases consuming query sequence'.
  - `mode|filter_config|library`: No value found for 'Filter by library'.
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: a value set at runtime.
  - `mode|filter_config|quality`: No value found for 'Filter by quality'.
  - `mode|filter_config|tag`: No value found for 'Filter by tag'.
  - `mode|output_options|adv_output|collapsecigar`: No value found for 'Collapse backward CIGAR operation'. Using default: 'False'.
  - `mode|subsample_config|subsampling_mode|seed`: No value found for 'Seed for random number generator'.
- step `view_map_unmap` (tool `samtools_view`):
  - `mode|filter_config|cigarcons`: No value found for 'Filter by number of CIGAR bases consuming query sequence'.
  - `mode|filter_config|library`: No value found for 'Filter by library'.
  - `mode|filter_config|qname_file`: No value found for 'Filter by readnames'. Using default: a value set at runtime.
  - `mode|filter_config|quality`: No value found for 'Filter by quality'.
  - `mode|filter_config|tag`: No value found for 'Filter by tag'.
  - `mode|output_options|adv_output|collapsecigar`: No value found for 'Collapse backward CIGAR operation'. Using default: 'False'.
  - `mode|subsample_config|subsampling_mode|seed`: No value found for 'Seed for random number generator'.
- step `fastqc_post_single` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: a value set at runtime.
  - `contaminants`: No value found for 'Contaminant list'. Using default: a value set at runtime.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: a value set at runtime.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.
- step `merge_unmapped` (tool `samtools_merge`):
  - `bed_file`: No value found for 'Merge only reads overlapping the specified regions in the BED file'. Using default: a value set at runtime.
  - `headerbam`: No value found for 'File to take @headers from'. Using default: a value set at runtime.
  - `region`: No value found for 'Merge files in a region'.
- step `fastqc_post_paired` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: a value set at runtime.
  - `contaminants`: No value found for 'Contaminant list'. Using default: a value set at runtime.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: a value set at runtime.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.

## 2. Frames

- No frames in this workflow; Foundry's template marks them optional.
