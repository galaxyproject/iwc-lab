#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("deferred to phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "ancombc-branch-merged-tool" not in t
entry = """
- id: ancombc-branch-merged-tool
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'ancombc concretized as embedded UDT ampliseq_ancombc (qiime2/qiime2:2026.4 -
    both source modules pin it; ancombc2 ships inside q2-composition 2026.4, the
    q2-miyabi worry in the step plan does not apply): one tool, two branches switched by
    the use_ancombc2 text port fed from the ancombc2 boolean workflow input (shell matches
    True/true); category where-filter (''"$cat"<>""'' like the ancom tool), then
    composition ancombc --p-formula or ancombc2 --p-fixed-effects-formula (fixed effects),
    composition tabulate -> result.qzv published via NEW workflow output ancombc_result.
    Two formula ports (formula1/formula2) take ancombc_formula / ancombc2_formula and the
    branch picks. Empty formula -> category -> table basename. ALSO executed the
    filter-samples carry-forward on the concrete adonis step: its q2d2 metadata conditional
    port rewired from the raw workflow input to filter_samples/metadata (shared metadata
    != null guard). Step when unchanged ((ancombc||ancombc2) && metadata != null).'
  rationale: 'Author branch: the q2d2 ancombc wrapper covers one command and cannot chain
    the upstream per-category filtersamples nor branch ancombc/ancombc2 (the draft folds
    both flags into one step). Default-formula semantics preserved: the source default is
    the input table''s baseName, and since upstream feeds the per-category filtersamples
    product ${category}.qza, baseName == category - reproduced by the category fallback
    chain. Dropped (documented in tool help): tools-export folders (full-report inputs),
    da-barplot / ancombc2-visualizer qzvs and ancombc_volcanoplot.r volcano (formula-named
    outputs; Galaxy from_work_dir is static and the draft publishes one result),
    --p-num-processes uses 1 (Galaxy single-core precedent), versions (precedent),
    error_ignore warning echo. The adonis swap closes a known deviation class rather than
    a new decision: source rebinds ch_metadata at workflows/ampliseq.nf:1145 before every
    QIIME2 consumer.'
  evidence:
  - 'modules/local/qiime2_ancombc_asv/main.nf + qiime2_ancombc2_asv/main.nf (both
    container qiime2/qiime2:2026.4; ancombc2 uses --p-fixed-effects-formula,
    ancombc2-visualizer + bin/ancombc_volcanoplot.r volcano; formula = formula_in ?:
    table.baseName; error_ignore labels)'
  - 'subworkflows/local/qiime2_ancom/main.nf:57-67 (ancombc ASV called with empty formula
    over FILTERSAMPLES per-category qza products)'
  - 'draft grep: ancombc2 formula inputs exist (ancombc2_formula string optional); adonis
    when carries metadata != null making the filtered-metadata swap guard-consistent'
  - 'not run locally: no qiime2; runtime check deferred to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended ancombc-branch-merged-tool")
