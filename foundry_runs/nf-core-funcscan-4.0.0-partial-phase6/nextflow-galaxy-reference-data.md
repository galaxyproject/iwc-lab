# Reference-data brief — nf-core/funcscan → Galaxy

- **Run:** `funcscan-run1` · phase 2 (`nextflow-summary-to-galaxy-reference-data`)
- **Source:** `nf-core/funcscan` 4.0.0, commit `aee3dc965eb0c77267435544dda30da858763913`
- **Reads:** `summary-nextflow.json` (220 params, 28 `reference_assets[]` rows, 11 `reference_rebuilds[]` rules)
- **Consumers:** `nextflow-summary-to-galaxy-interface` (input list), `nextflow-summary-to-galaxy-data-flow` (edges), `nextflow-summary-to-galaxy-template` (gxformat2 skeleton)
- **Carried ledger:** `open-requirements.ledger.yml` (this phase starts it — phase 1 does not carry the ledger)

## 1. Classification

Against `nextflow-reference-data-classification`, funcscan matches **multi-DB pick-list** as
its primary kind, overlaid with **indexes with rebuild fallback (compute-if-missing)**.
The taxonomy names funcscan as the pick-list exemplar, and the source bears that out:
five `run_*` stage switches (`run_amp_screening`, `run_arg_screening`, `run_bgc_screening`,
`run_cazyme_screening`, `run_taxa_classification`, plus `run_protein_annotation`) and
twelve per-tool `*_skip_*` / `*_run_*` toggles, with a separate database param per tool.

| Kind | Applies | Evidence |
|---|---|---|
| None | no | 28 asset rows |
| Reference-producing | no | DB pulls are intermediate; the product is screening tables + MultiQC |
| Single asset | no | many independent assets, no coupling |
| Coordinated bundle | no | no shared section, no coupled switching; each DB belongs to one tool |
| Key-expanded bundle (iGenomes) | **no** — see §2 | zero `getGenomeAttribute`, no `conf/igenomes.config`, no `genome` param |
| Compute-if-missing | **yes** | 11 rebuild rules (§4.1) |
| **Multi-DB pick-list** | **primary** | per-tool DB param + per-tool skip flag |
| Parallel bundles + cohort data | no | no cohort/panel asset with no rebuild path |

The compute-if-missing overlay is an *aspect*, not a second surface: the same 11 params that
are optional user inputs are the 11 the pipeline can build for itself.

## 2. iGenomes / key-expanded disposition

**Nothing to resolve.** `getGenomeAttribute`, `igenomes`, and a `genome` param appear nowhere
in `main.nf`, `nextflow.config`, `conf/`, or `nextflow_schema.json`; every `params[]` entry in
the summary carries `source_kind: nextflow_schema`, with no config-synthesised params. The
Galaxy surface therefore starts at the per-asset params as declared — there is no key to
expand and no iGenomes key disposition to record per asset.

## 3. Galaxy posture adopted

Per `nextflow-to-galaxy-reference-data-mapping`, v1:

1. **No `dbkey` and no `from_data_table`/`.loc` tables.** Every funcscan database would need
   an admin install and a `tool_data_table_conf.xml` edit; a translated workflow must run on a
   stock Galaxy with user-uploaded inputs.
2. **One optional explicit workflow input per database**, `required: false`, matching the
   source's own `if (params.X_db) { use } else { build }` shape.
3. **Prefer wrapper-side rebuild** over a workflow-tier build step — with one deviation this
   pipeline forces, in §6.
4. **No bundled reference data in the workflow file**; a user who already holds a database
   uploads it and points the input at it. Input documentation must say where each DB comes from.
5. **Specific datatype when one exists, otherwise a documented fallback** (§7).

funcscan is the case the mapping note lists as an explicit representation gap — *"Multi-DB
pick-list (funcscan-style) translation pattern … no worked Galaxy exemplar"*. §8 records it as
a ledger obligation rather than inventing a shape for it.

## 4. Per-asset disposition

### 4.1 The eleven rebuild-capable databases

`reference_rebuilds[]` in the summary is the source of truth for these; each row's guard and
line number is there. `Multiplicity` is how often the consumer tool runs: **per-sample** means
the consumer takes a per-sample channel in the source, so a Galaxy step maps over the input
collection; **once** means the input is `.collect()`-ed first.

