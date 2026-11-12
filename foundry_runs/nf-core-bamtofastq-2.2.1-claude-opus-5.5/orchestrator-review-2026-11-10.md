# Orchestrator review: nf-core/bamtofastq 2.2.1 Galaxy translation (Claude Opus run)

Date: 2026-11-10. This was a read-only review. I did not run planemo or Galaxy. Beyond reading files, computing hashes and reading the job command lines that planemo recorded, I ran one small probe of shell exit codes. It ran in the cached nf-core samtools container (`--network none`, test BAM mounted read-only), and the probe is described under issue 1.

Paths used below:
- `RUN` = `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-claude`
- `SRC` = `RUN/source/bamtofastq` (tag 2.2.1)
- `WF` = `RUN/galaxy-workflow.gxwf.yml`
- `T` = `RUN/galaxy-workflow.gxwf-tests.yml`
- `JOBS` = `RUN/planemo/phase12/test-output.json` (the executed command lines)
- Wrapper XML comes from the local checkouts `~/Galaxy/tools-iuc` and `~/Galaxy/galaxytools`. Their versions match the pins (samtools 1.22+galaxy2, stats 2.0.9, fastqc 0.74+galaxy1, fastq_info 0.25.3+galaxy0). I did not compare them byte for byte against the pinned Tool Shed changesets.

Each finding is tagged **[model]** (a choice the model made) or **[Foundry]** (a gap in the skill or tooling). Following the house rule, this review reports findings and proposes no workflow fixes.

## Verdict: mostly correct, with issues

On the path the test exercised (BAM input, every sample paired-end, default parameters), the translation matches nf-core exactly:
- The executed samtools flags are identical.
- The merge order and the concatenation order are identical.
- The FASTQ output equals the nf-core snapshot. This rests on two things:
  - The planemo decompressed compare passed. The run checked from planemo's code that nested assertions are evaluated, but ran no negative control.
  - I hashed the expected files myself: `zcat test-data/expected/*.fastq.gz | md5sum` gives 9b0c0886…, 40e17982…, a4984fb5… and bde23801…, which are the tokens in `SRC/tests/default.nf.test.snap:101-104`.
- flagstat and idxstats match the snapshot md5s exactly.

The problems are elsewhere:
- Some failure modes are silent where nf-core would fail loudly.
- The chr filter runs before the single/paired check instead of after it.
- CRAM is declared as an input type but does not work.
- The single-end and chr branches have no test, even though nf-test fixtures for them exist.

## Issues ranked by impact on scientific results

Silent divergences come first, then loud failures and missing features, then tests and portability.

### 1. SILENT: the user-defined tools lost nf-core's pipefail / errexit [model; Foundry]

**What nf-core does.** nf-core runs every process under `bash -C -e -u -o pipefail` (`SRC/nextflow.config:218-225`).

**What Galaxy does with a user-defined tool.** It adds only `set -e` (`galaxy-arash/lib/galaxy/jobs/command_factory.py:211-212`, with `strict_shell` always true for YAML tools at `lib/galaxy/tool_util/parser/yaml.py:231-233`). It never adds pipefail. Galaxy's own fixture writes `set -euo pipefail` into `shell_command` explicitly (`test/unit/app/tools/test_tool_deserialization.py:108`).

**Effect on the collate tool (`WF:562`), demonstrated.** The command is `samtools collate … | samtools fastq …`. I ran this pipe under `set -e` without pipefail, which is what Galaxy gives a user-defined tool, in `htslib_samtools:1.23.1`:

| Case | What happened | Pipe exit |
|---|---|---|
| BAM truncated to 60 kB | `collate` errored after writing the header; `samtools fastq` printed "processed 0 reads" | **0**, with an empty R1 |
| Input missing or unreadable | `fastq` failed with "Failed to read header" | non-zero (loud) |

So a `collate` failure partway through (corrupt input, temp disk full) gives a green job with an empty or truncated FASTQ. nf-core would fail it because of pipefail.

**Effect on the paired-end check (`WF:237-243`).** It runs `bash check_paired_end.sh` with no `-e` at all.
- **Unreadable file:** samtools fails, so `N=0`, `LINES=0`, awk divides by zero, and the sample is classified `single`. The misroute itself is silent. However, the single-end collate then fails loudly on the same file (header read error), so the chain does not end green.
- **Truncated file:** the probe gave `N=1000`, so classification goes ahead as normal.

