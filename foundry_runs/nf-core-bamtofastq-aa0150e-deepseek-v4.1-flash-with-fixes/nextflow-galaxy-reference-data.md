# Reference-data brief — nf-core/bamtofastq → Galaxy

Source: `nf-core/bamtofastq` @ `aa0150e`, summary `summary-nextflow.json`.
Mold: `nextflow-summary-to-galaxy-reference-data`.

## 1. Source classification

| Classification | Applies? | Evidence |
|---|---|---|
| None | no | two path-shaped reference params exist |
| Reference-producing | no | the workflow emits FASTQ + QC reports, not a reference bundle |
| **Single asset (FASTA, optional)** | **yes** | `reference_assets[]`: `fasta` (`asset_kind: fasta`), `fasta_fai` (`asset_kind: fasta_index`), both `required: false`, both `used_by: [BAMTOFASTQ, NFCORE_BAMTOFASTQ]` |
| Coordinated bundle | no | FASTA and FAI are one logical pair, not an independently switchable set |
| Key-expanded bundle (iGenomes) | partial | `params.fasta` / `params.fasta_fai` fall back to `getGenomeAttribute()` in `workflows/bamtofastq.nf` (`main.nf:37-38` of `workflows/bamtofastq.nf`), but `conf/igenomes.config` only defines `fasta` for each key — no `fasta_fai` key exists in this pipeline's iGenomes table |
| **Compute-if-missing (FAI)** | **yes, detector missed it** | `subworkflows/local/prepare_indices/main.nf` branches the FASTA channel on `meta.index` and runs `SAMTOOLS_FAIDX` for the `to_index` branch; `reference_rebuilds[]` in the summary is empty (see §4) |
| Multi-DB pick-list | no | — |
| Parallel bundles + cohort data | no | — |

`reference_rebuilds[]` is **empty** in `summary-nextflow.json`, yet the source does rebuild the
FASTA index on absence. The detector only matches `if (!params.<x>) { BUILDER(...) }`-shaped
guards; bamtofastq instead branches a channel on a `meta` field
(`fasta_branch.to_index` → `SAMTOOLS_FAIDX`) inside a subworkflow. Per the mapping note this
asset is therefore **rebuild-unverified** from the summary alone; the rebuild is confirmed here
by reading `subworkflows/local/prepare_indices/main.nf`.

Per-sample BAM/CRAM indexes (`index` column of the samplesheet) are **not** reference data: they
travel with the sample and are rebuilt by `SAMTOOLS_INDEX` when the samplesheet leaves the
column empty (`prepare_indices/main.nf`). They belong to the data-flow brief, not here.

## 2. Per-asset Galaxy shape

| Source param | Galaxy input | `format` | Required | Consumed by | Notes |
|---|---|---|---|---|---|
| `fasta` | `fasta` (workflow `data` input) | `fasta` | **optional** | `CHECKPAIREDEND`, `SAMTOOLS_STATS`, `SAMTOOLS_VIEW*`, `SAMTOOLS_MERGE`, `SAMTOOLS_COLLATEFASTQ*`, `ALIGNMENT_TO_FASTQ` | only needed when an input is CRAM (`--reference`) or when stats/QC should use the reference. BAM-only runs pass an empty channel today (`channel.value([[:], [], []])`), so the Galaxy workflow must also accept "no reference" |
| `fasta_fai` | `fasta_fai` (workflow `data` input) | `fai` | **optional** | same consumers | derived from `fasta`; supplying it only saves the `samtools faidx` run |

Both are exposed as plain optional `data` inputs. No `dbkey`, no data table, no `.loc` lookup —
the v1 portability posture applies unchanged.

The `genome` **key is not exposed**. `conf/igenomes.config` in this pipeline supplies only
`fasta` (never `fasta_fai`), the key set is open-ended, and a Galaxy `dbkey`/`.loc` lookup would
break portability. A Galaxy user uploads the FASTA (and optionally its `.fai`).

## 3. Rebuild-on-absence behaviour

Source sequence (`subworkflows/local/prepare_indices/main.nf`):

1. If `params.fasta` is unset, the workflow passes a sentinel `[[:], [], []]` — no FASTA at all.
2. If `fasta` is set and `fasta_fai` is set, `meta.index: true` and the FAI is used directly.
3. If `fasta` is set and `fasta_fai` is unset, `meta.index: false`, `SAMTOOLS_FAIDX` runs on the
   FASTA, and its `.fai` is combined back into `[meta, fasta, fai]`.

Galaxy translation (v1 posture): keep both inputs optional and prefer **in-tool rebuild** — the
Galaxy `samtools` wrappers accept a reference FASTA and generate the `.fai` internally when no
index dataset is supplied. If discovery finds a wrapper that cannot do this, a workflow-tier
`SAMTOOLS_FAIDX` step is the fallback; it costs one cheap step and is not worth six conditional
precursor steps. This choice is recorded as a decision in `open-requirements.ledger.yml`; the
wrapper capability is **unverified** until tool discovery.

## 4. Open questions

1. **FAI rebuild location.** In-tool (preferred) vs an explicit workflow-tier `samtools faidx`
   step. Depends on the discovered wrapper's optional-index handling; must be re-checked at tool
   discovery, not assumed here.
2. **Empty-reference path.** The source models "no FASTA" as a sentinel empty channel. Galaxy
   workflows can leave an optional input unset, but every downstream tool step must tolerate an
   unconnected reference port. If any discovered wrapper marks the reference as required, the
   workflow will need a conditional reference step rather than a plain optional input.
3. **Reference requiredness for CRAM.** The source silently runs without a reference for BAM but
   CRAM needs one. Galaxy has no required-when-conditional input; the input's documentation must
   state that CRAM inputs need `fasta`.
