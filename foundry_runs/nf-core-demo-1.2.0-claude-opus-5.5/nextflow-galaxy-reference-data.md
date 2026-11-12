# Galaxy reference-data brief — nf-core/demo 1.2.0

Source: `summary-nextflow.json` (nf-core/demo @ 32893af). Consumers: nextflow-summary-to-galaxy-interface, -data-flow, -template.

## Classification

**None** (per nextflow-reference-data-classification). No process in the primary workflow `DEMO` consumes reference data:

- `FASTQC`, `SEQTK_TRIM` take only the samplesheet reads; `COWPY` takes no inputs; `MULTIQC` takes the QC bundle plus optional config/logo.
- `reference_assets[]` lists one entry, `fasta` (`asset_kind: fasta`, `required: false`), with **empty `used_by`**.
- `reference_rebuilds[]` is empty, and no builder process exists in `processes[]` — no compute-if-missing branch.

The `Reference genome options` group (`genome`, `fasta`, `igenomes_base`, `igenomes_ignore`) is nf-core template scaffolding. `main.nf:29` assigns `params.fasta = getGenomeAttribute('fasta')` (a key-expanded iGenomes hook), but the resolved value is never threaded into `NFCORE_DEMO`/`DEMO`. Note: the summary records `fasta.source_kind` as `nextflow_schema`, not `getGenomeAttribute` — the main.nf assignment was not detected; it changes nothing here because the asset is unused.

## Per-asset decisions

| Param | Nextflow role | Galaxy shape | Requiredness | Rebuild-on-absence | Disposition |
|---|---|---|---|---|---|
| `fasta` | template vestige; consumed by nothing | **not exposed** | n/a | n/a | dropped (no consumer) |
| `genome` | iGenomes key selector; consumed by nothing | **not exposed** (no data table introduced) | n/a | n/a | dropped (no consumer) |
| `igenomes_base`, `igenomes_ignore` | runtime/config control | not exposed | n/a | n/a | runtime control, excluded |

## Non-reference file params (for the interface Mold)

`multiqc_config`, `multiqc_logo`, `multiqc_methods_description` are optional report-configuration files, not reference data. They are left to nextflow-summary-to-galaxy-interface; this brief takes no position beyond noting they are not genome assets.

## iGenomes key disposition

`--genome` is not mapped to any Galaxy data table or `.loc`-keyed selector: there is nothing downstream to select a build for, and the mapping note forbids introducing new data tables.

## Open questions

- None blocking. If a future nf-core/demo release wires `fasta` into a process, re-run this Mold: the shape would be a single optional `data` input (`fasta`) with no rebuild step.
