# Workflow debug report — nf-core-demo-glm

**Date:** 2026-11-09 20:45 (local, via `date +%H:%M:%S`)
**Input:** `workflow-test-result.json` (run-workflow-test handoff)
**Outcome:** nothing to triage — the test passed.

## Classification

- Structured handoff `status: pass`, exit 0, no `failure_modality`.
- Planemo result: `galaxy-workflow.gxwf.yml_0: passed` / "All 1 test(s) executed passed."
- Invocation `0e72c1a5e870b840` (history `0e72c1a5e870b840`, workflow `0e72c1a5e870b840`): `invocation_state: scheduled`, `history_state: ok`, `end_datetime 2026-11-09T20:40:15.794601`, no `output_problems`, no `execution_problem`.
- No import rejection, no errored jobs, no collection mismatch, no missing outputs, no assertion failure. None of the six failure surfaces is present, so no evidence-capture steps (2–7 of the debug procedure) apply and no repair is recommended.

## Residual observations (no action required)

Two log lines recur even on green runs and are confirmed non-failures:

1. `galaxy.workflow.modules WARNING ... Failed to use input connections for inputs [{'when'}]` (6×).
2. Momentary `workflow tool request state: ... validation_failed` for seqtk and multiqc during scheduling.

Both appear verbatim in the phase-10 green run's log (planemo-test-9.log) and this run's (planemo-test-10.log); in both runs the invocation nonetheless finished `scheduled`/`ok` and every assertion passed. They are scheduling-order transients in Galaxy's workflow monitor, not defects in the workflow, the test file, or the tools.

## Recommendation

None. The pipeline can proceed to maturation/review phases on its own merits; the open-requirements ledger's remaining open entries (`wrapper-sample-sheet-variant-acceptance`, `trimmed-reads-element-identifiers`, `fastqc-archives-zip-output-not-built`) are maturation-tier work, not debug items.

## Feedback pass

No events cleared the bar: the phase was a no-op classification against an already-green structured handoff, and every step of the procedure had its inputs present. The two residual log lines were checked against green-run evidence rather than guessed at, and they are runtime behavior of the workflow under test, not a canonical Foundry asset defect.
