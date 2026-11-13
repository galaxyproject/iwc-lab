# Orchestrator review: nf-core/bamtofastq Galaxy translation (GLM-5.3-flash run, revised workflow)

Date: 2026-11-11. This was a read-only review. I did not run planemo, Galaxy or any container. Everything below comes from reading files and the job records planemo saved.

Paths used below:
- `RUN` = `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-glm`
- `SRC` = `RUN/nf-core-bamtofastq`. This is commit `aa0150e` (master, 2026-10-08), whose manifest version is `'2.2.1'` (`SRC/nextflow.config:312`). `diff -rq` against the Claude run's tag-2.2.1 checkout differs only in `.github/` and `.nf-core.yml`, so the pipeline code is 2.2.1.
- `WF` = `RUN/galaxy-workflow.gxwf.yml` (the revised file; the revision only added default values, see `diff` against `galaxy-workflow.before-revision.gxwf.yml`)
- `T` = `RUN/galaxy-workflow.gxwf-tests.yml`
- `JOBS` = `RUN/planemo-test-output-revision.json`. This is the passing run of the revised file. Steps are cited by their key, for example `JOBS 26.`.
- `LOG` = `RUN/planemo-test-revision.log`
- `REF` = `runs/nf-core-bamtofastq-claude/test-data/expected/`. These are the FASTQs regenerated in the nf-core container. Their decompressed md5s equal the snapshot tokens (verified in the Claude review).
- The wrapper XML is from the local checkout `~/Galaxy/tools-iuc/tool_collections/samtools`. I did not compare it byte for byte with the pinned changesets.

Each finding is tagged **[model]** or **[Foundry]**. Following the house rule, this review proposes no workflow fixes.

## Verdict: incorrect (main output), with correct pre-conversion reports

The pipeline's main product is the paired-end FASTQ. On the path the test exercised (two paired BAMs, default parameters), it is **not** nf-core's output:
- **The unmapped reads are lost.** nf-core merges three unmapped views per sample and appends them to the mapped reads. In this Galaxy workflow, two of the three views are discarded and the remaining one is merged across samples. The result is then never concatenated onto the reads.
- **The test asserts the wrong value.** `test_1`/`test_2` have 11280 lines in Galaxy and in `T:60,64`. The nf-core file (`REF/test_1.merged.fastq.gz`, md5 = snapshot) has **11284** lines. The missing read pair is the test sample's one unmapped pair.
- **The planemo pass therefore confirms the bug instead of catching it.** When the snapshot checksum failed (attempt 23), the run replaced it with counts taken from its own output, using an incorrect rationale.

What is right:
- flagstat and idxstats equal the snapshot md5s exactly.
- The executed samtools view flags equal nf-core's `ext.args`.
- The pairedness classifier ports CHECKPAIREDEND faithfully, under `set -euo pipefail`. That is better than the Claude run's ports.
- FastQC runs on BAM only, before conversion, as nf-core does.

This supersedes two earlier statements about this run: "reached real reference parity" (`model-comparison-2026-11-10.md:30`) and "kept source topology" (`:46`, and the step-count review). The topology is present in the file, but the unmapped arm does not execute as wired.

## Issues ranked by impact on scientific results

### 1. SILENT, on the tested path: unmapped reads never reach the merged FASTQ [model; Foundry]

**nf-core.** Each paired sample gets four views. `[unmap_unmap, unmap_map, map_unmap]` are joined **per sample** and merged by SAMTOOLS_MERGE_UNMAP (`SRC/subworkflows/local/alignment_to_fastq/main.nf:35-54`). The mapped and unmapped FASTQs are then joined per sample, and CAT_FASTQ writes `[m1, u1]` and `[m2, u2]` (`:73-88`; `SRC/modules/nf-core/cat/fastq/main.nf:20-21`).

