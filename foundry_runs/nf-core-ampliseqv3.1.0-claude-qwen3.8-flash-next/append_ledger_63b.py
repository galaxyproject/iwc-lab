#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("draft false - loop endstate'"), "unexpected ledger tail"
assert "conditional-state-composite-key-fix" not in t
entry = """
- id: conditional-state-composite-key-fix
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'Fixed three tax_dada_assign* step states where the wrapper-conditional case
    had been written as a YAML COMPOSITE MAPPING KEY - literal doubled braces in the
    draft text, reference_cond: {{ reference_select: history }}, which both Python and
    JS YAML parse as key={reference_select: history} value=null instead of the intended
    case selector. Now single-braced reference_cond: { reference_select: history } in
    the draft; re-gated exit 0 (76 ok) and re-extracted galaxy-workflow.gxwf.yml clean
    (no stringified-key warning). Loop endstate recorded: draft-next-step draft false,
    extracted workflow = class GalaxyWorkflow, 86 steps, 117 inputs, 19 outputs, 0
    TODOs.'
  rationale: 'Runtime landmine: Galaxy would fall back to the default reference_select
    case and the reference_cond|refFasta connections (custom taxonomy branch) would
    target an inactive conditional. Survived every gate because --strict-state matches
    the conditional name but does not descend into its state mapping keys (same blind
    spot class as the adonis leaf-key miss, entry
    core-metrics-depth-and-adonis-leaf-key). Provenance: f-string brace-doubling idiom
    leaking from a splice script into literal draft YAML - correct inside splice
    f-strings, wrong on disk; the state block predated this window. Not a topology
    repair (no computability gap), bounded local edit.'
  evidence:
  - 'grep draft: three lines reference_cond: {{ reference_select: history }} at
    tax_dada_assign / _sp / _sp_multi state blocks; sibling
    speciesreference_cond: { speciesreference_select: history } shows the intended
    single-brace form'
  - 'draft-extract stderr before fix: "Warning: Keys with collection values will be
    stringified due to JS Object restrictions"; absent after'
  - 'not exercised at runtime: phase 11 custom-reference test branch will hit
    tax_dada_assign first'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended conditional-state-composite-key-fix")
