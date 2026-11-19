- id: ancom-single-category-collapse
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'ancom concretized as embedded UDT ampliseq_ancom (qiime2/qiime2:2026.4):
    filtersamples->pseudocount->ancom command sequence fused into one job for the ONE
    metadata_category - feature-table filter-samples --p-where ''"$(category)"<>""'' ,
    composition add-pseudocount, composition ancom --m-metadata-column category; in =
    import_table/qza + filter_samples/metadata + metadata_category(text); when gained the
    metadata_category != null conjunct; NEW workflow output ancom_result publishes the
    qzv.'
  rationale: 'No wrapper: the q2d2 ancom wrapper covers only the third command; the
    source pipeline per-category filters samples with the category where-clause first
    (modules/local/qiime2_filtersamples default args filter<>""), which the shed step
    cannot chain (author branch). Fan-out collapse: the source runs ANCOM for EVERY
    metadata column (METADATA_ALL channel) and every rank tax_agglom_min..max
    (QIIME2_ANCOM_TAX); the draft interface exposes one chosen category on ASVs only (v1,
    step plan _plan_state). The metadata column identifier is double-quoted inside the
    where clause (module interpolates bare; quoting is a superset for legal names). No
    port for params.ancom_sample_min_count: main.nf:190 default is its ONLY occurrence in
    the pipeline - dead parameter upstream, do not invent consumers. qzv export folders
    and the subworkflow WARNING log channel dropped (report/publish + display
    channels); metadata via filter_samples reproduces the ch_metadata rebind and shares
    the metadata != null guard, and category != null is added so the text port can never
    bind empty.'
  evidence:
  - 'subworkflows/local/qiime2_ancom/main.nf:33-55 (FILTERSAMPLES per metacolumn_all,
    then ANCOM_TAX over tax_agglom_min..max and ANCOM_ASV per category) and
    workflows/ampliseq.nf:1243-1253 (ch_metacolumn_all = METADATA_ALL categories)'
  - 'modules/local/qiime2_filtersamples/main.nf (--p-where ''${filter}<>""'' default args,
    qiime2/qiime2:2026.4) and modules/local/qiime2_ancom_asv/main.nf (add-pseudocount +
    ancom + tools export ancom/Category-${baseName}-ASV; error_ignore label)'
  - 'grep ancom_sample_min_count across source: only main.nf:190 (parameter default) -
    no consumer'
  - 'not run locally: no qiime2; commands are module-verbatim modulo documented edits,
    runtime check deferred to phase 11'