nf-core fails CHECKPAIREDEND itself: the `LINES_TO_CHK=$(… | wc -l)` assignment at `SRC/modules/local/checkpairedend/main.nf:27` aborts under -e/pipefail.

This only triggers on read or IO errors, never on healthy input.

**Foundry gap.** There is no guidance on authoring user-defined tools that says to start `shell_command` with `set -euo pipefail` when porting from Nextflow.

### 2. SILENT: fastq_info no longer fails the run [model; Foundry]

**nf-core.** FASTQUTILS_INFO runs `fastq_info ${reads}` and only echoes "found no issues" if that succeeds (`SRC/modules/nf-core/fastqutils/info/main.nf:24-28`). A malformed or unpaired FASTQ therefore fails the pipeline.

**Galaxy.** The pinned `bgruening/fastq_info` wrapper maps exit codes 1 (unreadable or truncated file) and 3 (duplicate names, unpaired reads) to a **successful** job (`galaxytools/tools/fastq_info/fastq_info.xml:24-35`, commit e50b2852). JOBS confirms this command ran. A broken conversion therefore produces a green invocation, and the problem shows up only as text inside a report.

None of the run's artifacts records this change in semantics.

**Foundry gap.** This is the same root cause as the run's own major feedback entry `tool-summary-omits-command-template`: the tool summary does not show the wrapper's exit-code policy.

### 3. SILENT (rare): the chr filter runs before CHECKPAIREDEND [model]

**nf-core** classifies the full input first (`SRC/workflows/bamtofastq.nf:85`) and applies `SAMTOOLS_CHR` afterwards (`:119-121`).

**Galaxy** feeds `check_paired_end` from `pick_alignments`, which is the output of `chr_extract` when `chr` is set (`WF:208-209, 270`).

**Consequence.** If the first 1000 records of the region subset classify differently from the full file, the sample goes down the other branch. An empty subset gives `LINES=0`, which means `single`. A paired sample that is misrouted to the single-end branch loses its R1/R2 reads.

The model saw this divergence (`RUN/nextflow-galaxy-data-flow.md:77`) but did not record it in the ledger. The chr branch has no test.

### 4. LOUD / feature loss: CRAM is declared but not supported [model; Foundry]

The input accepts `cram` (`WF:18-20`), but:
- **Pre-conversion FastQC gets CRAM elements.** `fastqc_pre` takes all of `alignments` (`WF:145`). nf-core runs FastQC on BAM only (`SRC/subworkflows/local/pre_conversion_qc/main.nf:27-33`). The FastQC wrapper does not accept cram (`tools-iuc/tools/fastqc/rgFastQC.xml:69`), so Galaxy would insert its implicit `cram_to_bam_converter.xml`, which is `samtools sort` with no reference.
- **The shed samtools steps get no reference.** samtools view ×4, `chr_extract` and stats all have `addref_select: "no"` (`WF:134-135, 197-198, 364-365, …`). nf-core passes `--reference` whenever a FASTA is given (`SRC/modules/nf-core/samtools/view/main.nf:35`, `.../stats/main.nf:24`).

**Outcome.** These steps fail unless htslib can fetch the reference by M5, which needs network access and a public reference. When the fetch works, the reference is MD5-matched, so the data is not wrong. In that case there is one extra pre-FastQC output compared with nf-core.

The nf-core tests `cram.nf.test` and `no_crai.nf.test` have no Galaxy counterpart. The open ledger entries are `cram-elements-fastqc-pre` and `reference-not-wired-to-shed-samtools-steps`.

**Foundry gap.** There is no pattern for routing an optional reference into a wrapper's required `addref_cond` branch.

### 5. Outputs: minor gaps [model]

- **Missing output: the chr-extracted BAM.** nf-core publishes it because `SAMTOOLS_CHR` has no publishDir override (`SRC/conf/modules.config:161-165`); the snapshot lists `samtools/test3.chrX_chrY_X_Y.bam` (`SRC/tests/chr.nf.test.snap:66`). `chr_extract/outputsam` is not a Galaxy workflow output.
- **Justified substitutions:**
  - FastQC `.zip` becomes `fastqc_*_data` (text), because the wrapper has no zip output.
  - MultiQC is dropped. In 2.2.1 it only receives versions, the params summary and the methods YAML (`SRC/workflows/bamtofastq.nf:171-172, 217-225`); the QC mix is commented out.
  - The `<id>.<chr>` rename is dropped (cosmetic).
  - iGenomes `--genome` is dropped.

