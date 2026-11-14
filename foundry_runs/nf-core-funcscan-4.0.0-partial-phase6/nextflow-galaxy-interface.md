# Interface brief — nf-core/funcscan → Galaxy

- **Run:** `funcscan-run1` · phase 3 (`nextflow-summary-to-galaxy-interface`)
- **Source:** `nf-core/funcscan` 4.0.0, commit `aee3dc965eb0c77267435544dda30da858763913`
- **Reads:** `summary-nextflow.json` (220 params, 1 sample sheet, 55 processes, 14 subworkflows, 11 `reference_rebuilds[]`), `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`
- **Consumers:** `nextflow-summary-to-galaxy-data-flow` (edges + `when:`), `compare-against-iwc-exemplar`, `nextflow-summary-to-galaxy-template` (gxformat2 `inputs:`/`outputs:`), `nextflow-test-to-galaxy-test-plan`
- **Not this document:** the gxformat2 skeleton, step wiring, tool selection. Input *and* output choices only, with their evidence and losses.

## 1. Where 220 params land

The buckets are exhaustive and disjoint (verified over `params[]`; the same script produced these counts):

| Bucket | params | Galaxy disposition |
|---|---|---|
| Sample-sheet input | 1 | **4 collection inputs** (`input` fans out; §2) |
| Reference / annotation data | 15 | **15 optional `data` inputs** (§3) |
| Reference selectors | 9 | **8 `select`/`text` inputs**, 1 pinned (§4) |
| Workflow-shape controls | 27 | **25 inputs**, 2 pinned (§5) |
| Output-set-altering save flags | 8 (of 141 tool knobs) | **8 `boolean` inputs** (§6) |
| MultiQC report config | 4 | **1 `text` input**, 3 omitted (§7) |
| Tool knobs | 133 | **pinned at source defaults**, not exposed (§8) |
| Runtime / publish / CLI / report transport | 23 | **excluded**, assessed in §9 |

**Totals: 58 params become 61 Galaxy workflow inputs; 136 are pinned at a fixed value; 26 are omitted.**

