# Galaxy data-flow brief — nf-core/demo

Source: `nf-core/demo` @ `671a0726` (v1.2.0). Inputs: `summary-nextflow.json`, `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`.

Scope: `workflow DEMO` (`workflows/demo.nf`) only. The two utility subworkflows (`PIPELINE_INITIALISATION`, `PIPELINE_COMPLETION`) are template plumbing with no Galaxy counterpart and are dropped.

## Abstract nodes

| id | operation | inputs (shape) | outputs (shape) | confidence | evidence |
|---|---|---|---|---|---|
| `in_samples` | workflow input | — | `list:paired_or_unpaired` of FASTQ | high | interface brief |
| `fastqc` | per-sample read QC | `samples` (`list:paired_or_unpaired`) | `fastqc_html` (`paired_or_unpaired` of `html`), `fastqc_zip` (`paired_or_unpaired` of `zip`) | high | `FASTQC(ch_samplesheet)`, outputs `html`, `zip` |
| `trim` | per-sample read trimming, gated | `samples` (`list:paired_or_unpaired`) | `trimmed_reads` (`paired_or_unpaired` of fastq) | high | `SEQTK_TRIM(ch_samplesheet)`, `when: !params.skip_trim` |
| `cowpy` | fixed text artifact | — | `cowpy_text` (`txt`, `File`) | high | `COWPY()` with no inputs; local module |
| `flatten_html` | shape change: de-nest map-over output | `fastqc_html` (`paired_or_unpaired` of `html`) | `fastqc_html_flat` (`list` of `html`) | medium | see *Placeholder transformations* |
| `flatten_zip` | shape change: de-nest for the MultiQC fan-in | `fastqc_zip` (`paired_or_unpaired` of `zip`) | `fastqc_zip_flat` (`list` of `zip`) | medium | see *Placeholder transformations* |
| `multiqc` | aggregate all per-sample QC reports into one report | `fastqc_zip_flat` (`list` of `zip`), `multiqc_config` (`yml`, optional) | `multiqc_report` (`html`, `File`) | high | `MULTIQC(ch_multiqc_files.flatten().collect().map{...})` |

## Edges

```
in_samples ─┬─> fastqc ─┬─> fastqc_html ─> flatten_html ─> [output fastqc_html]
            │           └─> fastqc_zip  ─> flatten_zip  ─> multiqc ─> [output multiqc_report]
            └─> trim    ─────────────────────────────────> [output trimmed_reads]
cowpy ─────────────────────────────────────────────────────> [output cowpy_text]
multiqc_config ────────────────────────────────────────────> multiqc
```

Map-over: `fastqc` and `trim` are mapped over `in_samples` (Galaxy implicit map of a single-dataset input over a collection). `cowpy` runs once. `multiqc` runs once and reduces the flattened list.

## Collection decisions

- **Map-over, not reduction.** `FASTQC`/`SEQTK_TRIM` are per-sample in the source (`ch_samplesheet` is a repeated `tuple(meta, reads)` with a one-element list per row, normalized through `samplesheetToList`). Galaxy expresses this by mapping the tool over the `list:paired_or_unpaired` input.
- **No join/synchronize steps.** Every downstream consumer takes the whole collection; nothing zips per-sample outputs back together. `meta.id` is only used for publish paths, which Galaxy replaces with element identifiers.
- **Element identifiers.** The source sample name (`sample` column → `meta.id`) is the only uniqueness key; the test rows (`SAMPLE1_PE`, `SAMPLE2_PE`, `SAMPLE3_SE`) are unique. Galaxy element identifier = sample name. No positional `_1`/`_2` suffix is used to build identifiers, so no mate-detection trap.
- **MultiQC fan-in is a reduction over `fastqc_zip` only.** The source's `ch_multiqc_files` also carries `versions.yml`, `workflow_summary_mqc.yaml`, and `methods_description_mqc.yaml`; those are nf-core reporting plumbing (see *Dropped*), not per-sample data. The Galaxy MultiQC step receives only the flat zip list plus the optional config.

## Placeholder transformations

