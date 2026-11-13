# nf-core/demo — Galaxy reference-data brief

Source: `summary-nextflow.json` (nf-core/demo @ 671a0726, v1.2.0+5).

## Classification

**None** (per nextflow-reference-data-classification), with an inert iGenomes key-expanded vestige.

- `reference_assets[]` holds one entry, `fasta` (`asset_kind: fasta`, `required: false`, `used_by: []`, confidence medium).
- `reference_rebuilds[]` is empty, and no process consumes a reference: FASTQC, SEQTK_TRIM, COWPY and MULTIQC take only reads, QC files or nothing.
- `params.fasta = getGenomeAttribute('fasta')` in `main.nf` plus `genome`, `igenomes_base` and `igenomes_ignore` are nf-core template residue. Nothing reads `params.fasta` in `workflows/demo.nf`. The summary records `fasta` with `source_kind: nextflow_schema` because it also appears in `nextflow_schema.json`.

## Per-asset decisions

| Param | Galaxy shape | Requiredness | Rebuild on absence | Rationale |
|---|---|---|---|---|
| `fasta` | not exposed | — | — | Not consumed by any process; exposing it would add a dead workflow input. |
| `genome` (iGenomes key) | not exposed | — | — | Key-expanded selector with no consumer; Galaxy posture also forbids introducing new data tables. |
| `igenomes_base`, `igenomes_ignore` | not exposed | — | — | Runtime config for the key resolver. |

## iGenomes key disposition

Dropped. The key resolves only `fasta`, which is unused. No `.loc`/data-table selector is proposed.

## Downstream guidance

- Interface: no reference-data inputs. The only data-bearing input is the samplesheet-derived reads.
- Data-flow: no reference edges, no dbkey propagation concerns.
- Template: no reference input nodes.

## Open questions

- None blocking. If a future nf-core/demo revision wires `fasta` into a process, re-run this step: it would become a *single asset* optional `data` input (`fasta`).