Two rules from `nextflow-params-to-galaxy-inputs` drive the split. First, classify by *effect*, not name — "if the param only changes `publishDir`, exclude; if it changes whether processes run, which tool is called, or which files a command creates, keep". Second, `params[].default` is now real (corrected in the phase-1 artifact: funcscan's `nextflow_schema.json` carries a default for only 91 of 220 params, 3 of its 102 booleans; all 220 are assigned in `nextflow.config`), so every input below carries the value Nextflow actually uses.

## 2. Primary input — one samplesheet, four Galaxy collections

`summary.sample_sheets[0]`: `param: input`, `discovered_via: nf-schema`, `schema_path: assets/schema_input.json`, materialised by `samplesheetToList` into `ch_samplesheet` (`required_runtime: true`). nf-schema root `required: ["sample", "fasta"]`.

| nf-schema column | kind | required | pattern / enum | Galaxy column or slot | Confidence |
|---|---|---|---|---|---|
| `sample` | meta | yes | `^\S+$` | `element_identifier` column | High |
| `fasta` | data | yes | `^\S+\.(fasta\|fas\|fna\|fa)(\.gz)?$` | element dataset, `fasta` / `fasta.gz` | High |
| `protein` | data | no | `^\S+\.(faa\|fasta)(\.gz)?$` | element dataset, `fasta` | High |
| `gbk` | data | no | `^\S+\.(gbk\|gbff)(\.gz)?$` | element dataset, **`genbank`** | **Low — see below** |
| `gff` | data | no | `^\S+\.(gff\|gff3)(\.gz)?$` | element dataset, `gff3` (or `gff`) | Medium |
| `gff_type` | meta | no | enum `NCBI_prok` / `prodigal` / `NCBI_euk` / `JGI` | `string` column + `restrictions` | High |

### 2.1 Chosen shape: four parallel `sample_sheet` collections, not one `sample_sheet:record`

`galaxy-sample-sheet-collections` maps "heterogeneous typed per-row artifacts" to `sample_sheet:record`, and on its face funcscan's row is exactly that. Three facts in the source rule the variant out here:

1. **Three of the four path columns are per-row optional.** nf-schema requires only `sample` + `fasta`, with `dependentRequired: {protein: [gbk], gbk: [protein], gff: [protein]}`. Valid rows are therefore `{fasta}`, `{fasta, protein, gbk}`, or `{fasta, protein, gbk, gff}` — the *same row shape is not fixed*. A Galaxy `record` has a fixed named member set for every element, so `sample_sheet:record` would force every row to carry all four datasets and make the fasta-only row — the common case — unrepresentable.
2. **`record` is the one variant with `allow_implicit_mapping: False`.** Every mapped step would need an explicit record-slot extraction first, against a pipeline whose per-sample fan-out is exactly what implicit mapping is for.
3. **The source itself splits the row apart.** `ch_prepped_input` is a `multiMap` into `fastas | faas | gffs | gbks`, and each consumer takes only the slot stream it needs (`ch_prepped_input.fastas → AMP/ARG/TAXA_CLASS`, `.faas → CAZYME/AMP/ARG/BGC`, `.gffs → CAZYME`, `.gbks → AMP`). Separate per-slot collections mirror the existing structure instead of fighting it.

So:

| Galaxy input id | collection_type | required | columns |
|---|---|---|---|
| `input_fasta` | `sample_sheet` | **yes** | `sample` → `element_identifier` |
| `input_protein` | `sample_sheet` | no | `sample` → `element_identifier` |
| `input_gbk` | `sample_sheet` | no | `sample` → `element_identifier` |
| `input_gff` | `sample_sheet` | no | `sample` → `element_identifier`; `gff_type` → `string` + `restrictions` |

`gff_type` travels on the GFF sheet, not the FASTA sheet, because that is what it describes: it is passed as `val(gff_type)` into `RUNDBCAN_EASYCGC`/`RUNDBCAN_EASYSUBSTRATE` (`input_gff, val(gff_type)`).

Costs of this choice, all carried to the ledger rather than hidden:

- **Row coupling is unexpressible.** `protein` ⟺ `gbk` and `gff` → `protein` cannot be stated across four independent collections. A user may supply `protein` for sample A and `gbk` for sample B and nothing rejects it. The source's `dependentRequired` becomes prose in the input help. Ledger: `samplesheet-row-coupling-unexpressible`.
- **Identifier sync replaces schema validation.** The three optional sheets must align with `input_fasta` by `element_identifier`. Galaxy can dot-product structurally identical sample sheets, but nothing enforces the alignment the way one sheet with per-row slots would. Data-flow owns the join/zip steps.
- **`uniqueItems: true` on the sheet has no Galaxy equivalent** — duplicate rows are rejected by nf-schema and silently accepted here. Prose note.
- **Sample-ID alphabet silently narrows.** nf-schema accepts `^\S+$`; Galaxy restricts sample-sheet strings and column names to `[\w\-_ ?]*`. An ID valid in Nextflow (`SAMPLE[1]`, `a/b`) is rejected here. Tightening, not loss, but it invalidates sheets that pass in Nextflow today. Ledger: `sample-id-alphabet-narrowed`.
- **Output side does not propagate `column_definitions`.** Anything downstream that still needs `gff_type` must re-attach it; the mapping note says carry-forward is explicit. Flagged for phase 4.

**Alternative for phase 5 to test:** one `sample_sheet:record` with all four slots required, if the corpus shows a workflow that carries optional record slots or if a placeholder-dataset idiom is accepted practice. Recorded as `samplesheet-per-row-optional-slots`.

### 2.2 The `gbk` datatype

`nextflow-path-glob-to-galaxy-datatype`'s core table covers `.fa*/`, `.gff*/`, `.gtf`, `.vcf`, `.bed`, `.bam`, archives — and has **no GenBank/EMBL row**, while funcscan takes `gbk`/`gbff` in, and `PROKKA` (`.gbk`), `BAKTA_BAKTA` (`.gbff`), `PYRODIGAL`/`GUNZIP_PRODIGAL_GBK` and GECCO (`gbk` convert mode) all emit it. `genbank` is asserted from Galaxy's registered datatypes, not from the note: **low confidence**, and it is an input *slot* as well as an output, so a wrong guess is visible to users. Ledger: `gbk-slot-datatype-unconfirmed`.

## 3. Fifteen optional data inputs (reference + annotation assets)

All from `nextflow-galaxy-reference-data.md` §4; `optional: true` throughout, `default: null` (confirmed in the corrected summary — every one of these 15 is genuinely null in `nextflow.config`). No data tables, no `dbkey` (decision `no-galaxy-reference-data-tables`).

| Input id | source param | gates under | shape/datatype |
|---|---|---|---|
| `amp_ampcombi_db` | `amp_ampcombi_db` | `run_amp_screening` | unresolved (§3.1) |
| `annotation_bakta_db` | `annotation_bakta_db` | `annotation_tool == bakta` | unresolved |
| `arg_amrfinderplus_db` | `arg_amrfinderplus_db` | `run_arg_screening && !arg_skip_amrfinderplus` | unresolved |
| `arg_rgi_db` | `arg_rgi_db` | `run_arg_screening && !arg_skip_rgi` | raw **or** processed CARD — the source only accepts it as-is when the name contains `card_database_processed` |
| `arg_deeparg_db` | `arg_deeparg_db` | `run_arg_screening && !arg_skip_deeparg` | unresolved |
| `bgc_antismash_db` | `bgc_antismash_db` | `run_bgc_screening && !bgc_skip_antismash` | `.tar.gz` **or** unpacked dir (two accepted shapes) |
| `bgc_bigslice_db` | `bgc_bigslice_db` | `run_bgc_screening && bgc_run_bigslice` | unresolved; keeps the one-shot rebuild |
| `bgc_deepbgc_db` | `bgc_deepbgc_db` | `run_bgc_screening && !bgc_skip_deepbgc` | unresolved |
| `cazyme_dbcan_db` | `cazyme_dbcan_db` | `run_cazyme_screening && !cazyme_skip_dbcan` | unresolved |
| `interproscan_db` | `protein_annotation_interproscan_db` | `run_protein_annotation` | unresolved |
| `mmseqs_db` | `taxa_classification_mmseqs_db` | `run_taxa_classification` | unresolved |
| `amp_hmmsearch_models` | `amp_hmmsearch_models` | `amp_run_hmmsearch` — **conditionally required** (`error()` at `amp.nf:72-77`) | `hmm3`, `multiple: true` |
| `bgc_hmmsearch_models` | `bgc_hmmsearch_models` | `bgc_run_hmmsearch` — conditionally required (`bgc.nf:153-158`) | `hmm3`, `multiple: true` |
| `annotation_bakta_hmms` | `annotation_bakta_hmms` | `annotation_tool == bakta` | `hmm3`, `multiple: true` |
| `abricate_db` | `arg_abricate_db` | `run_arg_screening && !arg_skip_abricate` | **override only** — empty means ABRicate's bundled DBs |

### 3.1 What is deliberately unresolved here

Nine of the eleven database inputs are multi-file directories or tarballs, and no packaged note picks between a `directory`-typed input, one uploaded archive unpacked by a first step, and a `multiple: true` file list. The provisional shape stays "one uploaded archive dataset, upload as-is" (decision `db-inputs-as-uploaded-archives`, **confidence low**), and `format` is left unset here rather than guessed: writing `format: tar.gz` into a template would hard-code a low-confidence choice into the user-facing form. **Phase 5 (`compare-against-iwc-exemplar`) must settle it by citing a wrapped tool that takes a database argument.** Ledger: `db-directory-input-shape-unsettled` (open since phase 2), `db-asset-sizes-unmeasured`.

The two conditionally-required HMM inputs have no clean gxformat2 expression — the params note lists that as an open question of its own. Both stay optional with the requirement stated in help text; if the branch runs without them the workflow fails, where Nextflow fails with a written message. Ledger: `hmm-models-required-when-branch-enabled`.

## 4. Eight selectors exposed, one pinned

| Input id | type | options / default | note |
|---|---|---|---|
| `amp_ampcombi_db_id` | `select` | `DRAMP` (default) / `APD` / `UniRef100` | also names what the builder downloads |
| `annotation_bakta_db_downloadtype` | `select` | `full` (default) / `light` | only meaningful when `annotation_bakta_db` is empty |
| `abricate_db_id` | `select` | `ncbi` (default) / `resfinder` / `argannot` / `megares` + free text | the four are special-cased at `arg.nf:180`; a `select` loses the free-string case, so either `select` + "other" or a text input with the four listed in help — **phase 5 call** |
| `arg_fargene_hmmmodel` | `select multiple` | 10 bundled model names, all 10 selected by default | source stores a comma-joined string, which is what Galaxy's multi-select yields |
| `arg_rgi_data` | `select` | `NA` (default) / `wgs` / `plasmid` / `chromosome` | input-datatype flag, not a database |
| `arg_deeparg_model` | `select` | `LS` (default) / `SS` | as above |
| `amp_ampir_model` | `select` | `precursor` (default) / `mature` | as above |
| `mmseqs_db_id` | `text` | default `Kalamari`, **no enum in source** | needs a list the source does not carry — do not invent one (`mmseqs-db-id-has-no-option-list`) |
| ~~`interproscan_db_url`~~ | *pinned* | the pinned `interproscan-5.72-103.0-64-bit.tar.gz` URL | it only selects *which* tarball a rebuild fetches; phase 2 established that no wrapper rebuild is assumed for InterProScan, so the input would be inert. **It returns if phase 5 adds a workflow-tier fetch step.** |

## 5. Twenty-five shape controls, two pinned

All 27 become `boolean`/`select` inputs whose only downstream role is a `when:` expression — this is where `workflow.conditionals[]` (13 guards over `ANNOTATION`, `AMP`, `ARG`, `BGC`, `CAZYME`, `TAXA_CLASS`, `PROTEIN_ANNOTATION`, `SEQKIT_SEQ_LENGTH`, `SEQKIT_SEQ_FILTER`) is realised in Galaxy. Defaults are the corrected `nextflow.config` values: every boolean `false`, `annotation_tool = pyrodigal`.

- 6 stage switches: `run_amp_screening`, `run_arg_screening`, `run_bgc_screening`, `run_cazyme_screening`, `run_protein_annotation`, `run_taxa_classification`
- 16 tool `*_skip_*` / `*_run_*` toggles (`amp_skip_amplify`, `amp_skip_ampir`, `amp_skip_macrel`, `amp_run_hmmsearch`, `arg_skip_amrfinderplus`, `arg_skip_deeparg`, `arg_skip_fargene`, `arg_skip_rgi`, `arg_skip_abricate`, `arg_skip_argnorm`, `bgc_skip_antismash`, `bgc_skip_deepbgc`, `bgc_skip_gecco`, `bgc_run_bigslice`, `bgc_run_hmmsearch`, `cazyme_skip_dbcan`) + `dbcan_skip_cgc`, `dbcan_skip_substrate`
- 1 real tool selector: `annotation_tool` — `prodigal` / `pyrodigal` / `prokka` / `bakta`, default `pyrodigal` → drives the ANNOTATION branch and, with §10's caveat, the annotation output port

**Pinned, not exposed:** `taxa_classification_tool` (enum `[mmseqs2]`) and `protein_annotation_tool` (enum `[InterProScan]`). Each has exactly one admissible value in this source, so exposing them offers a choice the workflow cannot honour. Pinning them at `mmseqs2` / `InterProScan` matches the source exactly and drops one confusing control each; the cost is that adding a second taxa tool later becomes a workflow edit rather than a form change. Ledger: `single-option-tool-selectors-pinned`.

Note the interaction the source encodes and the interface must preserve: `run_taxa_classification` forks every screening branch into a `<X>` / `<X>+taxonomy` pair in `conditionals[]`, and it also decides **which file the user receives** for the AMP/ARG/BGC summary tables (§10). It is the single most load-bearing boolean on the interface.

## 6. Eight save flags promoted, because they change command output

These are the tool-bucket flags that are *not* publish-only — each changes either the command or which files exist, which the params note's effect test says to keep:

| Input id | Effect, traced in source | Default |
|---|---|---|
| `amp_hmmsearch_savealignments` / `_savetargets` / `_savedomains` | passed as `val(write_align/write_target/write_domain)` into `HMMER_HMMSEARCH` (`amp.nf:91`), gating the optional `alignments` (`*.sto.gz`), `target_summary` (`*.tbl.gz`), `domain_summary` (`*.domtbl.gz`) outputs | `false` |
| `bgc_hmmsearch_savealignments` / `_savetargets` / `_savedomains` | same, `bgc.nf:173` | `false` |
| `taxa_classification_mmseqs_db_savetmp` | `modules.config:44` — `params.… ? "" : "--remove-tmp-files"`, a command argument | `false` |
| `taxa_classification_mmseqs_taxonomy_savetmp` | `modules.config:69` — same idiom | `false` |

All eight default `false`, so the interface adds no behaviour the source had off; they are exposed because a Galaxy user otherwise cannot reach outputs the underlying tool can produce.

Three further `*_save*` flags — `arg_rgi_savejson`, `arg_rgi_savetmpfiles`, `arg_fargene_savetmpfiles` — gate `publishDir` **only** (`modules.config:390/397/338`), so they are excluded by class (§9) with a pointer to §10: in Galaxy those datasets exist as step outputs whether or not anything "publishes" them, so the flag's whole effect is already the Galaxy default.

## 7. MultiQC report config

`multiqc_title` → optional `text` input (a string the report consumes; cheap, and the one MultiQC knob a Galaxy user plausibly wants). `multiqc_config`, `multiqc_logo`, `multiqc_methods_description` → omitted per decision `multiqc-config-assets-omitted-by-default`: the source falls back to `assets/multiqc_config.yml` and `assets/methods_description_template.yml` inside the repo, whose Galaxy equivalent is the wrapper's bundled config. `max_multiqc_email_size` is email transport only → excluded.

## 8. 133 tool knobs pinned at source defaults

The remaining tool parameters are grouped by stage: `annotation_*` 40, `bgc_*` 40, `arg_*` 27, `amp_*` 22, `taxa_classification_*` 10, `protein_annotation_*` 2 = **141**, minus the 8 promoted in §6 = **133**. They stay fixed at the `nextflow.config` value the source ships, and every one is a plain scalar (no path, no reference selector, no branch guard — checked: none appears in `workflow.conditionals[]` guards, and the only enum-bearing ones are the 8 below).

This is a deliberate, lossy interface decision, not an oversight. 141 more fields on one form would bury the 61 inputs that decide what runs and what data is needed, and Galaxy has no section/advanced-panel affordance that keeps a parameter invisible *and* discoverable the way `--help_full` does in Nextflow. The eight closed enums inside the pinned set are named here so a reviewer can see exactly what is being fixed:

`annotation_bakta_gram` = `?` · `annotation_prokka_kingdom` = `Bacteria` · `arg_rgi_alignmenttool` = `BLAST` · `arg_hamronization_summarizeformat` = `tsv` · `bgc_antismash_hmmdetectionstrictness` = `relaxed` · `bgc_antismash_taxon` = `bacteria` · `bgc_gecco_convertmode` = `clusters` · `bgc_gecco_convertformat` = `gff`

(Each value above is the corrected `nextflow.config` default; verify against the source before the template hard-codes them.)

Ledger: `tool-surface-pinned-at-source-defaults` (`kind: dropped`, units recorded, with the promotion rule stated so the boundary is reviewable). If the corpus comparison at phase 5 finds a Galaxy idiom for a collapsed advanced section, this entry is the one that reopens.

## 9. Excluded control params — class, effect, assessment

Per the params note, each gets a class, an effect, and a safe/problematic call; a name match alone is not an assessment. **Problematic** means the omission changes scientific output, not just UX.

| source_param | class | effect | assessment | reason |
|---|---|---|---|---|
| `outdir` | output location | every `publishDir` path root | safe | Galaxy owns history layout |
| `publish_dir_mode` | output location | symlink/copy mode for all 61 publishes | safe | no Galaxy analogue |
| `save_db` | publish toggle | gates 13 `publishDir` rows, all of them **downloaded databases** | **problematic** | decides whether the DBs a run pulled are kept at all; in Galaxy a pulled DB is a step output that exists, so promote-don't-drop lands as §10's optional DB-echo outputs |
| `save_annotations` | publish toggle | gates 4 `publishDir` rows of per-sample annotation output | **problematic** | same shape as `save_db`; annotation products are the point of the ANNOTATION branch |
| `bgc_savefilteredcontigs` | publish toggle | gates `SEQKIT_SEQ_LENGTH` publish (`modules.config:99`) | safe | the filtered-contigs dataset is still a step output in Galaxy |
| `arg_rgi_savejson` | publish toggle | gates RGI JSON publish (`:390`) | safe (noted) | RGI JSON remains reachable as a step output |
| `arg_rgi_savetmpfiles` | publish toggle | gates RGI tmp publish (`:397`) | safe | intermediate files |
| `arg_fargene_savetmpfiles` | publish toggle | gates fARGene tmp publish (`:338`) | safe | intermediate files |
| `email` | notification | summary email | safe | Galaxy owns notification |
| `email_on_fail` | notification | failure email | safe | as above |
| `plaintext_email` | notification | email format | safe | as above |
| `max_multiqc_email_size` | notification | email attachment cap | safe | as above |
| `validate_params` | runtime UX | nf-schema launch validation | **problematic** | drops the pre-flight that would otherwise catch a bad sheet or a missing HMM set; the residue is Galaxy column restrictions + prose (§2.1). Recorded as validation loss, not silently dropped |
| `monochrome_logs` | runtime UX | log colour | safe | — |
| `help`, `help_full`, `show_hidden`, `version` | CLI plumbing | Nextflow CLI behaviour | safe | no Galaxy equivalent needed |
| `config_profile_name`, `config_profile_description`, `config_profile_url`, `config_profile_contact` | institutional config | profile banner | safe | site config |
| `custom_config_base`, `custom_config_version` | institutional config | remote nf-core configs URL | safe | site config; the URL is a template over `custom_config_version`, so no flat value exists |
| `trace_report_suffix` | runtime UX | trace filename | safe | — |
| `pipelines_testdata_base_path` | test fixtures | base path for the pipeline's own nf-test fixtures, referenced only from `conf/test*.config` | safe | already carried as `testdata-base-path-not-carried`; phase 8 territory |

`save_db` and `save_annotations` are the two to argue about, and they are why the note's "promote, don't drop" clause exists. Resolution: they do **not** come back as booleans. Their whole effect in Nextflow is "does this dataset reach the user", which in Galaxy is decided by which step outputs get promoted — so §10 promotes the DB echoes and the annotation outputs explicitly, and the boolean disappears.

## 10. Outputs

### 10.1 The asymmetry that drives this section

`NFCORE_FUNCSCAN` (main.nf) emits **one** channel: `multiqc_report`. The primary workflow `FUNCSCAN` emits `multiqc_report` + `versions`. Everything else — all 61 per-tool result sets — reaches the user through `publishDir`, and **all 61 of those declarations live in `conf/modules.config` `withName:` selectors**, none inline in a process. (`processes[].publish_dir` is null for all 55 processes; only `publish_dir_matches` carries them. Read the wrong field and the pipeline looks like it publishes nothing.) 25 of the 61 carry an `enabled:` expression — `params.save_db` ×13, `params.save_annotations` ×4, `params.run_protein_annotation` ×2, and one each of `params.run_taxa_classification`, `params.bgc_savefilteredcontigs`, `params.arg_rgi_savejson`, `params.arg_rgi_savetmpfiles`, `params.arg_fargene_savetmpfiles`, plus `GUNZIP`'s literal `enabled: false`.

Consequences for the Galaxy interface:

1. Galaxy has no publishing step, so **nothing is promoted unless this brief asks for it.** §10.3 is the interface's real work, not an appendix.
2. The other side is a **gain**: 36 unconditional publishes need no special handling, because every step output already lands in the history. What is lost is the tidy `{outdir}/<stage>/<tool>/<sample>/` tree, not the data.
3. **The headline summary tables are published by a different step than the one that computes them.** `MERGE_TAXONOMY_{AMPCOMBI,HAMRONIZATION,COMBGC}` publish nothing at all — their `saveAs: { _ -> null }` voids their own `publishDir` — and the file that arrives is the bgzip output of the aliased `AMP_/ARG_/BGC_TABIX_BGZIP` steps (canonical `TABIX_BGZIP`, `output` + `gzi` ports, `ext.prefix = "hamronization_complete_summary_taxonomy"` set in config). `HAMRONIZATION_SUMMARIZE`'s own publish carries `saveAs: { params.run_taxa_classification == false ? it : null }`. So the ARG summary the user receives is `hamronization_complete_summary_taxonomy.tsv.gz` **when taxa classification is on** and `hamronization_combined_report.tsv` **when it is off** — same purpose, two producers, two formats. A promoted output must therefore name the *bgzip step* and be conditional, or both variants must be promoted under separate labels. Same pattern for AMP (`Ampcombi_summary*` vs the taxonomy-merged table) and BGC (`combgc_summary` vs the merged table).

### 10.2 Promoted outputs — the public interface

| Output label | Source (step / port) | Format | Element ids | Why public |
|---|---|---|---|---|
| `multiqc_report` | `MULTIQC / report` (`*.html`) | `html` | single | the one output the source emits; the run's overview |
| `versions` | `FUNCSCAN` `versions` channel (collected `versions.yml`) | `yaml`/`txt` (low conf.) | single | provenance; the source's only other emitted output |
| `amp_summary_table` | `AMPCOMBI2_COMPLETE / tsv` (`Ampcombi_summary.tsv`) | `tabular` | single | per-hit AMP summary, stable content |
| `amp_cluster_table` | `AMPCOMBI2_CLUSTER / cluster_tsv` (`Ampcombi_summary_cluster.tsv`) | `tabular` | single | clustered AMP summary |
| `arg_hamronization_table` | `ARG_TABIX_BGZIP / output` when `run_taxa_classification`, else `HAMRONIZATION_SUMMARIZE / tsv` | `tabular.gz` / `tabular` | single | the combined ARG report — **conditional, §10.1(3)** |
| `bgc_combgc_table` | `COMBGC / tsv` (`${prefix}/combgc_summary.tsv`), or `BGC_TABIX_BGZIP / output` under taxa | `tabular` / `tabular.gz` | single | combined BGC summary |
| `cazyme_overview` | `RUNDBCAN_EASYCGC / cazyme_annotation` (`${prefix}_overview.tsv`) | `tabular` | sample id | per-sample CAZy summary, the only tabular dbCAN checkpoint |
| `cazyme_cgc` | `RUNDBCAN_EASYCGC / cgc_gff` (+ `cgc_standard_out`) | `gff3` / `tabular` | sample id | CGC calls, addressable per sample |
| `taxa_taxonomy_table` | `MMSEQS_CREATETSV / tsv` | `tabular` | sample id | the taxonomy assignment every merged table joins on |
| `interproscan_table` | `INTERPROSCAN / tsv` | `tabular` | sample id | protein annotation summary |
| `annotation_result` | **varies with `annotation_tool`**: `BAKTA_BAKTA / gff`,`gbff`; `PROKKA / gff`,`gbk`; `GUNZIP_PYRODIGAL_GFF / gunzip`,`GUNZIP_PYRODIGAL_GBK / gunzip` | `gff3`, `genbank`, `fasta` | sample id | **unresolved**: one label cannot bind four alternative producers — see §10.4 |
| `db_echo_*` (optional) | each DB builder step's output | unresolved (§3.1) | single | replaces `save_db`; only if the run built a DB |

### 10.3 Testability

`galaxy-workflow-testability-design` says to promote a checkpoint that could fail, not just an artifact that could exist. For funcscan that rules out judging a run by the MultiQC HTML (a report of the right shape proves something rendered). The candidates above were picked because each is a stable table with content an assertion can check:

- `amp_cluster_table`, `amp_summary_table` — deterministic cluster/summary tables; row counts and the `Ampcombi_summary_cluster_representative_seq.tsv` representatives are content-checkable.
- `arg_hamronization_table` — hAMRonization's harmonised columns are the pipeline's cross-tool contract; a wrong or empty table is exactly the failure a test should catch. **Note the conditional:** the test must assert the variant matching its `run_taxa_classification` job value, or hold taxa off to test the simpler producer and on in a second test.
- `bgc_combgc_table`, `cazyme_overview`, `taxa_taxonomy_table` — same argument per stage.
- Element identifiers: sample ids survive as `element_identifier` on the input sheet, and the note warns not to infer generated identifiers. Every per-sample promoted output above is keyed by the same id, so `element_tests:` can address samples; a phase-12 run must confirm the derived names rather than assume them.
- `GUNZIP`'s output is *not* published in the source (`enabled: false`), so a gzipped-input run has no checkpoint for the decompression step. Promoting `input_unpacked` is optional; it is cheap and it localises a whole class of failure, but it publishes data the source deliberately hides. Decision left to phase 6, noted here so it is not decided by accident.

### 10.4 Two output-shape problems this brief cannot close

1. **Conditional producers (`annotation_result`).** `annotation_tool` picks among four tools whose output ports differ in count, name, and even in *how many steps run*: `BAKTA_BAKTA` has 10 result ports (+versions), `PROKKA` 12 (+versions), and `pyrodigal` invokes the Pyrodigal module **twice** — `PYRODIGAL_GBK(fasta, "gbk")` and `PYRODIGAL_GFF(fasta, "gff")`, `annotation.nf:39-40` — then gunzips four of their outputs through four `GUNZIP` aliases, so one Nextflow "annotation directory" is six steps. Galaxy `outputs:` entries bind to one `outputSource` each, so a single label cannot follow the switch. Options: one label per producer (`annotation_bakta_gff`, `annotation_prokka_gff`, `annotation_pyrodigal_gff`, …) and accept a mostly-empty interface on any given run, or merge the alternatives upstream (`__MERGE_COLLECTIONS__` / filter-empty) and promote the merged collection under one label. Recorded as `conditional-output-producer-unexpressible`; phase 6 chooses.
2. **Multi-file per-sample outputs.** antiSMASH (`zip`/`html`/`json`/…), GECCO (genes/features/clusters/gbk/json), DeepBGC (`bgc_tsv`/`pfam_tsv`/`gbk`/`pngs`), InterProScan (tsv/xml/gff3/json) each emit several kinds per sample where Nextflow publishes them into one directory. Galaxy keeps one collection per output port, so the per-tool directory becomes N parallel collections that must stay identifier-aligned. Preference: promote one port per tool (the tabular or html summary) and leave the rest as step outputs; the full per-tool bundle has no single Galaxy home.

## 11. Labels and collection shapes (summary)

- Input: `input_fasta` / `input_protein` / `input_gbk` / `input_gff`, all `sample_sheet`, ids = sample id, `gff_type` column on the GFF sheet only.
- Every mapped step output: `list` keyed by the same sample id; a step with several ports yields several aligned `list`s rather than a `list:record`, so that each port can be promoted or asserted on independently (channel-shape note: a `tuple(meta, path(a), path(b))` is "usually a keyed record of multiple tool inputs", *not* a paired collection — and forcing `record` here would hit the same `allow_implicit_mapping` wall as §2.1).
- Cross-sample summary tables (`amp_*`, `arg_*`, `bgc_combgc_*`, `*_taxonomy_*`): single datasets, not collections — they are `collect()`-ed reductions in the source (`MERGE_TAXONOMY_*` take `path(ampcombi_df)` + a collected `path(taxa_list)`).
- `when:`-gated steps mean an entire collection can be absent for a given run, so any output asserted on must be reachable in the job's branch — the test plan's problem, noted here.

## 12. Confidence

| Choice | Confidence | Basis |
|---|---|---|
| Sample-sheet columns → `column_definitions`, `gff_type` → `restrictions` | High | nf-schema present; note's mapping is 1:1 for enum/pattern |
| Four parallel `sample_sheet` inputs over one `sample_sheet:record` | Medium | three source facts (§2.1); no corpus exemplar either way |
| 15 optional DB inputs, no data tables | High | source's own `if (params.X) {use} else {build}` shape |
| Datatype of the 9 directory-shaped DB inputs | **Low / unset** | obligation `db-directory-input-shape-unsettled` |
| `genbank` for `gbk` | **Low** | not in the datatype note (§2.2) |
| `gff3` for the GFF slot | Medium | note allows `gff` or `gff3` |
| Shape controls kept, single-option selectors pinned | High | `conditionals[]` guards; enums carry one value |
| 133 tool knobs pinned | Medium | interface judgement; effect-tested, reversible at phase 5 |
| Promoted output list | Medium | from `publish_dir_matches` + emit blocks; conditional producers unresolved (§10.4) |
| `versions` format | Low | `versions.yml` is YAML; no registry row consulted for it |

## 13. Ledger changes emitted with this brief

New obligations (`open-requirements.ledger.yml`): `samplesheet-row-coupling-unexpressible`, `samplesheet-per-row-optional-slots`, `sample-id-alphabet-narrowed`, `gbk-slot-datatype-unconfirmed`, `conditional-output-producer-unexpressible`, `published-only-results-need-explicit-promotion`, `single-option-tool-selectors-pinned` (decision), `tool-surface-pinned-at-source-defaults` (`dropped`), plus discoveries `funcscan-publishes-through-config-not-emits`, `headline-summary-tables-are-published-by-a-bgzip-step`, `three-quarters-of-the-param-surface-is-plain-tool-knobs`. Passed through unchanged and still open: `db-directory-input-shape-unsettled`, `wrapper-rebuild-capability-unverified`, `multi-db-pick-list-no-galaxy-exemplar` (note updated with the interim shape chosen here), `container-bundled-databases`, `hmm-models-required-when-branch-enabled` (note updated), `mmseqs-db-id-has-no-option-list`, `db-asset-sizes-unmeasured`, `testdata-base-path-not-carried`.

## 14. Feedback recorded

Four entries added to `foundry-feedback.ledger.yml` for this phase: `params-default-has-no-resolution-rule-when-the-schema-omits-it`, `sample-sheet-note-recommends-record-without-flagging-implicit-mapping`, `datatype-note-has-no-genbank-or-hmm-row`, `no-interface-vocabulary-for-a-param-pinned-at-a-default`. The ledger now holds 10 entries, all `open`.
