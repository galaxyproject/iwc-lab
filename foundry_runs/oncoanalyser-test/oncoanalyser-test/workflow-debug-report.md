# Workflow debug report — oncoanalyser core DNA spine

**Input:** `workflow-test-result.json`, `status: not-run` (user decision, 2026-11-11).
**Classification: no failure surface. There is no runtime evidence to triage.**

The workflow test was never executed, so no import, job, invocation, collection, or assertion failure exists to classify. This report records that state and the evidence that *was* gathered, so it isn't read as a clean run.

## What was checked instead (not a test run)

| Check | Result | Evidence |
|---|---|---|
| `gxwf validate` (terminal) | pass, 18/18 tool states | `galaxy-workflow-validation-result.json` |
| `gxwf validate-tests --workflow` | pass | same |
| Import into test.galaxyproject.org | pass: 34 steps, no step errors | workflow `30b0ca049992aa27` |
| UDT staging of a `bam` input | **finding**: staged as a bare `.dat`, no index | dataset `436268cefcc58209`; repaired by adding `.bai` edges from REDUX |
| Archive extraction in the hmftools image (first try) | **fail**: BusyBox tar has no wildcard members (`*/common/ensembl_data: not found in archive`) | dataset `703493f5161f518b`; would have failed every hmftools step |
| Archive extraction (revised: list → grep → `tar -T`) | pass; bioconda `amber` wrapper accepts `-Xmx` | dataset `2b536c102b57dd14` |

All probes are in history `b1251ce3b0e2e90f3f525f72ec419291`.

## Residual risks a real run must settle

1. **Resources.** The test needs ~59 GB of references against a 10.7 GB quota. UDT jobs got 3.8 GB RAM and 4 slots despite `ram_min`. The bwa-mem2 index build from the history FASTA needs about 64 GB.
2. **Unexecuted hmftools command lines.** REDUX, COBALT, ESVEE, SAGE, PAVE, PURPLE, and LINX have never run; only AMBER's image start-up was probed.
3. **VCFs without `.tbi`** feed PAVE, PURPLE and LINX germline. These tools are assumed to read VCFs sequentially.
4. **Checksum parity** with the nf-test snapshot depends on identical alignments (bwa-mem2 2.3 vs 2.2.1, samtools vs sambamba sort).

## Recommended next step

Run the test on a Galaxy server that allows user-defined tools with ≥32 GB per job and has the GRCh38_hmf references staged. Alternatively, smoke-run each hmftools UDT on a small real BAM pair first. If a step fails, start from its job stderr (galaxy-tool-job-failure-reference) before touching assertions.
