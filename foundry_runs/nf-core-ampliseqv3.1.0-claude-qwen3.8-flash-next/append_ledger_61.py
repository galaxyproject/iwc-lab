#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("deferred to phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "barplotavg-fused-single-category" not in t
entry = """
- id: barplotavg-fused-single-category
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'barplots concretized as embedded UDT ampliseq_barplots (qiime2/qiime2:2026.4,
    the pin all four source modules share): QIIME2_BARPLOTAVG fused to one job -
    feature-table relative-frequency, featuretable_group''s where-filter ("cat"<>'''') +
    feature-table group --p-axis sample --p-mode sum, taxa barplot on import_taxonomy/qza
    with NO metadata document (average mode: grouping already collapsed samples); in =
    import_table/qza + import_taxonomy/qza + filter_samples/metadata +
    metadata_category_barplot(text); the barplots workflow output now reads
    barplots/barplots (qzv).'
  rationale: 'Author branch (no wrapper spans relativize->filter->group->barplot). The
    source exports the relative table to biom-tsv (qiime2_export_relasv) and re-imports it
    (QIIME2_INASV_BPAVG) only because rel_tsv is separately published; inside one job the
    qza feeds forward - byte-equivalent abundances, zero re-import. Single category:
    upstream tokenizes metadata_category_barplot by comma and fans out; v1 = one column
    (ancom collapse precedent). Exported svg folder dropped (full-report input; static
    from_work_dir + one published qzv). The step plan''s tax_agglom_min/max concern does
    not apply: barplotavg passes the consolidated tax qza unagglomerated (agglom levels
    feed ANCOM_TAX only) - verified in the subworkflow source. metadata via
    filter_samples closes the ch_metadata rebind for this consumer; guard parity holds
    (when carries metadata != null).'
  evidence:
  - 'subworkflows/local/qiime2_barplotavg/main.nf (inasv->group->barplot(…, "average");
    tokenize('','')) and workflows/ampliseq.nf:1237-1238 (call with
    QIIME2_EXPORT.out.rel_tsv, gated metadata_category_barplot)'
  - 'modules/local/qiime2_export_relasv/main.nf (relative-frequency + biom --to-tsv),
    qiime2_featuretable_group/main.nf (filter-samples --p-where "cat"<>'''' then group
    --p-mode sum), qiime2_barplot/main.nf (taxa barplot, metadata_cmd empty for the
    average call, tools export folder) - all container qiime2/qiime2:2026.4'
  - 'not run locally: no qiime2; commands module-verbatim modulo fused-chain edits,
    runtime check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended barplotavg-fused-single-category")
