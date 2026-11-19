# Reference-data brief — nf-core/bamtofastq → Galaxy

Source: `summary-nextflow.json` (nf-core/bamtofastq @ aa0150e). This brief decides the Galaxy-side shape of the external reference data the pipeline consumes, per the nextflow-reference-data-classification taxonomy and the v1 Galaxy posture (explicit optional inputs, no data tables, portability-first).

## Classification

**Single asset (with index rebuild aspect).** nf-core/bamtofastq consumes exactly one reference asset — the genome FASTA — plus its FAI index:

- `fasta` (param `fasta`, `asset_kind: fasta`, `format: file-path`, `required: false`, schema group "Reference genome options", used_by: `BAMTOFASTQ` via `NFCORE_BAMTOFASTQ`). Needed whenever any input alignment is CRAM (samtools `--reference` decoding) and used to derive the FAI.
- `fasta_fai` (param `fasta_fai`, `asset_kind: fasta_index`, `format: file-path`, `required: false`). Consumed alongside the FASTA by the samtools steps.

This is the canonical single-asset rung from the classification note (the note itself cites bamtofastq: "FASTA needed only when input is CRAM"). It is **not** a key-expanded bundle in any load-bearing way: `main.nf` falls back to `getGenomeAttribute('fasta')` / `getGenomeAttribute('fasta_fai')` only when the direct params are unset (summary records both params with `source_kind: nextflow_schema`; the dynamic fallback assignments live in `main.nf` and are not captured in `params[].source_expression` — noted below as an evidence gap).

**Compute-if-missing aspect on `fasta_fai`.** `reference_rebuilds[]` is **empty** in the summary, so the structured rebuild signal is absent. However, the summary's own subworkflow inventory shows the rebuild: `PREPARE_INDICES` (subworkflows/local/prepare_indices) calls `SAMTOOLS_FAIDX`, is invoked as `PREPARE_INDICES(ch_samplesheet, fasta_fai)`, and emits `ch_fasta_fai`. The branch idiom (`fasta_fai.branch { is_fasta_indexed / to_index }` keyed on a channel-embedded `index` flag, not on a `!params.X` guard) is not one of the forms the rebuild detector matches (negated-guard or fused-assignment forms). Per the classification note's protocol, `fasta_fai` is therefore flagged **rebuild-unverified in `reference_rebuilds[]`**, but rebuild behavior is attested by the subworkflow call inventory above. Note this evidence came from the summary artifact, not a re-parse of source files.

The per-alignment index rebuild (bai/crai for BAM/CRAM inputs) is **not** reference data — it is per-sample input handling and belongs to the interface/data-flow briefs.

## Galaxy-side shape per asset

| Param | Galaxy surface | Datatype | Required | Notes |
|---|---|---|---|---|
| `fasta` | explicit workflow `data` input, optional | `fasta` | optional (conditionally required, see open question 1) | `auto_compressed_types` makes a `fasta.gz` upload sniff as `fasta`. |
| `fasta_fai` | explicit workflow `data` input, optional | `fai` | optional | Rebuild path below. |
| `genome` (iGenomes key) | **not carried** | — | — | See iGenomes disposition. |
| `igenomes_base`, `igenomes_ignore` | **not carried** | — | — | Execution-environment plumbing for the source's config layer; no Galaxy meaning under the no-data-tables posture. |

### Rebuild-on-absence behavior for `fasta_fai`

The source pipeline rebuilds the FAI at the **workflow tier** (PREPARE_INDICES → SAMTOOLS_FAIDX) when the FASTA is supplied without an FAI, and threads the resulting `ch_fasta_fai` into every samtools consumer. The v1 mapping posture prefers *in-tool rebuild* for optional indexes, but that preference assumes the chosen Galaxy wrapper verifiably supports the "no index supplied → build one" branch — the mapping note itself lists wrapper-rebuild-capability discovery as an open gap, and the samtools wrappers we will select are not yet verified. Two additional properties push this case toward keeping the workflow-tier step:

1. The FAI is consumed by **many** downstream steps (samtools stats/view/collate for CRAM decoding and region filtering), so per-tool rebuild would repeat the work more than the ~3× threshold the note gives for preferring a workflow-tier build.
2. The source pipeline's own structure already has exactly this step; carrying it keeps the translation faithful and testable against the upstream nf-test snapshots.

**Decision: carry `SAMTOOLS_FAIDX` as an explicit workflow step mirroring PREPARE_INDICES.** Concretely: when the user supplies a FASTA (and no FAI), the Galaxy workflow indexes it once and fans the FAI out to consumers; when the user supplies both, the supplied FAI is used. Conditional wiring of "use supplied FAI else rebuilt FAI" is a data-flow-phase concern (Galaxy step-level conditionals are weak; the likely shape is: run faidx unconditionally on the provided FASTA, which is idempotent, and prefer the user FAI input when present). This deviation from the in-tool-rebuild default is recorded here so the data-flow and interface briefs inherit it.

## iGenomes key disposition

`params.genome` + `conf/igenomes.config` resolve `fasta`/`fasta_fai` at config-load time. Under the v1 posture (no data tables, no cached lookups) a genome **key** has no Galaxy surface: the Galaxy workflow interface starts at the resolved per-asset inputs. The `genome` param is therefore **dropped from the translated interface**, and users supply the FASTA (and optionally FAI) directly. Recorded as a `dropped` entry in `open-requirements.ledger.yml`.

## Datatype notes

- `fasta` → Galaxy `fasta` (per the mapping note's datatype table).
- `fasta_fai` → Galaxy `fai` (tabular subclass, emitted by `samtools faidx`).
- No sequence dictionary, no BWA-style index — nothing else to classify.

## Open questions

1. **FASTA is required only when the input contains CRAM.** The source enforces this at runtime (CRAM without reference fails inside samtools). Galaxy's required-when-conditional input affordance is weak; the workflow will take the FASTA as optional and the failure mode surfaces at tool runtime if a CRAM is supplied without one. Interface brief should document this in the input's help text. (Ledger: `cram-requires-fasta`, gap, non-blocking.)
2. **`getGenomeAttribute` fallback assignments are not in `params[].source_expression`.** The summary records `fasta`/`fasta_fai` as `source_kind: nextflow_schema`; the `params.fasta = params.fasta ?: getGenomeAttribute('fasta')` assignments in `main.nf` are not surfaced. Immaterial here (the iGenomes key is dropped anyway), but noted for honesty. (Feedback ledger entry candidate — see model-test-log; not appended as it does not change this brief's decisions.)
3. **FAI rebuild step vs. supplied FAI precedence** is deferred to the data-flow brief, per the decision above.
