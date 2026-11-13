# Reference-data brief — nf-core/bamtofastq → Galaxy

Source: `nf-core/bamtofastq` @ `aa0150e` (v2.4.0), MIT. Input: `summary-nextflow.json`.

## Classification

**Single asset plus compute-if-missing index.** One reference FASTA (`--fasta`), whose `.fai` index is built on demand when the user does not supply one.

Evidence:

- `reference_assets[]` (both `required: false`, `used_by: [BAMTOFASTQ, NFCORE_BAMTOFASTQ]`):
  - `fasta` — `asset_kind: fasta`
  - `fasta_fai` — `asset_kind: fasta_index`
- `workflows/bamtofastq.nf:61-65` builds `fasta_fai` from `params.fasta`, flagging `meta.index` true when `params.fasta_fai` is given.
- `subworkflows/local/prepare_indices/main.nf:40-57` branches on `meta.index` and runs `SAMTOOLS_FAIDX` on the `to_index` branch, mixing the freshly built `.fai` back in. This is the **positive-form** compute-if-missing idiom (`if indexed { pass } else { build }`), which `summary-nextflow` reports as an empty `reference_rebuilds[]` — the asset is therefore *rebuild-confirmed by source inspection* but not by the structured field. Recorded as a feedback entry.
- The FASTA is consumed as the CRAM reference by `SAMTOOLS_VIEW`, `SAMTOOLS_MERGE` and `CHECKPAIREDEND`; it is not read when inputs are BAM.

## Per-asset disposition

| Nextflow param | Asset kind | Required | Galaxy disposition |
|---|---|---|---|
| `fasta` | fasta | no (but needed for CRAM input) | **Explicit optional `data` input**, format `fasta`. Wired to every CRAM-consuming step. |
| `fasta_fai` | fasta_index | no | **Not exposed.** No separate workflow input: Galaxy's samtools wrappers build/accept an index themselves (in-tool rebuild), matching the v1 posture. |
| `genome`, `igenomes_ignore`, `igenomes_base` | iGenomes key/controls | no | **Not exposed.** `bamtofastq.nf` has no `getGenomeAttribute` call; nothing resolves through the key. |

## Rebuild-on-absence behaviour

Source: absent `.fai` → `SAMTOOLS_FAIDX` on the FASTA, index re-mixed into the reference tuple.

Galaxy: the reference tuple collapses to a single optional FASTA dataset. Index building is left to the samtools wrappers that need it (they accept a FASTA and index internally, or take an optional index). No workflow-tier `samtools faidx` step is added: with one FASTA and several consumers, the "rebuild more than ~3 times" threshold for a workflow-tier build step is not clearly crossed and the wrappers already handle it.

Consequence to carry: if a chosen Galaxy samtools wrapper does **not** rebuild the index for CRAM, the workflow loses the source's compute-if-missing guarantee. Flagged for tool discovery, not as a current blocker.

## Datatypes

| Asset | Galaxy format | Confidence |
|---|---|---|
| reference FASTA | `fasta` | high (source extension `.fasta`) |
| index | — (not exposed) | n/a |

## Open questions

1. Does the Galaxy `samtools view`/`merge` wrapper used in this translation accept a FASTA without a separate `.fai` and index it itself (or expose an optional index input)? Settle at tool discovery.
2. The pipeline only needs the FASTA for CRAM inputs; a BAM-only run ignores it. Galaxy cannot express "required only when the input is CRAM" cleanly, so the input stays optional with documentation saying it is needed for CRAM.
