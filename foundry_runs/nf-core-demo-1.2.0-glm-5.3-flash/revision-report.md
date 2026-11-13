# Revision report — nf-core-demo-glm (2026-11-10)

Task from biohackaton2026-8f: fix the workflow issues Galaxy reported when
importing `galaxy-workflow.gxwf.yml` (see `orchestrator-findings-2026-11-10.md`),
using the Foundry skills. Baseline preserved as
`galaxy-workflow.before-revision.gxwf.yml` (copy made 15:35, before any edit).
Revised workflow: `galaxy-workflow.gxwf.yml`.

## Diagnosis

Both flagged steps (FastQC, MultiQC) show one defect class: parameters absent
from the step's `state`, so Galaxy's import recovery
(`check_and_update_param_values`, `tools/__init__.py:2707`) fills each with its
default and lists it in the editor's "Issues loading this workflow" dialog.
`RuntimeValue` is the rendering of an unconnected optional dataset input, not a
separate problem.

Checked against the nf-core/demo source: no flagged parameter is set to a
non-default value by the pipeline (FASTQC receives only `--quiet` via
`ext.args`; MULTIQC gets no comment, title or image content). The fix is
representation only: carry the effective defaults explicitly, leave optional
dataset inputs unconnected.

## Encoding decision

Exported native workflows (IWC corpus) encode an unconnected optional dataset as
`{__class__: RuntimeValue}` in `tool_state`; in gxformat2 that marker is not
legal on optional data inputs — gxwf's own converter
(`stateful-convert.js:100-108`) omits it when converting native → format2, so
the absent key is the canonical unconnected-optional-dataset representation.
Verified empirically with `gxwf validate`: `RuntimeValue` markers were rejected
(`Expected never, actual {"__class__":"RuntimeValue"}`), absent keys pass. Peer
run nf-core-demo-deepseek reached the same conclusion independently.

So: scalars that the wrapper schema can express are written explicitly
(`null` for unset optional integer `min_length`, `""` for text `comment`/`title`,
`false` for the three MultiQC booleans, `7` for `kmers`); the optional data
inputs (`adapters`, `contaminants`, `limits`, `image_content_input`) stay
**absent** from state.

## Findings and dispositions

| # | step (tool) | finding | disposition |
|---|---|---|---|
| 1 | `FastQC` (fastqc 0.74+galaxy1) | `adapters`, `contaminants`, `limits` missing | left absent (optional data; source passes none) |
| 1 | same | `kmers`, `min_length` missing | **added**: `kmers: 7`, `min_length: null` (wrapper defaults; `nogroup: false` was already present) |
| 2 | `MultiQC` (multiqc 1.35+galaxy5) | `comment`, `export`, `flat`, `png_plots`, `title` missing | **added**: `comment: ""`, `export: false`, `flat: false`, `png_plots: false`, `title: ""` |
| 2 | same | `image_content_input` missing | left absent (optional data) |

No wiring, tool ids/versions, outputs, inputs, labels, or canvas/frame
`position`/`size` changed. Structural diff vs backup: 12 added lines, all inside
the two state blocks.

## Foundry skills and commands used

- `foundry-skills:apply-galaxy-workflow-changeset` procedure shape (direct
  `change-parameter` edits inline — no drafty steps, no advance-galaxy-draft-step
  loop; untouched regions byte-for-byte, verified by structural diff).
- Ledger pass-through: `open-requirements.ledger.yml` re-emitted unchanged —
  none of its entries is discharged by this revision.
- Validation:
  - `gxwf validate --strict --cache-dir tool-cache --offline --json` → exit 0, 0 fails
  - `gxwf validate --connections --strict --json` → exit 0, connection_report valid
  - `gxwf validate-tests galaxy-workflow.gxwf-tests.yml --workflow galaxy-workflow.gxwf.yml --json` → valid: true
- Test: `flock /tmp/galaxy-arash-planemo.lock planemo test --galaxy_root
  ~/Galaxy/galaxy-arash --docker galaxy-workflow.gxwf.yml
  --test_output_json planemo-test-output-revision.json`
  (log `planemo-test-revision.log`).

## Results

- **gxwf validation:** PASS (strict + connections + tests).
- **planemo test:** **PASS** — `All 1 test(s) executed passed.`
  galaxy-workflow.gxwf.yml_0: passed, exit 0 (17:32:41, 2026-11-10; started
  17:23:35 under `flock /tmp/galaxy-arash-planemo.lock`). Log
  `planemo-test-revision.log`, structured result
  `planemo-test-output-revision.json` (num_tests 1, num_errors 0,
  num_failures 0, test data status success, no execution/output problems). Test
  assertions unchanged.

## Blocked / notes

- **Orchestrator correction incorporated (2026-11-10, after completion):**
  biohackaton2026-8f confirmed that "RuntimeValue" entries for unconnected
  optional dataset inputs are not a defect (87 of 133 IWC workflows carry the
  state; it is what Galaxy's editor saves), and that such an input should be
  connected only if the nf-core source actually feeds it. The revision as
  completed already complies: no optional dataset input was connected, and in
  gxformat2 they are left **absent** from state — the format2 equivalent of the
  native `RuntimeValue` form (gxwf's converter omits the marker on optional
  params when converting native → format2). No further change was needed.
- No blockers. One encoding iteration (RuntimeValue → absent key) resolved
  locally from the validator's converter semantics.
- Session bookkeeping (not a workflow issue): the first background planemo
  launch accidentally executed in the demo directory instead of bamtofastq's
  (shell cwd carried into the background command), so the demo test ran twice
  under the lock — both green, same workflow file, second run redundant but
  harmless. It was re-run from the correct directory for the bamtofastq run.
- Galaxy will keep showing informational hints for the 4 optional dataset inputs
  that stay absent from state — the editor's rendering of gxformat2 optionality,
  not a defect; no value fabricated, nothing connected that the source does not
  feed.
- Completed run records (`foundry-run.yml`, `foundry-feedback.ledger.yml`) were
  not overwritten; revision artifacts use `-revision` suffixes.
