#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "parquet-two-jobs-and-taxonomy-output" not in t
entry = """
- id: parquet-two-jobs-and-taxonomy-output
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'parquet_tables concretized as TWO steps running the same embedded UDT
    ampliseq_duckdb_table2parquet (module''s exact wave image
    community.wave.seqera.io/library/duckdb-cli:1.5.5--9c6d18d9f687a45d, manifest probe
    HTTP 200 anonymously pullable; SQL verbatim COPY read_csv -> FORMAT PARQUET):
    parquet_tables (counts: summary_counts/tsv, when !skip_parquet_summary AND
    !skip_abundance_tables) and NEW parquet_taxonomy (tax_table_knot, when
    !skip_parquet_summary). Interface bounded edit: summary_parquet repointed to
    parquet_tables/table_parquet and a new summary_parquet_taxonomy output added; frame
    exports updated.'
  rationale: 'The nf-core module converts ONE table per job (caller maps it over the
    summary-table collection, workflows/ampliseq.nf:1133-1135) - a single two-port drafty
    step cannot reproduce per-job shape, and the source collection also holds more tables
    than the draft''s interface keeps (BUILD_ASV_ANNOTATIONS rows), so the split realizes
    the module job-per-table for exactly the summary tables the draft exposes. Output name:
    the module derives the parquet stem from the input filename (prefix = meta.id); a UDT
    from_work_dir must be static, so the file is table.parquet and the workflow-output
    labels carry identity. Delimiter fixed to tab - the module''s suffix derivation
    (.tsv->tab) always yields tab for the draft''s inputs; gz auto-decompressed by
    read_csv. SET threads/memory_limit (task.cpus/task.memory - no Galaxy equivalent)
    dropped, SET temp_directory kept; ext args/args2 and the versions eval line dropped
    (pipeline_info precedent). The counts job''s compound when mirrors the collection: the
    counts table is only in ch_summary_tables when !skip_abundance_tables (mix at :658
    inside the abundance-tables branch).'
  evidence:
  - 'modules/nf-core/duckdb/table2parquet/main.nf + environment.yml (wave +
    community-cr-prod blob URIs; duckdb=1.5.5; heredoc SQL quoted in the UDT help; stub
    branch translation-irrelevant)'
  - 'workflows/ampliseq.nf:1131-1136 (duckdb branch gated !skip_parquet_summary, map with
    id = filename stem) and :658/:1127 (collection members: SUMMARY_TABLE_COUNTS.tsv,
    SUMMARY_TABLE_TAXONOMY.out.tsv - the draft keeps counts + taxonomy)'
  - 'wave registry probe: cerbero.seqera.io token -> manifests/library/duckdb-cli/1.5.5--
    9c6d18d9f687a45d HTTP 200'
  - 'not run locally: no duckdb binary; SQL is the module verbatim, runtime check deferred
    to phase 11'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended parquet-two-jobs-and-taxonomy-output")
