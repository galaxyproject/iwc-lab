# Foundry issue drafts — nf-core/demo → Galaxy run

Target repository for every draft: `galaxyproject/foundry`. Nothing here has been posted.
Foundry main checked: `94ce4ea2` (2026-11-09). Every hashed Foundry subject below is unchanged on main (sha256 of the file equals the ledger `content_hash`).
Each posted body must begin with `Posted by an AI assistant on <user>'s behalf.`; no @-mentions.

Index (posting order suggestion):

| # | Kind | Target | Subject | Severity | Entries |
|---|---|---|---|---|---|
| D1 | comment | #762 | summarize-nextflow edge extraction | major | summarize-nextflow-cli-edges-tokenize-multiline-call-args |
| D2 | comment | #764 | nextflow-snapshot-to-galaxy-assertions (.gz md5) | major | snapshot-note-silent-on-gz-md5-semantics |
| D3 | comment | #666 | summarize-nextflow getGenomeAttribute in main.nf | minor | summarize-nextflow-misses-getgenomeattribute-in-main-nf |
| D4 | comment | #580 | frame comments without position/size | major | gxwf-accepts-frames-without-position-size |
| D5 | comment | #576 | scalar inputs in test plan + test-data-refs | minor | test-plan-fixture-no-scalar-value, test-data-refs-no-shape-for-scalar-inputs |
| D6 | comment | #743 | paired_or_unpaired → flatten → reduction recipe | major | collection-patterns-no-paired-or-unpaired-to-reduction-recipe |
| D7 | new | — | run-workflow-test: container-only recipe on docker-less hosts | major | run-workflow-test-no-guidance-container-only-planemo |
| D8 | new | — | summary-nextflow: samplesheet channel built in a utility subworkflow | major | summary-omits-samplesheet-channel-construction-in-utility-subworkflow |
| D9 | new | — | summarize-nextflow: utility subworkflows classified `pipeline` | minor | summarize-nextflow-cli-utility-subworkflows-classified-pipeline |
| D10 | new | — | reference-data classification: declared-but-unconsumed asset | minor | reference-classification-no-unconsumed-template-asset-case |
| D11 | new | — | params-to-inputs: duplicate sample rows merged by groupTuple | minor | params-to-inputs-no-rule-for-duplicate-sample-rows |
| D12 | new | — | interface Mold: identifier-uniqueness rule lives only in data-flow Mold | minor | identifier-uniqueness-rule-only-in-data-flow-mold |
| D13 | new | — | compare-against-iwc-exemplar: secondary-exemplar idiom excerpts | minor | iwc-exemplar-no-guidance-for-multi-exemplar-idiom |
| D14 | new | — | advance-galaxy-draft-step: loop gates skip strict structure | minor | draft-loop-validation-skips-strict-structure |
| D15 | new | — | advance-galaxy-draft-step: lighter path for exemplar-pinned steps | minor | harness-loop-ran-leaf-skills-inline |
| D16 | new | — | nextflow-to-galaxy pipeline: implement-test "run green" vs later run phase | minor | implement-test-run-green-duplicates-run-workflow-test |
| D17 | new | — | gxwf (galaxy-tool-util-ts): convert --compact noise; strict-state null message | minor | gxwf-convert-compact-leaves-null-and-uuid-noise, strict-state-null-optional-data-message-unclear |
| D18 | new | — | debug-galaxy-workflow-output: persistent-server bisection recipe | minor | debug-bisection-needs-managed-galaxy-recipe |

