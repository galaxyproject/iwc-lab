#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to phase 11'"), "unexpected ledger tail"
assert "compare-profile-observed-side-realization" not in t
entry = """
- id: compare-profile-observed-side-realization
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'compare_expected_profile concretized as embedded UDT ampliseq_compare_profile
    (quay.io/biocontainers/r-base:4.2.1, the module container/env pin): bin/compare_profile.r
    BYTE-VERBATIM (verified byte-diff) plus the import_taxonomy-identical observed-side
    normalization (adjudicate.py + verbatim bin/parse_dada2_taxonomy.r) plus a small authored
    build_profile.R that joins the normalized sequence+lineage table to asv_table_knot
    abundances and aggregates raw counts per lineage into observed_profile.tsv (taxon column +
    one column per sample). Args fixed per conf/modules.config:1322-1324 (mode=level,
    fbeta=2); tag a constant text input; outputs profile_summary.tsv, profile_per-sample.tsv,
    profile_lineplot svg/png; guarded when expected_profile != null. Wired tax:
    tax_table_knot/data_param, table: asv_table_knot/data_param, expected: expected_profile.'
  rationale: 'The template wired tax+table+expected precisely because the source has no
    main-branch observed profile - the COMPARISON_WF call site passes
    run_qiime2 && !skip_abundance_tables ? QIIME2_EXPORT.out.rel_tax : channel.empty()
    (workflows/ampliseq.nf:1339) and comparison_wf slices the max-level rel-table-<level>.tsv,
    so on the main input path COMPARE_PROFILE never fires in the source; v1 realizes the
    template-intended main-path comparison instead (recorded deviation). Full-depth lineage
    strings are equivalent-or-better than the max-level slice because compare_profile.r
    evaluates every level 1..max_lev from the lineage strings themselves. Observed lineage
    labels trimmed and rejoined with "; " to match the QIIME2 rel_tax style the expected files
    are written against (compare_profile.r does not trim labels on either side - separator
    style mismatches fail identically in the source). A null knot (no classifier ran) leaves
    the required tax input unsatisfied so Galaxy skips the step, mirroring the empty channel
    (import_taxonomy precedent). fbeta/mode have no interface params in the schema (ext-only),
    so they are fixed shell literals; tag column constant replaces val_md5sum_version
    (pipeline_info dropped precedent); profile.log not published.'
  evidence:
  - 'modules/local/compare_profile/main.nf + environment.yml (r-base=4.2.1; argv tag,obs,exp,
    fbeta,mode; outputs profile_summary.tsv, profile_per-sample.tsv, *.svg, *.png, profile.log)'
  - 'bin/compare_profile.r read in full (biom-header branch, common_samples intersect,
    get_taxa_by_mode split on ; with mode complete/level, per-level classification/distance/
    correlation metrics, lineplot); embedded byte-identical'
  - 'subworkflows/local/comparison_wf/main.nf:54-59 (observed .collect() max-baseName-level
    slice, meta relabel); workflows/ampliseq.nf:1339 (rel_tax only on the QIIME2 branch,
    channel.empty() on main)'
  - 'conf/modules.config:1322-1324 (ext.mode=level, ext.fbeta=2)'
  - 'draft import_taxonomy UDT (adjudicate.py shapes ASV_ID-wide / Feature ID+Taxon /
    headerless-2col; verbatim parse_dada2_taxonomy.r); parse_dada2_taxonomy.r embedded
    byte-identical into the new UDT'
  - 'not run locally: no Rscript on this host; build_profile.R is authored base-R
    (rowsum aggregation over the label factor), runtime check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended compare-profile-observed-side-realization")
