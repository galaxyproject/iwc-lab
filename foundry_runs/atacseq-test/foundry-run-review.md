# Foundry run review: nf-core/atacseq 2.1.2 → Galaxy (`atacseq-test`)

Produced by `report-foundry-run-feedback` (Mold revision 1, content hash `cffa8d81…270da`) from
`<run>/foundry-feedback.ledger.yml`. Checked against `galaxyproject/foundry` main
`df991d0d789b0a29618cbcdbe7eb6d9508f1f062` (2026-11-11) and the repository's 313 open and
closed issues, read on 2026-11-12. **Nothing has been posted.** Every draft in
`foundry-issue-drafts.md` is local and waits for explicit confirmation.

## Run status and coverage

| | |
|---|---|
| Pipeline | `nextflow-to-galaxy` (assembled from pipeline revision 5) |
| Run status | **complete** (started 2026-11-12T03:53:55Z, finished 06:45:25Z) |
| Outcome | Workflow test passed on attempt 3 (182/182 jobs) on test.galaxyproject.org |
| Phases | 13 of 13 `done`, 13 of 13 `feedback_checked: true` |
| Entries | 28, all `status: open`, none filed |

Every phase reported a feedback outcome, so the ledger counts as reviewed. It is not a clean
run. Two phases were not run as declared, and both are logged as feedback:

- **Phase 7** (`advance-galaxy-draft-step`) records `iterations: 1`. The whole 78-step loop ran
  as one batched pass instead of one step per invocation.
- **Phase 13** (`debug-galaxy-workflow-output`) contains two repairs and two re-runs (attempts 2
  and 3). The pipeline declares no phase for either.

## Ledger integrity and redaction

- **Missing subject hashes.** None of the 28 entries carries `subject.content_hash`. For Mold
  subjects, `observed_in.content_hash` is the same file, so the hash check still works. For the
  three research-note subjects, I recovered the hashes from the cast bundles' `refs[].src_hash`.
  For the two schema subjects, I hashed the cast bundles' schema copies. The `summary-nextflow`
  and pipeline subjects have no cast-time hash, so I compared them by content only. This was a
  writer error in this run, not a Foundry defect.
- **Implementation locators.** The 8 `@galaxy-foundry/summarize-nextflow` CLI entries use the
  locator `packages/summarize-nextflow` with a prose label. I clustered them by the code path
  each correction touches.
- **Redaction.** The ledger holds no credentials, private URLs, or participant data. The drafts
  use `<run>/` for the run directory and cite only public nf-core and Foundry paths. The Galaxy
  server, test.galaxyproject.org, is public. The drafts leave out invocation and history ids.
- **Hash algorithm.** The protocol never says how `content_hash` is computed. Plain sha256 of
  the file reproduced every observed Mold hash, so I used it throughout. This is logged as
  feedback below.

## Current-main check

