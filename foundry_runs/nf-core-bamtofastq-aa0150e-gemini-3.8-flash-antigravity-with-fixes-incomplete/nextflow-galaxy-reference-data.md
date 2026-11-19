# Nextflow to Galaxy Reference Data Brief: nf-core/bamtofastq

## Reference Asset Inventory

The pipeline declares two reference assets under `nextflow_schema.json` and `main.nf`:
1. `params.fasta`: Reference genome sequence in FASTA format (`asset_kind: fasta`). Optional. Required when input alignments are in CRAM format and sequence headers lack embedded references.
2. `params.fasta_fai`: FASTA index file (`asset_kind: fasta_index`). Optional. When absent but `fasta` is supplied, Nextflow invokes `SAMTOOLS_FAIDX` to index the FASTA file.

## Classification

- **Classification**: Single asset with compute-if-missing index fallback.
- **iGenomes Key Disposition**: `params.genome` is provided in the source pipeline for looking up references via iGenomes. Following Foundry v1 posture, data tables and cached lookups (`dbkey`, `.loc`) are avoided to preserve portability across stock Galaxy instances. Reference data is translated as explicit optional inputs.

## Galaxy-Side Mapping

- `reference_fasta`: Explicit optional workflow `data` input (format: `fasta`).
- `reference_fasta_fai`: Optional workflow `data` input (format: `fai`). In accordance with Galaxy v1 conventions and tool capabilities, tools consuming reference sequence (such as `samtools stats` or `samtools view`) can take the FASTA dataset directly; samtools generates or caches index files automatically or handles uncompressed/bgzip FASTA. If needed, an explicit `samtools faidx` step or in-tool indexing is used.

## Rebuild-on-Absence Behavior

- If `fasta` is not provided (standard BAM input), no reference is needed and reference-dependent indexing is skipped.
- If `fasta` is provided and `fasta_fai` is absent, downstream tools (samtools) handle indexing automatically or a `samtools faidx` tool step is used.

## Open Questions

- None blocking. Optional FASTA input maps directly to Galaxy optional `data` input.
