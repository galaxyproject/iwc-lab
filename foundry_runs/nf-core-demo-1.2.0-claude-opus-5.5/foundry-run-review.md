# Foundry run review — nf-core/demo → Galaxy (`nf-core-demo-galaxy`)

Ledger: `<run>/foundry-feedback.ledger.yml` (24 entries, all `open` before triage). Reviewed 2026-11-10 against `galaxyproject/foundry` main `94ce4ea2` (2026-11-09). Issues searched: all 292 open and closed issues in `galaxyproject/foundry`; Galaxy upstream searched for the import defect.

## Run coverage

- `run.status: complete`; pipeline `nextflow-to-galaxy`, 13 top-level phases, **all `done` and all `feedback_checked: true`**. The ledger reflects a reviewed run, not an unreviewed one.
- Phase 7 (draft loop): 4 iterations. Phase 8 branch: `nextflow-to-test-data` was selected.
- Run notes that matter for triage: phases 7–13 ran leaf sub-skills inline (also recorded as an entry). Phase 12 passed only with the cowpy step bound to an XML twin, because of a Galaxy import defect (see C-GAL).

### Follow-up session (2026-11-10, after the run record closed)

The debug report's recommended next steps were carried out:

1. **Embedded-UDT import 500 re-checked on current Galaxy master** (`7c18ab768ac`, 26.1.3.dev0) using a persistent `planemo serve` and 9 synthetic import variants. **All 9 imported**, including the trigger shape from galaxy#24471 and the delivered workflow with workflow outputs intact. The run's Galaxy (`b18269a10f8`, 2026-10-07) predates the fix (galaxy PR #24475, merged 2026-10-29; `merge-base --is-ancestor` → no).
2. **`trimmed_reads` strengthened** to a full-content comparison: `file:` fixtures (`test-data/expected/trimmed_sample{1,2}_R{1,2}.fastq.gz`) regenerated with the wrapper's own seqtk container. Their decompressed md5s equal the nf-core snapshot exactly. Each element is checked with `decompress: true` and `compare: diff`.
3. **`skip_trim: true` test case added** (the `when:` gate had never been exercised at runtime).
4. Delivered workflow tested **as delivered** (embedded GalaxyUserTool, no XML twin): **2/2 tests passed** (`planemo test --engine external_galaxy`, Planemo 0.75.48, Galaxy master `7c18ab768ac`, container-only). The XML twin used in attempt 9 is no longer needed.

## Ledger integrity and redaction

- The ledger is well-formed. Every entry has `what`/`expected`/`evidence`, a subject locator, and `observed_in` provenance. No entry was edited or removed.
- Redaction: entries carry no credentials or user paths. Scratchpad paths in `workflow-test-result.json` / `workflow-debug-report.md` are user-identifying. They were kept out of the drafts and replaced with `<run>/` where cited.
- Minor: `implement-test-run-green-duplicates-run-workflow-test` names a pipeline subject with no `content_hash` (current main sha256 `4fe7fae2160f…` recorded in the draft instead).
- Content-hash check: every hashed Foundry subject is **byte-identical on main**. None of those corrections has landed.

## Dispositions

