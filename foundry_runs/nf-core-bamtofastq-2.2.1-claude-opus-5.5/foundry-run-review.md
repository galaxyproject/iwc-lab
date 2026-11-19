# Foundry run review — nf-core/bamtofastq → Galaxy (nf-core-bamtofastq-claude)

| | |
|---|---|
| Model | Claude Opus 5.5 (`claude-opus-5-5`) |
| Harness | Claude Code; `/foundry-skills:pipeline-nextflow-to-galaxy --feedback nf-core-bamtofastq-claude`. The Ponytail output-style add-on and an advisor (reviewer-model) tool were active; the advisor was called 3 times in total. |
| Foundry skills | plugin `foundry-skills` 0.2.0; CLIs `@galaxy-tool-util/cli` 1.15.0 (`gxwf`, `galaxy-tool-cache`), `@galaxy-foundry/gxwf-foundry` (`foundry`), planemo 0.75.48 |
| Pipeline | `nextflow-to-galaxy` revision 5 (`foundry-run.yml`: `harness_name: pipeline-nextflow-to-galaxy`, `source_revision: 5`, `foundry_head: null`) |
| Source | nf-core/bamtofastq 2.2.1 (8a29586) |
| Phases completed | 13 of 13 (`foundry-run.yml` status `complete`). The revision round used the update-pipeline Molds (see below). |
| Planemo test attempts | 3. Phase 10: 1 of 8 outputs failed on test format. Phase 12: **pass**. Revision: **pass**. The revision's `planemo serve` editor check was lost to a session end. |
| Wall time (measured with `date`) | Original run 09:19:24–10:25:57 on 2026-11-10 (66 min 33 s). Revision 17:57:05 to about 18:08 on 2026-11-10: the session ended, and the last real timestamps are serve start 18:05:30 and Galaxy shutdown 18:08:34 in serve.log. Then 09:30:10–09:37:30 on 2026-11-11. |
| Result | Workflow with 28 steps (2 embedded user-defined tools), 7 inputs, 13 outputs. Final planemo result 1/1 pass, jobs ok 44 / skipped 2. |

Issue owners: **Foundry** (skills, notes, schemas or `foundry` validators), **gxwf** (galaxy-tool-util CLI, counted with Foundry tooling), **Galaxy**, **gxformat2**, **planemo**, **model** (my own mistakes). Full entries are in `foundry-feedback.ledger.yml` (15, none filed).

## Issues found during the run

### 1. Gzipped nf-test snapshot md5s translated to raw checksums can never pass. Owner: Foundry (note). Severity: major.
- **What:** `nextflow-snapshot-to-galaxy-assertions` (§1a/§6) says to translate `<file>:md5,<hex>` to `checksum: md5$<hex>`. For `*.gz`, nf-test hashes the *decompressed* content, while Galaxy's `galaxy.tool_util.verify._verify_checksum` hashes the stored bytes and ignores `decompress`.
- **Evidence:** the 4 `reads/*.merged.fastq.gz` tokens equal `zcat | md5sum` of an nf-core-container regeneration (`test-data/expected/decompressed-md5.txt`, `regenerate-with-nfcore-container.sh`); the raw-byte md5s differ. Ledger: `snapshot-gz-md5-is-over-decompressed-content`.
- **What I did:** a decompressed `file` compare against expected files regenerated with the nf-core container and commands, not taken from the Galaxy run.
- **Foundry should:** state that gz tokens are content md5s and prescribe a decompressed compare or content asserts, never a raw `checksum`.

### 2. `ext.when` gating is invisible to summarize-nextflow. Owner: Foundry (Mold + CLI). Severity: major.
- **What:** `--no_read_QC` and `--no_stats`, two of the pipeline's nf-test cases, exist only as `ext.when = { !params.X }` in `conf/modules.config`. The deterministic summary had one conditional (`params.chr`).
- **What I did:** added the two conditionals by hand in the LLM pass (`summary-nextflow.json`). Ledger: `summarize-nextflow-ext-when-gating-not-captured`.
- **Foundry should:** read `withName … ext.when` closures and emit `conditionals[]`.

