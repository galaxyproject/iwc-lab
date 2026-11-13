# Nextflow → Galaxy reference-data brief: nf-core/bamtofastq

- **Pipeline:** nf-core/bamtofastq at `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78` (`source/`)
- **Input:** `summary-nextflow.json` (summarize-nextflow output, schema-valid, after a reconciliation pass; see `phase1-raw/` for the deterministic original)
- **Mold:** nextflow-summary-to-galaxy-reference-data, revision 5, commit `77425ce0`
- **Carried ledger:** `open-requirements.ledger.yml` (started empty, first Mold of the run)

## Summary

The pipeline consumes two reference assets, `fasta` and `fasta_fai`. Both are optional, both are used by `BAMTOFASTQ` and `NFCORE_BAMTOFASTQ`, and both can arrive either as explicit params or through the iGenomes key `genome`. The pipeline rebuilds the `.fai` when it is absent (verified in source; the summary's `reference_rebuilds[]` is empty).

Recommended Galaxy shape: two optional `data` inputs (`fasta`, format `fasta`; `fasta_fai`, format `fai`). No data tables and no genome key. Three points stay open: reference-free runs, CRAM requiredness, and whether the chosen Galaxy wrapper can rebuild the index in-tool.

## Evidence used

| Source | What it gave |
|---|---|
| `summary-nextflow.json` `reference_assets[]` | `fasta`, `fasta_fai`; `required: false`; `used_by: [BAMTOFASTQ, NFCORE_BAMTOFASTQ]`; `source_kind: nextflow_schema`; evidence list empty |
| `summary-nextflow.json` `reference_rebuilds[]` | empty |
| `summary-nextflow.json` `params[]` | `fasta` and `fasta_fai` reported as plain `nextflow_schema` params, `source_expression: null` (**discrepancy**, see below) |
| `source/main.nf:37-38` | `params.fasta = params.fasta ?: getGenomeAttribute('fasta')`; same for `fasta_fai` |
| `source/main.nf:106-115` | `getGenomeAttribute` reads `params.genomes[params.genome]`, returns null when absent |
| `source/nextflow.config` | `igenomes_base` default `s3://ngi-igenomes/igenomes/`; `includeConfig conf/igenomes.config` unless `igenomes_ignore` |
| `source/workflows/bamtofastq.nf` | `fasta_fai` channel: `meta.index = has_fai`; `channel.value([[id:'none', index:false], [], []])` when no `params.fasta` |
| `source/subworkflows/local/prepare_indices/main.nf` | `fasta_branch` on `meta.index`; `index == false` → `SAMTOOLS_FAIDX`; `ch_fasta_fai` via `.mix(...).first()` |
| `source/modules/nf-core/samtools/faidx/main.nf` | `when: task.ext.when == null \|\| task.ext.when`; `conf/modules.config` sets no `ext.when` for `SAMTOOLS_FAIDX` (only `publishDir` off) |
| `source/tests/*.nf.test` | all 9 supply `fasta` (remote URL); only `fai.nf.test` also supplies `fasta_fai`; none runs without a reference |

**Discrepancy.** The summary reports `fasta` and `fasta_fai` as ordinary schema params. `main.nf:37-38` shows they are also iGenomes-key defaults, which is the key-expanded-bundle signal. I checked this one signal by reading `main.nf` directly, as the Runtime Notes allow when the summary is wrong; this is the only source read outside the summary in this brief apart from the test and config checks above. Logged as feedback `summarize-nextflow-getgenomeattribute-defaults-missed`.

## Classification

| Asset | Classes (see classification note) | Evidence | Confidence |
|---|---|---|---|
| `fasta` | *single asset*, optional and CRAM-conditional; *key-expanded bundle* member | `reference_assets[]`; `main.nf:37` | high |
| `fasta_fai` | *indexes with rebuild fallback* (compute-if-missing); *key-expanded bundle* member | `prepare_indices`; `main.nf:38` | high for the rebuild; summary detector silent |

The two form a coupled pair: the `.fai` must match the FASTA, so they travel together as one `(meta, fasta, fai)` tuple. Not applicable: reference-producing, multi-DB pick-list, parallel cohort bundles.

## Per-asset reference inputs

### `fasta`

- **Nextflow:** `fasta` param (`nextflow_schema.json`; `format: file-path`; pattern `\.fn?a(sta)?(\.gz)?$`). Not required by the schema or by source.
- **Galaxy input (proposed):** `fasta`, type `data`, format `fasta` (auto-decompresses `.gz`), `optional: true`, no default.
- **Consumers:** the `(meta, fasta, fai)` tuple reaches `PREPARE_INDICES`, `PRE_CONVERSION_QC` (`SAMTOOLS_STATS`), `CHECKPAIREDEND` (`--reference` for CRAM), `SAMTOOLS_CHR` / `SAMTOOLS_CHR_INDEX` (only with `params.chr`), `SAMTOOLS_COLLATEFASTQ_SINGLE_END`, and every `ALIGNMENT_TO_FASTQ` step (views, merge, collate).
- **Requiredness:** optional for the BAM path. CRAM input needs a reference, and no check in the source enforces that (see open entries).
- **Rebuild on absence:** none. The FASTA itself has no builder.
- **iGenomes:** default via `getGenomeAttribute('fasta')`. Disposition: explicit input replaces the key path (see iGenomes section).

### `fasta_fai`

- **Nextflow:** `fasta_fai` param (`nextflow_schema.json`; `format: file-path`; pattern `\.fn?a(sta)?.fai(\.gz)?$`). Not required.
- **Galaxy input (proposed):** `fasta_fai`, type `data`, format `fai`, `optional: true`.
- **Consumers:** same tuple as `fasta`. Built by `SAMTOOLS_FAIDX` when absent.
- **Rebuild on absence (compute-if-missing, source-verified):** when `fasta` is supplied and `fasta_fai` is not, `PREPARE_INDICES` runs `SAMTOOLS_FAIDX` on the `meta.index == false` branch and reattaches the new `.fai`. The summary's `reference_rebuilds[]` does not detect this (channel-branch idiom; logged as feedback `summarize-nextflow-channel-branch-rebuild-missed`).
- **Galaxy posture:** in-tool rebuild (v1 posture). The consuming wrapper builds the `.fai` from the FASTA when no index is supplied. Whether the chosen wrapper does this is **not verified** (open entry).
- **iGenomes:** default via `getGenomeAttribute('fasta_fai')` (`main.nf:38`).

## Requiredness

| Param | Schema `required` | Enforced in source | Galaxy input | Note |
|---|---|---|---|---|
| `fasta` | false | no | optional `data` (fasta) | Schema help says "mandatory if `--genome` is not specified" and mentions a BWA index. This text is copied from an alignment template; this pipeline builds no BWA index, so the help text is not trusted for requiredness. |
| `fasta_fai` | false | no | optional `data` (fai) | Same help text. |

## Rebuild-on-absence behaviour

| Case | Behaviour (static reading) | Status |
|---|---|---|
| `fasta` + `fasta_fai` both given | used as given | verified |
| `fasta` given, `fasta_fai` absent | `SAMTOOLS_FAIDX` builds `.fai` (`PREPARE_INDICES`) | verified statically; detector silent |
| no `fasta` and no `genome` (BAM input) | `channel.value([[id:'none', index:false], [], []])` → `to_index` branch → `SAMTOOLS_FAIDX` with an empty FASTA. No `when` guard on `SAMTOOLS_FAIDX`. | **unverified, likely failure**; no nf-test covers it |
| no `fasta`, CRAM input | no `--reference` reaches `CHECKPAIREDEND` or the views | **unverified**; no check in source |
| `genome` set, `fasta` / `fasta_fai` not given | `getGenomeAttribute` fills both from `conf/igenomes.config` (S3 base) | verified statically; Galaxy disposition below |

## iGenomes key disposition

| Item | Disposition | Reason |
|---|---|---|
| `genome` (key string) | **dropped** | No Galaxy data table: the mapping note and the params note both forbid introducing one. The key resolves only through `conf/igenomes.config` and `igenomes_base`, which points at S3 keys a stock Galaxy cannot read. Recorded as a `dropped` entry in the ledger. |
| `genome` as a curated string with `restrictions` | considered, **not chosen** | The params note prefers a curated enum for a closed reference set, but here each key would resolve to S3 URLs, so the enum adds surface without a working path. |
| `conf/igenomes.config` `genomes` map | excluded | Only `fasta` and `fasta_fai` are consumed from it; the other attributes in the map (bwa, dict, …) are not used by this pipeline. |
| `igenomes_base`, `igenomes_ignore`, `aws.client.anonymous` | excluded | Infrastructure and runtime controls (params note, runtime-control exclusion). `igenomes_base` is hidden in the schema. |

## Galaxy handoff (for interface, data-flow and template Molds)

- Pin workflow inputs `fasta` (`data`, format `fasta`, optional) and `fasta_fai` (`data`, format `fai`, optional). Both feed the same `(meta, fasta, fai)` reference tuple.
- Do **not** pin a `genome` input, any `igenomes_*` input, or any data-table reference.
- Keep `fasta` optional in the interface until the reference-free and CRAM entries are settled. The interface Mold should document in the input help that CRAM rows need a reference.
- The `.fai` rebuild is an in-tool step, so the data-flow Mold should not add a workflow-level indexing step for it (mapping note: in-tool is preferred below about three rebuilds).

## Sample-level indexes (out of reference scope)

The sample sheet's `index` column (`data`, optional) is per-sample. `PREPARE_INDICES` runs `SAMTOOLS_INDEX` for each BAM/CRAM without an index. That is a per-sample compute-if-missing step, not a reference input. The interface and data-flow Molds should treat it as sample data with an in-tool rebuild (`samtools index`), not as a reference.

## Test-fixture notes (for later phases)

Every nf-test case passes a remote FASTA URL; `fai.nf.test` also passes `fasta_fai`. None exercises a reference-free run. Galaxy test data needs a FASTA, plus an FAI for the `fai` case; that is handled in test-data resolution (phase 8).

## Open questions and unverified assumptions

1. **Reference-free BAM run.** The static reading suggests an empty reference reaches `SAMTOOLS_FAIDX`. Unverified; needs a runtime check or an explicit interface decision. Open ledger entry `reference-free-run-path-unverified`.
2. **CRAM requires a reference.** Not enforced by the source, and Galaxy cannot make an input required only for some sample rows (mapping note gap). Open entry `cram-input-needs-reference-unenforced`.
3. **In-tool `.fai` rebuild.** The chosen Galaxy wrapper's ability to build the index is unverified (mapping note gap "in-tool rebuild capability discovery"). Open entry `fasta-fai-rebuild-in-tool-unverified`.
4. **Summary detector gaps.** Two (see feedback ledger). The brief was checked against source for both.
5. **Schema help text** for `fasta` and `fasta_fai` is copied from another template and not trusted for requiredness.
