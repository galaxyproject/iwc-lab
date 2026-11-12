# Workflow debug report — nf-core/demo → Galaxy

Input: `workflow-test-result.json` (run-workflow-test). **Latest status: pass** (attempt 9, Planemo 0.75.48, Galaxy `master` @ `b18269a10f8`, invocation `2fd90a3f9f9c52a3`, 1/1 test passed). This report triages the failures recorded in `prior_attempts` and the residual gap that the passing run does not cover.

## Summary

| Attempt | First failure surface | Classification | Owner | Status |
|---|---|---|---|---|
| 1 | Planemo (pre-Galaxy) | Harness defect: Planemo 0.75.47 `KeyError: 'tool_id'` on embedded GalaxyUserTool step | Planemo (fixed in 0.75.48) | resolved by upgrade |
| 2 | Workflow import (400) | Environment/permission: test user lacked `USER_TOOL_EXECUTE` role | Planemo 0.75.47 (0.75.48 grants it) | resolved by upgrade |
| 3 | Workflow import (400) | **Workflow-content error**: frame comments missing `position` / `size` | nextflow-summary-to-galaxy-template (phase 6) + validator gap in gxwf | **fixed in delivered workflow** |
| 5 | Workflow import (500) | **Upstream Galaxy defect** importing an embedded GalaxyUserTool | Galaxy | **open** (unbisected — see below) |
| 6 | Workflow invocation (400 "tools not installed") | Environment: conda launcher shebang picked Galaxy's Python 3.14 venv → every Tool Shed install aborted | test environment | resolved: conda disabled, containers only |
| 7 | — | Stopped by harness (switched to prefetched `.sif` images) | — | n/a |
| 8 | Assertion | **Assertion-choice problem**, not an output regression | nextflow-test-to-galaxy-test-plan (phase 9) translation | **fixed in delivered test file** |
| 9 | — | pass | — | — |

## Attempt 8 — assertion mismatch on `trimmed_reads`

**Evidence.** Planemo structured result `scratchpad/planemo/attempt8-out/planemo-test-output.json`: 1 failure, 0 errors; invocation state `scheduled`, history state `ok` (no job, invocation, or collection failure). Single output problem:

```
seqtk_trimfq on trimmed ... different than expected
Output checksum [df27878f315d2a3f1a56da884a2f7429] does not match expected [7dd2fd0d542d9259d9aed53550907fae] (md5)
```

The element identifier resolved (no missing-element error), so the flattened identifiers `<element>_<forward|reverse|unpaired>` are correct.

**Diagnosis.** Comparing the six downloaded Galaxy outputs with the nf-core snapshot (`tests/default.nf.test.snap`):

| Content | md5 of gzip bytes (Galaxy) | md5 after decompression (Galaxy) | nf-core snapshot md5 | Lines |
|---|---|---|---|---|
| sample1 R1 (SAMPLE1_PE fwd, SAMPLE3_SE) | `df27878f…` | `7dd2fd0d…` | `7dd2fd0d…` ✅ | 110 884 |
| sample1 R2 | `42873781…` | `1995fe84…` | `1995fe84…` ✅ | 110 884 |
| sample2 R1 (SAMPLE2_PE fwd, SAMPLE3_SE) | `25599c23…` | `05dba9c2…` | `05dba9c2…` ✅ | 85 924 |
| sample2 R2 | `110f585d…` | `63d5e4ac…` | `63d5e4ac…` ✅ | 85 924 |

Decompressed trimmed reads are byte-identical to the nf-core outputs (and differ from the raw inputs, so trimming took effect). nf-test hashes `.gz` paths over their decompressed content; a tests-format `checksum:` hashes the dataset's compressed bytes, which depend on the compressor (nf-core `gzip --no-name` vs the Galaxy wrapper's `pigz`). → **assertion-choice problem, not a regression.**

