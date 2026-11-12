#!/usr/bin/env python3
"""Iteration 59: concretize ancom (single-category collapse); publish qzv result."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  ancom:
    label: ancom
    doc: >-
      QIIME2_ANCOM (ASV branch) for the single chosen metadata_category: the
      qiime2_filtersamples where-clause (category<>"") + add-pseudocount + composition
      ancom command sequence on qiime2:2026.4, fused into one job. Source's per-column /
      per-rank fan-outs collapsed to the interface's metadata_category (v1, step plan);
      ancom_sample_min_count is dead upstream (no consumer - no port invented). metadata
      is the filtered metadata (ch_metadata rebind; shared metadata != null guard).
    when: "$(inputs.ancom) && $(inputs.metadata) != null && $(inputs.metadata_category) != null"
    in:
      table: import_table/qza
      metadata: filter_samples/metadata
      category: metadata_category
    out: [ {{id: result}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-ancom.yml")}
"""

text = open(DRAFT).read()
start_key = "  ancom:\n    tool_id: TODO"
end_key = "  ancombc:\n    tool_id: TODO"
assert text.count(start_key) == 1, "ancom anchor not unique"
assert text.count(end_key) == 1, "ancombc anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "  alpha_rarefaction_plot: { outputSource: alpha_rarefaction/plot, label: alpha_rarefaction_plot }"
assert new.count(out_old) == 1, "alpha_rarefaction_plot ref not unique"
new = new.replace(out_old, out_old +
    "\n  ancom_result: { outputSource: ancom/result, label: ancom_result }")

assert "ancom/TODO" not in new, "residual ancom/TODO"
open(DRAFT, "w").write(new)
print("spliced ancom:", j - i, "->", len(step), "; ancom_result output added")
