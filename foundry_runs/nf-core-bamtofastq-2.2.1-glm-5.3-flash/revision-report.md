# Revision report — nf-core-bamtofastq-glm (2026-11-10)

Task from biohackaton2026-8f: fix the workflow issues Galaxy reported when
importing `galaxy-workflow.gxwf.yml` (see `orchestrator-findings-2026-11-10.md`),
using the Foundry skills. Baseline preserved as
`galaxy-workflow.before-revision.gxwf.yml` (copy made 15:35, before any edit).
Revised workflow: `galaxy-workflow.gxwf.yml`.

## Diagnosis

All 16 flagged steps show one defect class: parameters absent from the step's
`state`, so Galaxy's import recovery (`check_and_update_param_values`,
`tools/__init__.py:2707`) fills each with its default and lists it in the
editor's "Issues loading this workflow" dialog. `RuntimeValue` is the rendering
of an unconnected optional dataset input, not a separate problem.

Per finding, decided against the nf-core source (`modules/nf-core/...`,
`conf/modules.config`, `workflows/bamtofastq.nf`): **no flagged parameter is set
to a non-default value by the pipeline** (FASTQC gets only `--quiet`; fastq_info
and samtools merge/view get no options; MultiQC gets no comment/title/image
content; the UDT's `lines_to_check` matches the source's 1000-record sample). So
the fix is representation only: make the state carry the effective defaults
explicitly, and leave optional dataset inputs unconnected (the source feeds none
of them).

## Encoding decision (the one non-obvious call)

Exported native workflows (IWC corpus: 87 of 133 carry it, 553 occurrences)
encode an unconnected optional dataset as `{__class__: RuntimeValue}` inside
`tool_state`. In **gxformat2** that marker is not legal on optional data inputs:
gxwf's own converter (`stateful-convert.js:100-108`) **omits** `RuntimeValue` on
optional params when converting native → format2 — the absent key is the
canonical unconnected-optional-dataset representation in format2. Verified
empirically: the IWC `.ga` with `qname_file: RuntimeValue` validates clean, the
same marker in my `.gxwf.yml` is rejected (`Expected never, actual
{"__class__":"RuntimeValue"}`), and the roundtrip-converted native of the revised
workflow validates clean. Peer run nf-core-demo-deepseek reached the same
conclusion independently (its `revision-report.md` correction section).

So: scalars that the wrapper schema can express are written explicitly
(`null` for unset optional scalars, `""` for empty strings, `false`/`true` for
booleans, `7`/`1000` for integers); optional **data** inputs (fastqc
`adapters`/`contaminants`/`limits`, samtools_view `qname_file`, samtools_merge
`bed_file`/`headerbam`, multiqc `image_content_input`) stay **absent** from
state — Galaxy's informational hint for them is the editor's rendering of
optionality, not a defect.

## Findings and dispositions

