# Four-Masker Genome Soft-Masking and Repeat Track Generation

This workflow produces uniformly soft-masked genome assemblies and UCSC-ready BED6 repeat tracks for comparative genomics and whole-genome alignment.

Every input assembly is first uppercased (`fasta_uppercase`) so pre-existing masking does not bias comparisons across assemblies from different sources. Four complementary repeat and low-complexity finders then run in parallel:

- **NCBI DustMasker** (symmetric DUST low-complexity regions)
- **NCBI WindowMasker** (`mkcounts` + `ustat` genome-frequency repeats, with internal DUST disabled)
- **tantan** (probabilistic simple-repeat finder)
- **FasTAN** (tandem-repeat arrays, natively BED6)

Low-complexity intervals from DustMasker, WindowMasker, and tantan are annotated by repeat unit and purity with `lc_classify` (BED6). The union of all four interval sets is sorted, merged, soft-masked onto the uppercased assembly (`bedtools maskfasta -soft`), indexed (`samtools faidx`), and summarized per masker and union in a coverage table and MultiQC report.

## Inputs

- **Genome assemblies** (`list` collection of `fasta`): Input genome assemblies; element identifiers carry through every output collection and the coverage summary table.

## Outputs

- **Soft-masked assemblies** (`list` of `fasta`): Soft-masked genomes ready for pairwise alignment (`growler-ucsc-pair` / `growler-ucsc-panel`).
- **FASTA indexes** (`list` of `fai`) and **Chromosome sizes** (`list` of `tabular`): Indexes and two-column `chrom.sizes` tables.
- **DustMasker / WindowMasker / Tantan / FasTAN BED6 tracks** (`list` of `bed`/`bed6`): Per-masker repeat tracks suitable for UCSC assembly hubs.
- **Masking coverage table** (`tabular`) and **Masking MultiQC report** (`html`): Per-assembly percent-masked proportions across all four maskers and their union.