| id | need | candidate idiom | confidence |
|---|---|---|---|
| `flatten_html` | `fastqc_html` exposed as a flat `list` rather than a `paired_or_unpaired`-nested collection | `__FLATTEN__` (or `__UNZIP_COLLECTION__` then `__FLATTEN__` if typed-name nesting blocks it) | medium |
| `flatten_zip` | MultiQC consumes a flat `list` of per-sample zips | same as above | medium |

Rationale: Galaxy mapping a single-dataset input over a `paired_or_unpaired` collection mirrors the outer shape, so the tool outputs stay nested. Both the published `fastqc_html` output and the MultiQC input want a flat list. If `__FLATTEN__` refuses `paired_or_unpaired`, unzip into a `list` of pairs, flatten, and — for the output — keep mate slots or select the html by extension with `__APPLY_RULES__`/filter. Resolve during implementation; this is the only shape-changing step in the workflow.

## Conditional disposition

`workflow.conditionals[]` has one entry: guard `!params.skip_trim`, `affects: [SEQTK_TRIM]`.

**Inline `when:` on the `trim` step**, gated on the `skip_trim` boolean input (expression `!(inputs.skip_trim)`).

Rationale: the cascade is one step; the source does not put SEQTK_TRIM in a subworkflow; the only consumer of `trimmed_reads` is the workflow output, so there is no fan-in to reconcile and no need for `pick_value`. Wrapping a single tool step in a subworkflow would add boundary wiring for nothing.

## Galaxy tool needs

| node | what the tool must do | input shape | output shape |
|---|---|---|---|
| `fastqc` | compute FastQC HTML + zip per FASTQ | one FASTQ (mapped) | `html`, `zip` |
| `trim` | trim FASTQ reads (`seqtk trim`) | one FASTQ (mapped) | FASTQ |
| `cowpy` | write the cowpy ASCII-art text artifact | none | `txt` |
| `multiqc` | run MultiQC over a list of FastQC zips; optional config; single HTML report | `list` of `zip`, optional `yml` | `html` |

`cowpy` is `modules/local/`, not nf-core-wrapped, and the Galaxy corpus is unlikely to carry it; discovery decides whether it is found, authored, or dropped. This brief does not adjudicate that.

## Dropped

| source unit | reason |
|---|---|
| `versions.yml` collation (`softwareVersionsToYAML`, versions topic) | nf-core reporting plumbing; Galaxy tools report their own versions |
| `workflow_summary_mqc.yaml`, `methods_description_mqc.yaml` | MultiQC report decoration generated from nf-core config |
| `PIPELINE_INITIALISATION` / `PIPELINE_COMPLETION` | template utility subworkflows: params validation, completion email, `pipeline_info` |
| `FASTQC.out.zip` publication | not published by `conf/modules.config` (pattern `*.{html,json}`); still consumed by MultiQC |
| `params.multiqc_logo`, `params.multiqc_methods_description` | report cosmetics with no Galaxy wrapper input |

## Confidence and open questions

- High confidence on nodes, edges, and map-over/reduction choices: the pipeline's data flow is a fan-out to two per-sample tools plus one reduction.
- Medium confidence on the two flatten transforms (Galaxy collection nesting rules for `paired_or_unpaired`) — the only real translation risk in this workflow.
- Open question: whether the Galaxy `cowpy` tool exists; if not, the output is dropped or authored (routing belongs to discovery).
- Open question: MultiQC wrapper input shape — does it accept a flat `list` of zips directly (preferred) or require a nested collection?

## Revision after IWC exemplar comparison (phase 5)

`compare-against-iwc-exemplar` found the flatten pattern used by `transcriptomics/rnaseq-pe`: `__FLATTEN__` the **input** collection once (`join_identifier: "_"`), then map per-file steps over the resulting flat list. That supersedes the `flatten_html` / `flatten_zip` placeholder transforms above:

- `in_samples` (`list:paired_or_unpaired`) → `flatten_inputs` (`list` of FASTQ, identifiers `SAMPLE_1`/`SAMPLE_2`)
- `fastqc`, `trim`, and the MultiQC input all take the flat list; no output flattening is needed.
- `trimmed_reads` is exposed as a flat `list`, not `paired_or_unpaired`.

See `iwc-comparison-notes.md` for the evidence. The node table above is left as written for the audit trail.
