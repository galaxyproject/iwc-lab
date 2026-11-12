# Nextflow → Galaxy reference-data brief — nf-core/ampliseq 3.1.0

Input: `<run>/summary-nextflow.json` (source `nf-core/ampliseq` @ b9bd579).
Classified per `nextflow-reference-data-classification`; Galaxy posture per `nextflow-to-galaxy-reference-data-mapping` (v1: explicit optional inputs, no dbkey/`.loc` tables, in-tool rebuild only where the asset is locally derivable).

## Classification

| Classification | Applies | Evidence |
|---|---|---|
| **Multi-DB pick-list (primary)** | yes | Six independent taxonomy branches — DADA2, QIIME2, SINTAX, VSEARCH-LCA, Kraken2, SIDLE — each with a `<tool>_ref_taxonomy` selector param and a `<tool>_ref_tax_custom` path override, each gated by `skip_taxonomy`/`skip_qiime*`/branch flags (`workflows/ampliseq.nf:172-452`). User picks 0..N. This is the funcscan shape the mapping note records as having **no worked Galaxy exemplar** — amplified here by a 144-key download catalog per branch (`conf/ref_databases.config`). |
| **Compute-if-missing aspect — NO (download-if-missing instead)** | variant | `reference_rebuilds[]` has 7 rules, but every guard is positive-form `"<selector> set && params.ref_taxonomy_storage"` and every builder is `DOWNLOAD_REFERENCE_<TOOL>` fetching from the catalog and running a `taxref_reformat_*.sh` script into the storage dir. Nothing is rebuilt from a user-supplied asset; **in-tool rebuild does not apply to any asset in this pipeline** — no database is derivable from any other input. Treat these as *acquire-from-catalog*, not rebuild. |
| **Coordinated bundle** | yes | Three coupled groups: pplace set (`pplace_tree` + `pplace_aln` + `pplace_model`, optional `pplace_taxonomy`, keyed to `pplace_sheet` rows); SIDLE-custom quartet (`sidle_ref_tax_custom` + `_seq_custom` + `_aln_custom` + `_tree_custom`); DADA2-custom pair (`dada_ref_tax_custom` + `dada_ref_tax_custom_sp`). Switching one member means switching the group. |
| Key-expanded bundle (iGenomes) | **no** | Zero `getGenomeAttribute` occurrences in the tree; no `params.genome`. |
| Single asset | no | — |
| Reference-producing | no | DOWNLOAD_REFERENCE_* outputs are a runtime cache (`params.ref_taxonomy_storage`), not a workflow product. |

## Per-asset disposition

v1 posture: one explicit optional Galaxy `data` input per asset. Selectors themselves are **not** surfaced as data (see obligations). Datatypes per the mapping table; `data` where Galaxy has no specific format.

### Taxonomy branches (pick-list; each branch = one optional input group)

| Source param | Galaxy input | Format | Notes |
|---|---|---|---|
| `dada_ref_tax_custom` | `dada_ref_tax_custom` | `data` | DADA2 reference taxonomy (assignTaxonomy training set). |
| `dada_ref_tax_custom_sp` | `dada_ref_tax_custom_sp` | `data` | Optional mate for species re-assignment; coupled to the row above. |
| `qiime_ref_tax_custom` | `qiime_ref_tax_custom` | `data` | Source accepts *one* string that is a tarball/dir **or two comma-separated paths** (`workflows/ampliseq.nf:388-396`). Galaxy has no comma-string affordance → split into two optional inputs (`qiime_ref_tax_custom` + `qiime_ref_tax_custom_2`) or accept single tarball/qza only. Recorded as obligation. |
| `kraken2_ref_tax_custom` | `kraken2_ref_tax_custom` | `data` (tgz) or directory | Kraken2 DBs are tens of GB; input docs must describe acquisition. Workflow cannot bundle payloads. |
| `sintax_ref_tax_custom` | `sintax_ref_tax_custom` | `fasta` | SINTAX-compatible taxonomy FASTA. |
| `vsearch_lca_ref_tax_custom` | `vsearch_lca_ref_tax_custom` | `fasta` | Same shape as SINTAX. |
| `sidle_ref_tax_custom` | `sidle_ref_tax_custom` | `data` (headerless .txt) | Member of SIDLE quartet; seq + aln members are `fasta`, tree member is a QIIME2 qza (`data`). All four travel together. |
| `sidle_ref_seq_custom` | `sidle_ref_seq_custom` | `fasta` | |
| `sidle_ref_aln_custom` | `sidle_ref_aln_custom` | `fasta` | |
| `sidle_ref_tree_custom` | `sidle_ref_tree_custom` | `data` (qza) | Catalog key adds `tree_qza` as a separate download (`DOWNLOAD_REFERENCE_SIDLE_TREE`). |
| `<tool>_ref_taxonomy` (6 selectors) | *(not exposed in v1)* | string | Free-text keys into the 144-entry catalog in `conf/ref_databases.config`; resolving them means workflow-tier download + per-DB reformat scripts. v1 exposes custom paths only; see `taxonomy-selector-catalog-no-carrier`. Confidence high that exposure requires either a data table (discouraged) or fetch steps per branch. |
| `ref_taxonomy_storage` | *(drop)* | directory | Cross-run download cache; stateful storage with no Galaxy carrier. See obligation. |

