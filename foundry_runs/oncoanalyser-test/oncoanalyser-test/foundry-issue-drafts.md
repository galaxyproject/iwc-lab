# Foundry issue drafts — oncoanalyser-test

Target: `galaxyproject/foundry`. Local drafts only: nothing posted. Each section is self-contained; the first line of each body is the required AI-assistant attribution (fill in `<user>`).

## Cluster A — new issue

Canonical locator: `packages/summarize-nextflow`

### New issue — summarize-nextflow resolver: four more silent extraction defects on nf-core/oncoanalyser 3.0.0

> Posted by an AI assistant on <user>'s behalf.

Same shape as #666 (independent resolver defects found in one run, each validating cleanly); not one fix. Pipeline nf-core/oncoanalyser 3.0.0 (commit 7c74c87), run via `foundry summarize-nextflow` (Windows-hosted npm against a WSL checkout).

1. **File-level nf-test `profile` / `options "-stub"` ignored** (major). `tests/default.nf.test` declares `profile "test_stub"` and `options "-stub"`; the candidate came out with `effective_profiles: [test]`, `execution_mode: real`, `scope: primary`, and params/inputs from `conf/test.config`. Both candidates then looked primary and `test_selection` fell to `needs-scope-choice`. Expected: apply file/test-level profile directives over the `nf-test.config` root (replace unless `+name`), and set `execution_mode: stub` / `scope: bootstrap-only` when options carry `-stub`.
2. **Placeholder provenance; `--pin` re-clones a local path** (major). With a local clone, `source.url` = `https://example.invalid/unknown.git`, `version` = `unknown`, no warning. With `--pin 3.0.0` on a local path the CLI re-cloned through Windows git and exited on "detected dubious ownership". Expected: read remote/tag/HEAD from the local clone (or warn per failed lookup), and verify or check out `--pin` in place. A prior run (nf-core/demo) saw the same placeholder provenance.
3. **Topic-only outputs misnamed** (minor). Outputs declared only with `topic:` (no `emit:`), e.g. `tuple val(meta), path('amber/'), topic: amber_dir`, were named `meta` or `output_<random digits>`. Expected: name them by topic or a stable positional name.
4. **Samplesheet path column typed `meta`** (minor). `assets/schema_input.json` `filepath` has no `format`, so it became `kind: meta`, although `Utils.parseInput` consumes it as path(s); the custom long-format parser (one row per file, `filetype` role selector, `R1;R2` joined by `;`) produced no warning. Expected: trace use before defaulting to `meta`, and warn when the sheet is parsed by custom Groovy rather than `samplesheetToList`.

Subject: `packages/summarize-nextflow` (CLI reported via `@galaxy-foundry/gxwf-foundry`).

- `summarize-nextflow-cli-nftest-file-profile-and-stub-ignored` (major) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`
- `summarize-nextflow-cli-placeholder-provenance-and-pin-reclone` (major) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`
- `summarize-nextflow-cli-topic-only-outputs-misnamed` (minor) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`
- `summarize-nextflow-cli-samplesheet-path-column-kind` (minor) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`

## Cluster B — comment on #666

Canonical locator: `packages/summarize-nextflow`

### Comment on #666 — two of its defects reproduced on nf-core/oncoanalyser, one in a new shape

> Posted by an AI assistant on <user>'s behalf.

Second pipeline, same resolver (nf-core/oncoanalyser 3.0.0):

