#!/usr/bin/env python3
"""Iteration 61: concretize barplots (barplotavg subworkflow fused); rewire barplots output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  barplots:
    label: barplots
    doc: >-
      QIIME2_BARPLOTAVG fused to one job (qiime2/qiime2:2026.4): relative-frequency, the
      featuretable_group where-filter + group --p-mode sum on the chosen
      metadata_category_barplot, taxa barplot on the consolidated taxonomy qza - module
      commands verbatim; the biom-tsv round-trip/re-import of the relative table collapses
      (identity inside the job), single category in v1, exported svg folder dropped and
      taxa-bar-plots.qzv published instead (tool help). metadata = filtered metadata
      (ch_metadata rebind; shared metadata != null guard).
    when: "!$(inputs.skip_barplot) && $(inputs.metadata_category_barplot) != null && $(inputs.metadata) != null"
    in:
      table: import_table/qza
      taxonomy: import_taxonomy/qza
      metadata: filter_samples/metadata
      category: metadata_category_barplot
    out: [ {{id: barplots}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-barplots.yml")}
"""

text = open(DRAFT).read()
start_key = "  barplots:\n    tool_id: TODO"
end_key = "  ancom:\n    label: ancom"
assert text.count(start_key) == 1, "barplots anchor not unique"
assert text.count(end_key) == 1, "ancom anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "barplots: { outputSource: barplots/TODO_barplots, label: barplots }"
assert new.count(out_old) == 1, "barplots output ref not unique"
new = new.replace(out_old, "barplots: { outputSource: barplots/barplots, label: barplots }")

assert "barplots/TODO" not in new, "residual barplots/TODO"
open(DRAFT, "w").write(new)
print("spliced barplots:", j - i, "->", len(step), "; barplots output rewired")