| Param (optional input) | Consumer | Multiplicity | Builder when absent | Rebuild mechanism | Builder is the tool itself? |
|---|---|---|---|---|---|
| `amp_ampcombi_db` | `AMPCOMBI2_PARSETABLES` | per-sample | `AMP_DATABASE_DOWNLOAD` | `bin/ampcombi_download.py --database_id …` (DRAMP / APD / UniRef100), vendored from upstream AMPcombi | **no** — pipeline-vendored script |
| `annotation_bakta_db` | `BAKTA_BAKTA` | per-sample | `BAKTA_BAKTADBDOWNLOAD` | `bakta_db download`, full/light chosen by `annotation_bakta_db_downloadtype` | yes |
| `arg_amrfinderplus_db` | `AMRFINDERPLUS_RUN` | per-sample | `AMRFINDERPLUS_UPDATE` | `amrfinder_update -d amrfinderdb` + re-tar | yes |
| `arg_rgi_db` | `RGI_MAIN` | per-sample | `UNTAR_CARD` → `RGI_CARDANNOTATION` | fetch of hard-coded `https://card.mcmaster.ca/latest/data`, untar, then `rgi cardannotation` | partly — the fetch is a plain download, only the processing is the tool |
| `arg_deeparg_db` | `DEEPARG_PREDICT` | per-sample | `DEEPARG_DOWNLOADDATA` | `deeparg downloaddata` | yes |
| `bgc_antismash_db` | `ANTISMASH_ANTISMASH` | per-sample | `ANTISMASH_ANTISMASHDOWNLOADDATABASES` | `download-antismash-databases --database-dir` | yes |
| `bgc_bigslice_db` | `BIGSLICE_BIGSLICE` | **once** | `BIGSLICE_DOWNLOADDB` | `download_bigslice_hmmdb` shipped in the BiG-SLiCE env (`cp $(which …)`) | yes (in-env script) |
| `bgc_deepbgc_db` | `DEEPBGC_PIPELINE` | per-sample | `DEEPBGC_DOWNLOAD` | `deepbgc download` | yes |
| `cazyme_dbcan_db` | `RUNDBCAN_CAZYMEANNOTATION` | per-sample | `RUNDBCAN_DATABASE` | `run_dbcan database --db_dir dbcan_db --aws_s3` | yes |
| `protein_annotation_interproscan_db` | `INTERPROSCAN` | per-sample | `INTERPROSCAN_DATABASE` | `curl -L $protein_annotation_interproscan_db_url` + `tar -xzf` | **no** — plain curl of a URL the user can repoint |
| `taxa_classification_mmseqs_db` | `MMSEQS_TAXONOMY` | per-sample | `MMSEQS_DATABASES` | `mmseqs databases <db_id> …` | yes |

Galaxy disposition for all eleven: **optional workflow input**, and the rebuild lives with the
consumer wrapper where the tool can do it itself. §6 records where that lands as an explicit
input or a workflow-tier step instead.

Two supply-side shapes the interface must not lose:

- `bgc_antismash_db` accepts **either** a `.tar.gz` (the source pipes it through
  `UNTAR_ANTISMASHDB`) **or** an already-extracted directory (`bgc.nf:39-44`). One input, two
  accepted shapes.
- `arg_rgi_db` is *not* simply "the database": whatever is supplied is passed through
  `RGI_CARDANNOTATION` unless its name already contains `card_database_processed`
  (`arg.nf:105-117`). A Galaxy user can supply either the raw or the processed CARD form.

### 4.2 Assets with no builder — user-supplied or nothing

| Param | Consumer | Behaviour when unset | Galaxy disposition |
|---|---|---|---|
| `amp_hmmsearch_models` | AMP `HMMSEARCH` | `error('[nf-core/funcscan] error: HMM model files not found …')` when `amp_run_hmmsearch` is on (`amp.nf:72-77`) | **conditionally required** input — see obligation `hmm-models-required-when-branch-enabled` |
| `bgc_hmmsearch_models` | BGC `HMMSEARCH` | same hard `error()` when `bgc_run_hmmsearch` is on (`bgc.nf:153-158`) | as above |
| `annotation_bakta_hmms` | `BAKTA_BAKTA` | `ch_bakta_hmm = []` — bakta runs without trusted HMMs (`annotation.nf:96-101`) | plain optional input |
| `arg_abricate_db` | `ABRICATE_RUN` | `params.arg_abricate_db ? file(…) : []`, so abricate's own bundled DBs are used (`arg.nf:172`) | optional *override* input |

