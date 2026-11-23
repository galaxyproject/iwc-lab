# Reference-Free Multiple Genome Alignment (multiz TBA)

This workflow builds a reference-free multiple genome alignment (MAF) from a collection of species genome assemblies (FASTA), a collection of all ordered pairwise reciprocal-best MAF alignments, and a rooted Newick guide tree using `multiz tba`.

Element identifiers are extracted inside Galaxy using `collection_element_identifiers` so unprefixed FASTA headers and MAF `s`-lines are automatically prefixed with `<species>.` inside the `multiz_tba` job—avoiding any download, manual relabelling, or re-upload.

## Inputs

- **Species genome assemblies** (`list` collection of `fasta`): One genome assembly per species in the guide tree. Element identifiers name each species (or match column 1 of the optional identifier-to-species map).
- **Pairwise reciprocal-best MAFs** (`list` collection of `maf`): All `N*(N-1)` ordered pairwise MAF alignments (both `A.B` and `B.A` directions). Element identifiers encode the ordered pair (`sp1__sp2`, `sp1.sp2`, or `sp1_sp2`).
- **Species guide tree** (`newick`): Rooted Newick tree giving the progressive merge order. Branch lengths and internal node labels are stripped; leaf names must match `[A-Za-z][A-Za-z0-9_]*` and must not contain `maf` or `eof`.
- **Identifier to species map** (`tabular`, optional): Two-column TSV (`collection_id<TAB>tree_leaf_name`) translating raw collection identifiers (such as NCBI accessions containing dots like `GCA_032713075.1`) into TBA-safe leaf names.

## Outputs

- **Multiple genome alignment** (`maf`): Reference-free threaded blockset MAF produced by `multiz tba`.

## Notes and Limitations

- `tba` re-scores multi-way merges with its built-in `HOXD70` scoring matrix and assumes collinearity within alignment blocks.
- When aligning reference-anchored panels or very large numbers of genomes where all-vs-all `N*(N-1)` pairwise alignment is impractical, prefer the reference-guided `multiz-roast` workflow (`wfi-split` → `multiz-roast` → `wfi-track`).
