# One-to-Many Whole-Genome Alignment Panel with KegAlign and UCSC Chain/Net (Growler Panel)

This workflow aligns a single soft-masked reference genome (`Target genome FASTA`) against a list collection of soft-masked query genomes (`Query genome FASTAs`) in one flat Galaxy workflow, emitting per-query collections of chains, nets, syntenic-net MAFs (ready for `wfi-split` → `multiz-roast` → `wfi-track`), and reciprocal-best MAFs.

## Inputs

- **Target genome FASTA** (`fasta`) and **Target chromosome sizes** (`tabular`)
- **Query genome FASTAs** (`list` of `fasta`) and **Query chromosome sizes** (`list` of `tabular`, matching order and identifiers)
- **LASTZ scoring matrix** (`tabular`) and **axtChain linear gap table** (`tabular`)
- **Alignment parameters**: UCSC/LASTZ defaults (`K`, `L`, `X`, `Y`, `H`, `M`, `T=2`, entropy, `chain_min_score`, `batch_lines`, `num_gpu`).

## Outputs

Per-query `list` collections keyed by query element identifier:
- **All chains**, **Syntenic nets**, **LiftOver chains**, **Filtered syntenic nets**, **Syntenic net MAFs**
- **Reciprocal-best chains**, **Reciprocal-best nets**, **Reciprocal-best MAFs**

## Hardware / CI Requirement

- The `kegalign` seeding step requires a **CUDA GPU** runner. On CPU-only CI runners, `planemo test` cannot execute `kegalign`; run workflow tests on a GPU-enabled Galaxy instance.