### 4.3 Curated selectors — these are **not** data inputs

They appear in `reference_assets[]` because of their names, but each is a short string the tool
consumes, so they belong in the Galaxy interface as select/multi-select options, never as
`data` inputs:

| Param | Values | Note |
|---|---|---|
| `amp_ampcombi_db_id` | `DRAMP` / `APD` / `UniRef100` (closed enum) | also the builder's argument — the pick names what gets downloaded |
| `annotation_bakta_db_downloadtype` | `full` / `light` (closed enum) | only meaningful when `annotation_bakta_db` is absent |
| `arg_abricate_db_id` | free string, default `ncbi`; `ncbi`/`resfinder`/`argannot`/`megares` are special-cased at `arg.nf:180` | closed list only for the bundled DBs |
| `arg_fargene_hmmmodel` | comma-separated list of 10 bundled model names | multi-select over models that ship in the container |
| `arg_rgi_data` | `NA` / `wgs` / `plasmid` / `chromosome` | summary mis-files this as `tool_reference_database`; it is an input-datatype flag |
| `arg_deeparg_model` | `LS` / `SS` | as above |
| `amp_ampir_model` | `precursor` / `mature` | as above |
| `taxa_classification_mmseqs_db_id` | free string, default `Kalamari`; **no enum** | needs an option list the source does not carry — obligation `mmseqs-db-id-has-no-option-list` |
| `protein_annotation_interproscan_db_url` | URL string, default pinned to `interproscan-5.72-103.0-64-bit.tar.gz` | plain text input, not data; it *selects which* DB the builder fetches |

### 4.4 Reference data that rides inside the container

AMPlify, ampir, Macrel, GECCO, argNorm, ABRicate's default databases and fARGene expose **no**
database param at all — only `*_skip_*` flags — because their reference data is installed inside
the conda env / container their modules declare. That is invisible in `reference_assets[]` (no
param to list) and is where most of funcscan's actual reference-data volume sits. In Galaxy the
same fact must hold: the wrapper must ship the same env, or the database becomes an input the
user never had to supply in Nextflow. Recorded as obligation `container-bundled-databases`.

### 4.5 Path params that are not reference data

| Param | Why it is out of the reference surface |
|---|---|
| `pipelines_testdata_base_path` | base URL/dir for the pipeline's own nf-test fixtures, referenced only from `conf/test*.config`; recorded as a `dropped` ledger entry |
| `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` | optional MultiQC config assets; when unset the pipeline falls back to `assets/multiqc_config.yml` and `assets/methods_description_template.yml` inside the repo. In Galaxy: omit the input and let the wrapper's bundled config stand |

## 5. What "pick 0..N" costs the interface

Each stage toggle gates a group of optional inputs, so the honest Galaxy surface is
`1 samplesheet + the toggles + up to 11 optional database inputs + 9 selector options`, where
each database input is only *meaningful* under its toggle (`bgc_bigslice_db` under
`bgc_run_bigslice`, `taxa_classification_mmseqs_db` under `run_taxa_classification`,
`annotation_bakta_db` under `annotation_tool == bakta`, …). Galaxy has no
"required only when X" affordance to express that, which is the same weakness the mapping note
flags for cohort data. The brief's position: expose everything optional, state the gating in
each input's help text, and let the conditional `when:` expressions on the workflow steps carry
the actual gating. Ledger: `multi-db-pick-list-no-galaxy-exemplar`.

## 6. Rebuild placement — the one deviation from the v1 default

The mapping note's own deviation rule is *"rebuild more than ~3 times → workflow-tier step;
below → in-tool"*. Ten of the eleven consumers here are **per-sample** steps: in Galaxy they run
as one job per input dataset, so a wrapper that rebuilds when no database was supplied re-pulls
a full public database once **per sample**, not once per workflow. Only `BIGSLICE_BIGSLICE`
takes a `.collect()`-ed input and would rebuild once.

This is also the case the note's "Index sharing across siblings" clause covers in reverse: the
source itself separates the download from the analysis precisely so it happens once
(`AMRFINDERPLUS_UPDATE`, `BAKTA_BAKTADBDOWNLOAD`, … are standalone processes whose output is
`first()`-ed and broadcast to every sample).

**Decision.** For the ten per-sample consumers the reference-data surface is an explicit optional
workflow input, and the workflow must not rely on per-job wrapper rebuild for them. Two admissible
realisations, to be settled by `discover-shed-tool` / `compare-against-iwc-exemplar` against what
the corpus actually wraps:

