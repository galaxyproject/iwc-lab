#!/usr/bin/env python3
"""Iteration 62: concretize core_metrics (core-metrics-phylogenetic UDT); rewire div_plots + distance_matrix."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  core_metrics:
    label: core_metrics
    doc: >-
      QIIME2_DIVERSITY_CORE as embedded UDT (qiime2/qiime2:2026.4): sampling depth =
      minimum per-sample count (awk column sums over the wide ASV table - same minimum as
      count_table_minmax_reads.py over the filter-taxon stats table, taxa filtering drops
      features not samples) raised to the diversity_rarefaction_depth floor, then
      qiime diversity core-metrics-phylogenetic --output-dir with --p-n-jobs-or-threads 1.
      Publishes the shannon alpha-group-significance qzv (DIVERSITY_ALPHA module pattern)
      as div_plots and the weighted UniFrac matrix as distance_matrix for adonis (source
      flattens ALL four matrices; single-port v1 choice - tool help). metadata = filtered
      metadata (ch_metadata rebind at workflows/ampliseq.nf:1145; shared metadata != null
      guard closes the last raw-metadata QIIME2 consumer).
    when: "!$(inputs.skip_diversity_indices) && $(inputs.metadata) != null"
    in:
      table: import_table/qza
      phylogeny: qiime2_tree/rooted_tree
      metadata: filter_samples/metadata
      stats: asv_table_knot/data_param
      min_depth: diversity_rarefaction_depth
    out: [ {{id: div_plots}}, {{id: distance_matrix}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-core-metrics.yml")}
"""

text = open(DRAFT).read()
start_key = "  core_metrics:\n    tool_id: TODO"
end_key = "  alpha_rarefaction:\n    label: alpha_rarefaction"
assert text.count(start_key) == 1, "core_metrics anchor not unique"
assert text.count(end_key) == 1, "alpha_rarefaction anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "diversity_results: { outputSource: core_metrics/TODO_div_plots, label: diversity_results }"
assert new.count(out_old) == 1, "diversity_results output ref not unique"
new = new.replace(out_old, "diversity_results: { outputSource: core_metrics/div_plots, label: diversity_results }")

ad_old = "distance_matrix: core_metrics/TODO_distance_matrix"
assert new.count(ad_old) == 1, "adonis distance_matrix ref not unique"
new = new.replace(ad_old, "distance_matrix: core_metrics/distance_matrix")

assert "core_metrics/TODO" not in new, "residual core_metrics/TODO"
assert "TODO_div_plots" not in new and "TODO_distance_matrix" not in new, "residual TODO ports"
open(DRAFT, "w").write(new)
print("spliced core_metrics:", j - i, "->", len(step), "; diversity_results + adonis rewired")
