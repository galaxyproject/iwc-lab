#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "core-metrics-depth-and-adonis-leaf-key" not in t
entry = """
- id: core-metrics-depth-and-adonis-leaf-key
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'core_metrics concretized as embedded UDT ampliseq_core_metrics
    (qiime2/qiime2:2026.4): exports verbatim, sampling depth = awk minimum of per-sample
    column sums over asv_table_knot raised to the diversity_rarefaction_depth floor
    (int workflow input, default 500, now wired as the min_depth port - the
    count_table_minmax_reads.py minimum vs param rule), qiime diversity
    core-metrics-phylogenetic --output-dir --p-n-jobs-or-threads 1. Two published ports:
    div_plots = alpha-group-significance on the shannon vector (DIVERSITY_ALPHA
    pattern, fixed name alpha-shannon.qzv; feeds the diversity_results workflow output)
    and distance_matrix = weighted_unifrac matrix copied to a fixed name (feeds the
    concrete adonis step; upstream flattens all four matrices, single-port v1 choice).
    metadata = filter_samples/metadata - closes the ch_metadata rebind for the last raw
    consumer. ALSO fixed a latent adonis wiring defect surfaced when its producer became
    concrete: the q2d2 wrapper metadata repeat''s conditional must be addressed down to
    its data leaf, key now
    metadata_0|__q2galaxy__GUI__conditional__metadata__|source.'
  rationale: 'Author branch (no wrapper spans depth-derivation -> core-metrics ->
    selective publication; the plan''s q2d2 coremetricsphylogenetic alternative emits a
    bundle the single-port consumers cannot take, the split the _plan_context anticipated
    - the UDT replaces both). Depth parity: taxa filtering drops features (rows) never
    samples (columns), so column-sum minima over the wide table equal the module
    minimum over the filter-taxon stats table (alpha-rarefaction precedent). Shannon is
    the representative alpha metric (the draft has one div_plots port; per-vector and
    per-category beta/betaord visualizers have no draft counterpart - documented drop
    with the WARNING depth-note display files, tsv exports of the other three matrices,
    and versions.yml). The adonis failure proves --concrete skips tool-state checks for
    steps fed by drafty producers: earlier 73-ok gates never validated adonis; the
    state block (repeat with conditional discriminator tsv) was already right, only the
    connection leaf was missing.'
  evidence:
  - 'modules/local/qiime2_diversity_core/main.nf (UNIFRAC_USE_GPU=N + XDG/MPL/NUMBA
    exports; mindepth from bin/count_table_minmax_reads.py minimum, raised when below
    params.diversity_rarefaction_depth; core-metrics-phylogenetic --output-dir
    diversity_core --p-n-jobs-or-threads task.cpus; four beta-matrix tools-export + mv
    steps)'
  - 'subworkflows/local/qiime2_diversity/main.nf:40-80 (vector.flatten -> per-alpha
    DIVERSITY_ALPHA qzvs, distance.flatten -> beta + ADONIS over all four matrices);
    modules/local/qiime2_diversity_alpha/main.nf (${core.baseName}-vis.qzv)'
  - 'cached wrapper summary q2d2 qiime2__diversity__adonis 2026.1.0+q2galaxy.2026.1.0:
    metadata is gx_repeat(min 1) of gx_conditional(type: tsv|qza) whose when-branches
    both carry gx_data source (tabular/qiime2.tabular or qza) - leaf is source'
  - 'gate: draft-validate --concrete --strict-state exit 0, tool_state 75 ok/0 fail/0
    skip, strict [], todo only picrust; not run locally: no qiime2, runtime check
    deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended core-metrics-depth-and-adonis-leaf-key")
