#!/usr/bin/env python3
"""Iteration 56: concretize parquet_tables as two duckdb steps (module is one-table-per-job);
add summary_parquet_taxonomy workflow output."""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"

def emb(p):
    return "\n".join(("      " + ln) if ln else "" for ln in open(p).read().splitlines())

UDT = "/home/abennett/nf-core-ampliseq/udt-duckdb-table2parquet.yml"

step = f"""  parquet_tables:
    label: parquet_tables
    doc: >-
      DUCKDB_TABLE2PARQUET on the long counts summary table (ampliseq.counts.tsv.gz; the
      module's wave duckdb-cli image pinned, SQL verbatim). Split from the template's
      two-port single step: the module converts ONE table per job (source maps it over the
      summary-table collection), so the taxonomy summary gets its own step
      (parquet_taxonomy) and static from_work_dir names the fixed table.parquet -
      workflow-output labels carry the identity. Gated by BOTH source conditions: the
      parquet branch and the presence of the counts table (skip_abundance_tables removes
      it from the mapped collection upstream).
    when: "!$(inputs.skip_parquet_summary) && !$(inputs.skip_abundance_tables)"
    in:
      table: summary_counts/tsv
    out: [ {{ id: table_parquet }} ]
    run:
{emb(UDT)}
  parquet_taxonomy:
    label: parquet_taxonomy
    doc: >-
      DUCKDB_TABLE2PARQUET on the consolidated taxonomy table (the source maps the module
      over the summary-table collection; the draft exposes counts + taxonomy parquets -
      the summary tables its interface keeps). Same pinned wave duckdb-cli image.
    when: '!$(inputs.skip_parquet_summary)'
    in:
      table: tax_table_knot/data_param
    out: [ {{ id: table_parquet }} ]
    run:
{emb(UDT)}
"""

text = open(DRAFT).read()
start_key = "  parquet_tables:\n    tool_id: TODO"
end_key = "  pplace_align:\n    label: pplace_align"
assert text.count(start_key) == 1, "parquet_tables anchor not unique"
assert text.count(end_key) == 1, "pplace_align anchor not unique"
i = text.index(start_key); j = text.index(end_key)
assert i < j
new = text[:i] + step + text[j:]

out_old = "summary_parquet: { outputSource: parquet_tables/TODO_parquet, label: summary_parquet }"
assert new.count(out_old) == 1, "summary_parquet ref not unique"
new = new.replace(out_old,
    "summary_parquet: { outputSource: parquet_tables/table_parquet, label: summary_parquet }\n"
    "summary_parquet_taxonomy: { outputSource: parquet_taxonomy/table_parquet, label: summary_parquet_taxonomy }")

fr_old = "[export_tree, phyloseq, tse, parquet_tables, pplace_align,"
assert new.count(fr_old) == 1, "frame anchor not unique"
new = new.replace(fr_old, "[export_tree, phyloseq, tse, parquet_tables, parquet_taxonomy, pplace_align,")

assert "parquet_tables/TODO" not in new and "TODO_parquet" not in new, "residual parquet TODO"
open(DRAFT, "w").write(new)
print("spliced parquet_tables+parquet_taxonomy:", j - i, "->", len(step), "; outputs + frame updated")