### 6. Tests: honest but narrow [Foundry; model]

**Strong assertions**
- `paired_reads`: decompressed compare against nf-core-container regenerations whose md5 equals the snapshot. I verified the md5s myself (see the verdict).
- `samtools_flagstat`, `samtools_idxstats`: exact snapshot md5 (`T:56-69` vs `SRC/tests/default.nf.test.snap:105-109`).

**Moderate**
- `samtools_stats`: 3 SN lines only, and just 1 for test2 (`T:70-82`).
  - Replacing the checksum is justified: the snapshot md5 covers the version and command header.
  - The values are consistent: 2821 reads per mate × 2 = 5642.

**Weakened, and the weakening is justified**
- `fastq_info_paired` was cut to `not_has_text ERROR`. I verified the snapshot tokens are md5s of nf-core's echo sentence, not of fastq_info output: `echo "fastq_utils fastq_info ran and found no issues with test_1.merged.fastq.gz test_2.merged.fastq.gz" | md5sum` gives db31682c…, and the test2 sentence gives 0222a414…. Both equal `snapshot:98-99`.
  - Given issue 2, this text check is the only failure signal at all.
  - I did not verify that fastq_info actually prints "ERROR" when it fails.
- `single_end_reads` is existence-only. Galaxy and planemo cannot assert an empty collection (Foundry feedback entries `planemo-collection-output-needs-element-tests` and `validate-tests-misses-collection-without-element-tests`).
- FastQC `has_text FastQC` matches nf-core, whose `.nftignore` ignores FastQC content (`SRC/tests/.nftignore:3`). Only element `test` is asserted.

**Coverage gap, plus an inaccurate claim**
- Only `default.nf.test` was translated.
- The debug report asks for "a single-end fixture" as new work (`RUN/workflow-debug-report.md:17`), and the model log says only that the default test has no single-end sample (`RUN/model-test-log.md:41`). The test plan does list `no_bai` and `chr` as untranslated (`RUN/galaxy-test-plan.yml:247`). The run just never connected those two cases to the single-end branch. Both already have a single-end fixture with a snapshot md5:
  - `SRC/tests/no_bai.nf.test.snap:98,119` has sample `test3_other.fq.gz`, md5 d8a93570….
  - `SRC/tests/chr.nf.test.snap:64,74` covers chr and single-end together.
- Still untested: the single-end branch, chr, collate_fast, the skip toggles, CRAM, and running without a FASTA. The default test supplies `reference_fasta`.

### 7. Parameters: correct, including the 59 "missing" ones [model OK; Foundry]

**Explicit state against nf-core** (executed command lines in JOBS):

| Step | nf-core (`conf/modules.config`) | Galaxy executed | Match |
|---|---|---|---|
| view_map_map | `-b -f1 -F12` (:68) | `-b -f 1 -F 12 -G 0` | yes |
| view_unmap_unmap | `-b -f12 -F256` (:131) | `-b -f 12 -F 256 -G 0` | yes |
| view_unmap_map | `-b -f4 -F264` (:123) | `-b -f 4 -F 264 -G 0` | yes |
| view_map_unmap | `-b -f8 -F260` (:115) | `-b -f 8 -F 260 -G 0` | yes |
| collate ×3 | args `-f -r N` if fast; args2 `-N` (:40-41, :50-51, :59-60) | `collate [-f -r N] … \| fastq -N` | yes |
| fastqc pre/post | `--quiet`; when `!no_read_QC` (:20-29) | `--quiet --extract --kmers 7 -f bam/fastq`; `when: !skip` | yes (7 is FastQC's default; `-f bam` = nf-core's extension auto-detect) |
| flagstat/idxstats/stats | no args; when `!no_stats` (:76-94) | no args; `when: !skip` | yes |
| stats `--reference` | passed when FASTA given (stats/main.nf:24) | not passed | inert for BAM; matters only for CRAM (issue 4) |
| merge_unmap | no args, order uu, um, mu (alignment_to_fastq/main.nf:35-40) | `merge -s 1 -f out 0.sam 1.sam 2.sam` in the same order | yes |
| chr_extract | `-hb` plus regions (:162-163) | `-b`, regions split on whitespace (samtools_view.xml:107) | yes for BAM (`-h` is a no-op); never executed |
| fastq_info | no args | `-q` checked (no flag), `-r` off | yes, apart from the exit-code semantics in issue 2 |

