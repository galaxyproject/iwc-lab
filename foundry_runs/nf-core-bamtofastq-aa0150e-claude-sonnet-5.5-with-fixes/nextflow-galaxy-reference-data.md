# Reference-data brief: nf-core/bamtofastq → Galaxy

Source summary: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e). Notes applied: nextflow-reference-data-classification, nextflow-to-galaxy-reference-data-mapping.

## Classification

**Single asset (optional), with an optional companion index and a compute-if-missing index build.** Reference data is used only for CRAM inputs (decoding CRAM needs the reference when it is not embedded) and passed to `SAMTOOLS_VIEW` (`--chr` region extract), `SAMTOOLS_COLLATEFASTQ`, `CHECKPAIREDEND`, and the paired-end subworkflow. No reference is *produced* by the pipeline, and there is no reference-key expansion beyond the standard nf-core `genome` iGenomes selector.

## Per-asset decisions

| Asset | Source param | `reference_assets[]` | Required? | Galaxy shape | Datatype |
|---|---|---|---|---|---|
| Reference genome FASTA | `fasta` | `asset_kind: fasta`, used_by `BAMTOFASTQ` | **No** in the schema; **required in practice for CRAM** inputs whose reference is not embedded/retrievable | Optional workflow `data` input (single file, no data table) | `fasta` |
| FASTA index | `fasta_fai` | `asset_kind: fasta_index`, used_by `BAMTOFASTQ` | No | **Not exposed as a workflow input** (see below) | (`fai` if it were exposed) |

### Rebuild-on-absence

- `reference_rebuilds[]` in the summary is empty. The source nevertheless has a compute-if-missing block: `PREPARE_INDICES` branches on `meta.index` and runs `SAMTOOLS_FAIDX` when a FASTA is given without a `.fai`. This positive-form idiom is not matched by the detector → classify the asset **`fasta_fai`: rebuild-unverified** per the Mold's rule, and treat the compute-if-missing behaviour as real (it is visible in `PREPARE_INDICES.calls` = `SAMTOOLS_FAIDX`, `SAMTOOLS_INDEX`).
- Galaxy posture (in-tool rebuild, mapping note): do **not** add a `fasta_fai` workflow input and do **not** add an explicit `samtools faidx` step. Galaxy samtools wrappers that take a history FASTA index it internally. This is **unverified for the specific wrappers** (assumption; to be checked when the data-flow/draft phases choose wrappers) → open-requirements entry `fasta-fai-input-not-exposed`.
- The same Nextflow block also builds **alignment indexes** (`SAMTOOLS_INDEX`) for BAM/CRAM inputs without `.bai/.crai` (`index` column of the samplesheet is optional). That is an *input-companion* concern, not reference data; it is handled in the interface/data-flow briefs (Galaxy BAM datasets carry/compute their index implicitly).

### iGenomes / `genome` key disposition

- `genome`, `igenomes_base`, `igenomes_ignore`: **not carried.** `params.fasta = params.fasta ?: getGenomeAttribute('fasta')` resolves a key to an S3 FASTA/FAI under `igenomes_base`. Galaxy posture is "no new data tables, explicit user inputs": the user supplies the FASTA directly. The iGenomes key selector is a **dropped** surface (recorded in the ledger as `kind: dropped`).
- The summary records `fasta`/`fasta_fai` with `source_kind: nextflow_schema`, not `getGenomeAttribute`, even though `main.nf` backfills both from the iGenomes key (feedback entry raised).

### CRAM requiredness

`fasta` is optional so BAM-only runs need no reference. A CRAM whose `@SQ` reference cannot be resolved needs it. Galaxy's workflow input optionality cannot express "required when any input is CRAM" (mapping note gap: *required-when-conditional input affordance is weak*). Brief proposal: make the FASTA input **optional**, document in its annotation that it is required for CRAM inputs.

## Open questions / assumptions

1. Wrappers' in-tool FASTA indexing and CRAM reference handling: unverified (carried as ledger gap).
2. Whether an optional workflow `data` input left empty can be consumed by tools that have a conditional "reference from history" selector. Downstream phases must decide how to model "no reference" (conditional branch vs. required reference for all runs). Carried forward.
3. Test data: nf-core test samplesheets for BAM likely include a reference; to be resolved in phase 8.
