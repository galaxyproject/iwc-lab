# Galaxy data-flow brief — nf-core/demo 1.2.0

Source summary: `summary-nextflow.json` (primary workflow `DEMO`). Upstream briefs: `nextflow-galaxy-reference-data.md` (None), `nextflow-galaxy-interface.md`. Ledger: `open-requirements.ledger.yml`.
Not gxformat2; no Tool Shed ids resolved here.

## Granularity rationale

The source is one flat workflow (`DEMO`) with four processes and no pipeline subworkflows; plumbing (version collation, workflow summary, methods text) outweighs scientific work. Galaxy keeps one node per scientific process plus one explicit shape transform; the nf-core plumbing collapses away (Galaxy records versions/provenance natively — already a `dropped` ledger entry).

## Workflow inputs (from interface brief)

- `reads` — `list:paired_or_unpaired` of `fastqsanger.gz`.
- `skip_trim` — `boolean`, default `false`.
- `multiqc_title` — optional `string`.

### Element identifiers

One element per samplesheet **row** (interface decision). The `sample` column repeats in the source test sheet (`SAMPLE3_SE` × 2), so `sample` alone is not unique. Key each element as `<sample>_<run>` where `<run>` is the `fastq_1` basename with `.f(ast)q.gz` and a trailing `_R1`/`_1` mate tag stripped: `SAMPLE1_PE_sample1`, `SAMPLE2_PE_sample2`, `SAMPLE3_SE_sample1`, `SAMPLE3_SE_sample2`. Uniqueness comes from the run file name, which matches how the source itself names trimmed outputs (`${meta.id}_$(basename $f)` → `SAMPLE3_SE_sample1_R1.fastq.gz`). Mate position is carried by the inner `paired_or_unpaired` structure (`forward`/`reverse` vs `unpaired`), not by a positional `_1`/`_2` suffix — those are only mates for paired rows.

## Nodes

| # | Node | Source | Galaxy idiom | In shape | Out shape | Confidence |
|---|---|---|---|---|---|---|
| N1 | `flatten_reads` — split every element into its individual FASTQ files | implicit: source `fastqs.flatten()` in PIPELINE_INITIALISATION; FASTQC/SEQTK iterate files | **placeholder transformation** (collection flatten) | `reads` `list:paired_or_unpaired` | `list` of `fastqsanger.gz`, identifiers `<element>_<forward|reverse|unpaired>`-style (exact suffixes chosen by implementation) | medium — whether consumers could map over `paired_or_unpaired` directly is unverified; an explicit flatten is the safe shape |
| N2 | `fastqc` — per-file read QC | `FASTQC` (`ext.args --quiet`) | map-over | N1 `list` fastq | `html` list; raw-data list (`zip` or text) | high |
| N3 | `seqtk_trim` — Phred quality trimming per file (`seqtk trimfq`, default args) → gz FASTQ | `SEQTK_TRIM` | map-over + **inline `when:`** on `skip_trim` | N1 `list` fastq | `list` of `fastqsanger.gz` | high (tool), medium (output shape) |
| N4 | `cowpy` — render the fixed text "nf-core rules!" as ASCII-art cow | `COWPY` (no inputs, `ext.args` empty) | standalone source step (no data inputs) | — (text parameter "nf-core rules!") | `File` `txt` | high (semantics) |
| N5 | `multiqc` — aggregate FastQC results into one report | `MULTIQC` | **reduction** (whole list into one invocation) | N2 raw-data list (+ `multiqc_title`) | report `html`; stats tables | high (report), medium (stats shape) |

### Edges

| From | To | Via (source operators) | Galaxy wiring | Confidence |
|---|---|---|---|---|
| `reads` | N1 | `samplesheetToList → map → groupTuple → flatten` | direct | medium |
| N1 | N2 | `ch_samplesheet` direct | map-over list | high |
| N1 | N3 | `ch_samplesheet` direct, guard `!params.skip_trim` | map-over list; `when: $(!inputs.skip_trim)` with `skip_trim` connected as step input | high |
| `skip_trim` | N3 | `if (!params.skip_trim)` | `when` input | high |
| N2 (zip / raw data) | N5 | `FASTQC.out.zip.map{_meta,file->file}.mix(...).flatten().collect()` | whole collection into a multiple/collection input (reduction) | high |
| `multiqc_title` | N5 | `ext.args --title` | parameter connection | high |

Dropped inputs to MULTIQC: `ch_collated_versions`, `workflow_summary_mqc.yaml`, `methods_description_mqc.yaml`, custom config/logo (ledger: `software-versions-and-plots-not-exposed`, `multiqc-custom-config-not-exposed`). Effect: report lacks the nf-core "software versions" and "workflow summary" sections; FastQC sections unchanged.

## Conditional disposition

`!params.skip_trim` → **inline `when:` on N3**. One-step cascade, no source subworkflow boundary, and `SEQTK_TRIM.out.reads` has no downstream consumer — so no `pick_value` fan-in is needed; when skipped, `trimmed_reads` resolves to Galaxy's typed skipped/null output.

## Workflow outputs

| Label | Source node/output | Shape |
|---|---|---|
| `fastqc_html` | N2 html | `list` html |
| `fastqc_zip` | N2 raw data (checkpoint) | `list` |
| `trimmed_reads` | N3 | `list` `fastqsanger.gz` (skipped when `skip_trim`) |
| `cowpy_output` | N4 | `File` txt |
| `multiqc_report` | N5 report | `File` html |
| `multiqc_stats` | N5 stats | `File`/`list` tabular |

Shape change vs interface brief: `trimmed_reads` is a per-file `list` (the interface left `list:paired_or_unpaired` or per-file `list` open); per-file matches the source's file-wise trimming and published `fq/<id>/<prefix>_<basename>` naming.

## Unresolved tool needs (for discovery)

| Node | Need | Inputs → outputs |
|---|---|---|
| N2 | FastQC read QC | fastqsanger(.gz) → html + raw data usable by MultiQC |
| N3 | seqtk trimfq (quality trimming) | fastqsanger.gz → fastqsanger(.gz) |
| N4 | cowpy ASCII-art text renderer | string → txt |
| N5 | MultiQC with FastQC module and title option | collection of FastQC outputs → html + stats |

## Placeholder transformations

- N1 collection flatten (`list:paired_or_unpaired` → `list`). Implementation picks the built-in operation and identifier suffixes.

## Open questions

1. N1: confirm Galaxy's flatten behaviour for `paired_or_unpaired` inner elements (identifier suffixes), or map consumers directly if supported.
2. N3: seqtk trimfq output may be uncompressed in the Galaxy wrapper; source gzips. Datatype `fastqsanger` vs `fastqsanger.gz` affects md5 comparisons in tests.
3. N4: availability of a cowpy wrapper is for discovery to report; no judgement here.
4. N5: which FastQC output (zip vs text) the Galaxy MultiQC wrapper consumes; stats output shape (`multiqc-stats-output-shape`).
