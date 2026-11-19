#!/usr/bin/env python3
"""Iteration 58: concretize alpha_rarefaction; meta via filtered metadata; add qzv output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  alpha_rarefaction:
    label: alpha_rarefaction
    doc: >-
      QIIME2_ALPHARAREFACTION - module command block verbatim on qiime2/qiime2:2026.4;
      --p-max-depth auto-derived by awk column sums over the knot count table (equal to
      the module's minmax-reads over the filter-taxon stats table: taxa filtering drops
      features, never samples; the draft has no q2 filter-taxon step), qzv export-folder
      unpack and versions dropped (tool help). metadata is the FILTERED metadata
      (source ch_metadata rebind, ledger filter-samples carry-forward; filter_samples
      shares this step's metadata != null guard). New workflow output publishes the qzv
      (the source publishes the visualization; the simplified report has no rarefaction
      section).
    when: "!$(inputs.skip_alpha_rarefaction) && $(inputs.metadata) != null"
    in:
      table: import_table/qza
      phylogeny: qiime2_tree/rooted_tree
      metadata: filter_samples/metadata
      stats: asv_table_knot/data_param
    out: [ {{id: plot}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-alpha-rarefaction.yml")}
"""

text = open(DRAFT).read()
start_key = "  alpha_rarefaction:\n    tool_id: TODO"
end_key = "  barplots:\n    tool_id: TODO"
assert text.count(start_key) == 1, "alpha_rarefaction anchor not unique"
assert text.count(end_key) == 1, "barplots anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "  diversity_results: { outputSource: core_metrics/TODO_div_plots, label: diversity_results }"
assert new.count(out_old) == 1, "diversity_results ref not unique"
new = new.replace(out_old, out_old +
    "\n  alpha_rarefaction_plot: { outputSource: alpha_rarefaction/plot, label: alpha_rarefaction_plot }")

assert "alpha_rarefaction/TODO" not in new, "residual alpha_rarefaction/TODO"
open(DRAFT, "w").write(new)
print("spliced alpha_rarefaction:", j - i, "->", len(step), "; qzv output added")
