# Pairwise MAF Split and Regroup for Multiz Roast (WF-I Split)

This workflow is Part 1 of the three-stage WF-I multiple alignment and UCSC `bigMaf` hub track pipeline (`wfi-split` → `multiz-roast` → `wfi-track`).

For each species' pairwise MAF alignment, it prefixes target and query rows with species names (`maf_name_rows`), splits the MAF along a reference BED cut list (`ucsc_mafsplit_bed`), and transposes the resulting `species:piece` collection into `piece:species` via Galaxy's native `__APPLY_RULES__` tool so `multiz-roast` can process each genomic piece independently.

## Inputs

- **Pairwise synNet MAFs** (`list` collection of `maf`): Unprefixed pairwise MAF alignments (`axtToMaf` output), keyed by panel label.
- **Species name tables** (`list` collection of `tabular`): Parallel list collection (matching element identifiers) where each dataset contains one `label<TAB>species` row.
- **Sequence rename map** (`tabular`): Three-column TSV (`genome`, `hub_name`, `original_name`) mapping raw assembly sequence names to UCSC hub-safe names.
- **Reference chromosome sizes** (`tabular`): Reference `chrom.sizes` (`chrom<TAB>length`).
- **Cut intervals BED** (`bed`): One `chrom<TAB>pos<TAB>pos+1` cut per line defining reference chromosome piece boundaries.
- **Reference species name** (`string`): Reference species prefix for row 1 of every MAF block.

## Outputs

- **Regrouped MAF pieces** (`list:list` collection of `maf`, `piece:species`): Durable partitioned pairwise MAFs ready for `multiz-roast`.
