# Galaxy reference-data brief — nf-core/demo (1.2.0)

Source: `summary-nextflow.json` (nf-core/demo, tag 1.2.0, commit 32893afe).

## Classification

**None** — the pipeline consumes no reference data.

Evidence:

- `reference_assets[]` is empty. No process input (`FASTQC`, `SEQTK_TRIM`, `COWPY`, `MULTIQC`) is a reference asset; all process inputs are FastQ reads, tool-produced QC artifacts, or MultiQC support files.
- `reference_rebuilds[]` is empty. No compute-if-missing branch exists anywhere in the pipeline — nothing is ever built from a reference.
- The pipeline *declares* iGenomes plumbing (`params.genome`, `conf/igenomes.config`, `params.fasta = getGenomeAttribute('fasta')` in `main.nf`), which on its face signals a key-expanded bundle. But the synthesized `fasta` param is **never consumed by any process or channel**: `getGenomeAttribute` feeds only `genomeExistsError()` validation (in `validateInputParameters()`), which errors when an unknown `--genome` key is passed. The key-expanded bundle is vestigial boilerplate inherited from the nf-core template.

## Per-asset disposition

| Param | source_kind | Disposition for Galaxy |
|---|---|---|
| `genome` | nextflow_schema (Reference genome options) | **Exclude from the Galaxy interface.** Runtime-control/selector param with no data-bearing consumer; carrying it would force users to answer a question the workflow never uses. |
| `fasta` | getGenomeAttribute → `conf/igenomes.config` | **Exclude.** No process consumes it. Flag: this is a key-expanded-bundle *signal* with no asset behind it — do not synthesize a `data` input from it. |
| `igenomes_base`, `igenomes_ignore` | nextflow_schema (hidden) | Exclude; config plumbing only. |

## Galaxy posture

- No reference-data inputs are added to the workflow. The v1 posture (explicit optional inputs, no data tables, no dbkey lookups) is trivially satisfied: there is nothing to map.
- Downstream Molds (interface, data-flow, template) should treat the workflow as having a **reads-in / QC-reports-out** shape with no reference surface.
- If a future nf-core/demo version wires `fasta` into a process, this brief must be revisited — the correct shape then would be a single optional `fasta` input (single-asset classification).

## Open questions

None. The empty `reference_assets[]` + empty `reference_rebuilds[]` + consumed-nowhere `getGenomeAttribute` param is a complete, unambiguous classification.

## Ledger

No reference-data obligations raised: no genome key lacks a data table, no runtime build exists, no bundle is missing. `open-requirements.ledger.yml` is started empty by this step.
