#!/usr/bin/env python3
L = "/home/abennett/nf-core-ampliseq/open-requirements.ledger.yml"
t = open(L).read()
assert t.rstrip().endswith("runtime check deferred to phase 11'"), "unexpected ledger tail"
assert "import-table-identity-corrected-udt" not in t
entry = """
- id: import-table-identity-corrected-udt
  decided_by: advance-galaxy-draft-step
  basis: agent
  decision: 'import_table concretized as embedded UDT ampliseq_import_table
    (quay.io/qiime2/qiime2:2026.4, the source module container), replacing the template''s
    pinned q2d2 qiime2_core__tools__import (identity-pinned tool_id, TODO version). The UDT
    shell is the verbatim QIIME2_INASV script (sed biom-header strip; biom convert
    --table-type="OTU table" --to-hdf5; qiime tools import --type FeatureTable[Frequency]
    --input-format BIOMV210Format) plus the source XDG/MPL/NUMBA cache exports. Consumer
    filter_samples''s TODO_table RHS rewired import_table/TODO_qza -> import_table/qza.'
  rationale: 'The q2d2 import wrapper consumes a BIOM artifact only; this draft carries the ASV
    table as a plain tab-separated, ASV-sequence-keyed tsv, so the tsv-to-biom pre-conversion
    the source performs (biom convert) must live in the step tool - same identity correction
    class as import_taxonomy (that step''s help already records it for the taxonomy sibling).
    biom-format''s load_table accepts the plain tsv as a simple BIOM text table (first column
    observations, header row samples), so no conversion of keys is needed; the biom-header sed
    is kept verbatim and is a no-op for header-less inputs. Deviations: versions.yml not
    published (pipeline_info dropped precedent); no when guard mirrors the source (the main-branch
    import always runs).'
  evidence:
  - 'modules/local/qiime2_inasv/main.nf (container qiime2/qiime2:2026.4; script lines quoted in
    the UDT help; emits table.qza) + environment.yml (biom-format=2.1.17 in the qiime2 image)'
  - 'draft pinned identity q2d2/qiime2_core__tools__import with _plan_state "feature-table format
    per exemplar qiime2-VI import idiom" - exemplar import cannot pre-convert tsv'
  - 'sibling precedent in-draft: import_taxonomy (qiime2/qiime2:2026.4 UDT with the same cache
    exports; identical q2d2 identity correction documented in its tool help)'
"""
open(L, "w").write(t.rstrip() + "\n" + entry.lstrip("\n"))
print("appended import-table-identity-corrected-udt")
