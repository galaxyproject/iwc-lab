# nf-core/demo — Galaxy data-flow brief

Inputs read: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`, `open-requirements.ledger.yml`.

## Workflow inputs

- `reads`: `list:paired_or_unpaired` of `fastqsanger.gz`
- `skip_trim`: boolean, default false
- `multiqc_title`: optional text

## Element identifiers

The outer identifier is the sample sheet's `sample` value, which matches the NF `meta.id` used in `fastqc/<id>/` and `fq/<id>/`. `sample` can repeat: the test sheet has two `SAMPLE3_SE` rows, each a single-end run. A repeated sample is keyed `<sample>_run<k>`, where k is the 1-based row order within that sample, so each element stays unique per dataset. The `run` token is deliberate: a bare `_1`/`_2` suffix would read as mates, and these rows are unpaired. Inner identifiers are Galaxy's fixed `forward`/`reverse` for pairs and `unpaired` for singles.

Test sheet → Galaxy elements: `SAMPLE1_PE {forward, reverse}`, `SAMPLE2_PE {forward, reverse}`, `SAMPLE3_SE_run1 {unpaired}`, `SAMPLE3_SE_run2 {unpaired}`.

## Nodes

| id | Operation | Input shape | Output shape | Galaxy idiom | Source | Confidence |
|---|---|---|---|---|---|---|
| `fastqc` | Per-file read QC report (HTML + raw data archive) | `reads` `list:paired_or_unpaired` | `html`, `zip`/raw text, both `list:paired_or_unpaired` | map-over (single-dataset tool input over every leaf) | FASTQC | high |
| `seqtk_trim` | Quality end-trim each read file (seqtk trimfq, default args), gzip output | `reads` `list:paired_or_unpaired` | `list:paired_or_unpaired` `fastqsanger.gz` | map-over; inline step `when: skip_trim == false` | SEQTK_TRIM, guard `!params.skip_trim` | high |
| `cowpy` | Render fixed text "nf-core rules!" as ASCII art | none (constant text) | File `txt` | source-less step | COWPY | medium |
| `multiqc` | Aggregate FastQC results into one report, title = `multiqc_title` | `fastqc` raw-data output, `list:paired_or_unpaired` | `html` report + stats table (File) | reduction: whole collection into one multiple=true / repeat input | MULTIQC via `flatten().collect()` | high |

## Edges

| from | to | Shape before → after | Operators (NF) | Galaxy translation |
|---|---|---|---|---|
| `reads` | `fastqc` | `list:paired_or_unpaired` → same | none | direct map-over |
| `reads` | `seqtk_trim` | `list:paired_or_unpaired` → same | none | direct map-over, gated |
| `fastqc` (zip/raw data) | `multiqc` | `list:paired_or_unpaired` → File | `map{drop meta}`, `mix`, `flatten`, `collect`, `map{tuple}` | reduction; `mix` with versions/summary YAMLs not carried |

## Conditional disposition

`!params.skip_trim` gates only `seqtk_trim`, and nothing consumes its output. Use an **inline tool-step `when:`** driven by `skip_trim`: one step, no rejoin, so no `pick_value` and no subworkflow. `trimmed_reads` becomes an optional workflow output.

## Placeholder transformations

None required. The map-over keeps the nested structure on its own, and MultiQC reduces the collection in one input. If the chosen MultiQC wrapper cannot take a nested `list:paired_or_unpaired` directly, insert a `flatten collection` step (`list:paired_or_unpaired` → `list`) before `multiqc`. Confidence medium; implementation decides.

## Not carried (Nextflow-runtime plumbing)

- `ch_collated_versions` (topic `versions` → `softwareVersionsToYAML` → `collectFile`): Galaxy records tool versions per job.
- `ch_workflow_summary` (`paramsSummaryMultiqc`) and `ch_methods_description` (`methodsDescriptionText`): NF run-introspection YAMLs fed to MultiQC. Galaxy has no equivalent.

Both are recorded in the ledger as dropped.

## Unresolved tool needs

| node | Needs a tool that… | Inputs | Outputs |
|---|---|---|---|
| `fastqc` | runs FastQC on one FASTQ(.gz) | 1 × fastqsanger.gz | html report; raw data (zip or txt) that MultiQC can parse |
| `seqtk_trim` | runs `seqtk trimfq` with default quality trimming | 1 × fastqsanger.gz | fastqsanger(.gz) |
| `cowpy` | renders a given text string as cowsay-style ASCII art, no data input | text parameter "nf-core rules!" | txt |
| `multiqc` | aggregates FastQC outputs with an optional report title | multiple FastQC raw-data datasets | html report, general-stats table |

## Handoff notes

- Template: four tool steps plus three inputs. `seqtk_trim` carries `when:`. The workflow outputs are those listed in the interface brief.
- Exemplar comparison: look for IWC QC workflows with FastQC → MultiQC map/reduce over read collections.

## Open questions

- The FastQC raw-data output datatype must match what the MultiQC wrapper's FastQC module accepts (e.g. `txt` raw data vs `zip`). Implementation settles it.
- `cowpy` tool availability is unknown. Discovery decides (see ledger `cowpy-galaxy-tool-unknown`).