### 3. The tool summary has no command template. Owner: Foundry / gxwf. Severity: major.
- **What:** the summary's `parsed_tool` has no command block and `raw_tool_source_path` was null. Whether iuc `samtools_fastx` 1.22+galaxy2 collates or name-sorts decided read order and md5 equality, and it was only answerable from the wrapper XML on GitHub. It runs `samtools sort -n`, while nf-core uses `samtools collate -O`.
- **What I did:** this led to a fall-through to an authored user-defined tool (`steps/samtools_collatefastq/galaxy-user-tool.yml`). Ledger: `tool-summary-omits-command-template`.
- **Foundry should:** include the command (or a source path) in the summary, or tell the agent when it must fetch the wrapper source.

### 4. summarize-nextflow edge extractor emits token fragments. Owner: Foundry (CLI). Severity: minor.
- **What:** 14 of 33 edges had `from` values such as `[[:]`, `[]]`, `]`, `}`, which came from multi-line call arguments like `SAMTOOLS_CHR(ch_input_new, ch_fasta_fai, [[:], []], [[:], []], [])`. No edges internal to local subworkflows were emitted.
- **What I did:** the LLM pass rebuilt the edge list. Ledger: `summarize-nextflow-cli-edge-tokenizer-fragments`.

### 5. Reference-data detection misses `params.fasta ?: getGenomeAttribute(...)` and the branch-on-meta fai rebuild. Owner: Foundry (CLI). Severity: minor.
- Ledger: `summarize-nextflow-misses-elvis-getgenomeattribute-and-branch-rebuild`.

### 6. There is no recipe for a per-element runtime `branch`. Owner: Foundry (note). Severity: minor.
- **What:** `nextflow-operators-to-galaxy-collection-recipes` lists the per-element branch pattern as a TODO. `ch_input_new.branch { single_end }` after CHECKPAIREDEND needed an invented chain: classifier UDT → `collapse_dataset` → `Filter1` → `Cut1` → `__FILTER_FROM_FILE__`. That chain worked.
- Ledger: `per-element-branch-has-no-recipe`.
- **Foundry should:** add this recipe, including its plumbing cost.

### 7. Template pattern index links to pages that aren't bundled. Owner: Foundry (packaging). Severity: minor.
- **What:** `[[conditional-transform-or-pass-through]]` (when + pick_value) isn't packaged in the template skill, and there's no gxformat2 snippet for native `type: pick_value` versus the iuc `pick_value` tool.
- **What I did:** chose the iuc tool from IWC precedent. Ledger: `template-pattern-index-links-unbundled-pages`.

### 8. Collection output test without `element_tests` passes static gates and fails in planemo. Owners: planemo, Galaxy, Foundry / gxwf.
- **What:** `{class: Collection, element_count: 0}` for `single_end_reads` passed `gxwf validate-tests` and `foundry validate-tests-format`. Then phase-10 planemo failed with `No path specified for expected output file [single_end_reads]` (`planemo/phase10/planemo.log:8259`).
- **Planemo:** `for_collections()` keys on `element_tests`, not `class`.
- **Galaxy:** verify skips the count check when it is 0 (`if output_collection_def.count and …`), so an empty-collection assertion cannot be expressed.
- **Cost:** one 10 min 43 s planemo run.
- **What I did:** made it existence-only (`element_tests: {}`) and logged it as weak.
- Ledger: `planemo-collection-output-needs-element-tests`, `validate-tests-misses-collection-without-element-tests`.

### 9. `--strict-state` is green while Galaxy disagrees, twice. Owner: gxwf / Foundry (and Galaxy for messaging).
- **(a) Runtime:** Galaxy dev's ToolRequest capture logged `request state=validation_failed` for 14 of 28 steps (8 distinct tools) in phase 12, and again for the same 8 tools in the revision run (`planemo/revision/planemo.log`). Galaxy documents it as execution-neutral, and the jobs ran.
- **(b) Editor:** on import, Galaxy's editor reported 59 parameters missing from step `state` (`orchestrator-findings-2026-11-10.md`), while `draft-validate --concrete --strict-state` and `gxwf validate --strict --connections` reported 28/28 ok. `implement-galaxy-tool-step` doesn't say whether step state should carry tool defaults explicitly.
- Ledger: `strict-state-ok-but-galaxy-request-validation-failed`, `revision-strict-state-ok-but-galaxy-editor-reports-missing-state`.
- **Foundry / gxwf should:** have a completeness check that mirrors Galaxy's `upgrade_messages`, plus a rule in implement-galaxy-tool-step.

