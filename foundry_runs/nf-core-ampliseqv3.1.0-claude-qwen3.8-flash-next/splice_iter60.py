#!/usr/bin/env python3
"""Iteration 60: concretize ancombc (ancombc + ancombc2 branches in one tool); publish result."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

step = f"""  ancombc:
    label: ancombc
    doc: >-
      QIIME2_ANCOMBC_ASV / QIIME2_ANCOMBC2_ASV (both qiime2/qiime2:2026.4 - ancombc2 is
      in q2-composition 2026.4, no miyabi plugin): branch switch on the ancombc2 flag,
      category where-filter first (source runs the filtersamples per-category product
      through), ancombc --p-formula / ancombc2 --p-fixed-effects-formula, tabulate ->
      published qzv. Empty formula falls back to the category (upstream baseName of the
      per-category filtered table IS the category), then the table basename. Export
      folders, da-barplot/visualizer/volcano extras and versions dropped (tool help).
    when: "($(inputs.ancombc) || $(inputs.ancombc2)) && $(inputs.metadata) != null"
    in:
      table: import_table/qza
      metadata: filter_samples/metadata
      category: metadata_category
      formula1: ancombc_formula
      formula2: ancombc2_formula
      use_ancombc2: ancombc2
    out: [ {{id: result}} ]
    run:
{emb("/home/abennett/nf-core-ampliseq/udt-ancombc.yml")}
"""

text = open(DRAFT).read()
start_key = "  ancombc:\n    tool_id: TODO"
end_key = "  adonis:\n    tool_id: toolshed.g2.bx.psu.edu/repos/q2d2/qiime2__diversity__adonis"
assert text.count(start_key) == 1, "ancombc anchor not unique"
assert text.count(end_key) == 1, "adonis anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "  ancom_result: { outputSource: ancom/result, label: ancom_result }"
assert new.count(out_old) == 1, "ancom_result ref not unique"
new = new.replace(out_old, out_old +
    "\n  ancombc_result: { outputSource: ancombc/result, label: ancombc_result }")

# adonis carry-forward (ledger filter-samples-r-intersect-identity-correction): the
# source rebinds ch_metadata before QIIME2_DIVERSITY/ADONIS; adonis shares the
# metadata != null guard with filter_samples, so the swap can never dangle.
ad_old = "metadata_0|__q2galaxy__GUI__conditional__metadata__: metadata"
assert new.count(ad_old) == 1, "adonis metadata port not unique"
new = new.replace(ad_old, "metadata_0|__q2galaxy__GUI__conditional__metadata__: filter_samples/metadata")

assert "ancombc/TODO" not in new, "residual ancombc/TODO"
open(DRAFT, "w").write(new)
print("spliced ancombc:", j - i, "->", len(step), "; ancombc_result output added")