| Cluster | Subject (locator) | Entries | Disposition | Where |
|---|---|---|---|---|
| C-PLN | related: planemo 0.75.47 | planemo-0-75-47-keyerror-embedded-user-tool | **fixed** — Foundry pin is 0.75.48 (`content/cli/planemo/index.md`), closed #765 | — |
| C-GAL | related: Galaxy embedded-UDT import IntegrityError | galaxy-embedded-user-tool-import-integrityerror | **duplicate** — galaxy#24471 closed by galaxy#24475 (2026-10-29); Foundry #726 (closed) recorded the same bisection; re-verified fixed on master `7c18ab768ac` | — |
| C-PROF | `package://…gxwf-foundry#summarize-nextflow` (`--profile` default) | summarize-nextflow-cli-silent-test-profile-default | **duplicate** of open #763 (same pipeline, same evidence; nothing new to add) | — |
| C-EDGE | same package (edge extraction) | summarize-nextflow-cli-edges-tokenize-multiline-call-args | comment-draft → #762 (adds the zero-arg `COWPY()` loss) | D1 |
| C-GZ | `content/research/nextflow-snapshot-to-galaxy-assertions/index.md` | snapshot-note-silent-on-gz-md5-semantics | comment-draft → #764 (end-to-end confirmation of its prescription) | D2 |
| C-GGA | same package (getGenomeAttribute) | summarize-nextflow-misses-getgenomeattribute-in-main-nf | comment-draft → #666 item 4 | D3 |
| C-FRAME | related: gxwf comments schema | gxwf-accepts-frames-without-position-size | comment-draft → #580 | D4 |
| C-SCALAR | test-plan schema + test-data-refs schema | test-plan-fixture-no-scalar-value, test-data-refs-no-shape-for-scalar-inputs | comment-draft → #576 (two locators, one correction) | D5 |
| C-POU | `content/patterns/galaxy-collection-patterns.md` | collection-patterns-no-paired-or-unpaired-to-reduction-recipe | comment-draft → #743 (verified worked example) | D6 |
| C-CONT | `content/molds/run-workflow-test/index.md` | run-workflow-test-no-guidance-container-only-planemo | issue-draft (distinct from #730) | D7 |
| C-SS | `package://@galaxy-foundry/summarize-nextflow#summaryNextflowSchema` | summary-omits-samplesheet-channel-construction-in-utility-subworkflow | issue-draft | D8 |
| C-CLS | `package://…gxwf-foundry#summarize-nextflow` (classifier) | summarize-nextflow-cli-utility-subworkflows-classified-pipeline | issue-draft | D9 |
| C-REF | `content/research/nextflow-reference-data-classification/index.md` | reference-classification-no-unconsumed-template-asset-case | issue-draft | D10 |
| C-DUP | `content/research/nextflow-params-to-galaxy-inputs/index.md` | params-to-inputs-no-rule-for-duplicate-sample-rows | issue-draft | D11 |
| C-ID | `content/molds/nextflow-summary-to-galaxy-interface/index.md` | identifier-uniqueness-rule-only-in-data-flow-mold | issue-draft | D12 |
| C-IWC | `content/molds/compare-against-iwc-exemplar/index.md` | iwc-exemplar-no-guidance-for-multi-exemplar-idiom | issue-draft | D13 |
| C-STRICT | `content/molds/advance-galaxy-draft-step/index.md` | draft-loop-validation-skips-strict-structure | issue-draft | D14 |
| C-INLINE | same Mold, different correction | harness-loop-ran-leaf-skills-inline | issue-draft | D15 |
| C-PIPE | `content/pipelines/nextflow-to-galaxy/index.md` | implement-test-run-green-duplicates-run-workflow-test | issue-draft | D16 |
| C-GXWF | related: galaxy-tool-util-ts (`convert --compact`, `--strict-state` msg) | gxwf-convert-compact-leaves-null-and-uuid-noise, strict-state-null-optional-data-message-unclear | issue-draft (one issue, two numbered items) | D17 |
| C-CACHE | related: galaxy-tool-cache raw XML | tool-cache-summary-lacks-wrapper-command | **duplicate** of open #553 (no reachable route for pinned raw XML) / #648 | — |
| C-BIS | `content/molds/debug-galaxy-workflow-output/index.md` | debug-bisection-needs-managed-galaxy-recipe | issue-draft (recipe now exercised) | D18 |

Totals: 24 entries → 1 fixed, 3 duplicate (no post), 6 comment drafts (7 entries), 12 new-issue drafts (13 entries). No entry is `local-only`.

## Feedback pass for this triage (and the follow-up work)

New observations during this session, appended to the ledger only after confirmation (none are posted):

- `debug-galaxy-workflow-output` / `run-workflow-test`: neither says to **record and check the Galaxy commit against known upstream fixes** before treating an import 500 as an open upstream defect. The previous run spent attempts 5–9 on a bug fixed 11 days earlier, because the Galaxy checkout was a month old. This is folded into D18 rather than added as a separate entry.
- `run-workflow-test`: a Galaxy needs Python ≥ 3.10, which fails on hosts with Python 3.9. Folded into D7.

Outcome: no new ledger entries; the two observations above extend existing clusters D7 and D18.
