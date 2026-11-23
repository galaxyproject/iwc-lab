# Multiz Roast Pieces to UCSC bigMaf Track (WF-I Track)

This workflow is Part 3 of the three-stage WF-I multiple alignment and UCSC hub track pipeline (`wfi-split` → `multiz-roast` → `wfi-track`).

It regroups piece-wise `multiz-roast` MAF outputs (`<sequence>.<NN>`) by reference sequence, concatenates each sequence's pieces in coordinate order (`maf_concat`), restores hub species names from roast-safe aliases (`maf_name_rows`), converts each sequence MAF to `bigMaf` text (`ucsc_maftobigmaf`), concatenates the text across sequences, and compiles a single UCSC `bigMaf` BigBed track (`ucsc_bedtobigbed`).

## Inputs

- **Roasted alignment pieces** (`list` collection of `maf`): Per-piece multiple-alignment MAFs from `multiz-roast`, with element identifiers matching `<sequence>.<NN>`.
- **Reference species name** (`string`): Reference species prefix in the MAF rows.
- **Species alias rename map** (`tabular`): Headered two-column TSV (`from<TAB>to`) translating roast-safe species aliases back to hub display names.
- **Reference chromosome sizes** (`tabular`): Reference `chrom.sizes` (`chrom<TAB>length`).
- **bigMaf autoSql schema** (`txt`): UCSC `bigMaf.as` autoSql definition.

## Outputs

- **Per-sequence multiple alignments** (`list` collection of `maf`): One coordinate-ordered MAF per reference sequence.
- **UCSC bigMaf track** (`bigbed`): Whole-genome `bed3+1` `bigMaf` BigBed track ready for a UCSC assembly hub.
