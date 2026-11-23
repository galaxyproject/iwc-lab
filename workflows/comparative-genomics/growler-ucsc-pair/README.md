# Pairwise Whole-Genome Alignment with KegAlign and UCSC Chain/Net (Growler Pair)

This workflow aligns a pair of soft-masked genome assemblies (`Target genome FASTA` × `Query genome FASTA`) using GPU-accelerated `KegAlign` seeding, mapped `growler_lastz_lav` gapped extension, and UCSC kent `doBlastzChainNet.pl` + `doRecipBest.pl` chaining and netting steps.

It produces both **syntenic-net MAF** (recommended for closely related genomes feeding `wfi-split` / `multiz-roast`) and **reciprocal-best MAF** (recommended for reference-free `multiz-tba` across divergent species), alongside liftOver chains (`over.chain`), reciprocal-best chains/nets, and all-chains.

## Inputs

- **Target genome FASTA** / **Query genome FASTA** (`fasta`): Soft-masked genome assemblies (e.g. from `genome-softmasking`).
- **Target chromosome sizes** / **Query chromosome sizes** (`tabular`): Two-column `chrom.sizes` files (`chrom<TAB>length`).
- **LASTZ scoring matrix** (`tabular`): LASTZ scoring matrix (e.g. `HOXD70`, `HoxD55`, or clade-specific matrix).
- **axtChain linear gap table** (`tabular`): UCSC `medium.lineargap` or `loose.lineargap` gap-cost file.
- **Alignment parameters**: UCSC/LASTZ defaults for `K` (`hspthresh`), `L` (`gappedthresh`), `X` (`xdrop`), `Y` (`ydrop`), `H` (`inner`), `M` (`masking`), `T=2` (`notransition`), entropy filtering, `chain_min_score`, `batch_lines`, and `num_gpu`.

## Outputs

- **All chains** (`chain`)
- **Syntenic net** (`net`), **LiftOver chain** (`chain`), **Filtered syntenic net** (`net`), and **Syntenic net MAF** (`maf`)
- **Reciprocal-best chain** (`chain`), **Reciprocal-best net** (`net`), and **Reciprocal-best MAF** (`maf`)

## Hardware / CI Requirement

- The `kegalign` seeding step requires a **CUDA GPU** runner. On CPU-only CI runners (such as default GitHub Actions `ubuntu-latest`), `planemo test` cannot execute `kegalign`; run workflow tests on a GPU-enabled Galaxy instance.