**Repair applied (accepted IWC idiom, not a relaxation).** Each `trimmed_reads` element now uses `decompress: true` with `has_n_lines` (exact count, no delta) and `has_line` (exact first read header). This still fails on wrong trimming (different reads change the line count or header). The prior file is preserved at `scratchpad/planemo/tests-before-decompress-fix.yml`. Attempt 9 passed with it. Strength note: weaker than a full-content hash; an exact decompressed-content comparison would need the nf-core trimmed files as `file:` fixtures.

## Attempt 5 — workflow import 500 with the embedded cowpy user tool (open)

**Evidence.** `POST /api/workflows/upload` → HTTP 500 (`scratchpad/planemo/keep-attempt5.log`). Galaxy traceback:

```
api/workflows.py _workflow_from_dict → managers/workflows.py _workflow_from_raw_description
→ __module_from_dict → workflow/modules.py ToolModule.from_dict (line 2442)
→ managers/tools.py create_unprivileged_tool (213) → managers/base.py create → session.commit()
sqlite3.IntegrityError: NOT NULL constraint failed: workflow_step.workflow_id
[INSERT INTO workflow_step ... tool_id='…/fastqc/0.74+galaxy1', order_index 4, workflow_id=None]
```

No invocation, history, or structured Planemo output exists for this attempt.

**Classification.** Upstream Galaxy defect (500 with an internal traceback; the same workflow passed `gxwf validate --strict` and, with only the cowpy step re-bound to an identical XML tool, imports and passes in attempt 9). The mechanism the traceback shows: building the embedded tool commits the session mid-import, flushing already-built workflow steps (FastQC) whose `workflow_id` is not yet set.

**Not done: bisection.** The procedure asks for a minimal synthetic repro and a passing control. These were **not run** (each needs its own import against a managed Galaxy). Proposed pair, both through gxformat2 conversion as the same user on one server:

