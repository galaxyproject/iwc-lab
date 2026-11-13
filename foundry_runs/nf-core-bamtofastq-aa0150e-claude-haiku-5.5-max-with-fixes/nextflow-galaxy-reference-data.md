# Reference data brief: nf-core/bamtofastq (aa0150e)

**Status:** draft for review.
**Produced by:** `nextflow-summary-to-galaxy-reference-data` (mold revision 5).
**Inputs:** `summary-nextflow.json` (phase 1, hand-corrected; see its `warnings`) and the pinned source (`source/`, commit aa0150e).
**Ledger:** `open-requirements.ledger.yml` (new; see section 8).

## 1. Summary

- The source consumes one optional reference, a FASTA, and one index derived from it, a FAI. The index is built at runtime when it is absent. A key-expanded iGenomes path (`genome`) also feeds both, but this brief does not carry it.
- Galaxy shape: two optional `data` inputs, `fasta` (format `fasta`) and `fasta_fai` (format `fai`). A workflow-tier `samtools faidx` step builds the index once per invocation when it is absent and a FASTA is given. The `genome` key is not carried.
- Open: whether a FASTA is needed for BAM-only runs. The source's no-FASTA behaviour is unverified (section 6, Q1).

## 2. Classification (eight Nextflow-side classes)

| Class | Present | Evidence |
|---|---|---|
| None | No | Two reference-type params are consumed. |
| Reference-producing | No | No database or index is a published output. |
| Single asset | Yes (FASTA) | `reference_assets[]`: `fasta`, `required: false`. Consumed as an optional reference, with CRAM-aware steps. |
| Coordinated bundle | No | `fasta_fai` is derived from `fasta` and is handled as the index aspect below, not as a separate bundle. |
| Key-expanded bundle (iGenomes) | Yes, from source | `genome` key. `main.nf` lines 37-38 expand `fasta` and `fasta_fai` with `getGenomeAttribute`. `conf/igenomes.config` has 39 `fasta` entries and no `fasta_fai`. The summary does not flag it (section 7). |
| Compute-if-missing | Yes (FAI) | `reference_rebuilds[]`: `fasta_fai` is built by `SAMTOOLS_FAIDX` when `meta.index == false` (`subworkflows/local/prepare_indices/main.nf` lines 40-58). |
| Multi-DB pick-list | No | |
| Parallel bundles plus cohort data | No | |

## 3. Per-asset reference inputs

| Source param | Role | Galaxy input (gxformat2) | Requiredness | If absent | Process-level consumers | Status |
|---|---|---|---|---|---|---|
| `fasta` | Reference genome | `type: data`, `format: fasta`, `optional: true` | Optional for BAM rows. Needed for CRAM rows (Q2). nf-schema: `required: false`. | No index can be built. | CHECKPAIREDEND (CRAM branch), SAMTOOLS_COLLATEFASTQ, SAMTOOLS_VIEW (aliases), SAMTOOLS_MERGE, SAMTOOLS_STATS, SAMTOOLS_FAIDX | Settled, except Q1 and Q2. |
| `fasta_fai` | FASTA index | `type: data`, `format: fai`, `optional: true` | Optional. nf-schema: `required: false`. | Built from `fasta` once per invocation (section 4). | Same as `fasta`. It fills the index slot of the `[meta, fasta, fai]` tuple. | Rebuild-unverified. No Galaxy faidx wrapper is discovered yet (Q3). |

`reference_assets[].used_by` lists only the two workflow scopes (BAMTOFASTQ, NFCORE_BAMTOFASTQ). The consumers above come from the process input shapes in the summary.

## 4. Rebuild on absence

- **Source behaviour.** `prepare_indices` marks the index as provided only when `params.fasta_fai` is given. Otherwise `SAMTOOLS_FAIDX` builds `*.fai` from `fasta`. The result is taken once per run with `.first()`. The module is published with `enabled: false` and has no `ext.when` gate.
- **Genome-key runs.** `igenomes.config` has no `fasta_fai`, so the index is always rebuilt in those runs.
- **No FASTA.** The source still calls `SAMTOOLS_FAIDX` with an empty FASTA, from `channel.value([[id:'none', index:false], [], []])`. This is unverified (Q1).
- **Galaxy shape (decision `fasta-fai-built-once-per-invocation`).** One workflow-tier `samtools faidx` step, run once per invocation when `fasta` is present and `fasta_fai` is absent. A user-supplied index bypasses it. In-tool rebuild in each consumer is rejected: the consumers run per sample, so the index would be rebuilt many times. The mapping note's deviation rule for repeated use applies.
- **Fallback.** If the template step cannot express the conditional step, use in-tool rebuild in the consumers, and keep `fasta_fai` marked rebuild-unverified until a consumer wrapper is confirmed.

## 5. iGenomes key disposition