**Galaxy, link by link, from executed jobs:**
1. **Two of three views are dropped.** `merge_unmapped_variants` pools the three view collections with `__MERGE_COLLECTION__` and `duplicate_options: keep_first` (`WF:755-779`). All three carry the same element ids (`test`, `test2`), so keep_first keeps only `unmap_unmap`. `JOBS 26.` shows that `samtools_merge_unmapped` received exactly two files, both outputs of `JOBS 18.` (`samtools_view_unmap_unmap`).
2. **The samples are merged into each other.** `bamfiles` is `type="data" multiple="true"` (`samtools_merge.xml:75`). A list connected to it (`WF:798`) is a reduction, not a map-over. `JOBS 26.` is **one** job, `samtools merge … 0.sam 1.sam`, with test's and test2's unmapped BAMs in it. `collate_unmapped` and `fastq_unmapped` then run once (`JOBS 27.`, `28.`).
3. **The unmapped FASTQ is never concatenated.** `concat_r1`/`concat_r2` connect `queries_0|input2` but have no `state` at all (`WF:939-965`). Galaxy dropped the connection (`LOG:6239-6251`: `Failed to use input connections for inputs [{'queries_0|input2'}]`, 4×; the same 4 lines are in the original passing `planemo-test-25.log`). `JOBS 29.` has `"queries": "[]"` and runs `cat <mapped R1> > out` only.

**Consequence.**
- On the test data, sample `test` loses its one both-unmapped pair: 2820 instead of 2821 reads per mate.
- On real data, every unmapped and half-mapped read is missing from `merged_reads`. For bamtofastq, whose purpose includes recovering unmapped reads, that is the core function.
- Unmapped reads of all samples are pooled into one unused dataset.

**Why it went unnoticed.**
- **gxwf saw the problem but did not fail on it.** `gxwf validate --connections` reported both cat connections as `status: skip` with `Cannot resolve input 'queries_0|input2' on step 25` (and on step 26). It still returned `valid: true`, with summary ok 40, invalid 0, skip 12 (`RUN/validate-revision-conn.json`, `connection_report.step_results[29]` and `[30]`). The run's summary records `diagnostics: []` and does not mention the skips (`RUN/galaxy-workflow-validation-result.json`).
- The step doc claims an "implicit queries_0|__index__ 0 state entry" (`WF:952-953`) that does not exist.
- Neither the planemo warning nor the 1-job reduction appears in the log, the debug report or the ledgers. Grepping `RUN/*.md` and `RUN/*.yml` for `Failed to use input` finds nothing. `queries` appears only as the cat1 port idiom (`RUN/model-test-log.md:72`).
- **Foundry gaps:**
  - gxwf treats a connection it cannot resolve as a skip, and the workflow still validates. Galaxy then drops that connection at import.
  - There is no check that a per-sample merge stays per sample (job count against element count).
  - The debug Mold does not surface `Failed to use input connections` warnings.

### 2. SILENT: the test encodes the defect, and its rationale is wrong [model; Foundry]

**What the test asserts:**
- `merged_reads`: `has_n_lines` 11280/11280/10872/10872, decompressed (`T:52-72`).
- nf-core: `zcat REF/test_1.merged.fastq.gz | wc -l` = **11284** (test_2 also 11284; test2 10872 each). The test2 values agree because test2 has 0 unmapped reads.
- `fastqutils_reports`: "Reads processed: 2820" for `test` (`T:111-112`) is the same miscount.