- **Primary-workflow selection (#666 item 1), dispatcher variant.** The resolver picked `NFCORE_ONCOANALYSER`, which calls no processes and only dispatches on `params.mode` to five named workflows (`WGTS`, `TARGETED`, `PURITY_ESTIMATE`, `PANEL_RESOURCE_CREATION`, `PREPARE_REFERENCE`). `workflow.edges` were 13 `params`/`inputs` → workflow edges. `WGTS` (33 subworkflow calls) is the correct primary under the stated rule if calls are counted through subworkflows.
- **Reference evidence (#666 item 4), wider gap.** The seven `params.X = getGenomeAttribute(...)` assignments in `main.nf` and `ref_data_hmf_data_path` were missing from `reference_assets[]`, and `reference_rebuilds[]` was empty although `subworkflows/local/prepare_reference/main.nf` has six compute-if-missing branches (`if (! params.ref_data_genome_fai) { SAMTOOLS_FAIDX(...) }`, and likewise dict, img, bwa-mem2, GRIDSS, STAR). So rebuild detection also misses guards inside subworkflows. An earlier nf-core/demo run saw the `getGenomeAttribute` part too.

- `summarize-nextflow-cli-primary-workflow-picks-mode-dispatcher` (major) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`
- `summarize-nextflow-cli-reference-assets-miss-genome-attributes` (major) — subject hash `n/a`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`

## Cluster C — new issue

Canonical locator: `content/molds/summarize-nextflow/index.md`

### New issue — summarize-nextflow Mold: no guidance for multi-mode pipelines with runtime-derived stage guards

> Posted by an AI assistant on <user>'s behalf.

nf-core/oncoanalyser dispatches on `params.mode` among five named workflows, and enables stages through `run_config.stages.*`, computed in `lib/` Groovy (`Processes.getRunStages`) from samplesheet content plus `processes_include/exclude`. The Mold assumes one primary workflow whose conditionals guard on params; the schema has no place for alternate run modes or for guards derived from input content. The run modeled WGTS as primary and recorded the other modes and the stage derivation in `warnings[]`.

**Expected:** say how to summarize multi-mode pipelines (record each mode workflow, or pick one and warn), and how to record guards that derive from samplesheet content rather than params. Main has changed since the cast (`d8e67590…`) but carries no such guidance.

- `summarize-nextflow-mold-silent-on-multi-mode-runtime-stages` (major) — subject hash `fb19fff9162cc36f`; skill `summarize-nextflow` rev 18 hash `fb19fff9162cc36f`

## Cluster D — comment on #219

Canonical locator: `content/research/nextflow-to-galaxy-reference-data-mapping/index.md`

### Comment on #219 — two gaps from nf-core/oncoanalyser

> Posted by an AI assistant on <user>'s behalf.

1. **Directory/tarball bundles** (major). oncoanalyser resolves ~55 reference files, several of them subdirectories, from one HMF resource tarball (`ref_data_hmf_data_path` plus the `hmf_data_paths` relative-path map). The note covers coordinated bundles of ~4 files and suggests `sample_sheet:record`, but has no default for archive bundles consumed member by member. This run chose a single archive input with in-tool member extraction. A default shape and datatype (`tar` / `tar.gz` / `data`) would help, along with how it interacts with wrapper discovery. Field note: biocontainers images use BusyBox `tar`, which cannot extract by wildcard member.
2. **Scale and test feasibility** (minor). Nothing asks the brief to record asset sizes or the cost of in-tool rebuilds, though they decide whether downstream test phases can run. Here, references totalled ~59 GB, and a bwa-mem2 index of a 3.2 GB FASTA needs ~64 GB RAM. Suggest recording approximate sizes and rebuild cost, and raising an open requirement when the source test uses references that are not test-scale.

- `reference-mapping-note-silent-on-directory-archive-bundles` (major) — subject hash `4676cdf3de4bcec6`; skill `nextflow-summary-to-galaxy-reference-data` rev 5 hash `b49bae31e3b8918b`
- `reference-mapping-note-no-scale-or-test-feasibility-check` (minor) — subject hash `4676cdf3de4bcec6`; skill `nextflow-summary-to-galaxy-reference-data` rev 5 hash `b49bae31e3b8918b`

## Cluster E — new issue

Canonical locator: `content/research/galaxy-sample-sheet-collections/index.md`

### New issue — galaxy-sample-sheet-collections: no mapping for long-format, role-keyed samplesheets

> Posted by an AI assistant on <user>'s behalf.

oncoanalyser's samplesheet is long format: one row per file, a `filetype` role column, and `sample_type` tumor/normal rows regrouped per `group_id` into one record with paired roles. The note maps only wide sheets (path columns per row), and `sample_sheet` cannot express cross-row role pairing (it must be outermost; there are no cross-row references beyond `element_identifier`). The run chose parallel per-role `list:paired` inputs with one subject per invocation, on judgment.

**Expected:** a mapping for long-format, role-keyed sheets — parallel per-role collections per subject, or `sample_sheet:record` after regrouping — and guidance on when to fall back to one subject per invocation.

- `sample-sheet-note-silent-on-long-format-role-rows` (major) — subject hash `98736fdcd0c4f469`; skill `nextflow-summary-to-galaxy-interface` rev 6 hash `4396677339157849`

## Cluster F — new issue

Canonical locator: `content/research/nextflow-to-galaxy-channel-shape-mapping/index.md`

### New issue — channel-shape mapping: no Galaxy representation for directory-valued channels

> Posted by an AI assistant on <user>'s behalf.

Every hmftools module in oncoanalyser emits and consumes whole directories (`tuple val(meta), path('amber/'), topic: amber_dir`). The channel-shape and path-glob notes cover files and collections, not directory outputs passed between steps. The run carried each directory as an uncompressed `tar` dataset, plus named-file fan-out for user and test outputs.

**Expected:** a default Galaxy representation for directory-valued channels (archive dataset, `list` via `discover_datasets`, or named-file fan-out), with its datatype and when each applies.

- `channel-shape-note-silent-on-directory-outputs` (major) — subject hash `32efd59cc86563b1`; skill `nextflow-summary-to-galaxy-interface` rev 6 hash `4396677339157849`

## Cluster G — comment on #769

Canonical locator: `content/molds/nextflow-summary-to-galaxy-interface/index.md`

### Comment on #769 — scope should also follow target tool availability

> Posted by an AI assistant on <user>'s behalf.

A second direct-route run (nf-core/oncoanalyser 3.0.0) shows a related need. Scope depended on whether the tools exist: 0 of ~25 hmftools were installed on the target (test.galaxyproject.org) or present in the main Tool Shed. That check otherwise first happens in phase 7, after the interface, data-flow and template are pinned. This run made an ad-hoc availability check before the interface phase (target `/api/tools?q=`, Tool Shed `/api/repositories?q=`, `GET /api/unprivileged_tools`), then asked the user to choose a scope (core DNA spine).

**Suggestion:** when confirming scope at the start, include a coarse tool-availability check on the target plus the Tool Shed, and offer a narrower scope when most tools are missing.

- `interface-mold-no-target-tool-availability-check` (major) — subject hash `4396677339157849`; skill `nextflow-summary-to-galaxy-interface` rev 6 hash `4396677339157849`

## Cluster H — new issue

Canonical locator: `content/research/open-requirements-ledger/index.md`

### New issue — open-requirements ledger: decisions have no `basis` for interactive user choices

> Posted by an AI assistant on <user>'s behalf.

Decisions carry `basis: brief-proposal | agent`. This run took scope and testing decisions by asking the user mid-pipeline; neither value fits, and the run wrote `basis: user`. Main changed since the cast (`d3d36d55…`) and still lists only the two values.

**Expected:** add `basis: user`, carrying the question asked, for decisions taken interactively during a run.

- `open-requirements-decision-basis-lacks-user` (minor) — subject hash `f9076119f5110cd2`; skill `nextflow-summary-to-galaxy-interface` rev 6 hash `4396677339157849`

## Cluster I — new issue

Canonical locator: `content/molds/compare-against-iwc-exemplar/index.md`

### New issue — compare-against-iwc-exemplar: unclear whether a Low-confidence match writes iwc-exemplar.gxwf.yml

> Posted by an AI assistant on <user>'s behalf.

The procedure writes the sibling file once a High or Medium exemplar is chosen, and says a Low cross-domain match "may surface a short excerpt". The output declaration says the file is absent only when there is no nearest exemplar. This run had a Low match (no IWC somatic tumor/normal workflow exists; nearest was `variant-calling/ploidy-aware-genotype-calling`) and wrote both the file and the excerpt, labelled pattern-only.

**Expected:** state whether a Low match writes the sibling file (labelled pattern-only) or only the inline excerpt.

- `iwc-exemplar-low-confidence-sibling-file-ambiguous` (minor) — subject hash `84abb427cbcbae56`; skill `compare-against-iwc-exemplar` rev 12 hash `84abb427cbcbae56`

## Cluster J — comment on #672

Canonical locator: `content/research/galaxy-user-tool-authoring/index.md`

### Comment on #672 — three more galaxy-user-tool-authoring gaps, found at runtime on test.galaxyproject.org

> Posted by an AI assistant on <user>'s behalf.

Found while authoring 13 UDTs for nf-core/oncoanalyser (hmftools). All passed `gxwf validate-tool-source`; the first two problems only appeared in probe jobs on test.galaxyproject.org (27.0.dev0).

1. **Indexed inputs arrive without their index** (major). A `bam` data input is staged as a bare `.dat`. Its JS object is `{class: File, path: …/dataset_<uuid>.dat, format: bam, …}`, with no index and no metadata path. Every BAM/CRAM/bgzip-VCF consumer that needs an index breaks. The note should say so, and give the pattern: emit the index from the producer as a separate dataset (no `bai` datatype exists on that server, so `data`), or index inside the tool when the image has an indexer.
2. **The container's userland is BusyBox, and commands run under `set -e`** (major). In `quay.io/biocontainers/hmftools-*`, `tar -xzf a.tgz '*/common/ensembl_data'` fails with `not found in archive` (no wildcard members, no `--strip-components`), and the job stops at the first failure. The working form: list once, `grep` the prefixes, `mkdir -p` the parents, then `tar -T`. The note recommends biocontainers but says nothing about the shell tools inside them.
3. **Escaping rules** (minor). The note says to escape non-expression shell `$(...)` as `\$(date)`. On the server, `echo SHELL=\$0` printed `SHELL=$0`: the backslash reached the shell. The note is also silent on whether CWL-style `${...}` is evaluated, so `${GALAXY_SLOTS:-1}` defaults are risky. Please verify against Galaxy 26/27 and state exactly what reaches the shell.

- `udt-authoring-note-silent-on-indexed-inputs` (major) — subject hash `365fad455369945a`; skill `advance-galaxy-draft-step` rev 11 hash `677bb3288b4b88a5`
- `udt-authoring-note-silent-on-busybox-userland` (major) — subject hash `365fad455369945a`; skill `validate-galaxy-workflow` rev 5 hash `74e3743fc376f33c`
- `udt-authoring-note-silent-on-dollar-brace` (minor) — subject hash `365fad455369945a`; skill `advance-galaxy-draft-step` rev 11 hash `677bb3288b4b88a5`
- `udt-dollar-escape-passed-literally` (minor) — subject hash `365fad455369945a`; skill `validate-galaxy-workflow` rev 5 hash `74e3743fc376f33c`

## Cluster K — comment on #654

Canonical locator: `content/molds/advance-galaxy-draft-step/index.md`

### Comment on #654 — the implement-by-copy side, from a twin-heavy draft

> Posted by an AI assistant on <user>'s behalf.

nf-core/oncoanalyser produced twins at template time rather than by repair: tumor and normal `bwa_mem2` alignment, and tumor and normal REDUX. Eleven authored UDT definitions served 12 hmftools steps. `advance-galaxy-draft-step` advances one drafty step per call, so realizing a twin set means re-reading the same evidence once per member, and nothing says the second twin should be a copy of the first. The run realized 18 steps in 5 batched iterations, copying definitions and state across twins.

**Suggestion (fits #654's implement-by-copy correction):** allow realizing a twin or sibling set in one iteration when the members share a wrapper or authored definition, record one iteration per set, and diff the set afterwards. Main's `advance-galaxy-draft-step` has changed since the cast (`12f242dd…`) but still advances one step per call.

- `advance-step-one-step-per-call-vs-twins` (minor) — subject hash `677bb3288b4b88a5`; skill `advance-galaxy-draft-step` rev 11 hash `677bb3288b4b88a5`

## Cluster L — new issue

Canonical locator: `https://test.galaxyproject.org (related project)`

### New issue — related project: test.galaxyproject.org UDT runner resource limits and first-pull latency

> Posted by an AI assistant on <user>'s behalf.

**Suspected upstream:** test.galaxyproject.org's user-defined-tool job runner (udt-scratch / apptainer destination).

- A UDT declaring `requirements: [{type: resource, ram_min: 16384, cores_min: 8}]` ran with `GALAXY_MEMORY_MB=3788` and `GALAXY_SLOTS=4`, so resource requirements on UDTs appear ignored or capped.
- The first job using `quay.io/biocontainers/hmftools-amber:4.3--hdfd78af_0` stayed `running` for over 15 minutes on a few-byte input; a samtools-image UDT finished in about a minute. The same image ran quickly afterwards, consistent with first-pull latency.

**Why upstream:** server resource mapping and image caching. **Meanwhile, the Foundry should:** record in its target-server guidance that UDT jobs on test.galaxyproject.org get ~3.8 GB / 4 slots and that first pulls of large images can take 15+ minutes, so runs neither plan heavy UDT tests there nor misread a pull as a hang.

- `udt-first-job-container-pull-latency` (minor) — subject hash `n/a`; skill `advance-galaxy-draft-step` rev 11 hash `677bb3288b4b88a5`
- `target-ignores-udt-ram-min` (minor) — subject hash `n/a`; skill `validate-galaxy-workflow` rev 5 hash `74e3743fc376f33c`

## Cluster M — new issue

Canonical locator: `package://@galaxy-foundry/gxwf-foundry#testDataRefsSchema`

### New issue — test-data-refs: no way to record an optional input deliberately left unset

> Posted by an AI assistant on <user>'s behalf.

An optional workflow input that the source test leaves unset (oncoanalyser `driver_gene_panel`, which defaults to a bundle member) can only be written as `resolved: false` / `storage: unresolved`. That reads as a gap, and tells the test-data-resolution branch to fall through to find-test-data. The harness had to judge the branch settled by hand. A prior run (nf-core/demo) logged the same need for scalars and omitted optionals.

**Expected:** a way to say "omitted by design" (e.g. `storage: omitted`, or `resolved: true` with a null fixture and a reason), so source-unset optionals aren't treated as search work.

- `test-data-refs-no-intentionally-omitted-optional` (minor) — subject hash `534dcb2f44e24a33`; skill `nextflow-to-test-data` rev 4 hash `842e097edfb5bfbc`

## Cluster N — new issue

Canonical locator: `content/molds/nextflow-test-to-galaxy-test-plan/index.md`

### New issue — nextflow-test-to-galaxy-test-plan declares only summary-nextflow as input

> Posted by an AI assistant on <user>'s behalf.

Producing a plan with resolved labels needed:
- `galaxy-workflow.gxwf.yml` (or the interface brief) for labels
- `test-data-refs.json` for fixtures
- the open-requirements ledger, for snapshot entries out of scope after narrowing
- the raw `.nf.test.snap`: the summary carries snapshot structure, but per-file md5 tokens came from `content[1]` of the sidecar

None of these is a declared input. A prior run (nf-core/demo) logged the same gap under the same entry id.

**Expected:** declare `galaxy-workflow` (or the interface brief), `test-data-refs` and `open-requirements-ledger` as inputs, and say whether per-file snapshot checksums come from the summary or the `.snap` sidecar.

- `test-plan-mold-declares-only-summary-input` (major) — subject hash `fa769216f621ef25`; skill `nextflow-test-to-galaxy-test-plan` rev 8 hash `fa769216f621ef25`
