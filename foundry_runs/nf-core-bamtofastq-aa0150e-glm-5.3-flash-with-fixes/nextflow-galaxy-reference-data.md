# Galaxy reference-data brief — nf-core/bamtofastq

Source: nf-core/bamtofastq @ aa0150e (summary-nextflow.json, phase 1).
Scope: how the pipeline's external reference data maps onto Galaxy workflow inputs, under the v1 posture (explicit optional inputs + in-tool rebuild, no data tables).

## Classification

Two classifications apply, one of them as an overlay:

1. **Single asset** — the pipeline has exactly one path-shaped reference asset family: a
   genomic FASTA (`params.fasta`, `source_kind: getGenomeAttribute`) plus its index
   (`params.fasta_fai`). nf-core/bamtofastq is the note's own worked example of this rung.
2. **Compute-if-missing (indexes with rebuild fallback)** — overlays the single asset.
   `reference_rebuilds[]` is non-empty and detected with high confidence:
   - `fasta_fai`: guard `meta.index == false` (FASTA supplied without an `.fai`) → `SAMTOOLS_FAIDX` → `fai`. `fallback_for: fasta_fai`.
   - `index` (per-sample alignment index, `.bai`/`.crai`): guard `files[0].index == false` (samplesheet `index` column empty) → `SAMTOOLS_INDEX` → `index`. No fallback param; the missing index is rebuilt from the alignment file itself.

Not applicable: none, reference-producing, coordinated bundle, multi-DB pick-list, parallel bundles plus cohort data.

**Key-expanded bundle signal, partially present but not load-bearing.** `params.genome`
exists and `main.nf` resolves `fasta`/`fasta_fai` via `getGenomeAttribute('fasta')` /
`getGenomeAttribute('fasta_fai')` from `conf/igenomes.config`. However the pipeline uses
*only* these two derived attributes — no dict, no aligner indexes, no known-variants. The
effective reference surface is the two resolved paths, so the translation starts at the
per-asset paths, not the key. The `genome` key itself is a config-time convenience, not a
workflow input.

## Per-asset translation

### 1. Reference FASTA (`params.fasta`)

- **Source behavior**: optional (`required: false` in nextflow_schema.json). Consumed by
  every stage when present — `PREPARE_INDICES` (build `.fai`), `CHECKPAIREDEND`,
  `ALIGNMENT_TO_FASTQ` (samtools view ×4, merge, collatefastq), `PRE_CONVERSION_QC`
  (samtools stats). It is *mandatory in practice* for CRAM inputs (`--reference` needed to
  read a CRAM whose reference is not in the header) and unused for BAM input unless the
  user wants an `.fai`. The test profile always supplies it; `igenomes_ignore = true`.
- **Galaxy shape (v1 posture)**: one optional workflow `data` input, `format: fasta`
  (`auto_compressed_types="gz,bz2"` handles `.fasta.gz`). Label it clearly: "Reference
  FASTA — required when converting CRAM files".
- **Requiredness**: optional. Data-flow Mold must not make it a hard-required input; a
  BAM-only run completes without it.
- **Rebuild**: no rebuild applies to the FASTA itself.

### 2. FASTA index (`params.fasta_fai`)

- **Source behavior**: optional; rebuild-if-absent via `SAMTOOLS_FAIDX` inside
  `PREPARE_INDICES` (workflow-tier rebuild, not in-tool). The rebuilt `.fai` is then
  threaded to every downstream consumer through `PREPARE_INDICES.out.ch_fasta_fai`.
- **Galaxy shape (v1 posture)**: optional workflow `data` input, `format: fai`.
- **Rebuild disposition**: two options exist and the brief recommends the second:
  1. Keep a workflow-tier `samtools faidx` step (mirrors the source exactly). Costs one
     extra step and a conditional in the DAG.
  2. **In-tool rebuild**: Galaxy's `samtools faidx` wrapper and the consuming samtools
     wrappers can build the index when absent. But the source's structure is
     *index-once, share-many*: one FASTA feeds ~7 samtools invocations per sample, which
     is well over the note's "rebuild more than ~3 times → workflow-tier step" threshold
     **for the rebuild step itself**. However — in Galaxy, samtools view/fastq/stats
     wrappers that accept a reference only need the FASTA, not a pre-built `.fai`
     (the index is used to look up contigs lazily); only `samtools faidx`/`idxstats`
     strictly require an index dataset. The practical Galaxy posture therefore is:
     expose the `.fai` as an optional input, and rebuild it with a single
     workflow-tier `samtools faidx` step **only if** the data-flow cannot avoid
     threading an index into per-sample tools. Final placement is the data-flow Mold's
     decision; this brief flags the trade-off rather than pinning it.
- **Unverified assumption**: whether the chosen Galaxy samtools wrappers accept a
  `.fai` dataset as an optional input at all (many samtools Galaxy wrappers auto-generate
  indexes in-tool). Flagged as rebuild-capability-unverified per the mapping note's gap.

### 3. Alignment index (samplesheet `index` column — `.bai`/`.crai`)

- **Source behavior**: per-sample, optional. `PREPARE_INDICES` branches
  `is_indexed`/`to_index` and runs `SAMTOOLS_INDEX` on rows without an index. This is
  sample data with a compute-if-missing rebuild, not a fixed reference asset — it rides
  the samplesheet (Galaxy `sample_sheet` collection territory, decided by the interface
  Mold).
- **Galaxy shape**: if the samplesheet maps to a `sample_sheet` collection with an
  `index` slot, absent indexes arrive as empty slots and need a rebuild step; the
  simpler Galaxy alternative is to require indexes or to build them with one
  `samtools index` map-over step (workflow-tier, unconditional, cheap). Galaxy's samtools
  view/flagstat/stats wrappers typically take an optional index input.
- **This asset is out of the reference-data brief's decision authority** (it is sample
  data); recorded here because `reference_rebuilds[]` binds it and the data-flow Mold
  must see the rebuild branch.

### 4. iGenomes key (`params.genome`, `params.igenomes_base`, `params.igenomes_ignore`)

- **Disposition: dropped from the Galaxy interface.** No Galaxy data table is introduced
  (v1 posture forbids new data tables). The user supplies FASTA + FAI directly. This is
  recorded as a ledger entry (kind `dropped`), with citation.

## Open questions carried forward

1. **`.fai` threading** — workflow-tier `samtools faidx` step vs. relying on wrappers
   that auto-index: unresolved here; decision delegated to nextflow-summary-to-galaxy-data-flow.
2. **CRAM-only runs without FASTA** — samtools view on a CRAM without `--reference`
   fails unless the reference is embedded in the header. The source errors clearly;
   Galaxy should surface the same dependency in the input description ("required for
   CRAM"). Not a blocker; description-level fix.
3. **Alignment index as sample-sheet slot vs. unconditional rebuild step** — interface +
   data-flow joint decision, flagged here so neither re-derives the source behavior.

## Ledger actions

- Started empty ledger (first Mold of the run).
- Appended `igenomes-key-dropped` (kind `dropped`).
- No obligations closed — none were open.
