# Reference data brief — nf-core/bamtofastq @ aa0150e

## Classification

- **Single asset** (primary) — one reference FASTA (`params.fasta`), with an optional FASTA index (`params.fasta_fai`). The note's own example of this rung is nf-core/bamtofastq.
- **Compute-if-missing** (overlay) — `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` when no `fasta_fai` is given (`fasta_branch.to_index`, guard `meta.index == false`, i.e. `!params.fasta_fai`). This is a branch-operator idiom, not the `if (!x)` form, so `reference_rebuilds[]` is empty → the FAI rebuild is **rebuild-unverified** by the summary detector; confirmed by reading `subworkflows/local/prepare_indices/main.nf` evidence recorded in summary edges.
- **Key-expanded bundle (vestigial)** — `main.nf` sets `params.fasta = params.fasta ?: getGenomeAttribute('fasta')` and same for `fasta_fai`. Only two attributes; summary reports `source_kind: nextflow_schema` (the `main.nf` fallback is not surfaced). No Galaxy data table will be introduced.

## Per-asset decisions

| Asset | NF param | Galaxy input | Format | Required | Rebuild on absence | Notes |
|---|---|---|---|---|---|---|
| Reference FASTA | `fasta` | `reference_fasta` (optional `data` input) | `fasta` | optional | n/a | Needed only for CRAM decoding (`--reference`) and passed to `samtools stats`. BAM-only runs work without it. |
| FASTA index | `fasta_fai` | **not exposed** | `fai` | — | in-tool: Galaxy samtools wrappers that take a reference FASTA build/locate the `.fai` themselves | Pipeline only indexes FASTA for tool consumption; no published output. Exposing an optional fai input adds surface with no behavioural effect in Galaxy. |
| iGenomes key | `genome` | **not exposed** | — | — | — | Discouraged per v1 posture (no data tables); user supplies `reference_fasta` directly. |

## Galaxy posture

- Explicit optional `data` input for the FASTA; no `dbkey`/`.loc` lookups.
- No workflow-tier `samtools faidx` step: wrapper-level reference handling (Galaxy samtools wrappers use a history FASTA via a `reference_source` conditional and index it internally).
- Default test (`tests/default.nf.test`) is BAM-only and supplies `fasta` anyway; the FASTA is consumed by `samtools stats` (`--reference`) and collate/fastq (`--reference`).

## Open questions

- Whether every chosen Galaxy samtools wrapper (stats, view, collate/fastq, merge) accepts an optional history FASTA — to be verified at discovery/implementation time (rebuild-unverified).
- CRAM inputs without a reference rely on the CRAM header `UR:` tags; in Galaxy that path is not portable — the CRAM tests always supply `fasta`.
