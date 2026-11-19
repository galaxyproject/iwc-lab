#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to\n    phase 11'") or t.rstrip().endswith("phase 11'"), "unexpected ledger tail"
assert "summary-counts-wave-udt" not in t
entry = """
- id: summary-counts-wave-udt
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'summary_counts concretized as embedded UDT ampliseq_summary_counts pinning the
    source process''s exact community wave image (community.wave.seqera.io/library/
    r-base_r-data.table_r-dplyr_r-dtplyr_pruned:a6608bc81b0e6546, anonymously pullable -
    verified via the registry auth challenge + manifest GET), R body verbatim from
    SUMMARY_TABLE_COUNTS except a positional first-column rename, gzipped
    ampliseq.counts.tsv.gz output kept. Consumers rewired: workflow output counts_table plus
    the two step consumers parquet_tables and summary_report now read summary_counts/tsv.'
  rationale: 'Custom inline-R summarizer - no Tool Shed wrapper melts the ASV matrix, and the
    wave image is the evidenced container (its singularity fallback is the same blob), so the
    wave URI is pinned as-is rather than substituting a different R image. The source rename
    targets the literal ASV_ID header produced by the DADA2 biom chain; this draft''s count
    tables carry sequence keys under producer-varying headers, so the rename is positional
    (documented in the tool help). versions.yml writeLines dropped (pipeline_info precedent).
    The first splice left two step-level consumers pointing at the removed TODO_counts_long
    port - draft-validate topology caught it and both were rewired in the same iteration
    (producer-consumer invariant: grep must cover step-level references, not only workflow
    outputs).'
  evidence:
  - 'modules/local/summary_table_counts/main.nf (inline R dplyr/tidyr/readr melt + filter
    count>0 + write_tsv gz; wave + community-cr-prod blob container URIs; stub branch)'
  - 'environment.yml (r-base=4.3.1, r-dplyr=1.1.4, r-tidyr=1.3.1, r-readr=2.1.5, r-data.table,
    r-dtplyr, r-purrr, r-stringr)'
  - 'wave registry probe: WWW-Authenticate cerbero.seqera.io token flow -> OCI manifest
    (14 layers) for tag a6608bc81b0e6546'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended summary-counts-wave-udt")
