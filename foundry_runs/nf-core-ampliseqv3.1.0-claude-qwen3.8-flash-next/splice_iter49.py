#!/usr/bin/env python3
"""Iteration 49: realize the expected-sequence comparison chain.

Replace the drafty compare_expected_sequences and compare_expected_abundances
blocks with concrete embedded-UDT steps plus the new expected_alignment
producer; add the producer to frame_postfilters. Asserts fire before the
write, so a failed expectation leaves the draft untouched.
"""

DRAFT = "/home/abennett/nf-core-ampliseq/galaxy-workflow-draft.gxwf.yml"
RUNDIR = "/home/abennett/nf-core-ampliseq"

def embedded(path):
    out = []
    with open(path) as fh:
        for ln in fh.read().splitlines():
            out.append(("      " + ln) if ln else "")
    return "\n".join(out)

udt_align = embedded(f"{RUNDIR}/udt-usearch-global-compare.yml")
udt_seq = embedded(f"{RUNDIR}/udt-compare-sequences.yml")
udt_perf = embedded(f"{RUNDIR}/udt-compare-performance.yml")

steps = f"""  expected_alignment:
    label: expected_alignment
    doc: >-
      ASV-to-expected global alignment - VSEARCH_USEARCHGLOBAL
      (comparison_wf:24-30, similarity 0.80 fixed there, BM args from
      conf/modules.config, --output_no_hits so unmatched ASVs get target "*" rows).
    when: "$(inputs.expected_sequences) != null"
    in:
      query: asv_fasta_knot/data_param
      db: expected_sequences
    out: [ {{id: tsv}} ]
    run:
{udt_align}
  compare_expected_sequences:
    label: compare_expected_sequences
    doc: >-
      EXPECTED_SEQUENCES comparison - COMPARE_SEQUENCES over the alignment above
      (bin/compare_sequences.r verbatim; region from expected_sequences_region,
      similarity 0.80). Emits the matches table consumed by compare_expected_abundances
      plus per-sample mismatch barplots. The optional expected_abundances input
      reproduces the source's ifEmpty([]) staging (absent - compare against all sequences).
    when: "$(inputs.expected_sequences) != null"
    in:
      alignment: expected_alignment/tsv
      observed: asv_table_knot/data_param
      expabund: expected_abundances
      region: expected_sequences_region
    out: [ {{id: matches}}, {{id: matches_per_sample}}, {{id: svg}}, {{id: png}} ]
    run:
{udt_seq}
  compare_expected_abundances:
    label: compare_expected_abundances
    doc: >-
      EXPECTED_ABUNDANCES comparison - COMPARE_PERFORMANCE (bin/compare_performance.r
      verbatim) over the sequence-comparison matches table; fbeta 2 and mismatch
      threshold 0 fixed (source ext values / schema default, no interface input),
      merge mode from expected_sequences_merge. Guarded on BOTH expected inputs: the
      source fires this task only when the matches producer ran (expected_sequences)
      AND the expected-abundance channel is non-empty. The val_md5sum_version tag
      column is a constant here (pipeline_info artifacts dropped precedent).
    when: "$(inputs.expected_sequences) != null && $(inputs.expected_abundances) != null"
    in:
      alignment: compare_expected_sequences/matches
      observed: asv_table_knot/data_param
      expabund: expected_abundances
      merge: expected_sequences_merge
    out: [ {{id: performance}}, {{id: performance_per_sample}}, {{id: abundance_table_per_sample}}, {{id: svg}}, {{id: png}} ]
    run:
{udt_perf}
"""

with open(DRAFT) as fh:
    text = fh.read()

start_key = "  compare_expected_sequences:\n    tool_id: TODO"
end_key = "  compare_expected_profile:\n    tool_id: TODO"
assert text.count(start_key) == 1, "sequences anchor not unique"
assert text.count(end_key) == 1, "profile anchor not unique"
i = text.index(start_key)
j = text.index(end_key)
assert i < j

frame_old = "asv_fasta_knot, compare_expected_sequences"
assert text.count(frame_old) == 1, "frame anchor not unique"

new = text[:i] + steps + text[j:]
new = new.replace(frame_old, "asv_fasta_knot, expected_alignment, compare_expected_sequences")

with open(DRAFT, "w") as fh:
    fh.write(new)
print("spliced: old", j - i, "-> new", len(steps))
