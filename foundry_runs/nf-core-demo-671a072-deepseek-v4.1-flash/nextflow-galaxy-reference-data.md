# Reference-data brief — nf-core/demo → Galaxy

Source: `nf-core/demo` @ `671a0726cb489b22636d90b7c7352baed473790d` (v1.2.0), MIT.
Input artifact: `summary-nextflow.json`.

## Classification

**None.** The pipeline consumes no reference data.

Evidence:

- `summary-nextflow.json` → `reference_assets[]` holds exactly one entry, `fasta`, with `required: false` and **`used_by: []`** — no process or subworkflow consumes it.
- `reference_rebuilds[]` is empty.
- `workflow DEMO` (`workflows/demo.nf`) takes only `ch_samplesheet`, `multiqc_config`, `multiqc_logo`, `multiqc_methods_description`, `outdir`. No reference take-slot exists.
- The only reference-looking parameters (`--genome`, `--fasta`, `--igenomes_*`) are inherited from the nf-core template: `main.nf:29` assigns `params.fasta = getGenomeAttribute('fasta')`, and `conf/igenomes.config` is included unless `igenomes_ignore`. They are never read by FASTQC, SEQTK_TRIM, COWPY, or MULTIQC.

This is *single asset declared but unused*, not *single asset*. The template's iGenomes key-expansion machinery is present but dead here.

Caveat on the summary: `params[].source_kind` reports `nextflow_schema` for `fasta` rather than `getGenomeAttribute`, so the key-expanded-bundle signal the note relies on is not visible in this artifact; the conclusion above comes from `reference_assets[].used_by` and the workflow body. See the feedback ledger entry `fasta-getgenomeattribute-override-lost`.

## Per-asset disposition

| Nextflow param | Asset kind | Consumed? | Galaxy disposition |
|---|---|---|---|
| `fasta` | fasta | no | **Not exposed.** No workflow input; nothing to wire. |
| `genome` | iGenomes key (selector) | no | **Not exposed.** Do not introduce a Galaxy genome `dbkey` selector or data table. |
| `igenomes_ignore`, `igenomes_base` | key-bundle controls | no | **Not exposed.** Runtime/config control only. |

No reference asset requires an explicit `data` input, no in-tool rebuild is needed, and no `dbkey` propagation applies.

## iGenomes key disposition

`--genome` is a template surface with no consumer in this pipeline. Per the v1 posture it is not translated: Galaxy data tables and `dbkey`-keyed cached lookups are discouraged, and there is no asset behind the key to look up. The Galaxy workflow should have no genome selector at all.

## Open questions

- None. The absence of reference-data consumption is settled by two independent signals (`used_by: []` and the `DEMO` take-block). No downstream phase needs a reference decision.
