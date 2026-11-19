#!/usr/bin/env python3
"""Iteration 50: concretize compare_expected_profile with the ampliseq_compare_profile UDT."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"
out = []
for ln in open("/home/abennett/nf-core-ampliseq/udt-compare-profile.yml").read().splitlines():
    out.append(("      " + ln) if ln else "")
udt = "\n".join(out)

step = f"""  compare_expected_profile:
    label: compare_expected_profile
    doc: >-
      EXPECTED_PROFILE comparison - COMPARE_PROFILE (bin/compare_profile.r verbatim,
      ext.mode=level and ext.fbeta=2 from conf/modules.config:1322-1324) of the expected
      profile against the taxonomy-derived observed profile. The source supplies an observed
      profile only on the run_qiime2 && !skip_abundance_tables branch
      (QIIME2_EXPORT rel_tax max-level slice); here the main-path tax_table_knot +
      asv_table_knot build it (shape adjudication shared with import_taxonomy; tool help
      carries the adaptation). A null knot - no classifier ran - leaves the required input
      unsatisfied and Galaxy skips the step, like the source's empty channel.
    when: "$(inputs.expected_profile) != null"
    in:
      tax: tax_table_knot/data_param
      table: asv_table_knot/data_param
      expected: expected_profile
    out: [ {{id: performance}}, {{id: performance_per_sample}}, {{id: svg}}, {{id: png}} ]
    run:
{udt}
"""

text = open(DRAFT).read()
start_key = "  compare_expected_profile:\n    tool_id: TODO"
end_key = "  # ================= QIIME2 stats & diversity"
assert text.count(start_key) == 1, "profile anchor not unique"
assert text.count(end_key) == 1, "end anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j
open(DRAFT, "w").write(text[:i] + step + text[j:])
print("spliced profile step:", j - i, "->", len(step))
