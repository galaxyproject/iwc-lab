# Reference-Data Design Brief: nf-core/bamtofastq

- **Source**: `nf-core/bamtofastq` (`aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`)
- **Upstream artifact**: `summary-nextflow.json`

## 1. Source Classification

- **Primary**: **Single asset** (`fasta`, optional `data` input used for CRAM decoding/indexing and optional stats).
- **Overlays**:
  - **Indexes with rebuild fallback (compute-if-missing)**: `fasta_fai` (paired `.fai` index for `fasta`). Note: `summary-nextflow.json` reports `reference_rebuilds: []` because `PREPARE_INDICES` implements compute-if-missing via a `.branch { is_fasta_indexed: meta.index == true; to_index: meta.index == false }` channel split feeding `SAMTOOLS_FAIDX`, rather than a negated `if (!params.fasta_fai)` block. Flagged **rebuild-unverified** at the summary tier and resolved here from `PREPARE_INDICES` evidence.
  - **Key-expanded bundle (minimal)**: `params.genome` (`conf/igenomes.config` maps `genome` keys to `fasta`; `main.nf` assigns `params.fasta` and `params.fasta_fai` via `getGenomeAttribute()`). Note that `params[]` entries for `fasta` and `fasta_fai` appear from `nextflow_schema.json` (`source_kind: nextflow_schema`), while `conf/igenomes.config` defines `fasta` per build.

## 2. Per-Asset Disposition (Galaxy v1 Posture)

| Source Param | Asset Kind | Source Required | Galaxy Input Shape | Galaxy Format | Disposition | Notes |
|---|---|---|---|---|---|---|
| `fasta` | `fasta` | `false` (`optional: true`) | Explicit optional `data` workflow input (`reference_fasta`) | `fasta` | Carry as optional `data` input | Required when inputs include CRAM files without embedded reference sequences; also supplied in `tests/default.nf.test` and `tests/fai.nf.test`. |
| `fasta_fai` | `fasta_index` | `false` (`optional: true`) | In-tool rebuild / Galaxy FASTA metadata indexing (defer explicit `fasta_fai` input unless wrapper requires it) | `fai` | Rebuild-unverified; defer to in-tool / Galaxy native FASTA handling | `PREPARE_INDICES` invokes `SAMTOOLS_FAIDX` when `fasta_fai` is omitted (`tests/default.nf.test` omits `fasta_fai`; `tests/fai.nf.test` provides it). Verify during wrapper discovery whether chosen Galaxy samtools wrappers index `fasta` automatically or accept `fasta` directly without a separate `.fai` port. |
| `genome` | iGenomes key | `false` | Not carried | N/A | Dropped per Galaxy v1 portability posture | Per v1 posture, do not introduce `.loc` / `dbkey` data tables; users supply explicit `fasta` instead of an iGenomes build name. |

> Note on sample alignment indexes (`index` column in samplesheet: `.bai` / `.crai`): `PREPARE_INDICES` also runs `SAMTOOLS_INDEX` when `meta.index == false` (`tests/no_bai.nf.test`, `tests/no_crai.nf.test`). These are per-sample alignment indexes rather than genome reference assets and are handled as sample collection/step data flow in subsequent briefs.

## 3. Rebuild-on-Absence & Wrapper Assumptions

- **v1 Posture**: Prefer Galaxy's native FASTA handling and in-tool index building over adding conditional `when:` `SAMTOOLS_FAIDX` workflow steps and `pick_value` merges, unless wrapper discovery reveals a selected tool wrapper cannot accept an unindexed `fasta` dataset directly.
- **`igenomes_ignore` / `igenomes_base`**: Runtime/config plumbing excluded from Galaxy workflow inputs.

## 4. Open Questions & Carried Obligations

1. **`fasta_fai` wrapper rebuild verification** (`reference-fasta-fai-rebuild-unverified` in `open-requirements.ledger.yml`): Confirm during `advance-galaxy-draft-step` whether the selected Tool Shed `samtools` wrappers (`samtools_view`, `samtools_stats`, `samtools_merge`, and any UDT/wrapper for `samtools collate`+`fastq`) accept a Galaxy `fasta` dataset directly (using Galaxy's built-in `.fai` metadata converter or internal `samtools faidx`) without requiring an explicit `fasta_fai` workflow input or `SAMTOOLS_FAIDX` step.
2. **`genome` iGenomes key disposition**: Logged as a design `decision` (start the Galaxy workflow surface at explicit optional `fasta`, omitting `genome` and iGenomes `.loc` tables).