### 10. The packaged CLI sidecar for `gxwf convert` gives no output-flag example. Owner: Foundry. Severity: minor (friction).
- **What:** `gxwf convert -o` fails (`error: unknown option '-o'`); only `--output` exists. In the revision, `gxwf draft-next-step --json` likewise failed, because that command has no `--json` option.
- Ledger: `compare-iwc-convert-flag-mismatch`.

### 11. Per-step artifact basenames collide in the loop. Owner: Foundry (harness). Severity: minor.
- **What:** `galaxy-tool-pin.json` and `galaxy-tool-summary.json` are fixed names, so each loop iteration overwrites the last.
- **What I did:** kept them under `steps/<tool>/` by hand. Ledger: `per-step-artifact-basenames-collide-in-loop`.

### 12. Datatype mismatch passed the loop's prescribed gate. Owners: model (mine) and Foundry / gxwf (gate).
- **What:** the CHECKPAIREDEND UDT output was `txt`. It feeds `collapse_dataset`, which inherits format, and then `Filter1`, which accepts tabular only.
- All 21 iterations of `draft-validate --concrete --strict-state` passed. The loop command doesn't include `--connections`. The advisor review caught the mismatch after phase 7, and I fixed it to `tabular` before any run.
- I did not test whether `--connections` would have flagged it through format inheritance, so whether the gate is enough is unverified.
- **Foundry should:** consider `--connections` in the loop gate.

### 13. Model mistakes (mine)
- My phase-7 helper left a stale `TODO_output` consumer reference after iteration 1. I fixed it by adding consumer rewiring.
- Helper-script bugs: a truncated `loop.sh`, and `$k_1` in the docker simulation.
- One `rm -rf $W/*` was blocked by the safety check, and nothing was deleted.
- The log needed corrections after the run: phase-6 tier counts, the wrapper count, the fastq_info line and the advisor-call count.

### 14. Upstream nf-core snapshot is not a usable expected value for fastq_info. Owner: nf-core (not Foundry). Noted for test quality.
- **What:** the `fastqutils/*.txt` md5 in `tests/default.nf.test.snap` is the md5 of an nf-core `echo` sentence, not tool output.
- **What I did:** weakened the test to `not_has_text ERROR`, logged as weak in `model-test-log.md` "Assertion strength".
- **Foundry could:** have the snapshot note warn that a snapshot md5 may not cover tool output.

## Feature gaps I recorded (workflow, not Foundry)

These are listed in `model-test-log.md` "Dropped / not carried":

- **CRAM:** effectively unsupported. Shed samtools view/stats steps get no reference, because the wrapper's reference conditional can't be driven by an optional workflow input (Galaxy/wrapper limitation). `fastqc_pre` would also receive CRAM elements.
- **Dropped:** MultiQC (versions-only in 2.2.1) and the `--chr` id rename.
- **Untested branches:** single-end, `chr`, `collate_fast`, both skip toggles, and CRAM. The skill consumes the one selected nf-test case, and 8 others were not translated.

## Revision round (2026-11-10 to 2026-11-11): what changed and why

- **Trigger:** Galaxy's "Issues loading this workflow" reported 59 parameters missing from `state` in 10 steps.
- **Method:** update-pipeline Molds, in order:
  - summarize-galaxy-workflow
  - interview-to-galaxy-workflow-changeset, with the findings file and nf-core source standing in for the interview
  - apply-galaxy-workflow-changeset
  - draft-next-step (`draft: false`) and draft-extract
  - changeset-to-galaxy-test-plan (baseline carried unchanged)
  - validate
  - planemo
- **Changed (43):** I wrote the value Galaxy already substitutes. That is `null` for empty optional integer, float, text and select parameters, and `false` for the `Using default: 'False'` booleans, across 5 samtools_view steps, stats, 3 FastQC steps and merge_unmapped.
  - **Why:** removes the editor noise with no command-line change.
  - nf-core 2.2.1 sets none of them: view uses `-b -f/-F` and `-hb`, stats and merge have no `ext.args`, and FastQC gets `--quiet`.
- **Left (16):** the "value set at runtime" optional dataset inputs: `qname_file` ×5, FastQC adapters/contaminants/limits ×3, merge `bed_file` and `headerbam`.
  - **Why:** nf-core feeds none of them (qname and bed are passed as `[[:],[]]`), and RuntimeValue is standard state.
