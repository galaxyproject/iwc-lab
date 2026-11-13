# Galaxy reference-data brief — nf-core/bamtofastq

*Source: summary-nextflow.json @ aa0150e; mold nextflow-summary-to-galaxy-reference-data. Written 2026-11-09 23:38 (time via date).*

## Classification

The pipeline is a **Single asset** pipeline with a **compute-if-missing (rebuild) overlay** on that asset, plus an inactive **key-expanded bundle (iGenomes)** pathway:

1. **Single asset — `fasta`.** Exactly one path-shaped reference param (`params.fasta`) is consumed by the pipeline proper. It is optional: it is only *needed* when an input row's `file_type` is `cram` (every samtools invocation threads `--reference ${fasta}` for CRAM), and it is an explicit user input otherwise. The nf-core/bamtofastq case in the classification note's "Single asset" rung is literally this pipeline.
2. **Index with rebuild fallback — `fasta_fai`.** When `params.fasta` is supplied without `params.fasta_fai`, the local subworkflow `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` to build the `.fai` (branch `fasta_branch.to_index`); a pre-built fai skips that branch (`tests/fai.nf.test` covers it). The summary's `reference_rebuilds[]` is **empty** because the guard is expressed as a `.branch { meta.index == true / false }` channel-branch rather than the negated `if (!params.X)` forms the detector matches — this is the documented "rebuild-unverified" blind spot; the classification here is from reading `subworkflows/local/prepare_indices/main.nf` directly, so it is verified by inspection, not by the summary.
3. **Key-expanded bundle — inactive.** `main.nf` calls `getGenomeAttribute('fasta')` / `getGenomeAttribute('fasta_fai')` when `params.genome` is set, resolving paths out of `conf/igenomes.config` (`params.genomes.<key>.fasta` per build). The summary carries no `source_kind: getGenomeAttribute` because the helper resolves into `params.fasta` at workflow-run time inside `NFCORE_BAMTOFASTQ`, not at config load. Galaxy-side this is an *alternate input pathway*, not a distinct asset: with the v1 no-cached-tables posture the Galaxy workflow takes the resolved FASTA (and optional fai) as explicit inputs; the iGenomes key itself has no Galaxy surface and is dropped.

Per-asset decision (v1 posture: explicit optional inputs + in-tool rebuild; no data tables):

| Asset | param | required? | Galaxy shape | Rebuild on absence |
|---|---|---|---|---|
| Reference FASTA | `fasta` | **optional** — required only for CRAM inputs; BAM-only runs need no reference | workflow `data` input, `format: fasta`, optional | n/a (user input) |
| FASTA index | `fasta_fai` | optional | workflow `data` input, `format: fai`, optional | **in-tool rebuild** by the samtools wrappers: Galaxy's samtools faidx/view/merge/stats wrappers take the FASTA and build the index inside the wrapper when none is staged — matching what every samtools nf-core module here does with its `--reference` ternary. *Unverified against specific Tool Shed wrappers at this stage* (documented mapping-note gap): the per-step skill must confirm the selected samtools wrapper's no-index branch before relying on it; the fallback shape is a workflow-tier `samtools faidx` step mirroring `PREPARE_INDICES`. |

## Dispositions and open questions

- **The genome key is dropped.** `params.genome` / `igenomes_base` / `igenomes_ignore` have no Galaxy translation under the no-data-tables posture; a user who wants iGenomes builds uploads the FASTA themselves. Flagged in the interface brief, not an asset.
- **CRAM-conditional requiredness.** Galaxy required-when-conditional affordance is weak (documented gap): `fasta` cannot be declared "required iff any row is CRAM". The brief records it as optional with help text stating the CRAM requirement; the test plan covers the BAM-only case (fasta unused by any step's reference branch — samtools still accepts it harmlessly).
- **`samtools_collate_fast` / `chr` / `no_read_QC` / `no_stats` are runtime controls, not reference data** — they route to the interface brief as Galaxy workflow parameters.
- **Index threading.** `PREPARE_INDICES` also builds missing BAM/CRAM `.bai`/`.crai` indexes (SAMTOOLS_INDEX). That is *sample-data* index repair, not reference data — but it is the same compute-if-missing idiom and belongs in the data-flow brief. In-tool rebuild via Galaxy's samtools wrappers (which accept the alignment without its index and generate one) is the matching posture; verify the wrapper's index-or-not branch per step.

## Ledger

No open-requirements entries inherited (first mold of the run). Nothing blocking appended: the fai rebuild is verified by direct source inspection; the only unverified assumption — samtools wrapper rebuild capability — is carried explicitly in the table above for the per-step loop to confirm.

**Feedback:** no feedback. The classification and mapping notes covered this pipeline's shapes (it is the named single-asset example in the note); the rebuild-detector blind spot for `.branch`-based guards is already documented in the mapping note's known-gaps list, so it is not a new observation about a Foundry asset.
