# Orchestrator questions — answers (nf-core-bamtofastq-glm, 2026-11-10)

## Q: `samtools_collate_fast` and `reads_in_memory` inputs are unwired — on purpose? Where is that recorded?

**Yes, unwired on purpose.** Two-part reason:

1. **Why they exist as workflow inputs at all:** they mirror the source's
   `params.samtools_collate_fast` / `params.reads_in_memory`. In the source
   (`conf/modules.config:40,50,59`) these feed exactly one thing:
   `ext.args = { params.samtools_collate_fast ? "-f -r " + params.reads_in_memory : "" }`
   on the three COLLATE_FASTQ arms. The interface brief declared them as
   workflow inputs for source-parameter parity
   (`nextflow-galaxy-interface.md` "Collate fast mode" row), and the data-flow
   brief classifies them as controls: "Feed `when:` gates and tool parameters
   only; no dataset edges" (`nextflow-galaxy-data-flow.md` Controls row).

2. **Why they are not wired to any step:** the wrapper
   (`samtools_collate 1.22+galaxy1`, tool-cache
   8c97d8f9d243fec3dc173dbe511744222103615443174bb98341a1383d40cbf5.json)
   exposes only `input`, `no_pg`, `fast_mode` — there is **no `-r`
   (reads-in-memory) input**, so the source's `-f -r N` cannot be expressed.
   `-f` (fast_mode) alone is not a faithful substitute either: the source's
   collatefastq fast mode relies on `-r N` to keep secondary/supplementary
   records in memory, and `-f` without `-r` would **drop** those records —
   wrong for the pipeline's read-extraction semantics, which must keep all
   reads. All three collate steps therefore pin `fast_mode: false` in state
   (the wrapper default, matching the source's default `ext.args = ""`) and
   leave the two inputs inert.

**Where recorded:** in the `doc:` blocks of all three collate steps in
`galaxy-workflow.gxwf.yml`:

- `collate_mapped` (COLLATE_FASTQ_MAP arm): "fast_mode false: source's
  samtools_collate_fast -f would DROP secondary/supplementary records and -r is
  not expressible in this wrapper (no -r input) — samtools_collate_fast/
  reads_in_memory inputs accepted but not effective (deviation; fast mode
  semantics differ)."
- `collate_unmapped`: same mode-semantics sentence.
- `collate_single`: adds "params.samtools_collate_fast would additionally pass
  -r reads_in_memory, which this wrapper cannot express (no -r input) —
  samtools_collate_fast/reads_in_memory inputs are accepted but not effective
  here (deviation, ledger-worthy at test tier if the param is exercised)."

**Honest gap you found:** there is **no entry in `open-requirements.ledger.yml`**
for this deviation — the recording lives only in the step docs. The
`collate_single` doc itself flags it as "ledger-worthy at test tier if the
param is exercised", and the test plan (`galaxy-test-plan.yml`) classifies
`collate_fast` as a bootstrap-only test branch not exercised by the default
test, so it never surfaced during the test phase. If you want it in the ledger
properly, it belongs as a `dropped`-style entry: "samtools_collate_fast /
reads_in_memory workflow inputs are declared but cannot affect any step — the
collate wrapper has no -r input; enabling the boolean in Galaxy would silently
do nothing, unlike in the source pipeline." Not added unilaterally since your
question asked for an answer, not a change — say the word and I'll add it.

No workflow change made for this question, as requested.
