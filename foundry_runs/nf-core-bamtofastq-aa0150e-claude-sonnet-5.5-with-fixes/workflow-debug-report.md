# Debug report: nf-core/bamtofastq → Galaxy

Final state: `planemo test` **passed** (attempt 3 of 3), see `workflow-test-result.json`. There is no open failure; this report classifies the two earlier red runs so the evidence is kept.

## Attempt 1 — failed before Galaxy started (not an import rejection by Galaxy)
- Surface: Planemo's own gxformat2 → native conversion (`ValueError: invalid literal for int() with base 10: 'convert_to_bam'`), 2 s after start; no ids, no structured JSON.
- Cause: map-form steps carried a descriptive `label` while `in:`/`outputSource` referenced the map key; gxformat2 resolves the step part by label when present. `gxwf validate`, `draft-validate --concrete --strict-state` and `validate-tests` all accepted the file (validator gap, recorded in the feedback ledger).
- Fix: label text moved into `doc`; re-extracted. Route: template/implement phase (wiring convention).

## Attempt 2 — invocation scheduled, all 11 tool steps' jobs `ok`, 2 output assertions failed
- Surface: assertion mismatch (collection elements `alignment_stats`, `fastq_integrity`), per `output_problems` in `planemo/attempt2.json`.
- Evidence: md5 of Galaxy output 53fc8329… vs snapshot token 3c3f8fa5… (samtools stats); dc9907ef… vs db31682c… (FASTQ info).
- Classification: **assertion-choice problem, not a workflow regression.** samtools stats prints the tool version and command line (`infile`, `-@`) in its header; the nf-core `fastqutils/*.txt` file is an echo written by the nf-core module (`source/modules/nf-core/fastqutils/info/main.nf`), whereas the Galaxy wrapper emits fastq_info's own stdout (which contains temp dataset paths). The flagstat and idxstats tokens did match, as did FASTQ line counts and read names.
- Fix and IWC-shortcut check: the checksums were replaced by content assertions measured from the fixture BAMs (stats `raw total sequences` 5642/5436; fastq_info `Number of reads` 2821/2718 and `OK`, the output layout observed by running the fastq_utils 0.25.3 biocontainer on a synthetic FASTQ). No md5 from the Galaxy output was adopted, and the relaxation is not an existence-only check.

## Residual risks (not exercised by the single planned test)
- `skip_read_qc` / `skip_stats` = true (skipped steps → null collections feeding MultiQC).
- CRAM input (needs reference decoding in `samtools_view`), single-end BAM (dropped feature), `--chr` (dropped).
- Read order of the FASTQ differs from nf-core's (single `samtools fastx` after name-sort), so nf-core's decompressed-md5 tokens for `reads/*.merged.fastq.gz` were not reproduced and are not asserted.
