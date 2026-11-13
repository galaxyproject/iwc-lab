# Foundry run review: nf-core/demo → Galaxy (Claude baseline)

| | |
|---|---|
| Model | Claude Opus 5.5 (`claude-opus-5-5`) |
| Harness | Claude Code CLI, `pipeline-nextflow-to-galaxy` (assembly revision 5), invoked as `--feedback nf-core-demo`, run inline (no `--use-subagents`, no `--checkpoint`) |
| Foundry skills | `foundry-skills` 0.2.0 (plugin cache; not a git checkout, so `foundry_head: null`). CLIs: `@galaxy-foundry/gxwf-foundry` and `@galaxy-tool-util/cli` (^1.15.0) from npm; planemo 0.75.48 (the harness pins 0.75.47) |
| Source pipeline | nf-core/demo 1.2.0+5, commit `671a0726cb489b22636d90b7c7352baed473790d` (the Nextflow-managed clone under `~/.nextflow/assets`) |
| Phases completed | 13/13, all `done` and `feedback_checked` (`foundry-run.yml`, `foundry-feedback.ledger.yml`) |
| Planemo attempts | 2. Attempt 1 failed (2 assertion problems; `planemo-run/planemo.log:8128`). Attempt 2 passed (`planemo-run2/planemo.log:4696`) |
| Wall time | 27 min 45 s (`foundry-run.yml` `started_at` 2026-11-06T12:44:00+01:00 → `finished_at` 13:11:45). Planemo attempt 1: 12:58:03 → 13:05:35 log span (test 12:59:14 → 13:05:28). Attempt 2: 13:08:09 → 13:11:28 (test 13:09:04 → 13:11:20) |
| Galaxy | Planemo-managed, using the existing local checkout `~/Galaxy/galaxy-arash` (dev @ `eaa885328b8`, chosen by the user's planemo config), `--biocontainers` |
| Revision round | **Yes, one, after phase 13 and outside the harness.** I applied debug's two fixes (`workflow-debug-report.md:32`), re-extracted, re-validated and re-ran planemo. The harness has no phase for this. |

Overall the run went smoothly. Every phase produced a schema-valid artifact. The workflow imported and ran all jobs on the first attempt: 14/14 ok, including the embedded GalaxyUserTool, map-over of `list:paired_or_unpaired` and the `when:`-gated step. The seqtk output content matches the nf-test snapshot md5 exactly. The one real workflow defect came from my own design call (model mistake M1 below). The rest is tooling friction.

## Issues found in or caused by Foundry and the tools

### 1. `foundry summarize-nextflow` fails its own schema check on a Nextflow-managed clone (Foundry)
- **Evidence:** run on `~/.nextflow/assets/.repos/nf-core/demo/clones/<sha>`, it exited 1 with `/source/url: must match format "uri"` and wrote no file. `git remote get-url origin` there is a local bare-repo path. Worked around with `--no-validate`, then a manual `source.url` rewrite to `https://github.com/nf-core/demo`, then `validate-summary-nextflow` → valid (`summary-nextflow.json:5643`). Ledger: `foundry-feedback.ledger.yml:20`.
- **Change:** when the remote is not a URI, fall back to `manifest.homePage` (or omit the remote) instead of failing validation. This clone is exactly what a user has right after `nextflow run nf-core/<x>`.

### 2. Edge extraction splits a multi-line call argument into fake edges (Foundry)
- **Evidence:** `MULTIQC(ch_multiqc_files.flatten().collect().map { files -> [ … ] })` in `workflows/demo.nf` produced 12 edges with `from` values `[`, `]`, `}`, `[]` and `? file(...)`. The real `FASTQC.out.zip → MULTIQC` edge was missing. I replaced `workflow.edges` by hand (`summary-nextflow.json:5643`). Ledger `:33`.
- **Change:** parse the balanced argument expression as one edge source with its operators in `via`, or at least flag low confidence instead of emitting line fragments.

### 3. CLI `--profile` defaults to `test`, but the Mold says there is no silent default (Foundry)
- **Evidence:** the `foundry summarize-nextflow --help` text vs `summarize-nextflow/SKILL.md:66`. Ledger `:45`. It made no difference here, because the only candidate was `test`.
- **Change:** default to none, or document why the CLI deviates.

### 4. Snapshot-translation note says nothing about how nf-test computes md5 for `.gz` (Foundry)
- **Evidence:** the nf-test token for `SAMPLE1_PE_sample1_R1.fastq.gz` (`7dd2fd…`) is the md5 of the *decompressed* content; the md5 of the raw file is `a1af53…`. The packaged `nextflow-snapshot-to-galaxy-assertions.md` has no mention of gz or decompress. This led straight to planemo failure 1 (see #5). Ledger `:68`.
- **Change:** state the semantics and prescribe the Galaxy equivalent: `compare: diff` + `decompress: true` against an expected file, or content asserts with `decompress`, never `checksum`.

### 5. Galaxy ignores `decompress` for `checksum`, and the static validators accept the combination (Galaxy, gxwf)
- **Evidence:** `lib/galaxy/tool_util/verify/__init__.py:146` calls `_verify_checksum(output_content, …)` (`:275-280`) on the raw bytes. `decompress` applies only to asserts (`:123`) and to `files_diff`. Both `gxwf validate-tests` and `foundry validate-tests-format` passed the test file. Planemo attempt 1 then failed: `Output checksum [df27878f…] does not match expected [7dd2fd…]`. The same seqtk 1.4 container reproduces `7dd2fd…` on the decompressed output, so the data was right. Ledger `:119`.
- **Change:** Galaxy should honour `decompress` for `checksum` or reject the combination. Until it does, gxwf should warn on it.

### 6. Embedded GalaxyUserTool under planemo: no documented recipe (Foundry, planemo)
- **Evidence:** `galaxy-user-tool-workflow-binding.md:89-91` leaves this open. `planemo test` has no flag for `enable_beta_tool_formats`. Setting `GALAXY_CONFIG_OVERRIDE_ENABLE_BETA_TOOL_FORMATS=true` worked on the first try, and no role setup was needed for planemo's bootstrap user. The cowpy job was `ok` in both attempts. Ledger `:94`.
- **Change:** record that recipe in the binding note, and have run-workflow-test apply it whenever a step embeds `run: GalaxyUserTool`.

### 7. Phase 10 and phase 12 both require a planemo run (Foundry, pipeline)
- **Evidence:** `implement-galaxy-workflow-test/SKILL.md:76` requires a green planemo run, and step 1 prefers bootstrapping from an invocation, but phase 12 runs the tests anyway. I deferred phase 10's run to phase 12. Ledger `:81`.
- **Change:** let phase 10 hand off statically valid tests, or let phase 12 skip the run when phase 10 already ran green.

### 8. No home for a revision round after debug (Foundry, pipeline)
- **Evidence:** phase 13 only triages and recommends. Turning the red run green took a topology repair and a test edit after the harness ended (`workflow-debug-report.md:32`). That round is not visible in `foundry-run.yml`'s phase roster. *(Not in the ledger; observed while writing this review.)*
- **Change:** add an optional repair-and-rerun loop after debug, bounded like the draft loop, or say explicitly that the run ends red.

### 9. Fixed artifact basenames collide inside the loop phase (Foundry, harness)
- **Evidence:** phase 7 writes `galaxy-tool-pin.json`, `galaxy-tool-summary.json` and `galaxy-user-tool.yml` once per step, under fixed basenames. The harness prefixes the run directory but says nothing about per-iteration names. I improvised `steps/<step>/…` (recorded in `foundry-run.yml` phase 7 artifacts). *(Not in the ledger.)*
- **Change:** specify per-iteration namespacing for loop-phase artifacts.

### 10. Minor items (Foundry, planemo)
- `galaxy-tool-discovery` `ToolCandidate` requires `score`, `matched_terms` and `match_fields` even for a confirmed identity pin with no search (multiqc), so I wrote `score: 0.0` (ledger `:56`).
- Planemo's `test-output.json` had empty `invocation_details.details`, so no invocation, history or workflow ids reached the debug phase (`workflow-test-result.json`; ledger `:107`).
- The Foundry CLIs are not preinstalled. The bootstrap `npm install -g` worked, but as a side effect it triggered a `mise` prune of an unrelated tool version on this machine.

## My own (model) mistakes

- **M1, design (caused planemo failure 2).** I mapped FastQC directly over the nested `list:paired_or_unpaired`. The wrapper names reports by the leaf identifier (`rgFastQC.xml:16`: `$input_file.element_identifier`), so MultiQC merged 6 reports into 3 rows (`Expected 7+-0 lines … found 4`). My own IWC comparison had surfaced the `__FLATTEN__` idiom, yet I wrote "Prefer direct map-over" (`iwc-comparison-notes.md:20`) without checking how the wrapper names its output. Fixed in the revision round by adding `flatten_reads` before `fastqc`.
- **M2, tests (caused planemo failure 1).** I used `checksum` + `decompress: true` on gz outputs, assuming `decompress` applied to it. I had even listed this as a residual risk (`galaxy-workflow-validation-result.json:14`) and did not check the Galaxy source before spending a planemo run on it.
- **M3, procedure.** In phase 7 I ran discovery for fastqc, seqtk and multiqc in a single iteration, while the orchestrator's contract is one step per invocation. Implementation still went one step per iteration.
- **M4, small validation slips, each caught by a validator on the first retry:**
  - The discovery pin `warnings` were strings instead of objects.
  - The FastQC `state` included `null` for unconnected data inputs (`contaminants: Expected never, actual null`).
  - Collection outputs in the test file lacked `class: Collection`.
  - I passed `gxwf convert -o` instead of `--output`.
- **M5, scope wording.** The interface brief raised `cowpy-galaxy-tool-unknown` as a gap. The data-flow procedure says tool-availability judgements belong to the draft loop, so this was premature. It was harmless: the loop resolved it with a UDT.
- **Unverified, not investigated:** the pinned FastQC changeset is `2c64fded1286`, but planemo installed `~/Galaxy/galaxy-arash/database/shed_tools/…/devteam/fastqc/e7b2202befea/`. I did not check whether the Tool Shed maps one to the other.