**The 59 omitted parameters.** The names below are my reading of the wrapper XML. They are consistent with the reported per-tool counts (35 + 12 + 9 + 3), but I did not diff the tool-cache input trees against each step's `state`. Some names may differ, for example nested conditionals such as view's subsample `seed`, and the last 3 being samtools_merge is an inference.
- samtools_view, 7 × 5 steps: `quality`, `library`, `cigarcons`, `tag`, `qname_file`, `collapsecigar`, `readtags`.
- fastqc, 4 × 3 steps: `contaminants`, `adapters`, `limits`, `min_length`.
- samtools_stats, 9: `gc_depth`, `insert_size`, `read_group`, `read_length`, `most_inserts`, `trim_quality`, `sparse`, `remove_overlaps`, `cov_threshold`.
- samtools_merge, 3: `bed_file`, `region`, `headerbam`.

On the executed steps, none of the defaulted parameters emits a flag beyond what nf-core runs. The executed command lines contain only the flags shown in the table above.
- Confirmed from executed command lines for view ×4, stats, fastqc_pre, fastqc_post_paired and merge.
- Confirmed only by reading the template for `chr_extract` (it was skipped) and `fastqc_post_single` (it mapped over an empty list).
- Residual risk: a future wrapper could change its defaults. Galaxy also logged `request state … validation_failed` for 14 of the 28 steps (`planemo/phase12/planemo.log:4987` onward). `gxwf validate --strict` disagrees with Galaxy's request model; this is recorded as Foundry feedback.

### 8. Two user-defined tools: faithful ports, justified, but costly to deploy [model]

**CHECKPAIREDEND** (`WF:222-273` vs `SRC/modules/local/checkpairedend/main.nf:24-36`). The port is faithful line by line, including the `<1000` fallback and the `= "1"` test. Differences:
- `--reference` is passed for BAM as well (inert).
- The outputs are `paired`/`single` tokens instead of files.
- pipefail is missing (issue 1).

No Tool Shed tool does this classification, so authoring one is justified.

**collatefastq** (`WF:550-624` vs `SRC/modules/nf-core/samtools/collatefastq/main.nf:29-50`). The command is the same, and the container is the same as nf-core's (`htslib_samtools:1.23.1`).

The reasons it gives for not using existing wrappers are valid:
- iuc `samtools_fastx` runs `samtools sort -n` before `fastq` (`samtools_fastx.xml:14`). Read order changes and there is no `-r`.
- The local tools-iuc checkout also contains `samtools_collate`, which the run did not record considering. It would not have reproduced nf-core either: it has only `-f` with no `-r`, accepts sam/bam only, and outputs `unsorted.bam`, which `samtools_fastx` would re-sort (`samtools_collate.xml:13, 19, 24`).

Scientifically, `samtools_fastx` would very likely give the same reads in a different order. The user-defined tool buys byte fidelity.

**Deployment cost:**
- Needs `enable_beta_tool_formats` plus the `user_tool_execute` role.
- Not available from the Tool Shed, so it cannot be submitted to IWC as is.
- Uses a wave.seqera.io container with no conda requirement.
- Mixes samtools 1.23.1 (the user-defined tools) with 1.22 (the shed steps).

### 9. Checked and matching nf-core (no issue)

- **Single/paired split.**
  - nf-core: CHECKPAIREDEND, then join and branch on `meta.single_end` (`SRC/workflows/bamtofastq.nf:85-115, 150-153`).
  - Galaxy: classifier, then `collapse_dataset` (adds element ids), `Filter1 c2=='paired'`, `Cut1 c1`, and `__FILTER_FROM_FILE__ remove_if_absent`. Filtered = paired, discarded = single (`WF:222-324`).
  - JOBS shows the table `test\tpaired`, `test2\tpaired` with Filter1 keeping 2/2 lines.
  - Empty branches map over empty lists; this was exercised on the single-end side in the run.
