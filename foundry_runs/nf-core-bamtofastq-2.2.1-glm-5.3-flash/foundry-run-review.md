# Foundry run review — nf-core-bamtofastq-glm

Written by the agent that executed the run, from its own experience. Evidence:
file:line, planemo attempt numbers, log files in this directory.

## Header

- **Model:** glm-5.3-flash-llmlb (GLM-5.3-flash via Freiburg LLM endpoint, claude-fr profile)
- **Harness:** Claude Code plugin `foundry-skills` 0.2.0 (mold casts dated 2026-11-06); CLI `@galaxy-foundry/gxwf-foundry` 0.4.0
- **Pipeline + version:** `pipeline-nextflow-to-galaxy` (harness `pipeline-nextflow-to-galaxy`, source_revision 5, assembly_sha256 d67b4ca0…)
- **Phases completed:** 13/13 (phase 8 branch test-data-resolution included)
- **Test attempts:** 25 planemo runs (attempts 1–2 unrecorded pre-log; 3–21 job/staging-level fails, one at a time; 22–24 assertion-level fails; 25 PASS 2026-11-10 08:15:44)
- **Wall time:** main run 2026-11-09 23:27:18 → 2026-11-10 08:16:39 (~8h49m, real timestamps from foundry-run.yml); revision round 2026-11-10 16:50:05 → 17:50:20 (~1h, real timestamps via `date +%H:%M:%S`)

## What went wrong, in order of impact

### 1. gxformat2 has no runtime verdict-driven collection split (Foundry design surface / gxformat2)
The source's CHECKPAIREDEND → SPLIT_PAIRED_END routes each sample into a
paired or single-end arm based on a runtime verdict. Galaxy rules-DSL
predicates are static; the Foundry notes offer no pattern for a
verdict-driven between-samples split. Resolved by authoring a
GalaxyUserTool (`pairedness_split`) that collapses classify+route into one
job — ~13 of the 25 test attempts were spent hardening that UDT (attempts
8–18), none of them caused by a Foundry skill defect; the cost came from the
absence of guidance. **Foundry should add a draft-format / data-flow note for
verdict-driven sample routing** (collection-split-by-runtime-computation),
including the element_identifier-preserving output naming idiom (runtime.py
`_element_to_runtime`) and the empty-collection downstream tolerance.
Classification: Foundry (missing pattern).

### 2. UDT configfile templating: every `$(...)` is a JS expression; escaping rules undocumented (Foundry notes gap → gxformat2/Galaxy)
Attempts 10–13: bash parameter expansion inside a UDT configfile collided
with Galaxy's Cheetah/JS templating — `$(inputs.x)` is JS, `\$(` is a shell
escape, and the two layers eat each other (attempt 13 was my own edit error
de-escaping). `t13-udt-configfile-all-dollar-parens-are-js-expressions` and
`t13-udt-interpolated-values-wrap-in-shell-quotes` in foundry-feedback.ledger.yml
record the concrete rules. **The draft-format note should state the
templating layers explicitly (Cheetah → JS `$(...)` → shell) and which
escapes survive which layer.** Classification: Foundry (note gap) + Galaxy
(templating layers).

### 3. `samtools view` when-gate needs a boolean, not a truthy string (gxformat2)
Attempt 5: bare `$(inputs.when)` on a string input fails
`when_not_boolean` ("Type is: str"). Fixed with `$(inputs.when != "")`.
`t12-when-expression-must-produce-bool-not-string` records it. **The
draft-format note should document that `when:` must produce a JS boolean and
that truthy-string gates fail validation.** Classification: gxformat2
(validator-enforced semantics) / Foundry (undocumented).

### 4. `__MERGE_COLLECTION__` needs repeat instances in state (Foundry note gap)
Attempt 6: connections into repeat parameters do not populate repeat
instances at invocation time — `augment_tool_state_for_input_connections`
(lib/galaxy/workflow/modules.py:3077) only runs on the `recover_state` import
path, not `from_workflow_step`. The fix (full `inputs:` array with
`__class__: ConnectedValue` placeholders) exists in IWC exemplars but is
nowhere in the packaged notes (`t12-merge-collection-tool-state-needs-repeat-
instance-array`, severity major). **Add the repeat-instance authoring idiom
to the draft-format note.** Classification: Foundry (note gap) + gxformat2
(import-vs-invocation asymmetry).

### 5. Step output `rename:` is consumer-invisible (gxformat2)
After `out: [{id: X, rename: Y}]`, consumers must still reference `step/X`;
`step/Y` is an unknown port. Hit 5+ times (t7 entry). **The draft-format note
should state renames are display-only.** Classification: gxformat2.

### 6. gxwf draft-validate error dumps are unreadable (gxwf CLI)
A 4-step draft with 5 errors produced ~81KB of JSON-Schema type-signature
noise; the actionable message was buried. `draft-extract-output-path-flag-
undocumented-in-run-record` records a related CLI friction. **Summarize each
violation to path + expected-vs-actual; keep type dumps behind --verbose.**
Classification: gxwf (tooling).

