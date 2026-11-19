# Reference-Data Design Brief — nf-core/bamtofastq

## Summary Classification

- **Primary classification:** **Single asset** (with sibling index) + **Indexes with rebuild fallback (compute-if-missing)**.
  - `params.fasta` (`asset_kind: fasta`, `required: false`) is a single optional reference FASTA needed when input alignments are CRAM (and optional/unused for BAM inputs).
  - `params.fasta_fai` (`asset_kind: fasta_index`, `required: false`) is the `.fai` index sibling for `fasta`. In `PREPARE_INDICES`, when `params.fasta` is provided without `params.fasta_fai` (`!meta.index`), `SAMTOOLS_FAIDX` builds the `.fai` index at runtime.
  - `params.genome` (`igenomes_base`, `igenomes_ignore`) implements an optional iGenomes key lookup (`getGenomeAttribute('fasta')` / `getGenomeAttribute('fasta_fai')` in `main.nf`).
- **Source evidence:** `summary-nextflow.json` (`reference_assets[]`, `reference_rebuilds[]`, `params[]`).

## Per-Asset Galaxy Translation

| Source Param | Asset Kind | Source Required | Galaxy Posture (v1) | Galaxy `format` | Optional | Disposition & Notes |
|---|---|---|---|---|---|---|
| `fasta` | `fasta` | `false` | Explicit optional workflow `data` input | `fasta` | `true` | Consumed by CRAM-capable steps (`CHECKPAIREDEND` / `SAMTOOLS_*` / `PRE_CONVERSION_QC` / `ALIGNMENT_TO_FASTQ`). Unused when inputs are BAM. |
| `fasta_fai` | `fasta_index` | `false` | Prefer in-tool rebuild from `fasta` (or optional `fai` input if a chosen wrapper requires it) | `fai` | `true` | Source `PREPARE_INDICES` builds `.fai` via `SAMTOOLS_FAIDX` when absent. Per v1 posture, omit workflow-tier `SAMTOOLS_FAIDX` step if chosen Galaxy wrappers index `fasta` internally; **rebuild assumption unverified** until `discover-shed-tool` inspects each wrapper's inputs. |
| `genome` (plus `igenomes_base`, `igenomes_ignore`) | iGenomes selector | `false` | Dropped / not surfaced as Galaxy data-table input | — | — | Data tables (`dbkey` / `.loc`) are discouraged in v1 for portability. Users supply `fasta` explicitly as a Galaxy dataset. |

## Compute-if-Missing & Rebuild Trade-off

- In `summary-nextflow.json`, `reference_rebuilds[]` records `SAMTOOLS_FAIDX` building `fai` when `params.fasta` is provided without `params.fasta_fai`.
- `fasta` is passed to multiple downstream steps (`SAMTOOLS_STATS`, `CHECKPAIREDEND`, `SAMTOOLS_CHR`, `SAMTOOLS_COLLATEFASTQ_SINGLE_END`, `SAMTOOLS_VIEW_*`, `SAMTOOLS_MERGE_UNMAP`, `COLLATE_FASTQ_*`). Note that in Galaxy, `samtools` Tool Shed wrappers typically accept a FASTA reference dataset directly (either history FASTA or cached `fasta_indexes`) and index or resolve `.fai` internally, or take `fasta` via `metadata.fai_index` rather than requiring a user-wired `.fai` dataset.
- Until Phase 7 (`discover-shed-tool` / `summarize-galaxy-tool`) confirms how the selected Galaxy wrappers (`samtools_view`, `samtools_stats`, `samtools_merge`, `samtools_fastx`/`collatefastq`, and `checkpairedend`) consume FASTA/FAI for CRAM inputs, keep `fasta_fai` rebuild verification open in `open-requirements.ledger.yml`.

## iGenomes Key Disposition

- `genome`, `igenomes_base`, and `igenomes_ignore` are excluded from the Galaxy workflow input interface. The Galaxy workflow starts at the resolved `fasta` dataset input.

## Open Obligations

Tracked in `open-requirements.ledger.yml`:
1. `fasta-fai-in-tool-rebuild-unverified` — verify during tool discovery (Phase 7) whether the chosen Galaxy wrappers for CRAM processing handle FASTA indexing in-tool (via Galaxy `fasta` metadata/wrapper) or require an explicit `.fai` / `samtools_faidx` workflow step.
2. `igenomes-key-not-carried` (`kind: dropped`) — `params.genome` / iGenomes lookup omitted per v1 no-data-table portability posture; users supply `fasta` explicitly.