- *Failing candidate:* `data` input → any toolbox tool step → embedded GalaxyUserTool step (distinct tool `id` per variant).
- *Passing control:* the same embedded GalaxyUserTool as the only tool step (Galaxy's own `inline_user_defined_tool.gxwf.yml` shape).

Do **not** reshape the delivered workflow to dodge this (e.g. reordering steps). Track it as an upstream issue.

**Impact on the deliverable.** `galaxy-workflow.gxwf.yml` with the embedded cowpy tool will not import on this Galaxy version. The workflow logic and the cowpy command/container are verified (attempt 9). Deployment options until Galaxy is fixed: install cowpy as an ordinary tool (the XML twin at `scratchpad/wkaround/tools/cowpy_say.xml`) and reference it by `tool_id`, or wait for an upstream fix.

## Attempt 3 — frame comments rejected (fixed)

Import 400: `RequestParameterMissingException: Field required in ('frame','position') / ('frame','size')`. Workflow-content error from the template phase; `position`/`size` added to both frames in `galaxy-workflow.gxwf.yml` and the draft. Validator gap: `gxwf validate --strict` accepted the frames without them.

## Environment findings (no workflow change needed)

- Attempt 6: conda dependency resolution was on by Planemo default; `conda`'s `#!/usr/bin/env python` resolved to the Galaxy venv's Python → `No module named 'conda'` → all three shed installs marked failed → invocation refused. Fixed by container-only execution.
- Container images: Apptainer conversion from `docker://` took >10 min per image and repeated for MultiQC; prefetching ready `.sif` files from `depot.galaxyproject.org/singularity/` (and the Seqera cowpy `.sif`) took 37 s for all four. Final configuration: `cached_mulled_singularity` + `explicit_singularity` resolvers, conda disabled.

## Not covered by the passing run

- The delivered embedded-cowpy form (Galaxy defect above).
- `skip_trim: true` branch (no upstream nf-test; `when:` gating untested at runtime).
- MultiQC stats/report contents beyond `has_text` smoke checks (upstream MultiQC md5s are not portable).

## Recommended next steps

1. File the Galaxy import defect with a minimal repro (bisection above) — or confirm against a newer Galaxy.
2. Optionally add a second test case with `skip_trim: true` (expect `trimmed_reads` skipped).
3. Optionally strengthen `trimmed_reads` to full-content comparison using the nf-core trimmed FASTQs as `file:` fixtures with `decompress: true`.

---

## Follow-up 2026-11-10 — attempt 10: delivered workflow passes as delivered

**Status: pass, 2/2 tests** (Planemo 0.75.48, Galaxy `master` @ `7c18ab768ac` / 26.1.3.dev0, invocations `a2000fe73578e736`, `7243f64491bf1ce0`). The cowpy step ran as the **embedded GalaxyUserTool**; no XML twin.

### Attempt 5 import 500: resolved upstream (classification revised)

- The defect is galaxyproject/galaxy#24471 ("Workflow import fails with IntegrityError when an embedded user-defined tool follows a step with a workflow output or PJA"). It was closed by PR #24475, merged into `release_26.1` on 2026-10-29 and forward-merged into `master`.
- The Galaxy used in attempts 5–9 (`b18269a10f8`, committed 2026-10-07) **does not contain the fix** (`git merge-base --is-ancestor 1c95d78 b18269a10f8` → false). The current master does.
- Bisection was executed this time on one persistent `planemo serve`, as one non-admin user with the `user_tool_execute` role, through Planemo's own gxformat2 conversion, with a distinct embedded tool id per variant (`bisection/`, results in `galaxy-import-bisection-results.json`):

| Variant | Shape | Result |
|---|---|---|
| A | UDT only | imported |
| B | data input → FastQC (no outputs) → UDT | imported |
| C | data input → UDT → FastQC | imported |
| D | data input + UDT only | imported |
| E | list input → `__FLATTEN__` → UDT | imported |
| F | delivered `galaxy-workflow.gxwf.yml` | imported, all 6 workflow outputs preserved |
| G | FastQC **with workflow output** → UDT (galaxy#24471 trigger) | imported |
| H | output on UDT only (control) | imported |
| I | UDT first, FastQC with output | imported |

No failing variant remains, so there is nothing left to bisect. **Classification: upstream Galaxy defect, already fixed; the run's Galaxy checkout was stale.** No workflow change is needed. Deployment requirement: Galaxy 26.1 containing galaxy#24475, `enable_beta_tool_formats`, and the `user_tool_execute` role for the running user.

### Test strengthening

- `trimmed_reads` (test 0): each of the 6 elements is now compared with `file:` + `decompress: true` + `compare: diff` against `test-data/expected/trimmed_sample{1,2}_R{1,2}.fastq.gz`. The fixtures were produced with `seqtk trimfq -q 0.05 -l 30` in the wrapper's own seqtk 1.5 + pigz 2.8 container; their decompressed md5s equal the nf-core snapshot md5s (`7dd2fd0d…`, `1995fe84…`, `05dba9c2…`, `63d5e4ac…`). This is a full-content check, stronger than the attempt-9 `has_n_lines`/`has_line` assertions (kept at `<scratchpad>/tests-before-fixture-upgrade.yml`).
- New test 1, `skip_trim: true`: the `when:` gate works at runtime. All 6 `seqtk_trimfq` jobs are `skipped`, `trimmed_reads` still has 6 elements, and they are null datasets. FastQC, cowpy and MultiQC run unchanged. No upstream nf-test covers this branch, so the expectations are agent-derived.

### Environment findings (no workflow change)

- `planemo serve` with a workflow argument does not install its Tool Shed repositories. They were installed through the admin API (`install_repository_revision`, pinned changesets).
- Host `python3` is 3.9 and Galaxy needs ≥ 3.10, so `--galaxy_python_version 3.12` was used with a 3.12 interpreter on `PATH`.
- Attempt 10a hung in `__DATA_FETCH__` because the 166-char scratch `TMPDIR` exceeded the AF_UNIX socket path limit for Celery's forkserver (`OSError: AF_UNIX path too long` in the server log only). Rerun with `TMPDIR=/data/tmp/<job>/gxtmp`.

### Remaining gaps

- MultiQC report/stats are smoke-checked with `has_text` only.
- The Galaxy instance was persistent (`planemo serve` + `--engine external_galaxy`) rather than a per-test managed Galaxy, with the same container-only configuration.