| Subject | Cast hash → main | Correction present on main? |
|---|---|---|
| `content/molds/summarize-nextflow/index.md` | `fb19fff9…` → `d8e67590…` changed | No. §3.5 still has no `SAMPLESHEET_CHECK` / `splitCsv`-on-process-output branch |
| `packages/summarize-nextflow` resolver | n/a (code) | `definitions`: no. `--profile` default `"test"`: still there. `example.invalid` fallback: still there. `getGenomeAttribute` regex (resolver.ts:961) matches only the one-argument form. **`ext.args`: yes** (`resolved_args`, root `includeConfig` chain, #665/#777) |
| `nextflow-summary-to-galaxy-reference-data` | `b49bae31…` unchanged | No |
| `nextflow-summary-to-galaxy-interface` | `43966773…` unchanged | No |
| `compare-against-iwc-exemplar` | `84abb427…` unchanged | No |
| `advance-galaxy-draft-step` | `677bb328…` → `12f242dd…` changed | No: no batch mode and no trivial in-loop edit path |
| `nextflow-test-to-galaxy-test-plan` | `fa769216…` unchanged | No |
| `validate-galaxy-workflow` | `74e3743f…` unchanged | No |
| research `galaxy-workflow-draft-format` | `e9b84eeb…` → `8bb5cad9…` changed | No: no repeated-lane or twin guidance |
| research `nextflow-operators-to-galaxy-collection-recipes` | `59d97f05…` unchanged | Not in this note, but the sibling `nextflow-to-galaxy-channel-shape-mapping` now has "Per-element parameters from `meta`" (#757) |
| research `iwc-test-data-conventions` | `b7ef1413…` unchanged | No `paired_or_unpaired` example |
| schema `test-data-refs` | `534dcb2f…` unchanged | No |
| schema `galaxy-workflow-test-plan` | `03fc1d58…` → `aaa611c5…` changed | No. The change is formatting only; `Tolerance.kind` is still `delta`/`delta_frac`/`lines_diff`/`none` |
| pipeline `nextflow-to-galaxy` | revision 5 | No: still ends at debug with no loop back |

## Dispositions

Legend: **comment-draft** adds a comment to an existing open issue. **issue-draft** opens a new
issue. **duplicate** is already reported or resolved elsewhere. **fixed** means current main
already contains the correction.

| # | Correction | Entry ids | Sev | Disposition |
|---|---|---|---|---|
| 1 | Resolver reads `definitions` (draft-07) as well as `$defs` | `summarize-nextflow-cli-draft07-definitions-params-empty` | major | comment-draft → #771 |
| 2 | Parse balanced call arguments; drop literal edge sources | `summarize-nextflow-cli-closure-args-split-into-edges` | major | comment-draft → #762 |
| 3 | No silent `--profile test`; emit every test profile as a candidate | `summarize-nextflow-cli-default-profile-treated-as-explicit` | major | comment-draft → #763 |
| 4 | Local-clone `source` falls back to a placeholder; `--pin` re-clones a local path | `summarize-nextflow-cli-local-clone-placeholder-provenance` | minor | comment-draft → #761 |
| 5 | Two-argument `WorkflowMain.getGenomeAttribute(params,'x')` form and positive-form rebuild guards | `summarize-nextflow-cli-reference-assets-empty-legacy-genome-attribute` | major | comment-draft → #666 (item 4 variant) |
| 6 | Script-scope channels missing from `workflow.channels` | `summarize-nextflow-cli-script-level-channels-missed` | minor | comment-draft → #666 (new item) |
| 7 | Unquoted numeric `params_delta` values dropped | `summarize-nextflow-cli-params-delta-drops-numeric` | minor | **duplicate**: already reported in a #666 comment (OceanOmics `blast_pid = 90`). Confirmed in one line inside the #666 draft |
| 8 | §3.5 branch for legacy `SAMPLESHEET_CHECK` + `splitCsv` on process output | `summarize-nextflow-samplesheet-discovery-no-branch-for-legacy-check` | minor | issue-draft |
| 9 | Reference-data Mold: fallback when the inventory is empty | `reference-data-mold-no-fallback-when-inventory-empty` | minor | comment-draft → #673 |
| 10 | Interface Mold: explicit scope-selection step | `interface-mold-no-scope-selection-guidance` | minor | comment-draft → #769 |
| 11 | Summary carries `ext.args` from `conf/modules.config` | `summary-nextflow-no-ext-args-from-modules-config` | major | **fixed** on main (`resolved_args`, #665 closed via #777; atacseq's `includeConfig 'conf/modules.config'` sits on the root chain) |
| 12 | Recipe for meta-flag-driven per-element behaviour | `data-flow-no-recipe-for-meta-flag-branching-across-chain` | minor | **duplicate** of #757 (closed). Main's channel-shape note now covers one branch per value, gated with `when` and rejoined with `pick_value` |
| 13 | IWC comparison artifact for several exemplars | `iwc-compare-single-exemplar-artifact-for-split-match` | minor | issue-draft |
| 14 | Draft shape for a chain repeated with different settings (twins) | `draft-format-no-guidance-for-repeated-lane` | minor | comment-draft → #654 |
| 15 | Per-wrapper batch mode for the draft loop | `advance-step-one-per-call-impractical-for-twinned-80-step-draft` | major | issue-draft |
| 16 | Lightweight path for trivial in-loop structural edits | `advance-step-in-loop-repairs-without-escalation` | minor | issue-draft |
| 17 | gxwf `--strict-state` diagnostic for null optional data params | `gxwf-strict-state-null-optional-data-message` | minor | issue-draft (related project: gxwf) |
| 18 | IUC bedtools genomecov: add `-pc` / `-fs` | `iuc-bedtools-genomecov-missing-pc-fs` | minor | issue-draft (related project: IUC wrapper) |
| 19 | IUC featureCounts: accept SAF annotation | `iuc-featurecounts-no-saf-annotation` | minor | issue-draft (related project: IUC wrapper) |
| 20 | `test-data-refs` carries derived scalar test values | `test-data-refs-no-carrier-for-computed-scalar-params` | minor | comment-draft → #576 |
| 21 | `test-data-refs` "left unset by source test" state | `test-data-refs-optional-unused-input-forced-unresolved` | minor | issue-draft |
| 22 | Test-plan assertion min/max bound | `test-plan-tolerance-cannot-express-min-bound` | minor | issue-draft |
| 23 | Test-plan Mold rule for profile-only candidates (no nf-test) | `test-plan-mold-silent-on-profile-only-evidence` | minor | issue-draft |
| 24 | `list:paired_or_unpaired` job-input example | `test-conventions-no-paired-or-unpaired-input-example` | minor | comment-draft → #743 |
| 25 | gxwf `--connections` infers the `__APPLY_RULES__` output type | `gxwf-connections-cannot-infer-apply-rules-output` | major | issue-draft (related project: gxwf) |
| 26 | Validate Mold names its gating command and flags | `validate-mold-silent-on-connections-flag` | minor | comment-draft → #644 |
| 27 | gxwf checks the frame comment `color` enum | `gxwf-validate-misses-frame-color-enum` | major | comment-draft → #580 |
| 28 | Pipeline loops back from debug to repair and re-run | `pipeline-no-repair-rerun-path-after-debug` | major | issue-draft |

**Totals:** 12 comment drafts, 12 new-issue drafts, 2 duplicates, 1 fixed, 0 local-only.
Entry #7 is a duplicate, but its confirmation travels inside comment draft #5/#6 (one #666
comment). Several issues I read and judged related but not duplicates are named inside the
drafts: #547, #644, #660, #663, #665, #668, #753, #792, #796, #798, #800.

## Issue drafts at a glance

The full self-contained texts for every item below are in
[`foundry-issue-drafts.md`](foundry-issue-drafts.md).

**Comments on existing issues**

- **C1 → #771:** nf-core/atacseq 2.1.2's draft-07 `definitions` schema gave `params: []`; still unread on main.
- **C2 → #762:** inline `.map { [ [:], it ] }` closures and literal args (`false`, `0`, `[]`) become bogus edges (213 vs 119 real).
- **C3 → #763:** default `--profile test` collapsed three test profiles to one candidate on a pipeline with no nf-test.
- **C4 → #761:** failed git calls silently yield `example.invalid` source URL; `--pin` re-clones a local path.
- **C5 → #666:** two-argument `WorkflowMain.getGenomeAttribute(params,'x')` unmatched; top-level channels missing; numeric `params_delta` drop confirmed.
- **C6 → #673:** reference-data Mold has no path when `reference_assets[]` and `reference_rebuilds[]` are both empty.
- **C7 → #769:** interface Mold never says who picks pipeline scope; excluded stages should be `kind: dropped`.
- **C8 → #654:** template-time PE/SE twins (30 of 80 steps) need a twin/delta idiom in the draft format.
- **C9 → #576:** `test-data-refs` cannot carry a computed scalar test value (`macs_gsize`).
- **C10 → #743:** working `list:paired_or_unpaired` job-input example; inner collections must not carry `type`.
- **C11 → #644:** validate Mold names no flags; `--strict` passes while `--connections` fails on false positives.
- **C12 → #580:** gxwf accepts frame `color: lightblue`; Galaxy import rejects it (400).

**New issues**

- **N1:** summarize-nextflow §3.5 has no branch for the legacy `SAMPLESHEET_CHECK` + `splitCsv` samplesheet idiom.
- **N2:** compare-against-iwc-exemplar assumes one exemplar; ATAC needed two (per-sample and consensus).
- **N3:** advance-galaxy-draft-step's one-step-per-call loop does not scale; allow per-wrapper batching.
- **N4:** no lightweight in-loop path for trivial structural fixes (insert `__FLATTEN__`, drop a dead-end step).
- **N5:** gxwf `--strict-state` gives misleading errors for null optional data params and blames the conditional.
- **N6:** IUC bedtools genomecov lacks `-pc` / `-fs`; bamCoverage used as substitute.
- **N7:** IUC featureCounts lacks SAF input; 2.1.1 also aborts on SE BAMs in `PE_fragments` mode.
- **N8:** `test-data-refs` has no "left unset by source test" state, so optional inputs fall through to search.
- **N9:** test-plan schema cannot express min/max bound assertions.
- **N10:** test-plan Mold has no rule for profile-only candidates (no nf-test).
- **N11:** gxwf `--connections` cannot infer `__APPLY_RULES__` output and flags all downstream edges invalid.
- **N12:** nextflow-to-galaxy pipeline has no repair and re-run loop after debug.

## This skill's own feedback pass

I appended 2 entries with `raised_by: report-foundry-run-feedback`. I added no phase row,
because the run's phase roster belongs to the harness and is already complete.

- `feedback-protocol-content-hash-algorithm-unstated` (gap, minor)
- `report-mold-multiple-clusters-one-existing-issue` (gap, minor)

## Next step

Confirm which drafts to post, by number, or say "none". Each posted body starts with
`Posted by an AI assistant on Chisomgold's behalf.` and @-mentions no one. After a successful
post, the matching ledger entries become `filed` with the issue or comment URL. Entries #7, #11
and #12 stay `open` until you confirm their `duplicate` / `fixed` dispositions.