1. user supplies the database → straight into the consumer step; or
2. user does not → a **single** workflow-tier fetch/build step (mirroring the source's own builder
   process) whose output feeds every sample.

`bgc_bigslice_db` keeps the in-tool/one-shot default, being a single invocation.

Whether the chosen Galaxy wrapper for each consumer actually supports
`no database supplied → build one` cannot be verified from this bundle; the mapping note names
that as an open discovery gap. Recorded as `wrapper-rebuild-capability-unverified`. Two builders
are additionally *not* the tool's own capability and therefore cannot be inherited from a wrapper
at all: `AMP_DATABASE_DOWNLOAD` (pipeline-vendored `bin/ampcombi_download.py`) and
`INTERPROSCAN_DATABASE` (curl + untar of a URL). If those rebuilds are wanted in Galaxy they must
be a workflow-tier step or an authored wrapper behaviour — this brief does not assume either.

## 7. Datatypes

`summary-nextflow.json` records `format_hint` for almost none of these: funcscan declares
`format` on `input`, `outdir` and `multiqc_config` only, so path-ness for every database is
name- and usage-derived. Known mappings and gaps:

| Asset shape | Galaxy `format` | Basis |
|---|---|---|
| HMM model files (`amp_hmmsearch_models`, `bgc_hmmsearch_models`, `annotation_bakta_hmms`) | `hmm3` | mapping note lists HMMER profile types |
| AMP reference sequences (`amp_ampcombi_db` after download) | `fasta` at best; the builder emits a **directory** `amp_<id>_database` | directory wins, see below |
| MMseqs2 database, antiSMASH db dir, BiG-SLiCE `bigslice-models/`, dbCAN `dbcan_db`, DeepARG / DeepBGC / bakta / AMRFinderPlus databases | **no specific datatype** — all are multi-file directories or tarballs | fall back per the note: `data`/`directory` plus documentation |

The unresolved part is real, not a gap in this brief's nerve: a Galaxy *workflow input* of type
`directory`, a zipped single dataset unpacked by a first step, and a `multiple: true` list of
files are three different shapes with different consequences for what a wrapper can accept, and
neither packaged note picks one for reference data. Provisional default, marked low-confidence:
**one uploaded archive dataset per database, documented as "upload the tarball/zip as-is"**,
because that is exactly the shape the source's own builders produce and consume. Settled at the
corpus-comparison step. Ledger: `db-directory-input-shape-unsettled`.

No asset size is recorded anywhere in the source, so the brief cannot say how big these are —
only that every builder is a network pull of a full public database. Measuring before recommending
"just upload it" on a real instance: obligation `db-asset-sizes-unmeasured`.

## 8. Open obligations (carried into `open-requirements.ledger.yml`)

| id | kind | what the next phase must settle |
|---|---|---|
| `db-directory-input-shape-unsettled` | gap | directory / archive / file-list shape for the 11 DB inputs |
| `wrapper-rebuild-capability-unverified` | gap | which of the 11 consumers' Galaxy wrappers can build on absence |
| `multi-db-pick-list-no-galaxy-exemplar` | gap | the pick-list input/conditional shape; anchor to an IWC exemplar if one exists |
| `container-bundled-databases` | gap | AMPlify / ampir / Macrel / GECCO / argNorm / ABRicate-default / fARGene data must ride in the wrapper env or become inputs |
| `hmm-models-required-when-branch-enabled` | gap | conditional-required expression for the two HMM-search inputs |
| `mmseqs-db-id-has-no-option-list` | gap | option list for a free-string DB selector feeding `mmseqs databases` |
| `db-asset-sizes-unmeasured` | gap | sizes, before upload guidance is written |
| `testdata-base-path-not-carried` | dropped | `pipelines_testdata_base_path` deliberately out of the Galaxy surface |

## 9. Feedback recorded

Four ledger entries in `foundry-feedback.ledger.yml` came out of producing this brief:
`reference-rebuild-asset-param-fk-is-prose-only-so-a-fabricated-binding-validates` (major),
`rebuild-guard-field-has-no-way-to-say-derived-or-absent` (minor),
`rebuild-detector-blind-to-aliased-multistep-and-url-sourced-builders` (major), and
`reference-asset-kind-is-free-form-while-the-mold-documents-a-closed-list` (minor).