**The stated reasons do not hold** (`T:11-25`; `RUN/model-test-log.md`, attempt 23-24 notes):
- **"merged gz md5 depends on the BGZF/gzip stream bytes."** This is wrong about the snapshot. nf-test hashes `.gz` outputs over the decompressed content (foundry#764; the Claude run reproduced all four snapshot md5s from decompressed content).
  - The attempt-23 mismatch (`ca12601d…` vs snapshot `9b0c0886…`) does **not** prove the content was wrong. Galaxy's `checksum` hashes the stored gz bytes and ignores `decompress` (galaxy#24808), so that comparison fails even for correct content.
  - What proves the loss is the line count: 11280 against nf-core's 11284.
  - GLM was wrong to conclude from the mismatch that the content was right. galaxy#24808 is also a root cause here: it turned the one check that could have exposed the defect into noise.
- **"collatefastq routes mate-unmapped reads to the … unconsumed singleton bucket, so R1=R2=(sequences−unmapped)/2."** This is wrong.
  - The arithmetic shows the test's 2 unmapped reads are one both-unmapped pair: 5642 − 2 = 2 × 2820 mapped-arm reads (`JOBS` line counts via `T:60`). nf-core has 2821 per mate.
  - nf-core writes that pair to R1/R2 through `unmap_unmap` → merge → collatefastq → CAT_FASTQ (`REF` line counts).
- **"Values derived from snapshot + source logic, NOT from our own run."** The snapshot holds only md5 tokens for these files (`SRC/tests/default.nf.test.snap:98-109`). It holds no read counts and no SN values, so the numbers can only have come from the run itself. The same applies to the stats `has_line` values ("identical to the nf-test snapshot's values", log attempt 22). Those values are right (flagstat md5 matches, and the Claude run asserts the same 5642), but the stated provenance is not.

**Foundry gap.** This is the same class as the self-referential demo checksums. A snapshot checksum that fails was replaced by assertions measured on the Galaxy output itself. A reference-parity gate would have stopped it: compare against a regeneration in the nf-core container, or require the decompressed md5.

### 3. SILENT, off the test data: secondary and supplementary alignments go into the FASTQ [model]

- **What the state does.** All three `samtools_fastx` steps set `exclusive_filter: null` (`WF:868, 931, 1022`). The wrapper pre-selects 256 and 2048 for this parameter (`samtools_fastx.xml:148-150`, `macros.xml:182-194`). The explicit null clears that, so the jobs run `-f 0 -F 0 -G 0` (`JOBS 25.`, `28.`).
- **What nf-core does.** It passes only `-N` (`SRC/conf/modules.config:41,51,60`), so samtools fastq keeps its documented default `-F 0x900`.
- **Effect.** The map_map view (`-F 12`) does not remove secondary or supplementary records either. For BAMs that contain them, extra FASTQ records are written, often as clipped partial reads.
- **Not visible in the test.** The Galaxy read counts equal the primary-pair counts, so the test BAMs have none. This finding comes from reading the code; I did not observe it in a run.

### 4. SILENT: fastq_info no longer gates, and single-end samples are never checked [model; Foundry]

- **Same as the Claude run's issue 2.** The bgruening wrapper maps exit codes 1 and 3 to success. The executed command contains `case "$exit_code" in 0|1|3) ;;` (`JOBS 31.`). nf-core fails the process (`SRC/modules/nf-core/fastqutils/info/main.nf:24-28`).
- **Single-end samples get no check.**
  - `fastqutils_info_single` is wired to `concat_r1`/`concat_r2`, the paired reads, exactly like the paired arm (`WF:1145-1174`). `JOBS 31.` and `32.` read identical files, and `merge_fastqutils` keep_first then drops the duplicates.
  - nf-core runs FASTQUTILS_INFO on `ch_reads_post_qc`, which includes the single-end `fastq_other` (`SRC/workflows/bamtofastq.nf:178,183`).
  - The step doc calls this a "structural approximation" (`WF:1170-1173`), and the ledger marks the related entry `resolved` (`RUN/open-requirements.ledger.yml:60-77`).

### 5. SILENT, rare: the chr filter runs before the pairedness check, though the doc says it matches [model]

- **nf-core** classifies the unfiltered input (`SRC/workflows/bamtofastq.nf:85`) and applies SAMTOOLS_CHR afterwards (`:119-121`).
- **Galaxy** feeds `pairedness_split` from `pick_input_collection`, which is the chr-filtered BAM when `chr` is set (`WF:482`, `331-334`).
- **The doc is wrong.** It says the order is "before the pairedness split, matching source order" (`WF:9-10`). This is the same divergence as in the Claude run, but here it is presented as matching.
- **Unverified risk: an unset `chr`.**
  - The gate is `when: $(inputs.when != "")` (`WF:271`). nf-core's default is `chr = null` (`SRC/nextflow.config:16`).
  - The test passes `chr: ""` explicitly (`T:46`), so a null was never tried.
  - If Galaxy passes null for an unset optional text input, `null != ""` is true. The step then runs with `regions` unset, and `regions` is a non-optional text parameter (`samtools_view.xml:285`).
- **Untested.** `samtools_chr_view` was skipped in every run (`JOBS 8.`: 2 × skipped).

### 6. Collate settings are inert, and read order is the name-sort order [model]

- **The collate settings have no effect.**
  - `samtools_collate_fast` and `reads_in_memory` are workflow inputs that feed no step (`WF:55-63`; acknowledged in `RUN/orchestrator-questions-answers.md`, with no ledger entry).
  - The stated reason is that `-f` without `-r` "would DROP secondary/supplementary records", while nf-core's fast mode keeps them. That is not what nf-core does: with `-f`, collate outputs only primary READ1/READ2 records regardless of `-r` (`samtools_collate.xml:21` help text). Per the samtools documentation (not checked in a file here), `-r` only sets how many reads are held in memory.
  - Wiring `fast_mode` would have matched nf-core's filtering.
- **The collate steps change nothing.** `samtools_fastx` name-sorts any input that is not typed `qname_sorted.bam` (`samtools_fastx.xml:12-14`). The executed command starts with `samtools sort … -n` (`JOBS 25.`), so the collate output is re-sorted.
- **Read order differs from nf-core.** nf-core pipes `collate -O | fastq` (`SRC/modules/nf-core/samtools/collatefastq/main.nf:36-50`), so its FASTQ follows collate order, not name-sort order. I did not measure this.

### 7. CRAM: declared but not supported, and the ledger claim is missing [model; Foundry]

- **The samtools steps get no reference.** The sample sheet accepts `cram` (`WF:34-36`), but every shed samtools step has `addref_select: "no"` (`WF:187-189, 273-275, 524-526, …`). nf-core passes the reference to view, stats, merge and collatefastq.
- **CRAM content is relabelled as BAM.** `pairedness_split` declares both output collections as `format: bam`, even for CRAM content (`WF:413-430`, acknowledged in `WF:384-387`). Downstream steps would then treat CRAM bytes as BAM.
- **Missing ledger entries.**
  - The chr view's doc says "CRAM inputs + chr restriction would need the reference (ledger entry added)" (`WF:320-321`). No such entry exists: grep for `cram` in `RUN/open-requirements.ledger.yml` finds nothing.
  - The collate_fast deviation is also missing from the ledger.
- **Positive.** FastQC before conversion is limited to BAM rows by `filter_bam_rows` (`WF:91-120`), matching `SRC/subworkflows/local/pre_conversion_qc/main.nf:26-40`. The Claude run did not do this.

### 8. Outputs and MultiQC [model]

**Missing.** The chr-extracted BAM is not a workflow output. SAMTOOLS_CHR falls under the default `publishDir` (`SRC/conf/modules.config:15-18, 161-165`). This is the same gap as in the Claude run.

**Added content.** MultiQC is fed samtools stats/flagstat/idxstats and the pre-conversion FastQC text (`WF:1273-1276`). In 2.2.1, MultiQC receives only versions, the params summary and the methods description (`SRC/workflows/bamtofastq.nf:171-172, 217-225`). The report therefore contains sections nf-core's does not. That is harmless, but it is not a translation.
- `merge_fastqc_pre` merges a collection with itself to satisfy the two-input minimum (`WF:1239-1263`), and it has no `tool_version`.
- I did not check whether MultiQC is skipped when `no_stats` or `no_read_QC` gates off its inputs. nf-core always runs MultiQC.

**Dropped parameters.**
- `multiqc_title` is not exposed (title fixed to `""`, `WF:1285`). nf-core passes `--title` when it is set (`SRC/conf/modules.config:32`). The interface brief calls it "safe, cosmetic" (`RUN/nextflow-galaxy-interface.md:32`).
- `multiqc_config` is dropped (`:33`).

**Substitutions.** These match the Claude run:
- The FastQC zip becomes the FastQC text output.
- The `<id>.<chr>` rename is dropped.

### 9. Tests: strength against the nf-core snapshot

| Output | Assertion | Against nf-core |
|---|---|---|
| flagstat ×2, idxstats ×2 | exact md5 (`T:73-90`) | equals `snapshot:105,106,108,109`: **strong** |
| stats ×2 | 2 SN `has_line` each (`T:91-103`) | values correct, but taken from the run, not the snapshot. Dropping the md5 is justified (the header embeds version and command) |
| merged_reads ×4 | `has_n_lines`, decompressed (`T:52-72`) | **contradicts nf-core** for `test` (11280 vs 11284). Encodes issue 1 |
| fastqutils ×2 | 4 `has_line` each (`T:104-120`) | measured on the defective output (2820). The snapshot md5s are of nf-core's echo sentence (Claude review), so no content parity is possible |
| unmapped_other_reads | `element_count: 0`, `element_tests: {}` (`T:121-125`) | **no-op**: planemo's bundled galaxy-tool-util 26.1.2 checks `if output_collection_def.count and …` (`…/site-packages/galaxy/tool_util/verify/interactor.py:1534`), so a count of 0 is never enforced |
| FastQC pre html | count + `has_size min 1000` | weak; nf-core `.nftignore` ignores FastQC content too (`SRC/tests/.nftignore:3`) |
| FastQC text ×2 collections, post html | count only | weak |
| multiqc_report | `has_size min 1000` | weak (smoke) |

**Coverage.**
- Only `default.nf.test` was translated.
- The single-end branch, chr, CRAM, collate_fast and the skip toggles were never executed. `collate_single` and `fastq_single` had 0 jobs (`JOBS 21.`, `24.`), and `chr_view` was skipped.
- The ledger notes that `no_bai` has a single-end sample (`RUN/open-requirements.ledger.yml:129-135`), but it was not translated.

### 10. Parameters: state against nf-core, step by step

The "Galaxy executed" column is the command line in `JOBS`.

| Step | nf-core | Galaxy executed | Match |
|---|---|---|---|
| samtools_flagstat / idxstats / stats | no args; when `!no_stats` (`modules.config:75-100`) | no args; `when: $(inputs.when == false)` on `no_stats` | yes. stats without `--reference` matters only for CRAM (issue 7) |
| fastqc_pre / fastqc_post | `--quiet`; when `!no_read_QC` (`:20-30`) | `--quiet --extract --kmers 7 -f bam\|fastq` (7 is the default) | yes. Post runs per mate file instead of one job per sample (names differ only) |
| view map_map / unmap_unmap / unmap_map / map_unmap | `-b -f1 -F12`, `-b -f12 -F256`, `-b -f4 -F264`, `-b -f8 -F260` (`:68,131,123,115`) | `-b -f 1 -F 12 -G 0`, `-f 12 -F 256`, `-f 4 -F 264`, `-f 8 -F 260` | **yes** |
| samtools_chr_view | `-hb` plus `params.chr` regions (`:161-165`) | `-b` plus regions split on whitespace (template only; skipped) | yes for BAM; gate risk (issue 5) |
| merge_unmap | per sample `[uu, um, mu]`, no args (`alignment_to_fastq/main.nf:35-54`) | 1 cross-sample job, `-s 1 -f out 0.sam 1.sam` (uu only) | **no** (issue 1) |
| collate ×3 | args `-f -r N` if `samtools_collate_fast` (`:40,50,59`) | `collate … --output-fmt BAM`, always standard | default case yes; fast mode ignored (issue 6) |
| fastx (fastq) ×3 | args2 `-N`; implicit `-F 0x900` | `-N … -f 0 -F 0 -G 0` after `sort -n` | **no** for secondary/supplementary records (issue 3) |
| cat R1 / R2 | `cat m1 u1`, `cat m2 u2` | `cat m1`, `cat m2` | **no** (issue 1) |
| fastq_info paired | `fastq_info r1 r2`; fails on error | same files; exit 1/3 treated as success | semantics differ (issue 4) |
| fastq_info single | `fastq_info other` | runs on the paired files | **no** (issue 4) |
| multiqc | `--title` if set; versions/params/methods only | 4 report sections, title `""` | divergent (issue 8) |
| filter_bam_rows (`__APPLY_RULES__`) | `branch { filetype == 'bam' }` before FastQC (`pre_conversion_qc/main.nf:26-40`) | 1 job, keeps rows with `file_type == bam`, ids from `sample_id` (`WF:91-120`) | yes |
| pick_input_collection (pick_value) | `if (params.chr)` swaps the channel (`bamtofastq.nf:119-144`) | 2 element-wise jobs, `first` of [chr-filtered, raw] (`WF:322-356`); raw was picked (chr unset) | yes for chr unset; chr set never run |
| merge_unmapped_variants (`__MERGE_COLLECTION__`) | per-sample join, `remainder: true` | `keep_first` over 3 lists with the same ids, so only `uu` is kept | **no** (issue 1) |
| merge_mered_reads (`__MERGE_COLLECTION__`) | publishes `<id>_1/_2.merged.fastq.gz` | `suffix_every` `_#` gives `test_1`, `test_2` (`WF:1202-1238`) | yes (names) |
| merge_reads_post_qc (`__MERGE_COLLECTION__`) | `mix(fastq_other, CAT_FASTQ.reads)` (`bamtofastq.nf:178`) | `keep_first` over merged and single ids, which cannot collide | yes |
| merge_fastqutils (`__MERGE_COLLECTION__`) | one report per sample | `keep_first` over two arms with identical inputs | output right for all-paired runs only (issue 4) |
| merge_fastqc_pre (`__MERGE_COLLECTION__`) | none (MultiQC gets no FastQC in 2.2.1) | the same collection twice, no `tool_version` | not a source unit (issue 8) |
| pairedness_split (UDT) | CHECKPAIREDEND: first 1000 records, `-f 1` fraction = 1 (`checkpairedend/main.nf:26-36`) | same logic via awk on `$2%2==1`, `set -euo pipefail` (`WF:432-480`) | **yes**. `--reference` is passed for BAM too (inert), and the whole file is counted once (performance only) |

**The 14 parameters left unset after the revision.** These are the optional data inputs reported as `RuntimeValue`. nf-core feeds none of them (`RUN/revision-report.md`).

The revision's additions all equal the defaults Galaxy substitutes and do not change the executed commands:
- FastQC `kmers`/`min_length`
- fastq_info `q`/`r`
- merge `region`
- MultiQC `comment`/`title`

### 11. Checked and matching nf-core

- **Inputs.** The `sample_sheet` with `sample_id`/`file_type` matches the samplesheet. The `index` column is dropped, because Galaxy's bam metadata index is used: `JOBS 10.`, `11.` and `17.`–`20.` link `infile.bai` from metadata.
  - `fasta` is optional.
  - `no_read_QC`, `no_stats`, `samtools_collate_fast` and `reads_in_memory` have the source defaults (`SRC/nextflow.config:16-20`); the last two are inert, see issue 6.
- **Pre-conversion QC.** It runs on all rows, with FastQC limited to BAM, as nf-core does.
- **The pairedness split.** It routes per element and keeps the identifiers, which come from `element_identifier` since UDT v1.0.13. Empty branches map over empty lists without error (`JOBS 21.`, `24.`: 0 jobs).
- **Mapped path to R1/R2.** `fastq_mapped` produces per-sample R1/R2 with `-N`. `merge_mered_reads` with `suffix_every`/`_#` produces `test_1/test_2`, matching the snapshot names (`WF:1202-1238`).
- **Post-conversion FastQC input.** `merge_reads_post_qc` mixes the paired and single arms, as `bamtofastq.nf:178` does.

### 12. Records

**`open-requirements.ledger.yml`:**
- One open entry: `multiqc-runner-boilerplate-dropped`.
- No entries for issues 1, 3, 5, 6 or 7, or for the missing chr BAM.
- The `fastqutils-per-sample-invocation` entry is marked resolved, although its single arm is miswired.

**`galaxy-workflow-validation-result.json`** lists 5 residual risks. None covers the unmapped arm.

**Not in any run artifact** (new in this review): issues 1, 2 (the counts contradict nf-core), 3, the miswired single-end fastq_info, the inert collate steps, and the missing CRAM ledger entry.

## Not checked

- I ran nothing. Issues 3, 5 (the null `chr`) and 7, and MultiQC under the skip toggles, come from reading code. Issues 1, 2 and 4 come from executed job records and line counts.
- I did not measure the FASTQ read order against nf-core (issue 6).
- I did not verify samtools fastq's behaviour on supplementary records beyond its documented `-F 0x900` default.
- I did not compare the wrapper XML with the pinned Tool Shed changesets.
- I did not read the feedback ledger (`RUN/foundry-feedback.ledger.yml`) in full.
