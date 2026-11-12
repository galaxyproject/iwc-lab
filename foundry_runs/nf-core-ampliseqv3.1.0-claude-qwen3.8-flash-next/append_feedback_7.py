#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/foundry-feedback.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("issue: null"), "unexpected feedback ledger tail"
assert "concrete-tool-state-omits-drafty-fed-steps" not in t
entries = """
  - id: concrete-tool-state-omits-drafty-fed-steps
    raised_by: advance-galaxy-draft-step
    observed_in:
      mold: advance-galaxy-draft-step
      path: content/molds/advance-galaxy-draft-step/index.md
      revision: 11
      content_hash: 677bb3288b4b88a5c4d66c878318c4d46bdc15f9ebcb01698ade2100a70ea835
      foundry_head: e2c26d735ea338046c61917fcf7627a7f1dc462e
    subject:
      kind: cli
      label: gxwf draft-validate --concrete --strict-state
      locator: content/cli/gxwf/draft-validate.md
      content_hash: 37cded427fbccf49ff19a6fe8b03f9e90857afe556e5db0e51a01402fbf33f1e
    kind: defect
    severity: major
    what: "draft-validate --concrete --strict-state silently omits concrete steps whose connections are fed by still-drafty producers: they appear in neither results nor the ok/fail/skip summary, so a green {ok: N, fail: 0, skip: 0} claims complete tool-state coverage of a projection that was never fully checked. This contradicts the documented intent (the skill cast states skipped tool-state checks must fail the gate) and the gate is the loop's per-iteration oracle, so authors trust the summary as coverage."
    expected: "Every concrete step appears in tool_state.results - steps unresolvable due to a drafty producer surface as skip (and fail --strict-state) or at least as a distinct omitted count in the summary, so the loop cannot report a clean gate while concrete steps with unvalidatable wiring go unchecked."
    evidence: "On this run the concrete q2d2 adonis step, fed by core_metrics/TODO_distance_matrix, passed nine consecutive green gates (tool_state 73 ok/0 fail/0 skip); the moment its producer was concretized the same gate emitted 74 ok/1 fail - checked count rose by two for one concretized step - and the failure was a real defect from an earlier iteration (No parameter definition matching connection key metadata_0|__q2galaxy__GUI__conditional__metadata__), which no gate had ever evaluated."
    status: open
    issue: null
  - id: strict-state-accepts-composite-key-conditional-state
    raised_by: advance-galaxy-draft-step
    observed_in:
      mold: advance-galaxy-draft-step
      path: content/molds/advance-galaxy-draft-step/index.md
      revision: 11
      content_hash: 677bb3288b4b88a5c4d66c878318c4d46bdc15f9ebcb01698ade2100a70ea835
      foundry_head: e2c26d735ea338046c61917fcf7627a7f1dc462e
    subject:
      kind: cli
      label: gxwf draft-validate --concrete --strict-state
      locator: content/cli/gxwf/draft-validate.md
      content_hash: 37cded427fbccf49ff19a6fe8b03f9e90857afe556e5db0e51a01402fbf33f1e
    kind: gap
    severity: major
    what: "strict-state validates step state shallowly for conditionals: the conditional name is matched against the parameter definition but the inner state mapping keys are not checked against the conditional test parameter or when-branch discriminators (the parsed-tool schema the cast bundles exposes whens[].discriminator for exactly this). A step whose conditional state is garbage validates green; a connection key into that conditional (reference_cond|refFasta) also passes, although Galaxy only activates the when-case data parameter when the test parameter selects that case at runtime."
    expected: "strict-state descends one level into conditional state: keys must match the conditional test parameter name, its value a declared option, when-case maps their declared parameters - unknown or composite keys are strict_state_errors; ideally also cross-check that in: keys under a conditional are consistent with the state-selected case."
    evidence: "Three tax_dada_assign* steps carried reference_cond: {{ reference_select: history }} (doubled braces parsed by both JS and Python YAML as a COMPOSITE MAPPING KEY with null value - a splice f-string brace-doubling idiom leaked into literal draft YAML) through 40+ green gates with strict_state_errors []; found only because draft-extract stderr warned 'Keys with collection values will be stringified due to JS Object restrictions'; at runtime Galaxy would fall back to the default reference_select case and strand the custom-taxonomy refFasta connections."
    status: open
    issue: null
"""
open(L, "w").write(t.rstrip() + "\n" + entries.lstrip("\n"))
print("appended 2 phase-7 feedback entries")