| Source param | Class | Effect in source | Disposition | Assessment | Reason |
|---|---|---|---|---|---|
| `genome` | Reference selector (key-expanded) | Sets the `fasta` and `fasta_fai` defaults through `getGenomeAttribute` (`main.nf` lines 37-38), with paths from `conf/igenomes.config` under `igenomes_base`. | Not carried. Ledger `genome-key-expansion-not-carried` (dropped). | Safe. The substitute is a user-supplied FASTA. | v1 posture: no admin data tables. The iGenomes paths are S3 URIs. |
| `igenomes_base` | Site config | Base path for iGenomes files (`nextflow.config` line 24). | Excluded. Ledger `igenomes-loader-controls-not-carried` (dropped). | Safe. | Site config. No effect once `genome` is not carried. |
| `igenomes_ignore` | Runtime control | Chooses `igenomes.config` or `igenomes_ignored.config` (`nextflow.config` lines 25 and 204). Source default `false`; the summary shows `null` (section 7). | Excluded (same ledger entry). | Safe. | Affects only the genome-key path. |

**Loss to record:** a user can no longer pick an iGenomes build by name. The source config has 39 FASTA builds. A curated enum of them would be a dead selector, because each build's path is an S3 URI.

## 6. Open questions

- **Q1. Is a FASTA required for BAM-only runs?**
  - *For optional:* nf-schema has `required: false`. Every BAM-path use of `fasta` is guarded (`fasta ? ... : ""` in the SAMTOOLS scripts). The classification note's example says FASTA is needed only for CRAM.
  - *Against:* `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` with an empty FASTA when none is given, and no `ext.when` gate exists. No nf-test runs without one: every `.nf.test` file mentions `fasta`, and the default test sets it.
  - *Recommendation:* keep `fasta` optional. The Galaxy design does not run the index step without a FASTA, so it avoids the source's possible failure. Record that as a divergence. Before claiming BAM-only support, run a BAM-only, no-FASTA case in the test plan (phases 9-12), or state the claim as unverified.
- **Q2. Conditional requiredness for CRAM rows.** `fasta` is needed only when a row is CRAM. gxformat2 has no conditional-required input, so the interface step should mark it optional with a review note (ledger `fasta-required-for-cram-not-expressible`).
- **Q3. Galaxy faidx wrapper.** The workflow-tier step needs a samtools `faidx` wrapper. Discovery (`discover-shed-tool`) must confirm one (ledger `faidx-precursor-wrapper-not-yet-discovered`).
- **Q4. Build selection later.** Whether v2 should offer a curated build selector (one `fasta` per build) is out of scope for v1.

## 7. Gaps in the summary this brief worked around

1. **Key-expanded bundle not flagged.** `fasta` and `fasta_fai` keep `source_kind: nextflow_schema`, although `getGenomeAttribute` assigns them in the workflow body (`main.nf` lines 37-38). Classified from source. Feedback entry `getgenomeattribute-in-workflow-body-not-detected`.
2. **Boolean defaults missing.** Ten boolean params show `default: null`, but `nextflow.config` sets `false`. Feedback entry `boolean-param-defaults-from-schema-only`. Defaults used here come from `nextflow.config`.
3. **Compute-if-missing rule added by hand in phase 1.** The deterministic pass emitted no `reference_rebuilds[]`. The `fasta_fai` rule was added in the phase 1 summary (see its warnings).
4. **Schema help text is template text.** The `fasta` and `fasta_fai` help says "mandatory if --genome is not specified" and mentions a BWA index. Neither matches this pipeline, so requiredness does not rely on it.

## 8. Ledger and feedback record

- **Open-requirements ledger** (`open-requirements.ledger.yml`, new, started empty): 5 entries. `genome-key-expansion-not-carried` and `igenomes-loader-controls-not-carried` are dropped. `fasta-required-for-cram-not-expressible`, `absent-fasta-source-behavior-unverified` and `faidx-precursor-wrapper-not-yet-discovered` are gaps. All are non-blocking. The file also holds 3 decisions, 5 discoveries and no brief-change recommendations.
- **Feedback ledger:** 2 entries, both about summarize-nextflow. Both are local, and nothing was filed.
- **Not raised as feedback:** the classification note's claim that FASTA is needed only for CRAM. The no-FASTA behaviour in Q1 is unverified, so it is not evidence that the note is wrong.

## 9. Notes for downstream steps

- **Interface:** two optional `data` inputs. No genome key. iGenomes controls excluded. A CRAM note on `fasta`.
- **Data flow:** `fasta` and `fasta_fai` are one dataset each per run, not per sample. Pass each as a single dataset to every consumer. The precursor's output fills the index slot of each consumer.
- **Template:** the precursor step needs a guard for FASTA present and index absent. If that cannot be expressed, use the fallback in section 4.
- **Per-sample index:** the sample sheet's optional `index` column controls whether `SAMTOOLS_INDEX` builds missing BAM and CRAM indexes. This is per-sample compute-if-missing, not reference data, but the interface must handle the column.