- **Diff:** additions only, 48 lines and 0 removed, no position or frame change.
- **Checks:**
  - static: `draft-validate --concrete --strict-state`, `gxwf validate --strict --connections` 28/28 ok, validate-tests OK;
  - planemo: pass, ok 44 / skipped 2.
- **Not proven:** these gates were already green before, so the fix itself (editor shows only the 16) was not re-checked by me. My `planemo serve` check was lost when the session ended, and the coordinator will measure it.
- **New Foundry observations (3):**
  - item 9(b);
  - the summary schema has no slot for an embedded `run:` user-tool step (`summarize-galaxy-workflow-schema-has-no-embedded-user-tool-step`);
  - the change-set anchor rule can't address a parameter absent from state, and the update pipeline has no input slot for import or editor messages (`changeset-anchor-rule-excludes-absent-state-keys`).
- **Friction:** apply-galaxy-workflow-changeset wants a byte-preserving edit, but no tool does that; I inserted keys textually and checked that draft-extract is byte-identical.

## Compared with the orchestrator review

I wrote the sections above before reading `orchestrator-review-2026-11-10.md`. One caveat on independence: the revision task message had already named its four topics in one line (pipefail in the UDTs, fastq_info exit codes, chr filter order, CRAM). I did not count any of them as my own findings unless I had already logged them during the run, as I had for CRAM.

**It found and I didn't:**
- **UDTs lack `set -euo pipefail`** (its issue 1).
  - Galaxy adds only `set -e` to YAML tools, so a mid-pipe `samtools collate` failure yields a green job with an empty or truncated FASTQ; it demonstrated this with a truncated-BAM probe.
  - CHECKPAIREDEND runs with no `-e`.
  - I authored both UDTs without it (`steps/*/galaxy-user-tool.yml`), and nothing in Foundry's UDT guidance prompted me. Owners: model, plus Foundry (no porting rule).
- **fastq_info wrapper maps exit codes 1 and 3 to success** (its issue 2), so nf-core's fail-on-bad-FASTQ became a report-only signal. I weakened that test without noticing the semantics change. Owners: model, plus Foundry; same root cause as my item 3 (no command or stdio in the tool summary).
- **chr filter runs before CHECKPAIREDEND** (its issue 3). I noted it as an open question in `nextflow-galaxy-data-flow.md:77` but never ledgered it as a risk. Owner: model.
- **The chr-extracted BAM is not exposed as an output** (its issue 5). Owner: model.
- **Single-end fixtures already exist** in `no_bai.nf.test` and `chr.nf.test` (its issue 6). My log and debug report only said the default test has no single-end sample. Owners: model, plus Foundry (the skill consumes one selected case).
- **The tools-iuc `samtools_collate` wrapper exists**, and it would not have reproduced nf-core either (its issue 8). I did not record considering it. Owner: model.
- **Per-flag verification against executed command lines.** It verified all nf-core flags against planemo's recorded commands, and confirmed that none of the 59 defaulted parameters emits a flag.

**I found and it didn't** (or it only cited my ledger):
- Process-level Foundry defects seen while running:
  - the edge-tokenizer fragments (item 4);
  - the reference-data detection misses (item 5);
  - unbundled pattern pages (item 7);
  - the `gxwf convert -o` and `draft-next-step --json` flag friction (item 10);
  - per-step basename collisions (item 11);
  - the txt→tabular mismatch passing the loop gate (item 12).
- The revision-round observations:
  - the summary schema has no embedded user-tool step;
  - the change-set anchor rule can't address absent state keys;
  - strict-state is green against Galaxy's editor messages.
- The concrete planemo/Galaxy mechanics behind the empty-collection assertion (`for_collections()` keying on `element_tests`, verify skipping `count == 0`) and the 10 min 43 s run they cost. It cited only the ledger ids.
- The 59-parameter list:
  - it inferred `readtags` for samtools_view, but Galaxy's actual message names `seed` (`mode|subsample_config|subsampling_mode|seed`) and not `readtags`;
  - its merge trio inference was right.

**Both found:** CRAM is effectively unsupported (shed steps get no reference, FastQC-pre gets CRAM); MultiQC and FastQC-zip substitutions are justified; there is no command template in the tool summary; and the static/runtime gate disagreement (request-state `validation_failed`).