Not drafted (see `foundry-run-review.md`): the planemo 0.75.47 KeyError is **fixed** (pin 0.75.48, #765). The Galaxy embedded-UDT IntegrityError is a **duplicate**: galaxy#24471, fixed by galaxy#24475, and already recorded in Foundry #726. This run hit it only because its Galaxy checkout (2026-10-07) predated the fix, and it was re-verified fixed on master `7c18ab768ac`. `--profile` default: duplicate of open #763. Tool-cache raw XML: duplicate of open #553/#648.

---

## D1 — comment on #762 (summarize-nextflow splits a multi-line closure argument)

- Subject: `package://@galaxy-foundry/gxwf-foundry#summarize-nextflow` (cli-command; no content hash recorded)
- Observed in: Mold `summarize-nextflow` rev 18, `content/molds/summarize-nextflow/index.md` sha256 `fb19fff9…` (unchanged on main)
- Entry: `summarize-nextflow-cli-edges-tokenize-multiline-call-args`

> Posted by an AI assistant on <user>'s behalf.
>
> Independent reproduction from a second nf-core/demo 1.2.0 → Galaxy run, plus one adjacent symptom not in the issue body.
>
> - Same split: the `MULTIQC(...)` call in `workflows/demo.nf` produced ~12 edges whose `from` values were Groovy fragments (`[`, `]`, `}`, `[]`, ternary halves). Reconciled by hand in the LLM pass.
> - **Also:** the zero-argument process call `COWPY()` produced no edge and no call record, so a source process with no inputs disappears from the DAG. Any fix that parses call arguments as one balanced expression should also record zero-argument invocations.

## D2 — comment on #764 (nf-test md5 of *.gz is over decompressed content)

- Subject: `content/research/nextflow-snapshot-to-galaxy-assertions/index.md`, sha256 `6d1009543d1b…` (unchanged on main)
- Observed in: Mold `nextflow-test-to-galaxy-test-plan` rev 8, sha256 `fa769216…`
- Entry: `snapshot-note-silent-on-gz-md5-semantics`

> Posted by an AI assistant on <user>'s behalf.
>
> Second nf-core/demo run, confirming the prescription in the issue end to end:
>
> - The Galaxy `seqtk_trimfq` 1.5+galaxy0 wrapper compresses with `pigz`; nf-core uses `gzip --no-name`. The compressed bytes differ (md5 `df27878f…` vs snapshot `7dd2fd0d…`), but the decompressed content of all six trimmed files equals the snapshot md5s exactly.
> - Repair that passes: `file:` fixtures for the four distinct trimmed FASTQs (regenerated with `seqtk trimfq -q 0.05 -l 30` from the wrapper's own container and checked byte-for-byte against the snapshot md5s), with `decompress: true` + `compare: diff` per collection element. Planemo test passed on Galaxy master (26.1.3.dev0).
> - An interim `has_n_lines` + `has_line` with `decompress: true` also passed, but it is weaker. The note should rank the file-diff route first when the expected content can be regenerated deterministically.

## D3 — comment on #666 (item 4, getGenomeAttribute provenance)

- Subject: `package://@galaxy-foundry/gxwf-foundry#summarize-nextflow`
- Observed in: Mold `nextflow-summary-to-galaxy-reference-data` rev 5, sha256 `b49bae31…`
- Entry: `summarize-nextflow-misses-getgenomeattribute-in-main-nf`

> Posted by an AI assistant on <user>'s behalf.
>
> Item 4 also reproduces on the plain nf-core template (nf-core/demo 1.2.0): `main.nf` assigns `params.fasta = getGenomeAttribute('fasta')`, but the summary records `fasta.source_kind: nextflow_schema` with a null `source_expression`. Every template-derived pipeline will hit this, not only rnaseq-sized ones.

## D4 — comment on #580 (frame comments without position/size)

- Subject (related project): `@galaxy-tool-util/cli gxwf validate --strict` (comments frame schema), https://github.com/jmchilton/galaxy-tool-util-ts
- Entry: `gxwf-accepts-frames-without-position-size`

> Posted by an AI assistant on <user>'s behalf.
>
> Reproduced again in an nf-core/demo run: Galaxy import returned 400 `Field required in ("frame","position")` / `("frame","size")`. Besides `draft-validate --concrete`, the **terminal** `gxwf validate --strict` also accepted the frames without them, so no gate in the pipeline catches this. Until the gxwf schema marks `position`/`size` as required, the template Mold and the comments note should always emit both.

## D5 — comment on #576 (scalar workflow parameters need a fixture)

- Subjects: `package://@galaxy-foundry/gxwf-foundry#galaxyWorkflowTestPlanSchema` (sha256 `03fc1d58…`) and `package://@galaxy-foundry/gxwf-foundry#testDataRefsSchema` (sha256 `534dcb2f…`)
- Entries: `test-plan-fixture-no-scalar-value`, `test-data-refs-no-shape-for-scalar-inputs`

> Posted by an AI assistant on <user>'s behalf.
>
> Same gap from an nf-core/demo run, plus the upstream half: `testDataRefsSchema` has the same problem. It requires "one ref per workflow input", and a resolved ref needs a fixture location or elements, so the boolean `skip_trim` and the optional string `multiqc_title` could not be recorded at all and were left out of `test-data-refs.json`. In the test plan, `skip_trim=false` had to go into `fixture.location` as the string `"false"` with `storage: null`. Suggested fix for both schemas: an optional `value` with `source: default | params_delta`, used instead of a fixture for scalar inputs (or state that test-data-refs covers data inputs only).

## D6 — comment on #743 (establish list:paired_or_unpaired examples)

- Subject: `content/patterns/galaxy-collection-patterns.md`, sha256 `2dbb4b7520ba…` (unchanged on main)
- Observed in: Mold `nextflow-summary-to-galaxy-template` rev 10
- Entry: `collection-patterns-no-paired-or-unpaired-to-reduction-recipe`

> Posted by an AI assistant on <user>'s behalf.
>
> A candidate worked example, verified at runtime, from an nf-core/demo translation (mixed single/paired samplesheet):
>
> `reads: list:paired_or_unpaired` → `__FLATTEN__` (`join_identifier: _`) → FastQC and seqtk map over the flat list → MultiQC (`multiple="true"`) reduces it.
>
> Observed identifiers after flattening: `<element>_forward`, `<element>_reverse`, `<element>_unpaired`. Flattening is needed because the bundled collection semantics reject `list:paired_or_unpaired` on a multi-data input, so mapping FastQC directly over the nested input breaks the MultiQC reduction. Planemo test passed on Galaxy master.
>
> Foundry-side ask: add this as a pattern (or a section of the flatten-after-fan-out pattern), state the suffixes, and cross-link it from the mixed-reads row of `nextflow-to-galaxy-channel-shape-mapping`.

## D7 — new issue: run-workflow-test has no container-only recipe for docker-less (HPC) hosts

- Subject: `content/molds/run-workflow-test/index.md`, sha256 `6e312c6ee27e…` (unchanged on main)
- Related but distinct: #730 (UDT and data-table guidance; it does not cover dependency resolution)
- Entry: `run-workflow-test-no-guidance-container-only-planemo`

> Posted by an AI assistant on <user>'s behalf.
>
> **Summary.** `run-workflow-test` says a Planemo-managed Galaxy "installs the workflow's tools from the Tool Shed/conda". It gives no recipe for a host with Apptainer but no Docker, where neither default works.
>
> **Observed (nf-core/demo → Galaxy, planemo 0.75.48, RHEL 9 HPC node, Apptainer):**
> - Default conda resolution: conda's `#!/usr/bin/env python` shebang resolved to Galaxy's venv Python (`No module named 'conda'`). Every Tool Shed install was marked failed, and the invocation was refused with "tools not installed".
> - `--biocontainers` alone: Apptainer converted each `docker://` image locally, taking over 10 minutes per image and repeating for MultiQC.
> - Prefetching ready `.sif` files from `depot.galaxyproject.org/singularity/` (names from `mulled-hash` over the wrapper requirements) took under a minute for all images. With them, the test passed.
> - Galaxy also needs Python ≥ 3.10. On a host whose `python3` is 3.9, `planemo serve/test` fails at `common_startup.sh` unless `--galaxy_python_version 3.12` is passed with a 3.12 interpreter on `PATH`.
> - A long `TMPDIR` (here a 166-character agent scratch path) makes Galaxy's Celery forkserver fail with `OSError: AF_UNIX path too long`. `__DATA_FETCH__` then sits in `running` indefinitely, with no job error and no Planemo error. A short `TMPDIR` (under 108 characters including the socket name) fixes it. The recipe should say to set one.
>
> **Expected.** Document a container-first recipe:
> - a job conf with `singularity_enabled: true` and `require_container: true`;
> - `--no_dependency_resolution --no_conda_auto_install --no_conda_auto_init`;
> - a `container_resolvers` file (`explicit_singularity` + `cached_mulled_singularity` pointing at a directory of prefetched depot `.sif` files);
> - how to derive image names with `mulled-hash`;
> - the Python version note.

## D8 — new issue: summary-nextflow misses the samplesheet channel built in a utility subworkflow

- Subject: `package://@galaxy-foundry/summarize-nextflow#summaryNextflowSchema`, sha256 `839e11b1…`
- Observed in: Mold `nextflow-summary-to-galaxy-interface` rev 6, sha256 `43966773…`
- Related: #211 (one-hop `from_param` bindings; a different case)
- Entry: `summary-omits-samplesheet-channel-construction-in-utility-subworkflow`

> Posted by an AI assistant on <user>'s behalf.
>
> **Summary.** In nf-core template pipelines, the only data-input channel (`ch_samplesheet`) is built inside the utility subworkflow `PIPELINE_INITIALISATION`: `samplesheetToList` → `map` → `groupTuple` → validate → `flatten`. `workflow.channels[]` only covers the primary workflow, so the summary has no channel with `from_param: input`, and the `groupTuple` multi-run merge is lost.
>
> **Evidence.** nf-core/demo 1.2.0, `subworkflows/local/utils_nfcore_demo_pipeline/main.nf` lines 109–125. The summary has no `from_param == "input"` channel. The interface Mold's translation order (index channels by `from_param`) found nothing, and the source tree had to be read by hand.
>
> **Expected.** Record channels that utility subworkflows emit into the primary workflow's `take:` (at least the samplesheet one) with `construct: samplesheetToList`, `from_param: input` and the literal operator chain, or add a `sample_sheets[].materialization` field carrying the post-parse chain.

## D9 — new issue: summarize-nextflow classifies utility subworkflows as `pipeline`

- Subject: `package://@galaxy-foundry/gxwf-foundry#summarize-nextflow`
- Observed in: Mold `summarize-nextflow` rev 18, sha256 `fb19fff9…`
- Entry: `summarize-nextflow-cli-utility-subworkflows-classified-pipeline`

> Posted by an AI assistant on <user>'s behalf.
>
> On nf-core/demo 1.2.0, `PIPELINE_INITIALISATION`, `PIPELINE_COMPLETION` and `UTILS_NFSCHEMA_PLUGIN` were emitted as `kind: pipeline` although they call no pipeline process. Free functions (`samplesheetToList`, `paramsHelp`, `completionEmail`) were listed in `calls[]`. The Mold and schema both cite `PIPELINE_INITIALISATION` as the canonical utility example.
>
> **Expected.** Classify a subworkflow as `pipeline` only when its transitive calls reach a process, and keep free-function names out of `calls[]`.

## D10 — new issue: reference-data classification has no rule for a declared-but-unconsumed asset

- Subject: `content/research/nextflow-reference-data-classification/index.md`, sha256 `2b33f3bddb63…` (unchanged on main)
- Observed in: Mold `nextflow-summary-to-galaxy-reference-data` rev 5
- Entry: `reference-classification-no-unconsumed-template-asset-case`

> Posted by an AI assistant on <user>'s behalf.
>
> The `None` class is detected by "no path-shaped reference asset and no `getGenomeAttribute` call". nf-core template pipelines such as nf-core/demo declare `fasta`/`genome` and call `getGenomeAttribute`, yet no process consumes them (`reference_assets[fasta].used_by == []`, `reference_rebuilds == []`). The note has no rule for this case, so the run decided by hand.
>
> **Expected.** A `reference_assets[]` entry with an empty `used_by` and no rebuild is template scaffolding. Classify it `None` and record a dropped ledger entry that cites the empty `used_by`.

## D11 — new issue: params-to-inputs has no rule for duplicate sample rows merged by groupTuple

- Subject: `content/research/nextflow-params-to-galaxy-inputs/index.md`, sha256 `b65bf1a16cb9…` (unchanged on main)
- Observed in: Mold `nextflow-summary-to-galaxy-interface` rev 6
- Entry: `params-to-inputs-no-rule-for-duplicate-sample-rows`

> Posted by an AI assistant on <user>'s behalf.
>
> The sample-sheet table covers optional second mates but not the common nf-core idiom of several rows sharing one `sample` (multi-run/multi-lane) merged by `groupTuple`. Galaxy element identifiers must be unique. The run had to choose between per-row elements, `list:list` keyed by sample, and a pre-merge step without guidance. The nf-core/demo test sheet lists `SAMPLE3_SE` twice.
>
> **Expected.** Add a row covering both options: nested `list:list` / `list:list:paired_or_unpaired` keyed by sample, or per-row elements with a recorded dropped grouping when every consumer works per file. State which is the default.

## D12 — new issue: identifier-uniqueness rule lives only in the data-flow Mold

- Subject: `content/molds/nextflow-summary-to-galaxy-interface/index.md`, sha256 `439667733915…` (unchanged on main)
- Raised by: Mold `nextflow-summary-to-galaxy-data-flow` rev 8, sha256 `f71cc2b4…`
- Entry: `identifier-uniqueness-rule-only-in-data-flow-mold`

> Posted by an AI assistant on <user>'s behalf.
>
> The rule "key each element on something unique per dataset; a positional `_1`/`_2` suffix means a mate only when every row is paired" appears only in `nextflow-summary-to-galaxy-data-flow`. Element identifiers are first chosen in the interface Mold. In an nf-core/demo run, the interface brief proposed `SAMPLE3_SE_1`/`_2` for repeated single-end rows, and the data-flow step had to override it.
>
> **Expected.** Move or duplicate the rule into `nextflow-summary-to-galaxy-interface`, or into its testability note.

## D13 — new issue: compare-against-iwc-exemplar assumes a single exemplar supplies every idiom

- Subject: `content/molds/compare-against-iwc-exemplar/index.md`, sha256 `84abb427cbcb…` (unchanged on main)
- Entry: `iwc-exemplar-no-guidance-for-multi-exemplar-idiom`

> Posted by an AI assistant on <user>'s behalf.
>
> The domain-nearest IWC workflow (short-read QC/trimming, fastp-based) lacked the key idiom (FastQC `text_file` → MultiQC `software=fastqc`). Only a low-confidence cross-domain workflow (MGnify amplicon QC) carried it. Nothing says whether a secondary exemplar's step may be spliced into `iwc-exemplar.gxwf.yml`, so the run did it by hand with an in-file provenance note (IWC @ 9f111cb).
>
> **Expected.** Allow secondary idiom excerpts and specify their shape: per-step provenance comments or a separate keyed section, labelled with the source workflow id and confidence.

## D14 — new issue: draft-loop validation gates skip strict structure checks

- Subject: `content/molds/advance-galaxy-draft-step/index.md`, sha256 `677bb3288b4b…` (unchanged on main)
- Raised by: Mold `validate-galaxy-workflow` rev 5, sha256 `74e3743f…`
- Entry: `draft-loop-validation-skips-strict-structure`

> Posted by an AI assistant on <user>'s behalf.
>
> The template wrote comment frames with `colour:` (typo for `color`). `draft-validate --concrete --strict-state` in the template step and in all four draft-loop iterations accepted it. Only the terminal `gxwf validate --strict` rejected it (`comments.0.colour is unexpected`), two phases later.
>
> **Expected.** Run `draft-validate` with `--strict` (or at least `--strict-structure`) in the template and per-step loop gates, so unknown envelope keys fail in the phase that wrote them.

## D15 — new issue: advance-galaxy-draft-step has no lighter path for exemplar-pinned steps

- Subject: `content/molds/advance-galaxy-draft-step/index.md`, sha256 `677bb3288b4b…`
- Entry: `harness-loop-ran-leaf-skills-inline`

> Posted by an AI assistant on <user>'s behalf.
>
> Three steps (FastQC, seqtk, MultiQC) had wrapper ids taken directly from an IWC exemplar. Running `discover-shed-tool` → `summarize-galaxy-tool` → `implement-galaxy-tool-step` as separate skill invocations for each was disproportionate. The run resolved version/changeset with `gxwf tool-revisions`, summarized via the tool cache, and bound state inline, and validation passed.
>
> **Expected.** Explicitly allow that shortcut for an exemplar-confirmed, identity-pinned step.

## D16 — new issue: pipeline should say whether implement-galaxy-workflow-test runs Planemo

- Subject: `content/pipelines/nextflow-to-galaxy/index.md` (no hash recorded in the ledger; current main sha256 `4fe7fae2160f…`)
- Raised by: Mold `implement-galaxy-workflow-test` rev 11, sha256 `34855691…`
- Entry: `implement-test-run-green-duplicates-run-workflow-test`

> Posted by an AI assistant on <user>'s behalf.
>
> `implement-galaxy-workflow-test` step 5 ("Run green: drive planemo test") and its step-1 bootstrap from a real invocation both need a Planemo-managed Galaxy run. The pipeline already runs `validate-galaxy-workflow` and `run-workflow-test` as phases 11–12. Inside the pipeline, the Mold's own run gate either duplicates an expensive Galaxy boot or gets skipped, and nothing says which.
>
> **Expected.** State that when a later `run-workflow-test` phase exists, `implement-galaxy-workflow-test` stops at the static gate and hands the run to that phase.

## D17 — new issue: gxwf (galaxy-tool-util-ts) friction: `convert --compact` noise and unclear strict-state message

- Subject (related project): https://github.com/jmchilton/galaxy-tool-util-ts (`gxwf convert`, `gxwf draft-validate --strict-state`)
- Entries: `gxwf-convert-compact-leaves-null-and-uuid-noise`, `strict-state-null-optional-data-message-unclear`
- Meanwhile: the Foundry Molds that consume these outputs should state the workaround (what to strip, and "omit unconnected data inputs from state").

> Posted by an AI assistant on <user>'s behalf.
>
> Two small `gxwf` issues from an nf-core/demo run, filed here for forwarding:
>
> 1. `gxwf convert --to format2 --compact` (1.15.x) still emits `fields: null` and `column_definitions: null` on every input, a uuid per step, and full `tool_state`. A converted IWC exemplar came out at 183 lines of noise. `compare-against-iwc-exemplar` calls its artifact a "cleaned" view, but has no cleaning step. Ask: a `--clean`/`--minimal` flag, or Mold guidance on what to strip.
> 2. Setting an unconnected optional data input to `null` in state (`contaminants: null` for devteam/fastqc 0.74+galaxy1) fails `draft-validate --strict-state` with `Expected never, actual null / Expected undefined, actual null`. The fix is to omit the key, but neither the message nor the bundle says so. Ask: an actionable diagnostic ("unconnected data input: omit from state") plus a line in the implement-galaxy-tool-step references.
>
> (Raw tool XML missing from `galaxy-tool-cache summarize` is already tracked in #553 and #648 and is not repeated here.)

## D18 — new issue: debug-galaxy-workflow-output bisection needs a persistent-server recipe

- Subject: `content/molds/debug-galaxy-workflow-output/index.md`, sha256 `0ea72a26de30…` (unchanged on main)
- Related: #726 (closed; added the import-rejection surface and bisection method that are now on main)
- Entry: `debug-bisection-needs-managed-galaxy-recipe`

> Posted by an AI assistant on <user>'s behalf.
>
> Step 3 requires importing several synthetic variants "as the same user on the same server". With a Planemo-managed Galaxy, every `planemo test` boots and tears down its own server (about 4 minutes or more each), so the first nf-core/demo run recorded the bisection as a proposal and did not run it. A follow-up session ran it with this recipe, which the Mold could carry:
>
> 1. `planemo serve <workflow> --extra_tools … --job_config_file … --no_dependency_resolution …` once (so Tool Shed repos are installed);
> 2. with the bootstrap admin key, create one non-admin user, an API key, and a `user_tool_execute` role (the same calls as `planemo.galaxy.api.ensure_user_tool_execute`);
> 3. import each variant through Planemo's own conversion (`planemo.galaxy.workflows.import_workflow`), one distinct embedded tool id per variant, recording status and body;
> 4. reuse the same server for `planemo test --engine external_galaxy`.
>
> Result with this recipe: 9/9 variants imported on Galaxy master `7c18ab768ac`, including the galaxy#24471 trigger shape. The 500 the run had hit came from a **stale Galaxy checkout** (`b18269a10f8`, 2026-10-07) that predated the fix in galaxy#24475. So, in addition to the recipe, step 3 should start with: *record the Galaxy commit and check it against known upstream fixes (search the Galaxy tracker for the traceback's exception and frame) before bisecting*. That check would have saved the run attempts 5–9.

---

## Added 2026-11-10 after deployment on usegalaxy.be

| # | Kind | Target | Subject | Severity | Entries |
|---|---|---|---|---|---|
| D19 | new | — | template: frames emitted without step positions | major | template-frames-without-step-positions |
| D20 | new | — | Galaxy editor: frame fit-to-content with empty bounds saves Infinity/null | minor | galaxy-editor-frame-fit-empty-bounds-infinity |
| D21 | new | — | nextflow-to-galaxy: Nextflow-output parity report + UDT-free deployable variant | major | pipeline-no-source-output-parity-or-non-udt-variant |

## D19 — new issue: template emits frames without step positions, so frames don't enclose their steps

- Subject: `content/molds/nextflow-summary-to-galaxy-template/index.md`, sha256 `77f885d6…`
- Related: #580 (frames missing position/size)

> Posted by an AI assistant on <user>'s behalf.
>
> **Summary.** The template writes `comments:` frames with fixed `position`/`size` but no position for any step. On import Galaxy stacks the steps at (0,0), (10,10), …, so frames no longer contain their `child_steps`. In the nf-core/demo translation, the "Reporting" frame (x = 660) was empty and its MultiQC step sat at (60,60). Saving that workflow in the usegalaxy.be editor (26.1.2.dev0) then failed with `Input should be a valid number in ('frame', 'position', 0)` (see D20).
>
> **Expected.** Whenever frames are emitted, emit a position for every input and step, and size each frame around its contained steps (or emit no frames). Add a static check that each frame's `child_steps` lie inside its rectangle. A v2 of the workflow laid out this way imported with all steps inside their frames and reran 14/14 jobs OK on usegalaxy.be.

## D20 — new issue (Galaxy, for forwarding): frame fit-to-content with no contained steps saves `null` positions

- Subject (related project): https://github.com/galaxyproject/galaxy, workflow editor frame comments
- Meanwhile, the Foundry should avoid the trigger (D19).

> Posted by an AI assistant on <user>'s behalf.
>
> In `release_26.1`, `FrameComment.vue` `onFitToContent` starts from an empty `AxisAlignedBoundingBox` (`x = y = Infinity`, `client/src/utils/geometry.ts`). When no step or comment lies inside the frame, it emits `move([Infinity, Infinity])`. `JSON.stringify` turns `Infinity` into `null`, and the save is rejected: `Input should be a valid number in ('frame', 'position', 0)` / `(…, 1)`. The stored workflow was valid (positions `[0.0, 0.0]`, `[660.0, 0.0]`), so the bad value is created in the client. Observed on usegalaxy.be 26.1.2.dev0. The exact UI action before saving was not confirmed; fit-to-content is the code path that produces it.
>
> **Expected.** Leave the frame unchanged when its bounding box is empty, and reject or clamp non-finite comment coordinates before saving.

## D21 — new issue: nextflow-to-galaxy should report parity with real Nextflow outputs and ship a UDT-free variant

- Subject: `content/pipelines/nextflow-to-galaxy/index.md`
- Raised from: `run-workflow-test` rev 8 (sha256 `6e312c6e…`)

> Posted by an AI assistant on <user>'s behalf.
>
> **Summary.** Two gaps came up when the user tried to use the translated nf-core/demo workflow:
>
> 1. **No parity report against real Nextflow outputs.** The only check against the source is the nf-test snapshot. Intended differences are spread over the interface brief, the open-requirements ledger, the test plan and the debug report, and nothing compares against an actual `results/` directory. A manual comparison found:
>    - all analysis content identical;
>    - 25 reference-only files (`multiqc_data/*`, `pipeline_info/*`) and 6 Galaxy-only files (`fastqc_raw`);
>    - names differ everywhere;
>    - tool versions differ (seqtk 1.4 vs 1.5, MultiQC 1.34 vs 1.35). The seqtk difference is recorded in no Foundry artifact.
> 2. **The deliverable can't be imported on public servers.** It embeds a GalaxyUserTool, which usegalaxy.* servers don't allow. The user had to ask for a variant without the UDT (cowpy step dropped), which then ran on usegalaxy.be with 14/14 jobs OK.
>
> **Expected.**
> - An optional parity phase that takes a Nextflow `results/` directory and produces a per-file table (identical / how it differs / missing on either side), including tool-version differences.
> - A UDT-free deployable variant emitted next to the embedded form, with UDT steps dropped or replaced by an XML-tool reference, and documented as such.
