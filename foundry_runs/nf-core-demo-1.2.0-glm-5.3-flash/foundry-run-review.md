# Foundry run review — nf-core-demo-glm

Written by the agent that executed the run, from its own experience. Evidence:
file:line, planemo attempt numbers, log files in this directory.

## Header

- **Model:** glm-5.3-flash-llmlb (GLM-5.3-flash via Freiburg LLM endpoint, claude-fr profile)
- **Harness:** Claude Code plugin `foundry-skills` 0.2.0 (mold casts dated 2026-11-06); CLI `@galaxy-foundry/gxwf-foundry` 0.4.0
- **Pipeline + version:** `pipeline-nextflow-to-galaxy` (harness `pipeline-nextflow-to-galaxy`, source_revision 5, assembly_sha256 d67b4ca0…)
- **Phases completed:** 13/13 (phase 13 as an explicit no-op triage)
- **Test attempts:** 10 planemo runs (attempts 1–2 pre-log, unlocked, aborted; 3 import rejected (frame colors); 4 staging AssertionError; 5 conda env corrupted + cowpy container; 6 FastQC green, cowpy still erroring; 7 all jobs OK, test moved to failure (output ids); 8–9 fix iterations; 9 PASS 2026-11-09 20:29:35; 10 re-confirmation PASS 20:40:20)
- **Wall time:** main run 2026-11-09 16:58:42 → 20:44:00 (~3h45m, real timestamps from foundry-run.yml; phase 1–9 timestamps in model-test-log.md were estimated and are flagged there); revision round 2026-11-10 16:50:05 → 17:36 (~46 min, real timestamps)

## What went wrong, in order of impact

### 1. UDT (GalaxyUserTool) execution requires container-enabled destinations — undocumented constraint chain (Foundry notes gap + Galaxy)
Attempts 5–7: the cowpy UDT's `container:` field IS its execution environment
(`tool_util_models/_models.py`: "every command used by shell_command must
already exist in it"); the UDT schema has NO package/conda requirement field
(adding `packages:` → 347 validate-tool-source errors), and the YAML parser
(tool_util/parser/yaml.py:196) reads only top-level `container`. So the job
runs only under a container-enabled destination — planemo needs `--docker`.
Nothing in the Foundry notes states this; it cost two attempts and a
source-reading session. **The author-galaxy-tool-wrapper / draft-format notes
should state: a UDT's shell_command runs inside its declared container only;
declare the container or the tool cannot run; planemo needs --docker for it.**
Classification: Foundry (note gap) + Galaxy (UDT model).

### 2. Nested `sample_sheet:paired_or_unpaired` staging requires collections at the nested rank (Galaxy + tests format)
Attempt 4: bare `File` elements at the subcollection rank crash planemo's
`to_elements` (galaxy/tool_util/cwl/util.py:335 AssertionError). Verified
against Galaxy source (types/paired_or_unpaired.py): a subcollection is
forward+reverse or a singleton with inner identifier `unpaired` — bare Files
are invalid. **The tests-format note should document how to author
paired_or_unpaired test fixtures (singleton-with-`unpaired` idiom).**
Classification: Galaxy (staging strictness) + Foundry (note gap).

### 3. Frame `color` accepts only named colors (gxformat2)
Attempt 3: import rejected hex `#D5E5F5`; pydantic WorkflowCommentModel
accepts only none/black/blue/turquoise/green/lime/orange/yellow/red/pink.
**draft-validate should flag non-named frame colors at authoring time.**
Classification: gxformat2 (validation gap).

### 4. Workflow-output test ids follow `label or id` — labels shadow ids silently (gxformat2)
Attempt 7→8: all jobs green but outputs "not found in results": gxformat2
`_wire_workflow_outputs` uses `label or id`, and my labeled outputs made the
test ids unmatchable. Fix: drop redundant labels. **The tests-format note
should warn that labels replace ids as test-facing names.** Classification:
gxformat2 (semantics) / Foundry (note gap).

### 5. A killed mid-install planemo run corrupts the conda env it was installing (planemo/process hygiene)
Attempt 5's FastQC `command not found` traced to a corrupted `__fastqc@0.12.1`
env — a rolled-back install from attempt 2 being killed mid-conda-install
(my own breakage; removed the env, recovered). **planemo could detect/repair
incomplete envs, or the notes should warn not to kill a running planemo
mid-install.** Classification: planemo + model (killed the process).

### 6. gxwf validate rejects `RuntimeValue` markers on optional data inputs in format2 (gxformat2 encoding asymmetry — surfaced in the revision round)
Same as the bamtofastq review item 7: native `.ga` (IWC corpus, 87/133
workflows) carries `{__class__: RuntimeValue}` for unconnected optional
datasets; gxwf's converter (stateful-convert.js:100-108) omits the marker
native→format2 and `gxwf validate` rejects it. Galaxy's import dialog then
renders the absent key as "RuntimeValue default", which reads as a defect and
triggered the revision round on an already-green workflow. Classification:
gxformat2/gxwf + Galaxy.

### 7. Shed tool install flakiness / transient log noise (Galaxy)
Attempt 3's tool install passed only on retry; every run logs benign noise
(submodule import-probe tracebacks, "Could not find lineage for tool
'CONVERTER_*'", sqlite "database is locked" ToolRequest warnings, transient
"Failed to use input connections for inputs [{when}]" ×6 with momentary
validation_failed states even on green runs — verified identical in the green
phase-10 log). Each cost diagnosis time. Classification: Galaxy (noise).

## Revision round (2026-11-10 16:50–17:36, real timestamps)

Task from biohackaton2026-8f: Galaxy's editor flagged FastQC and MultiQC
("Issues loading this workflow") — parameters absent from step `state`.
Checked against nf-core/demo source: no flagged parameter is set to a
non-default value (FASTQC ext.args = '--quiet' only). Changes (backup
galaxy-workflow.before-revision.gxwf.yml; no wiring/labels/position changes):
FastQC state += {kmers: 7, min_length: null}; MultiQC state += {comment: "",
export: false, flat: false, png_plots: false, title: ""}; optional data
inputs (adapters/contaminants/limits, image_content_input) left absent —
the canonical format2 unset (item 6). One encoding iteration: initial
RuntimeValue-marker pass caught by `gxwf validate --strict`, corrected to
absent keys. Validation (strict, connections, validate-tests) clean; planemo
PASS 17:32:41 exit 0 (the test ran twice under the lock due to a background
cwd mixup — both green; disclosed in revision-report.md). Full detail in
revision-report.md. No run-file defects introduced; both ledgers parse.

## Verdict summary

- Foundry (molds/notes): items 1, 2, 4 — UDT container constraints and
  paired_or_unpaired fixture authoring are the two gaps that cost the most
  attempts here.
- gxformat2: items 3, 4, 6.
- planemo: item 5 (env corruption on kill), plus general install flakiness.
- Galaxy: items 1, 2, 6, 7.
- Model: attempt 2 kill (env corruption), attempt 13-equivalent label/id
  mismatch (my authoring choice), background cwd mixup in the revision round.
