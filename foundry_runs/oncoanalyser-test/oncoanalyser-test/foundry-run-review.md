# Foundry run review — oncoanalyser-test

Pipeline `nextflow-to-galaxy` (harness rev 5), source nf-core/oncoanalyser 3.0.0. Ledger `<run>/foundry-feedback.ledger.yml`. Triaged 2026-11-11 against `galaxyproject/foundry` main `e72d75cb3a42` (2026-11-10).

> Full text for each issue and comment below (evidence, expected correction, contributing entries and hashes) is in `<run>/foundry-issue-drafts.md`. Nothing has been posted yet.

## Issues at a glance

| Cluster | Type | One-liner |
|---|---|---|
| A | new issue | summarize-nextflow resolver: four more silent defects on oncoanalyser (stub test's profile ignored, placeholder source URL/version and `--pin` re-clone, topic-only outputs misnamed, samplesheet path column typed as metadata). |
| B | comment on #666 | Same primary-workflow mistake (picks the run-mode dispatcher), and reference/rebuild detection misses rebuild steps inside subworkflows. |
| C | new issue | summarize-nextflow Mold has no guidance for pipelines with several run modes or stages switched on by samplesheet content. |
| D | comment on #219 | Reference-data note lacks a default for folder-in-a-tarball bundles, and never asks for reference size or rebuild cost. |
| E | new issue | Sample-sheet note has no mapping for long-format sheets keyed by tumor/normal role. |
| F | new issue | Channel-shape note has no Galaxy representation for channels that carry whole folders. |
| G | comment on #769 | When confirming scope at the start, also check which tools exist on the target and in the Tool Shed. |
| H | new issue | Open-requirements ledger has no `basis: user` for decisions made by asking the user. |
| I | new issue | compare-against-iwc-exemplar doesn't say whether a low-confidence match writes the exemplar file. |
| J | comment on #672 | User-defined-tool note: BAM inputs arrive without an index, images use BusyBox tools under `set -e`, and the `\$` escape rule is wrong. |
| K | comment on #654 | Let twin steps be built together by copying instead of one step per call. |
| L | new issue | test.galaxyproject.org caps user-defined-tool jobs at ~3.8 GB / 4 slots regardless of `ram_min`, and first image pulls take 15+ min (server issue, filed with the Foundry). |
| M | new issue | test-data-refs schema can't mark an optional input as deliberately left unset. |
| N | new issue | nextflow-test-to-galaxy-test-plan declares only the summary as input, but needs the workflow, test-data refs, ledger and `.snap` file. |

Also open but not drafted: `report-feedback-bundling-rule-vs-precedent`, raised during this triage. The skill's one-cluster-per-correction rule conflicts with the tracker's practice of bundling, which cluster A follows. It's held for a later triage pass.

## Run coverage

- `run.status: complete`; all 13 phases `done` and `feedback_checked: true`. Phase 7 loop: 5 iterations. Phase 8 branch selected `nextflow-to-test-data`.
- Phases 12–13 completed as recorded no-runs: the workflow test was **not executed** (user decision; references ~59 GB vs 10.7 GB quota). The ledger therefore has no runtime-failure evidence from a workflow test; its runtime observations come from small probe jobs on test.galaxyproject.org.
- Phases that reported `no feedback` explicitly: 4 (data-flow), 6 (template), 10 (implement test), 12 (run test), 13 (debug).

## Ledger integrity and redaction

- 24 entries, all `status: open`, 12 major / 12 minor (23 from the run, 1 raised during triage). No credentials, tokens or user paths found.
- Redacted from drafts: private test.galaxyproject.org history/dataset ids (kept in the ledger; not useful upstream).
- Phase-5 and phase-7 entries were appended after the phase row was marked done (same session; ordering only).
- Overlap with an earlier unfiled run ledger in this workspace (demo-test): `test-plan-mold-declares-only-summary-input` (same id), `test-data-refs-no-shape-for-scalar-or-omitted-optional`, `summarize-nextflow-cli-silent-provenance-and-profile-failure`, `summarize-nextflow-cli-misses-main-nf-getgenomeattribute`. Noted in the relevant drafts as a second observation.

## Main check

Unchanged on main (hash equal): reference-data mapping note, sample-sheet note, channel-shape note, interface Mold, compare-against-iwc-exemplar Mold, UDT authoring note, test-plan Mold, test-data-refs schema. Changed but without the correction: `content/molds/summarize-nextflow/index.md` changed on main (d8e67590…); no multi-mode/run-mode guidance added; `content/research/open-requirements-ledger/index.md` changed on main (d3d36d55…); basis still `brief-proposal | agent`; `content/molds/advance-galaxy-draft-step/index.md` changed on main (12f242dd…); still one step per call. No cluster is `fixed`.

## Dispositions

| Cluster | Subject | Disposition | Entries |
|---|---|---|---|
| A | `packages/summarize-nextflow` | issue-draft | `summarize-nextflow-cli-nftest-file-profile-and-stub-ignored`, `summarize-nextflow-cli-placeholder-provenance-and-pin-reclone`, `summarize-nextflow-cli-topic-only-outputs-misnamed`, `summarize-nextflow-cli-samplesheet-path-column-kind` |
| B | `packages/summarize-nextflow` | comment-draft on #666 | `summarize-nextflow-cli-primary-workflow-picks-mode-dispatcher`, `summarize-nextflow-cli-reference-assets-miss-genome-attributes` |
| C | `content/molds/summarize-nextflow/index.md` | issue-draft | `summarize-nextflow-mold-silent-on-multi-mode-runtime-stages` |
| D | `content/research/nextflow-to-galaxy-reference-data-mapping/index.md` | comment-draft on #219 | `reference-mapping-note-silent-on-directory-archive-bundles`, `reference-mapping-note-no-scale-or-test-feasibility-check` |
| E | `content/research/galaxy-sample-sheet-collections/index.md` | issue-draft | `sample-sheet-note-silent-on-long-format-role-rows` |
| F | `content/research/nextflow-to-galaxy-channel-shape-mapping/index.md` | issue-draft | `channel-shape-note-silent-on-directory-outputs` |
| G | `content/molds/nextflow-summary-to-galaxy-interface/index.md` | comment-draft on #769 | `interface-mold-no-target-tool-availability-check` |
| H | `content/research/open-requirements-ledger/index.md` | issue-draft | `open-requirements-decision-basis-lacks-user` |
| I | `content/molds/compare-against-iwc-exemplar/index.md` | issue-draft | `iwc-exemplar-low-confidence-sibling-file-ambiguous` |
| J | `content/research/galaxy-user-tool-authoring/index.md` | comment-draft on #672 | `udt-authoring-note-silent-on-indexed-inputs`, `udt-authoring-note-silent-on-busybox-userland`, `udt-authoring-note-silent-on-dollar-brace`, `udt-dollar-escape-passed-literally` |
| K | `content/molds/advance-galaxy-draft-step/index.md` | comment-draft on #654 | `advance-step-one-step-per-call-vs-twins` |
| L | `https://test.galaxyproject.org (related project)` | issue-draft | `udt-first-job-container-pull-latency`, `target-ignores-udt-ram-min` |
| M | `package://@galaxy-foundry/gxwf-foundry#testDataRefsSchema` | issue-draft | `test-data-refs-no-intentionally-omitted-optional` |
| N | `content/molds/nextflow-test-to-galaxy-test-plan/index.md` | issue-draft | `test-plan-mold-declares-only-summary-input` |

Totals: 8 new-issue drafts, 5 existing-issue comment drafts (#666, #219, #769, #672, #654); 0 fixed, 0 duplicate, 0 local-only.

Nothing has been posted. No GitHub CLI is available in this environment; drafts are local in `<run>/foundry-issue-drafts.md`.
