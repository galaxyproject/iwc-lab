# Orchestrator findings — nf-core-bamtofastq-deepseek (2026-11-10)

Observed by the orchestrating session when importing `galaxy-workflow.gxwf.yml` (unchanged) into Galaxy.
These are observations, not instructions: decide what to change, if anything, using the Foundry skills.

## 1. "Issues loading this workflow" (Galaxy's editor shows these on open)

Galaxy reports these parameters as missing from the step's `state` and substitutes a default.
`RuntimeValue` means Galaxy turned an unconnected optional dataset input into a value asked for at run time.

- step `fastx_single` (tool `samtools_fastx`):
  - `copy_arb_tags`: No value found for 'copy arbitrary tags to the FASTA header line'.
  - `exclusive_filter`: No value found for 'Exclude reads with any of the following flags set'. Using default: '['256', '2048']'.
  - `exclusive_filter_all`: No value found for 'Exclude reads with all of the following flags set'.
  - `inclusive_filter`: No value found for 'Require that these flags are set'.
- step `post_fastqc` (tool `fastqc`):
  - `adapters`: No value found for 'Adapter list'. Using default: 'RuntimeValue'.
  - `contaminants`: No value found for 'Contaminant list'. Using default: 'RuntimeValue'.
  - `limits`: No value found for 'Submodule and Limit specifing file'. Using default: 'RuntimeValue'.
  - `min_length`: No value found for 'Lower limit on the length of the sequence to be shown in the report'.
- step `multiqc` (tool `multiqc`):
  - `comment`: No value found for 'Custom comment'. Using default: ''.
  - `image_content_input`: No value found for 'Image content'. Using default: 'RuntimeValue'.

## 2. Frames

- frame `stage-input` ("Inputs and contig selection") has an empty `contains_steps`, so Galaxy draws it as an empty box.
- frame `stage-qc-stats` ("Pre-conversion QC and stats") has an empty `contains_steps`, so Galaxy draws it as an empty box.
