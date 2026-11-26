# Foundry run review — minderoo-module2

Pipeline `nextflow-to-galaxy` (harness revision 5), run `minderoo-module2`, source Minderoo-OceanOmics-Centre-UWA/OceanOmics-amplicon-nf @416807e (public). Run status **complete**: all 13 phases are `done` and every phase is `feedback_checked: true`. The phase-7 loop ran 51 iterations with 2 topology repairs, and the phase-8 branch selected `find-test-data`.

**The workflow test did not pass.** Phase 12 (run-workflow-test) and phase 13 (debug-galaxy-workflow-output) were rerun on test.galaxyproject.org (Galaxy 27.0) as an external Galaxy. The last run was attempt 5 (invocation `80211d01bf2a8c51`, `planemo workflow_test_on_invocation` exit 1): 61 of 73 steps scheduled, and 43 jobs ok, 4 failed and 8 paused.

| Attempt | Result | Fix before the next attempt |
|---|---|---|
| 1 | Import refused, 403: no permission to run user-defined tools | Account given the permission |
| 2 | Import refused, 400: unterminated `$(` in a user-tool configfile comment | Comment removed |
| 3 | Invocation failed at a `__MERGE_COLLECTION__` step whose connections had no repeat instances | Repeat instances added to the four merge steps |
| 4 | 4 jobs failed: three user tools on `ubuntu:20.04` were refused because the server runs only `quay.io/biocontainers` images, and DADA2 gave an empty table | The three tools moved to a biocontainers image |
| 5 | 4 jobs failed: LULU's Docker Hub image was refused, and the empty DADA2 table broke three jobs on the ASV set (seqCounts, the LULU self-database, BLAST) | Not fixed: five custom-image tools and a too-small test dataset remain |

The three swapped tools all ran in attempt 5. The steps after LULU (curation, merges, LCA, NBC, phyloseq and the filters) have still not run. Details are in `<run>/workflow-debug-report.md` and `<run>/workflow-test-result.json`.

**Ledger:** 34 entries (15 major, 19 minor). This review triaged all 34. Before it, all were `open` with no issue. Five entries appended during the phase 12/13 reruns are included: one from report-foundry-run-feedback and four from debug-galaxy-workflow-output.

**Main checked** at `galaxyproject/foundry@df991d0d789b` (2026-11-11), against the previous check at `94ce4ea` (2026-11-09). Four subject files changed since the bundle was cast:
- `galaxy-user-tool-authoring`: commit 28b4a96, escaping rules and job shell.
- `discover-shed-tool`.
- `galaxy-workflow-draft-format`.
- The `summarize-nextflow` Mold: commits for #665.

