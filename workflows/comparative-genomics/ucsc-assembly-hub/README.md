# UCSC Assembly Hub Track and Manifest Builder

This workflow builds the core binary track and manifest artifacts needed to publish a comparative genomics UCSC Genome Browser assembly hub:

- **Genome sequences (`2bit`)** via `ucsc_fatotwobit`
- **Multiple alignment (`bigMaf`)** via `process_maf` → `maf_to_bigmaf_bed` → `sort1` → `ucsc_bedtobigbed` (`bed3+1`)
- **Pairwise alignment chains (`bigChain` + `bigLink`)** via `chain_to_bigChain` → `sort1` → `ucsc_bedtobigbed` (`bed6+6` and `bed4+1`, using per-chain target `chrom.sizes` derived directly from chain headers)
- **Gene annotations (`BigBed12`)** via `ucsc_gff3togenepred` → `ucsc_genepredtobed` → `sort1` → `ucsc_bedtobigbed` (`bed12`)
- **Hub genome manifest (`genomes.txt`)** via `build_genomes_txt`

## Inputs

- **Genome assemblies** (`list` of `fasta`): Assemblies included in the hub.
- **Multiple alignment MAFs** (`list` of `maf`): Multi-species MAF alignments whose `s`-lines are already prefixed with assembly identifiers matching **Reference genome identifier**.
- **Directed pairwise chains** (`list` of `chain`): Cleaned pairwise UCSC chains.
- **Gene annotation GFF3s** (`list` of `gff3`): Gene annotations on the reference assembly.
- **Reference chromosome sizes** (`tabular`): Reference `chrom.sizes` (`chrom<TAB>length`).
- **Hub genome metadata** (`tabular`): TSV with columns `accession`, `defaultPos`, `organism`, `scientificName`, `description`.
- **bigMaf / bigChain / bigLink autoSql schemas** (`txt`): Standard UCSC `.as` definitions.
- **Reference genome identifier** (`string`): Assembly identifier prefixing reference rows in the input MAFs.

## Outputs

- **TwoBit assemblies** (`list` of `twobit`)
- **UCSC bigMaf tracks** (`list` of `bigbed`)
- **UCSC bigChain tracks** (`list` of `bigbed`) and **UCSC bigLink tracks** (`list` of `bigbed`)
- **Gene annotation BigBed tracks** (`list` of `bigbed`)
- **Hub genomes definition** (`txt`, `genomes.txt`)

## Known Staging Scope & Post-Workflow Steps

This workflow generates all individual binary track collections and `genomes.txt`, but does **not** materialize the final static HTTP directory tree (`hub.txt`, per-assembly `trackDb.txt` via `build_trackdb`, and post-staging validation via `ucsc_hubcheck`), because Galaxy collections do not represent heterogeneous nested directory trees on disk. Stage the emitted outputs into the hub directory layout and run `ucsc_hubcheck` against the published `hub.txt` URL as the final verification gate.

For large reference-guided `multiz roast` runs split across chromosome pieces, see the companion `wfi-split` → `multiz-roast` → `wfi-track` pipeline for building the `bigMaf` track directly from pieces.
