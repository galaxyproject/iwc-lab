# workflow-debug-report (phase 13 — debug-galaxy-workflow-output)

## Classification

**No debug target.** Phase 12 (`workflow-test-result.json`) carries `status: not-run` with no
`failure_modality` and no invocation/history/workflow ids. Per the run-workflow-test skill
contract, a `not-run` result is *no runtime evidence*, not a debug target: no Galaxy job,
invocation, collection, or assertion surface exists to triage — no workflow step ever executed
in any of the four attempts.

## What was nonetheless diagnosed (root causes of the not-run conditions)

The run-workflow-test pass classifies failures; the environmental blockers were diagnosed there
and are recorded here for completeness, with the failure surface each was verified against:

1. **planemo 0.75.48 format2 shed-install gap (FOUNDRY-ISSUES.md #51).** Attempt 1 failed with
   Galaxy HTTP 400 "required tools are not installed" at invocation time, while the workflow
   import itself returned 200. Verified against planemo source (`load_shed_repos` in
   `planemo/galaxy/workflows.py`): tool installation is only driven from `.ga` files via
   ephemeris, and ephemeris (`extract_tool_shed_repositories_from_workflow_dict`) reads only
   `tool_shed_repository` blocks — never `tool_id`. Authored/compiled format2 (and plain
   conversions of it) carry no such blocks, so `tools_info` is empty and installation is
   silently skipped. **This is a workflow-adjacent tooling defect, not a workflow-content
   defect** — the same workflow was accepted by Galaxy's importer on every attempt.
   Workaround (applied in-run): `.ga` conversion + `tool_shed_repository` injection using
   pinned `changeset_revision`s fetched from the Tool Shed version API.

2. **Zero retry resilience in the Galaxy/ephemeris install path (FOUNDRY-ISSUES.md #52).**
   Attempts 2–4 each died when a *single* Tool Shed TCP connect timeout inside Galaxy
   (`repository_dependency_manager`/`install_manager`, `urllib URLError [Errno 110]`, surfaced
   as HTTP 500 on the install API) cascaded into an ephemeris `AssertionError` in
   `wait_for_install` ("Repository 'X' from owner 'Y' not in list of repositories") and a full
   run abort. Verified against the run logs (planemo-test-run2/3/4.log): the failing repo
   differed per run (fastqc, stringtie, samtools_faidx) — i.e. the trigger is which request
   happens to hit the flaky network window, not repo-specific content.

3. **Environmental network instability.** Direct probes of `toolshed.g2.bx.psu.edu` from this
   host showed intermittent connect timeouts (e.g. 2-of-3 failures at 11:30, 5-of-5 healthy at
   12:20 immediately before attempt 4 — which still died mid-run). DNS resolves to a single
   IPv4 (128.118.250.5, no AAAA), ruling out an IPv6/dual-stack cause; the flakiness is upstream
   or path-level.

## Recommended next step — EXECUTED (attempt-5+ resumption, rectify-and-rerun directive)

The persistent-daemon path recommended above was executed: a persistent planemo-served Galaxy
daemon on `http://127.0.0.1:9210` with all 14 Tool Shed repositories installed via per-repo
retryable installs, and `planemo test --engine external_galaxy` against it. Eight further
attempts (5–12), each failure diagnosed to root cause, cured, and re-run — 14 numbered
findings (**FOUNDRY-ISSUES.md #53–#66**):

- **Invocation-level (#53, #54)**: versionless tool_ids are un-invokable because
  `require_exact_tool_versions` defaults true and shed tools are keyed by versioned guid —
  cured by rewriting all 14 tool_ids to versioned guids; the `/api/tools in_panel=true`
  flat-reading trap that misleads diagnosis.
- **State/output-filter reachability (#55, #62, #64)**: outputs a wrapper filters out of
  existence (`trim_galore report_file`, FastQC `html_file` vs `text_file`, MultiQC picard
  `type` select defaulting to `alignment_metrics`) pass every static gate and fail only at
  invocation scheduling or job preparation — no validator checks output-filter reachability or
  connection formats against wrapper input formats.
- **Translation fidelity (#56, #57)**: the foundry chose `MarkDuplicatesWithMateCigar` where
  nf-core uses `MarkDuplicates` (structurally fails on STAR BAMs), and dropped
  `CUSTOM_GTFFILTER` entirely (salmon cannot parse the fixture GTF's empty-`transcript_id`
  record) — both cured with the pipeline's actual semantics: tool retarget + a new awk
  "GTF filter" step wired to all six GTF consumers.
- **Environment/ecosystem (#58, #63, #65)**: bedclip's mulled env ships UCSC binaries needing
  `libmysqlclient.so.18` but resolves mysql 8.x (`.so.18` staged in from the conda package
  cache); Galaxy single-user auth is newest-key-wins (monitor only via bootstrap master key);
  tmpfs job-working-dir exhaustion across attempts killed STAR with an opaque write error
  (stale work dirs cleared).
- **Test schema (#66)**: planemo's collection checker selects on `element_tests` alone — a
  `class: Collection` + `element_count` declaration without it fails post-run with "No path
  specified for expected output file"; cured by adding `element_tests` to both collection
  outputs.

**Final verdict (attempt 12, 2026-11-13): PASS** — planemo exit 0, `galaxy-workflow.ga_0:
passed`, 19/19 steps scheduled, 36/36 jobs ok, all 9 output assertions satisfied. Evidence:
`workflow-test-result.json` (attempts 1–12), `planemo-test-run12.log`,
`workflow-test-output.{html,json}` (invocation `1519dce9cb4cf6f8`, status success,
output_problems null).

## Honest statement (original phase-13 close-out, superseded by the resumption above)

Nothing was debugged at the workflow-output level in the original four attempts because no
workflow output existed. In the resumption, the workflow ran end-to-end from attempt 7 onward;
the full runtime behavior — tool states, connections, output assertions — was verified green in
attempts 11 (36/36 jobs) and 12 (36/36 jobs + all output assertions).