### 7. gxwf validate rejects `RuntimeValue` markers on optional data inputs in format2 (gxformat2 encoding asymmetry — surfaced in the revision round)
Native `.ga` workflows (IWC corpus: 87/133 carry it) encode unconnected
optional datasets as `{__class__: RuntimeValue}` in tool_state; gxwf's
converter (stateful-convert.js:100-108) deliberately omits the marker
native→format2, and `gxwf validate` rejects it
("Expected never, actual {"__class__":"RuntimeValue"}"). Galaxy's import
dialog then renders the *absent* key as "RuntimeValue default", which reads
as a defect and triggered a whole revision round on an already-green
workflow. **gxwf validate should document the absent-key-is-canonical rule;
Galaxy's dialog should not list absent optional data keys as loading
issues.** Classification: gxformat2/gxwf + Galaxy (see feedback ledger entry
galaxy-editor-renders-absent-optional-data-key-as-runtimevalue-finding).

### 8. planemo output-side decompress default contradicts input-side (planemo)
Attempt 24: `has_n_lines` on a gz output counted raw gzip bytes — input-side
test data defaults `decompress: True` (planemo interactor.py:660) but
output-side `verify()` defaults `attributes.get("decompress", False)`
(planemo verify/__init__.py:102); `verify_assertions` decompresses only when
the element attribute is truthy (verify/asserts/__init__.py:47). Fix was
`decompress: true` per element test. **planemo should make the
input/output-side decompress defaults consistent.** Classification: planemo.

### 9. element_count-only collection outputs are undetectable as empty (planemo)
Count-only outputs (e.g. `unmapped_other_reads` element_count 0) fail
matching unless `element_tests: {}` is declared (planemo runnable.py:404
routing); the tests-format schema gives no way to say "expect empty".
`t12-empty-collection-map-over-is-silent-zero-jobs` (Galaxy side) and
`tests-format-element-count-only-collection-output-not-detectable` (Foundry
tests format) record it. **tests-format should support an explicit
empty-collection assertion.** Classification: Foundry (schema) + planemo.

### 10. Shed tool_ids require version suffixes for invocation (Foundry/validation gap)
Attempt 3: all 11 shed tools "not installed" with version-less ids. Fixed by
appending version segments. `t12-shed-tool-ids-require-version-suffix-for-
invocation`. **gxwf validate should flag version-less shed tool ids at
authoring time instead of failing at invocation.** Classification: Foundry
(validation gap).

### 11. Non-portable checksums: model chose md5 assertions on version-dependent outputs (model issue, caught by test rules)
Attempts 22–24: samtools stats headers embed version + command line; merged
gz md5 depends on the BGZF stream build; fastq_utils reports embed per-run
/tmp dataset UUID paths. The run's test rules required Foundry-skill-driven
snapshot→assertion translation; translating to has_n_lines/has_line with
derived counts fixed it. **Foundry's test-plan mold could warn when a
snapshot checksum targets output that embeds runtime paths or tool versions.**
Classification: model (initial choice) + Foundry (possible guardrail).

### 12. Non-blocking noise during every planemo run (Galaxy)
Import-probe Tracebacks from submodules.py, "Could not find lineage for
tool 'CONVERTER_*'", sqlite "database is locked" ToolRequest warnings, and
transient "Failed to use input connections for inputs [{when}]" warnings
appear on green runs too — each cost diagnosis time. Classification: Galaxy
(log noise).

## Revision round (2026-11-10 16:50–17:50, real timestamps)

Task from biohackaton2026-8f: Galaxy's editor flagged 16 steps ("Issues
loading this workflow") — all one class: parameters absent from step `state`;
import recovery fills defaults and lists each. Checked against nf-core/bamtofastq
source: no flagged parameter is set to a non-default value, so the fix was
representation only. Changes (backup galaxy-workflow.before-revision.gxwf.yml;
no wiring/labels/position changes): fastqc×2 += {kmers: 7, min_length: null,
nogroup: false}; pairedness_split += {lines_to_check: 1000}; multiqc +=
{comment: "", title: ""}; samtools_merge_unmapped += {region: null};
fastqutils_info×2 += {q: true, r: false}. Optional data inputs (adapters/
contaminants/limits, qname_file, bed_file/headerbam, image_content_input)
left absent from state — the canonical format2 unset (see item 7). One
encoding iteration: initial RuntimeValue-marker pass was caught by
`gxwf validate --strict` and corrected. Validation (strict, connections,
validate-tests) clean; planemo PASS (17:40:22, exit 0, attempt 1 of the
revision round). Full detail in revision-report.md.

One self-inflicted bookkeeping defect, disclosed: a scripted repair of a
pre-existing indentation malformation in foundry-feedback.ledger.yml damaged
its run/phases header; rebuilt with all 15 prior entries intact + head
restored (16 entries, parses). Also fixed a pre-existing YAML break in
open-requirements.ledger.yml line 50 (plain-scalar break; text preserved).
Neither touched workflow or tests.

## Verdict summary

- Foundry (molds/notes): items 1, 2, 4, 9, 10, 11 — the recurring cost was
  undocumented gxformat2 authoring idioms (repeat instances, renames,
  when-boolean, verdict-driven splits) discoverable only from IWC exemplars
  or Galaxy source.
- gxformat2: items 3, 4, 5, 7.
- gxwf tooling: items 6, 7.
- planemo: items 8, 9.
- Galaxy: items 2 (templating layers), 7 (import dialog), 12 (noise).
- Model: item 11 (initial checksum choices), attempt 13 (my own escaping edit).