The `summarize-nextflow` package schema also gained `resolved_args`, `publish_dir` and `template` (#665). Only two entries are corrected on main: the `$(` escaping entry and the ext.args entry. The other changed files do not contain the requested corrections.

**Duplicate search:** all 313 issues in `galaxyproject/foundry`, open and closed, with their 167 comments, were searched locally by keyword for each entry. GitHub's own search returned almost nothing for multi-word queries. The user filed #769, #770, #771, #772, #786, #787 and #788 by hand from this run, and commented on #769 and #666.

**How those map to the ledger:**
- #771 → `summarize-nextflow-cli-drops-draft07-definitions-params`.
- #772 → `summarize-nextflow-cli-ignores-literal-container-directives`.
- #786 → `udt-authoring-prefers-source-container-that-usegalaxy-refuses`.
- The #666 comment (point 2, test-candidate inputs) together with open #763 (profile default, not filed by the user) → `summarize-nextflow-cli-test-candidate-profile-default-and-inputs`.
- #769 (route scope; the comment adds profile choice), #770 (fact-check drafts, missed duplicate), #787 (param defaults from the schema, not `nextflow.config`) and #788 (test history name, invocation link) were filed from this run but match no ledger entry. They are run findings in their own right and are listed here so the report is complete.

**Integrity and redaction notes:**
1. Four entries were recorded without a subject `content_hash`. Two were recovered from bundle provenance: the foundry CLI reference `85505b02…`, unchanged on main, and `galaxy-workflow-draft-format` `e9b84eeb…`, changed on main. The pipeline subject has no hash anywhere, so its last change date (2026-09-23, before the run) was checked instead. The package-export schema was checked by field.
2. Phase-7 entries name advance-galaxy-draft-step in `observed_in` for work done through its sub-skills, because the run loaded each sub-skill once. That is itself entry 1.
3. Seven entries repeat observations from an earlier, unfiled ledger of the same pipeline on the same source (`minderoo-module4`, stopped at phase 3). They are reported once here.
4. One entry (`summarize-nextflow-cli-test-candidate-profile-default-and-inputs`) is covered by two issues, so its `issue` field is a list of two URLs rather than one.
5. The ledger has no `fixed` status, so the entry corrected on main without an issue stays `open` with `issue: null`, and its disposition here is `fixed`.
6. Redaction: the ledger and drafts contain no credentials, API keys, user paths or private URLs. The run directory is written as `<run>/`. The test server, the public source repository and its public test-data repository are named.

**Totals:** 4 filed, 1 duplicate, 1 fixed, 3 comment drafts, 25 new-issue drafts. Nothing is `local-only` or `wontfix`.

| # | Entry | Sev | Subject | Main (`df991d0d789b`) | Disposition |
|---|---|---|---|---|---|
| 1 | `loop-per-iteration-subskill-invocation-cost` | major | pipeline `content/pipelines/nextflow-to-galaxy/index.md` | unchanged since 2026-09-23 | issue-draft §1 (cites closed #547) |
| 2 | `udt-authoring-note-missing-element-identifier-and-collection-inputs` | major | research `content/research/galaxy-user-tool-authoring/index.md` | changed: escaping half fixed by 28b4a96, `element_identifier` still absent | comment-draft #672 §2 |
| 3 | `operators-note-no-recipe-for-key-rewriting-map-mix-join` | major | research `content/research/nextflow-operators-to-galaxy-collection-recipes/index.md` | unchanged | issue-draft §3 |
| 4 | `interface-no-rule-for-entry-branch-selection` | major | research `content/research/nextflow-params-to-galaxy-inputs/index.md` | unchanged | comment-draft #674 §4 |
| 5 | `refdata-classification-misses-hidden-runtime-references` | major | research `content/research/nextflow-reference-data-classification/index.md` | unchanged | issue-draft §5 |
| 6 | `galaxy-blastdbn-composite-lacks-v5-volumes` | major | related project: Galaxy `lib/galaxy/datatypes/blast.py` | n/a | issue-draft §6 |
| 7 | `no-preflight-for-user-tool-permission` | major | mold `content/molds/run-workflow-test/index.md` | unchanged | comment-draft #730 §7 (#786 covers the container half) |
| 8 | `summarize-nextflow-cli-drops-draft07-definitions-params` | major | cli-command `content/cli/foundry/index.md` | not fixed | **filed #771** |
| 9 | `summarize-nextflow-cli-ignores-literal-container-directives` | major | cli-command `content/cli/foundry/index.md` | not fixed | **filed #772** |
| 10 | `summarize-nextflow-cli-test-candidate-profile-default-and-inputs` | major | cli-command `content/cli/foundry/index.md` | not fixed | **filed: #763 (profile default) and #666 comment (inputs)** |
| 11 | `summary-nextflow-schema-no-field-for-ext-args` | major | schema `package://@galaxy-foundry/summarize-nextflow#summaryNextflowSchema` | `processes[].resolved_args` added | **duplicate of closed #665** (`ext.when` is open #791) |
| 12 | `galaxy-tool-cache-summarize-bare-id-with-version-fails` | minor | related project: galaxy-tool-util-ts CLI | n/a | issue-draft §8 (related #552, #323) |
| 13 | `discover-shed-tool-fixed-pin-filename-clobbers-in-loop` | minor | mold `content/molds/discover-shed-tool/index.md` | changed, correction absent | issue-draft §9 |
| 14 | `blastn-wrapper-column-group-order-undocumented` | minor | related project: `devteam/ncbi_blast_plus/ncbi_blastn_wrapper` | n/a | issue-draft §10 |
| 15 | `iuc-vsearch-wrappers-lack-unoise-uchime3-otutab` | minor | related project: `iuc/vsearch` | n/a | issue-draft §11 |
| 16 | `iwc-compare-no-retrieval-procedure` | minor | mold `content/molds/compare-against-iwc-exemplar/index.md` | unchanged | issue-draft §12 |
| 17 | `debug-procedure-no-branch-for-not-run-or-permission-403` | minor | mold `content/molds/debug-galaxy-workflow-output/index.md` | unchanged | issue-draft §13 |
| 18 | `find-test-data-no-guidance-for-moving-reference-snapshots` | minor | mold `content/molds/find-test-data/index.md` | unchanged | issue-draft §14 |
| 19 | `operators-note-no-split-chunk-scatter-recipe` | minor | research `content/research/nextflow-operators-to-galaxy-collection-recipes/index.md` | unchanged | issue-draft §15 |
| 20 | `interface-no-guidance-for-config-preset-maps` | minor | research `content/research/nextflow-params-to-galaxy-inputs/index.md` | unchanged | issue-draft §16 |
| 21 | `refdata-mapping-no-blastdb-guidance` | minor | research `content/research/nextflow-to-galaxy-reference-data-mapping/index.md` | unchanged | issue-draft §17 (related #219) |
| 22 | `draft-format-identity-pin-vs-versioned-tool-id` | minor | research `content/research/galaxy-workflow-draft-format/index.md` | changed, correction absent | issue-draft §18 |
| 23 | `draft-format-combine-node-smell-misfires-on-key-join` | minor | research `content/research/galaxy-workflow-draft-format/index.md` | changed, rule unchanged | issue-draft §19 (refines closed #303) |
| 24 | `test-plan-assumes-nf-test-evidence` | minor | mold `content/molds/nextflow-test-to-galaxy-test-plan/index.md` | unchanged | issue-draft §20 |
| 25 | `nextflow-to-test-data-no-rule-for-dead-declared-urls-and-derived-fixtures` | minor | mold `content/molds/nextflow-to-test-data/index.md` | unchanged | issue-draft §21 |
| 26 | `summarize-nextflow-cli-misses-backslash-multi-alias-include` | minor | cli-command `content/cli/foundry/index.md` | not fixed (resolver commits since do not touch includes) | issue-draft §22 |
| 27 | `summarize-nextflow-samplesheet-schema-vs-live-consumer-drift` | minor | mold `content/molds/summarize-nextflow/index.md` | changed, correction absent | issue-draft §23 |
| 28 | `summarize-nextflow-procedure-omits-foundry-cli-entrypoint` | minor | mold `content/molds/summarize-nextflow/index.md` | changed, correction absent | issue-draft §24 |
| 29 | `gxwf-connections-merge-collection-type-unresolved` | minor | related project: galaxy-tool-util-ts CLI | n/a | issue-draft §25 (related #648) |
| 30 | `report-feedback-runtime-note-contradicts-main-check` | minor | mold `content/molds/report-foundry-run-feedback/index.md` | unchanged | issue-draft §26 (related #770) |
| 31 | `udt-authoring-note-dollar-paren-parsed-in-comments` | major | research `content/research/galaxy-user-tool-authoring/index.md` | 28b4a96: every `$(`/`${` is a delimiter, escape as `\$(`, applies to configfiles; comments not named but covered | **fixed** |
| 32 | `gxwf-validate-accepts-unbalanced-udt-expression` | major | related project: galaxy-tool-util-ts CLI | n/a | issue-draft §27 (related #644, #652) |
| 33 | `gxwf-strict-state-accepts-repeat-connection-without-instance` | major | related project: galaxy-tool-util-ts CLI | n/a | issue-draft §28 (related #644) |
| 34 | `udt-authoring-prefers-source-container-that-usegalaxy-refuses` | major | research `content/research/galaxy-user-tool-authoring/index.md` | §7 still prefers the source's container | **filed #786** |

Drafts are in `<run>/foundry-issue-drafts.md`: 25 new-issue drafts and 3 comment drafts. Their numbering differs from the 2026-11-10 version.

**Posting:** nothing was posted or filed by this review. The four `filed` entries and the one `duplicate` record issues that already exist: the user filed #771, #772 and #786 by hand and wrote the comment on #666; #763 and #665 were filed by others. All other entries stay `open` with `issue: null`.

**Feedback pass for this review:** no new entry. The one friction this pass hit, reading Foundry main despite the runtime note, is already entry 30. The miss of #763 in the first pass is covered by #770.
