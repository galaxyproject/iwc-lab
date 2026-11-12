# Reference data — nf-core/bamtofastq 2.2.1 → Galaxy

Source: `summary-nextflow.json` (nf-core/bamtofastq @ 8a29586, tag 2.2.1). Upstream ledger: none (first design-tier Mold; ledger started here).

## Classification

| Classification | Applies | Evidence |
|---|---|---|
| None | no | `reference_assets[]` has `fasta`, `fasta_fai`. |
| Single asset | **yes** | One reference FASTA (`params.fasta`), optional. Needed only to decode CRAM (`--reference` in CHECKPAIREDEND, samtools view/stats/collate) and passed through to BAM steps where it is inert. |
| Key-expanded bundle (iGenomes) | partial | `main.nf:37-38` sets `params.fasta = params.fasta ?: getGenomeAttribute('fasta')` (and `fasta_fai`). Only two attributes are derived. The summary records `source_kind: nextflow_schema` for both, not `getGenomeAttribute` — the key-expanded signal was missed by the summarizer. |
| Compute-if-missing | **yes (fai), rebuild-unverified in summary** | `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` when `fasta_fai` is unset (branch on `meta.index == false`). `reference_rebuilds[]` is empty — the branch-on-meta idiom is not detected — so this is inferred from the edge/conditional evidence, not a structured rebuild entry. |
| Coordinated bundle / multi-DB / cohort | no | — |

Per-sample alignment indexes (`bai`/`crai`, rebuilt by `SAMTOOLS_INDEX` when the samplesheet `index` column is empty) are sample data, not reference data; they are handled by the interface brief.

## Per-asset Galaxy shape

| Asset | NF param | Galaxy input | format | Required | Rebuild on absence |
|---|---|---|---|---|---|
| Reference FASTA | `fasta` | `reference_fasta` (workflow `data` input) | `fasta` | optional (required in practice for CRAM whose reference is not resolvable from the header) | n/a |
| FASTA index | `fasta_fai` | **not exposed** | — | — | in-tool: Galaxy samtools wrappers (`samtools_view`, `samtools_stats`, `samtools_fastx`) take a history FASTA and index it inside the wrapper — matches the v1 in-tool-rebuild posture. |
| iGenomes key | `genome` | **not exposed** | — | — | v1 posture: no data tables / dbkey lookups. Users upload the FASTA. |

Rationale: with a single, cheap index (`samtools faidx`, reused by ≤ 6 steps per sample on small references) the in-tool rule applies; a workflow-tier `faidx` step is not warranted.

## Open questions / carried assumptions

- **Rebuild capability unverified.** The claim that each chosen samtools wrapper indexes a history FASTA internally must be confirmed at tool-discovery time (phase 7). If a wrapper needs a pre-built `fai`, add an optional `fasta_fai` input or a single workflow-tier faidx step.
- **Optional reference in Galaxy steps.** Galaxy samtools wrappers expose the reference as a conditional (`cached` / `history` / none). Wiring an *optional* workflow input into a conditional's `history` branch needs either a `when:` toggle or a "has reference" boolean; the data-flow brief must settle this.
- The default test (`tests/default.nf.test`) supplies `fasta` (genome.fasta) with BAM inputs only — the FASTA is exercised but not load-bearing there.
