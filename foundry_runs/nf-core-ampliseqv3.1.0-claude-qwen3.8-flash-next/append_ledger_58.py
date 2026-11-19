#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("deferred to phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "alpha-rarefaction-autodepth-and-filtered-meta" not in t
entry = """
- id: alpha-rarefaction-autodepth-and-filtered-meta
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'alpha_rarefaction concretized as embedded UDT ampliseq_alpha_rarefaction
    (qiime2/qiime2:2026.4, the draft''s standing qiime2 pin): module command block verbatim -
    XDG/MPL/NUMBA exports, max-depth rule (per-sample maximum, cap 75000, steps 250 above
    5000 else maxdepth/20), qiime diversity alpha-rarefaction --p-iterations 10 ->
    alpha-rarefaction.qzv. Wiring: table import_table/qza, phylogeny qiime2_tree/rooted_tree
    (qza is what q2 wants - no export_tree here), metadata filter_samples/metadata (NEW),
    stats asv_table_knot/data_param (NEW port, replaces the absent filter-taxon stats
    input); NEW workflow output alpha_rarefaction_plot publishes the qzv.'
  rationale: 'No Tool Shed wrapper: the shed q2d2 alpha-rarefaction takes numeric
    max-depth/steps and cannot derive them per the module''s rule from a stats dataset
    (author branch). Depth derivation: the module computes it with bin/count_table_minmax_
    reads.py over QIIME2_FILTERTAXA stats; the draft has no q2 filter-taxon step, and the
    per-sample MAXIMUM is invariant under taxa (row) filtering - filter-taxon drops
    features, never samples - so awk column sums over the same knot table the qza was
    imported from give the identical maxdepth (equivalence argument in tool help). The
    metadata port executes the filter-samples carry-forward: source rebinds ch_metadata
    before QIIME2_DIVERSITY, and filter_samples shares this step''s exact metadata != null
    guard so the dependency can never dangle. _plan_state''s "depth
    diversity_rarefaction_depth" was wrong from source: the subworkflow threads that
    param only to QIIME2_DIVERSITY_CORE (qiime2_diversity/main.nf:36-43); rarefaction
    depth is always auto-derived. qzv-folder unpack dropped (feeds the full summary
    report''s embedded plots; simplified report has no rarefaction section), versions
    dropped (precedent); visualization published as a workflow output because the source
    publishes it and no report embeds it here.'
  evidence:
  - 'modules/local/qiime2_alphararefaction/main.nf (command block quoted in shell_command;
    container qiime2/qiime2:2026.4 verbatim; bin/count_table_minmax_reads.py: skiprows
    [0,1], drop feature column, per-sample sums, maximum)'
  - 'subworkflows/local/qiime2_diversity/main.nf:13-43 (take list; if (!skip_alpha_
    rarefaction) QIIME2_ALPHARAREFACTION(ch_metadata, ch_asv, ch_tree, ch_stats=
    QIIME2_FILTERTAXA.out.tsv); diversity_rarefaction_depth only to DIVERSITY_CORE)'
  - 'workflows/ampliseq.nf:1258 (guard params.metadata && (!skip_alpha_rarefaction ||
    !skip_diversity_indices)) with draft when = !skip_alpha_rarefaction && metadata != null'
  - 'not run locally: no qiime2; command is the module verbatim, runtime check deferred
    to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended alpha-rarefaction-autodepth-and-filtered-meta")
