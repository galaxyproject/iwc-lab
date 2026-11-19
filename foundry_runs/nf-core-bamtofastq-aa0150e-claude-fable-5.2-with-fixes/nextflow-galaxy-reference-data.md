# Reference data brief — nf-core/bamtofastq → Galaxy

Source: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e). Read from `reference_assets[]`, `reference_rebuilds[]`, `params[]`, and the reconciled `workflow.edges[]`.

## Classification (Nextflow side)

| Classification | Applies | Evidence |
|---|---|---|
| None | no | two reference assets declared |
| Reference-producing | no | outputs are reads and QC, not references |
| **Single asset** | **yes** | `fasta` is the only real asset; `fasta_fai` is its derived index. The classification note names this pipeline as the example ("FASTA needed only when input is CRAM"). |
| Coordinated bundle | no | |
| Key-expanded bundle (iGenomes) | weak | `--genome` is a key into `conf/igenomes.config`; `main.nf` (lines 37-38) sets `params.fasta = params.fasta ?: getGenomeAttribute('fasta')` and the same for `fasta_fai`. Only two attributes are expanded. Note: the summary does not carry this (`params[].source_kind` is not `getGenomeAttribute` for either param), so this row was confirmed by reading `main.nf` directly — a deviation from the skill's 'do not re-parse source' rule, logged as feedback. |
| **Compute-if-missing** | **yes, rebuild-unverified in the summary** | `reference_rebuilds[]` is empty, but `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` when `fasta` is set and `fasta_fai` is not (channel `.branch { meta.index == false }` idiom, not an `if (!x)` guard — the detector does not match it). Recorded in the summary's edges/conditionals by the LLM pass. |
| Multi-DB pick-list | no | |
| Parallel bundles + cohort data | no | |

## Per-asset decisions (Galaxy side)

### `fasta` — reference genome FASTA

- **Galaxy shape:** one explicit optional workflow input, `type: data`, `format: fasta`, `optional: true`. Label suggestion: `Reference genome FASTA`.
- **Requiredness:** optional in the source (`required: false`). Functionally needed only for CRAM inputs whose reference cannot be resolved otherwise. For BAM input the source still passes `--reference` to every samtools call when a FASTA is given, but it has no effect on the result.
- **Consumers in the source:** `SAMTOOLS_STATS`, `CHECKPAIREDEND`, `SAMTOOLS_VIEW*` (all aliases), `SAMTOOLS_MERGE_UNMAP`, all three `SAMTOOLS_COLLATEFASTQ` aliases — every one as `--reference`.
- **Datatype:** `fasta` (the mapping note's default; `.fasta.gz` sniffs as `fasta` too).
- **No data table / dbkey lookup** (v1 posture: explicit inputs only).

### `fasta_fai` — FASTA index

- **Galaxy shape:** **not a workflow input.** Posture: in-tool rebuild. Galaxy samtools wrappers that take a history FASTA as reference index it themselves, so neither a `fai` input nor a workflow-tier `samtools faidx` step is planned.
- **Rebuild behaviour in source:** `SAMTOOLS_FAIDX` on absence (see above). In Galaxy this step is subsumed by the consuming wrappers.
- **Status: rebuild-unverified.** The mapping note says the brief cannot verify wrapper rebuild capability at this stage. Tool discovery (phase 7) must confirm that each chosen samtools wrapper accepts a history FASTA reference without a separate `.fai`. If one does not, add an explicit faidx step for it.
- Deviation thresholds do not apply: `samtools faidx` on a FASTA is cheap, so repeated in-tool rebuild across ~8 steps is acceptable.

### `genome`, `igenomes_base`, `igenomes_ignore` — iGenomes key

- **Disposition: not exposed.** Galaxy workflow starts at the resolved asset (`fasta`), not the key. No data table is introduced. Users pick a FASTA from their history.

## Summary table

| Source param | Asset kind | Galaxy input | Format | Optional | Rebuild on absence |
|---|---|---|---|---|---|
| `fasta` | fasta | `Reference genome FASTA` (`data`) | `fasta` | yes | n/a (user data) |
| `fasta_fai` | fasta_index | none | — | — | in-tool (wrapper indexes the FASTA) — unverified until tool discovery |
| `genome` (+ `igenomes_*`) | key | none | — | — | n/a |

## Open questions

1. **Does a Galaxy workflow need the FASTA at all for BAM-only use?** No. The input stays optional; the interface brief decides whether CRAM input is carried (see ledger entry `cram-input-support-unverified`).
2. **Optional reference input into samtools wrappers.** Galaxy tool reference selectors are usually a conditional (`no reference` / `history` / `cached`). An optional workflow input cannot flip that conditional at run time. The data-flow and template phases must decide whether the workflow always passes the FASTA (making it effectively required) or never does (BAM-only). Recorded as ledger entry `optional-reference-vs-tool-conditional`.
3. Bundled BAM/CRAM index files (`.bai`/`.crai`) are sample data, not reference data; they are left to the interface brief.