- **Single-end stream.** nf-core sends `SAMTOOLS_COLLATEFASTQ_SINGLE_END.out.fastq_other` on to post-QC and publishes `*other.fq.gz` (`SRC/workflows/bamtofastq.nf:178`, `SRC/conf/modules.config:39-45`). Galaxy's `single_end_reads` is `collate_fastq_single/fastq_other`, run with `single_end: true` (`WF:51, 802-809`), and it feeds `fastqc_post_single` and `fastq_info_single`.
- **Paired path.**
  - Four views feed `merge(uu, um, mu)` (`SRC/subworkflows/local/alignment_to_fastq/main.nf:23-54`).
  - Mapped and merged-unmapped BAMs are each collated.
  - `CAT_FASTQ` concatenates `[m1, u1]` and `[m2, u2]` (`SRC/modules/nf-core/cat/fastq/main.nf:35-40`).
  - Galaxy's `cat_r1`/`cat_r2` take mapped first, then unmapped (`WF:700-727`), and `__ZIP_COLLECTION__` produces `list:paired`.
  - Post-QC and fastq_info run on the concatenated reads, as in nf-core `:178-183`.
- **Index handling.** nf-core `PREPARE_INDICES` runs `SAMTOOLS_INDEX` only when the samplesheet has no index, and `SAMTOOLS_FAIDX` only when there is no fai (`SRC/subworkflows/local/prepare_indices/main.nf:24, 33, 37, 47`). Galaxy covers both:
  - BAM index: Galaxy's bam metadata index. JOBS shows `ln -s …metadata….dat infile.bai` for view, stats and idxstats.
  - fai: the user-defined tools pass `--reference`, and samtools builds the fai itself.
  - CRAM: the wrappers' `samtools index` fallback.
  - The drop is justified.
- **Inputs** (`SRC/nextflow_schema.json`, main options and references):

  | nf-core param | Galaxy input |
  |---|---|
  | `input` | `alignments` (list) |
  | `fasta` | `reference_fasta` |
  | `chr` | `chr` |
  | `no_read_QC` | `skip_read_qc` |
  | `no_stats` | `skip_stats` |
  | `samtools_collate_fast` | `collate_fast` |
  | `reads_in_memory` | `reads_in_memory` (default 100000, `SRC/nextflow.config` params) |

  Dropped, all justified (`RUN/nextflow-galaxy-interface.md:45-55`):
  - `fasta_fai`: rebuilt by samtools.
  - `genome`/`igenomes_*`: v1 policy of no reference data tables.
  - MultiQC options: MultiQC itself is dropped.
  - Publish, email and boilerplate options.
- **Published outputs.** fastqc, fastqutils, samtools flagstat/idxstats/stats, `reads/*.merged.fastq.gz` and `reads/*other.fq.gz` all have Galaxy outputs. The exceptions are in issue 5.

### 10. Unresolved per the run's own records

- `open-requirements.ledger.yml`, open entries: `igenomes-genome-key-dropped`, `cram-elements-fastqc-pre`, `multiqc-versions-report-dropped`, `chr-identifier-rename-not-carried`, `no-iwc-precedent-pair-class-split`, `reference-not-wired-to-shed-samtools-steps`, `fastqc-zip-not-exposed`.
- `foundry-feedback.ledger.yml`: 12 entries open, none filed. The three major ones are `summarize-nextflow-ext-when-gating-not-captured`, `tool-summary-omits-command-template` and `snapshot-gz-md5-is-over-decompressed-content`.
- `galaxy-workflow-validation-result.json`: 6 residual runtime risks, covering the user-defined tool role, pick_value fallback, empty single-end list, CRAM, the Apply Rules regex, and identifier characters.
- Model log: 14 steps failed Galaxy's request-state validation, which Galaxy says does not affect execution. SQLite lock retries were also logged.

**Not in any run artifact** (new in this review): issue 1 (pipefail), issue 2 (fastq_info semantics), the chr ordering as a ledgered risk, the chr BAM output, and the fact that single-end fixtures already exist in `no_bai`/`chr`.

## Not checked

- I ran no workflow. The untested branches (single-end, chr, collate_fast, CRAM, skip toggles, no FASTA) are assessed by reading code only. The only thing I executed was the exit-code probe in issue 1.
- I did not compare the local wrapper XML byte for byte against the pinned Tool Shed changesets.
- I did not verify that fastq_info prints "ERROR" on a bad file.
- I did not test whether samtools 1.22 exits non-zero on the unknown regions in `chr = 'chrX chrY X Y'`.
