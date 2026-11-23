# Reference-Guided Multiple Genome Alignment (multiz roast)

This workflow runs `multiz roast` (`autoMZ`) once per genomic piece over a nested `piece:species` collection of pairwise MAF alignments, emitting one reference-guided multiple-alignment MAF per piece.

It is Part 2 of the three-stage WF-I multiple alignment pipeline (`wfi-split` → `multiz-roast` → `wfi-track`). Splitting across independent genomic pieces allows individual pieces to be retried without re-running the entire genome.

## Inputs

- **Pairwise MAF pieces** (`list:list` collection of `maf`): Nested collection (`outer = piece`, `inner = species`) of species-prefixed pairwise MAF alignments, typically emitted by `wfi-split`.
- **Species guide tree** (`newick`): Rooted Newick guide tree whose leaves match the species names in the pairwise MAF rows (including the reference species).
- **Reference species name** (`string`): Reference species prefix (e.g. `hg38`) matching a leaf in the guide tree.

## Outputs

- **Multiple alignment pieces** (`list` collection of `maf`): One reference-guided multiple-alignment MAF per genomic piece, ready to pass to `wfi-track` for per-sequence concatenation and UCSC `bigMaf` track construction.

## Related Workflows

- **Upstream (`wfi-split`)**: Names pairwise MAF rows, splits each species MAF at a reference BED cut list, and transposes `species:piece` into `piece:species`.
- **Downstream (`wfi-track`)**: Regroups pieces by reference sequence, concatenates in coordinate order, restores hub species names, and builds a UCSC `bigMaf` BigBed track.
- **Reference-free alternative (`multiz-tba`)**: Use `multiz-tba` when aligning all `N*(N-1)` ordered pairs without a single reference coordinate system.