| # | step (tool) | finding | disposition |
|---|---|---|---|
| 1 | `samtools_chr_view` (samtools_view 1.22+galaxy2) | `mode\|filter_config\|qname_file` missing | left absent (optional data; unconnected = canonical unset) |
| 2–5 | `samtools_view_map_map`, `_unmap_unmap`, `_unmap_map`, `_map_unmap` | same | left absent, same reason |
| 6–7 | `fastqc_pre_conversion`, `fastqc_post_conversion` (fastqc 0.74+galaxy1) | `adapters`, `contaminants`, `limits` missing | left absent (optional data; source passes none — FASTQC `ext.args = '--quiet'` only) |
| 6–7 | same steps | `kmers`, `min_length`, `nogroup` missing | **added**: `kmers: 7`, `min_length: null`, `nogroup: false` (wrapper defaults, matching source no-op) |
| 8 | `pairedness_split` (UDT) | `lines_to_check` missing | **added**: `lines_to_check: 1000` (UDT default = source's first-1000-records sample) |
| 9 | `multiqc` (1.35+galaxy5) | `comment`, `title` missing | **added**: `comment: ""`, `title: ""` |
| 9 | same | `image_content_input` missing | left absent (optional data) |
| 10 | `samtools_merge_unmapped` (samtools_merge 1.22+galaxy2) | `region` missing | **added**: `region: null` (optional text) |
| 10 | same | `bed_file`, `headerbam` missing | left absent (optional data) |
| 11–12 | `fastqutils_info_paired`, `_single` (fastq_info 0.25.3+galaxy0) | `q`, `r` missing | **added**: `q: true`, `r: false` (wrapper defaults = source defaults) |

No wiring, tool ids/versions, outputs, inputs, doc text, labels, or
canvas `position`/frame `position`/`size` changed. Structural diff vs backup
touches only the state blocks above (47 diff lines before the data-input
correction, 16 after).

## Foundry skills and commands used

- `foundry-skills:apply-galaxy-workflow-changeset` procedure shape (direct
  `change-parameter` edits applied inline — no tool-introducing edits, so no
  drafty steps and no advance-galaxy-draft-step loop; untouched regions preserved
  byte-for-byte, verified by structural diff).
- Ledger pass-through: `open-requirements.ledger.yml` reviewed — none of its
  entries is discharged by this revision (state completion is representation, not
  a requirement resolution); re-emitted unchanged.
- Validation:
  - `gxwf validate --strict --cache-dir tool-cache --offline --json galaxy-workflow.gxwf.yml` → exit 0, 0 fails (30/30 steps ok)
  - `gxwf validate --connections --strict --json` → exit 0, connection_report valid
  - `gxwf validate-tests galaxy-workflow.gxwf-tests.yml --workflow galaxy-workflow.gxwf.yml --json` → valid: true
  - Intermediate probe: `gxwf validate` rejected `RuntimeValue` markers on
    optional data inputs (documented above); corrected encoding, re-validated
    clean. The pre-revision file passed the same validator — the strict gate was
    the instrument that caught the encoding.
- Test: `flock /tmp/galaxy-arash-planemo.lock planemo test --galaxy_root
  ~/Galaxy/galaxy-arash --docker --biocontainers
  galaxy-workflow.gxwf.yml --test_output_json planemo-test-output-revision.json`
  (log `planemo-test-revision.log`).

## Results

- **gxwf validation:** PASS (strict + connections + tests).
- **planemo test:** **PASS** — `All 1 test(s) executed passed.`
  galaxy-workflow.gxwf.yml_0: passed, exit 0 (17:40:22, 2026-11-10; started
  17:33:53 under `flock /tmp/galaxy-arash-planemo.lock`, ~6.5 min). Log
  `planemo-test-revision.log`, structured result
  `planemo-test-output-revision.json` (num_tests 1, num_errors 0,
  num_failures 0, test data status success, no execution/output problems). Test
  assertions unchanged from the pre-revision green run.

## Blocked / notes

- **Orchestrator correction incorporated (2026-11-10, after completion):**
  biohackaton2026-8f confirmed that "RuntimeValue" entries for unconnected
  optional dataset inputs are not a defect (87 of 133 IWC workflows carry the
  state; it is what Galaxy's editor saves), and that such an input should be
  connected only if the nf-core source actually feeds it. The revision as
  completed already complies: no optional dataset input was connected, and in
  gxformat2 they are left **absent** from state — the format2 equivalent of the
  native `RuntimeValue` form (gxwf's converter omits the marker on optional
  params when converting native → format2). No further change was needed; the
  reports' earlier "informational hints" wording already treats the dialog
  notes as optionality rendering, not a defect.
- No blockers. One encoding iteration (RuntimeValue → absent key) resolved
  locally from the validator's own converter semantics; no outside help needed.
- Session bookkeeping (not a workflow issue): the first background planemo
  launch accidentally executed in the demo run's directory (shell cwd carried
  into the background command), so the demo workflow was tested twice under the
  lock (both green) before the bamtofastq test was launched from the correct
  directory. The bamtofastq result above is from the correct-directory run.
- Ledger repair (self-inflicted, disclosed): while appending the feedback
  entry, a scripted indentation normalization corrupted
  `foundry-feedback.ledger.yml`'s run/phases header (the file had a
  pre-existing mixed-indentation malformation in the entries list that the
  script's rewrite did not preserve). The file was rebuilt: the 15 pre-existing
  entries were recovered intact from the parsed body (parsed as a bare list),
  the run/phases head was restored to the on-disk structure verified earlier in
  this session (run: pipeline/run_slug/status complete + 13 done/checked
  phases), and the new entry appended. All 16 entries parse; run status and
  every phase row preserved. No entry content was altered.
- Galaxy will keep showing informational hints for the 7 optional dataset
  inputs that stay absent from state. That is the editor's rendering of
  optionality for gxformat2 (absent key is the only legal "unset" form), not a
  workflow defect; no value was fabricated and no input was connected that the
  source does not feed.
- Completed run records (`foundry-run.yml`) were not overwritten; revision
  artifacts use `-revision` suffixes.