### Phylogenetic placement (pplace) coordinated bundle

| Source param | Galaxy input | Format | Notes |
|---|---|---|---|
| `pplace_tree` | `pplace_tree` | `newick` | Required-together with `pplace_aln` and `pplace_model`. |
| `pplace_aln` | `pplace_aln` | `fasta` | Reference sequences. |
| `pplace_model` | (string workflow input, not data) | — | e.g. `LG+F`; parameter, not asset. |
| `pplace_taxonomy` | `pplace_taxonomy` | tabular (`csv`/tsv) | Optional. |
| `pplace_sheet` | `pplace_sheet` | tsv | Config-style sheet naming targets/align methods per placement run; sheet-shaped but not sample-keyed — interface Mold owns its translation. |

Branch enablement in source: `run_pplace` plus "reference trees specified by the selected `--dada_ref_taxonomy`" — i.e. placement depends on the DADA2 catalog key carrying tree data. With selectors not exposed in v1, pplace enablement must key off the supplied custom inputs instead. Recorded as obligation (`pplace-bundle-required-together`).

### Non-reference path params (routed away, per asset_kind audit)

| Param | Disposition |
|---|---|
| `expected_sequences`, `expected_abundances`, `expected_profile` | Validation truth files for `EXPECTED_*` comparison processes — optional comparison inputs, not reference data. Route to interface (optional inputs) and test plan (they double as assertion fixtures). |
| `metadata` | Sample-metadata TSV consumed by QIIME2 sample-data merge — a second sheet-shaped input; interface Mold owns it. |
| `multiqc_config`, `report_abstract` | Config/text inputs for reporting; not biological references. |
| `sidle_ref_degenerates`, `sidle_ref_cleaning`, `pplace_alnmethod`, `expected_sequences_*` | Plain value params, not assets. |

## Rebuild-on-absence summary

**None of the reference assets supports in-tool rebuild.** Every taxonomy database comes from the external catalog (download + reformat script + citation/license metadata) or from a user path. The mapping note's "wrapper rebuilds the index when absent" posture has no application here; the correct v1 shape is: branch runs **only when** its explicit input is supplied (Galaxy optional-input + `when:`/pick gate), never rebuild. Index-style siblings the tools derive internally (e.g. Kraken2 hash tables inside a supplied DB) stay wrapper-internal.

## Decisions carried forward

1. Expose the six `*_ref_tax_custom` asset groups as explicit optional `data` inputs; do not expose selectors or run download steps in the translated workflow (v1 posture; recorded as ledger decision).
2. pplace inputs are four separate optional `data` inputs (not a `sample_sheet:record` bundle) — keeps v1 simple, coherence enforced by `when:` guards; the ≥4-coupled-inputs UX gap is a recorded mapping-note gap, not invented here.
3. `expected_*` truth files are interface inputs (optional) and test-plan assertion sources, not reference-data surface.

## Open questions (formalized in `open-requirements.ledger.yml`)

1. **Catalog exposure**: 144 curated DB names → URLs + reformat scripts + citations live only in `conf/ref_databases.config`. v1 drops them; is a later fetch-step tier (workflow-tier download) wanted for any single popular DB (e.g. SILVA)? → obligation `taxonomy-selector-catalog-no-carrier`.
2. **`ref_taxonomy_storage`** has no Galaxy equivalent (cross-run cache). Drop or force per-run re-acquisition. → obligation.
3. **QIIME2 custom two-path form**: split into two optional inputs vs. require tarball/qza only. → obligation.
4. **pplace enablement** was keyed off the DADA2 catalog key; with custom-input-only surface, re-key `when:` guards on supplied pplace inputs. → obligation.
5. Summary artifact note: `reference_assets[].used_by` attribution was populated for only 3 of 20 assets (DADA2/KRAKEN2 taxonomy WF); consuming-branch attribution above came from re-reading `workflows/ampliseq.nf` (branch `if` guards), not from the summary — a run-side summary limitation, flagged for the interface Mold.
