# Foundry issue drafts: nf-core/atacseq 2.1.2 → Galaxy (`atacseq-test`)

All drafts target `galaxyproject/foundry`. **Nothing here has been posted.** Each body begins
with the required attribution line. The run context below is shared by all of them and is
repeated in short form in each draft.

> Run: `/foundry-skills:pipeline-nextflow-to-galaxy --feedback`, Foundry skills 0.2.0, on
> nf-core/atacseq tag 2.1.2 (commit `1a1dbe5`). The scope was the core library spine (BWA only,
> per-library level). The test profile `test` passed on attempt 3 on test.galaxyproject.org
> (Galaxy 27.0.dev0). gxwf is `@galaxy-tool-util/cli` 1.15.x and planemo is 0.75.47. Checked
> against Foundry main `df991d0`.

---

## Comment drafts on existing issues

### C1. Comment on #771 (`definitions` / draft-07 schema)

Entries: `summarize-nextflow-cli-draft07-definitions-params-empty` (major). Subject:
`packages/summarize-nextflow` (resolver `parseParams`). Observed through Mold
`content/molds/summarize-nextflow/index.md` revision 18, hash
`fb19fff9162cc36fae916a456cfbbe31a33c4565063a522846c48222d02f7c37`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

A second pipeline hit this: nf-core/atacseq 2.1.2 (tag `2.1.2`, commit `1a1dbe5`), a
nextflow-to-galaxy run with Foundry skills 0.2.0.

- `nextflow_schema.json` is draft-07: 89 params in 10 groups under `definitions`.
  `foundry summarize-nextflow` emitted `params: []`.
- Unlike OceanOmics, atacseq's `input` param has no `schema:` keyword. Its samplesheet is checked
  by a `SAMPLESHEET_CHECK` process instead, so fixing `definitions` alone will not fill
  `sample_sheets[]` here. That gap is filed separately.
- Still unfixed on main `df991d0`: `resolver.ts` never reads `definitions`.

We rebuilt the 89 params by hand, which every older nf-core pipeline would force on a user.
```

### C2. Comment on #762 (closure arguments split into edges)

Entries: `summarize-nextflow-cli-closure-args-split-into-edges` (major). Subject:
`packages/summarize-nextflow` (`extractCallInvocations`). Observed Mold hash `fb19fff9…7c37`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

The same defect appears on nf-core/atacseq 2.1.2 (`workflows/atacseq.nf`), in two shapes worth
adding to the fix's test fixtures:

1. A short inline closure, `PREPARE_GENOME.out.fasta.map { [ [:], it ] }`, passed to
   `FASTQ_ALIGN_BWA`, became four edges with `from` values `.map {`, `[ [:], it ]`, `}` and the
   bare channel.
2. Literal positional arguments (`false`, `0`, `[]`) became edge sources.

The summary had 213 edges. After hand reconciliation, 119 were real. Expected: as proposed
above, treat the balanced argument expression as one source, attach the operators to `via`, and
drop arguments that are not channels (literals, `[]`) from `edges[]`.
```

### C3. Comment on #763 (`--profile` silently defaults to `test`)

Entries: `summarize-nextflow-cli-default-profile-treated-as-explicit` (major). Subject:
`packages/gxwf-foundry` `summarize-nextflow` command plus the resolver's candidate rationale.
Observed Mold hash `fb19fff9…7c37`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

Another consequence of the default, on a pipeline with **no nf-test at all** (nf-core/atacseq
2.1.2 has no `tests/` directory):

- `profiles[]` correctly classified `test`, `test_controls` and `test_full` as test profiles.
- `test_candidates[]` held only `profile:test`, with rationale "explicit caller profile override",
  although the caller passed no `--profile`.
- Per the Mold's profile fallback, all three should be candidates, with `test_full` classified
  reference-scale. We added `test_controls` and `test_full` by hand.

Main `df991d0` still has `.option("--profile <name>", "Profile to resolve config under", "test")`
in `packages/gxwf-foundry/src/commands/summarize-nextflow.ts:22`.
```

### C4. Comment on #761 (local clone breaks `source.url`)

Entries: `summarize-nextflow-cli-local-clone-placeholder-provenance` (minor). Subject:
`packages/summarize-nextflow` (source resolution). Observed Mold hash `fb19fff9…7c37`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

A related failure mode in the same source-resolution path, seen on a plain GitHub clone of
nf-core/atacseq at tag `2.1.2`:

1. When the resolver's git calls fail, here a Windows `node` on a WSL path with git's "dubious
   ownership" check, `source` falls back to `url: https://example.invalid/unknown.git` and
   `version: unknown` (`resolver.ts:418`). This is silent: no warning, and the summary passes
   validation.
2. Passing `--pin 2.1.2` to recover made the CLI *re-clone* the local path. That failed for the
   same reason.

Expected: emit a `warnings[]` entry (or fail) instead of a placeholder URL. With `--pin` on a
local path, verify or check out the ref in place rather than cloning. The fallback proposed above
(`manifest.homePage`) would also have produced a correct URL here.
```

### C5. Comment on #666 (resolver extraction defects): item 4 variant plus a new item

Entries: `summarize-nextflow-cli-reference-assets-empty-legacy-genome-attribute` (major),
`summarize-nextflow-cli-script-level-channels-missed` (minor), and
`summarize-nextflow-cli-params-delta-drops-numeric` (minor, already reported here; confirmation
only). Subject: `packages/summarize-nextflow`. Observed through `summarize-nextflow` (hash
`fb19fff9…7c37`) and `nextflow-summary-to-galaxy-reference-data` revision 5 (hash
`b49bae31e3b8918b45f852b8f50e1101e71837380b97f8e8ec237a5dd2955f7f`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

Three observations from nf-core/atacseq 2.1.2 (older nf-core template), checked against main `df991d0`.

**Item 4 variant: two-argument `getGenomeAttribute`.** The old template assigns
`params.fasta = WorkflowMain.getGenomeAttribute(params, 'fasta')` in `main.nf` (L20-31). The
regex at `resolver.ts:961` requires a quote right after `getGenomeAttribute(`, so this form never
matches. `reference_assets[]` and `reference_rebuilds[]` were both empty. The
`nextflow-reference-data-classification` note cites atacseq as a key-expanded example. Rebuild
guards in `subworkflows/local/prepare_genome.nf` use the positive form
(`if (params.bwa_index) { UNTAR } else { BWA_INDEX }`) and the negated form
(`if (!params.tss_bed) { TSS_EXTRACT }`, `if (!params.macs_gsize)`). The negated ones should
already be detectable. Expected: accept `(?:WorkflowMain\.)?getGenomeAttribute\(\s*params\s*,\s*'x'\)`,
and emit rebuilds at least for the negated guards.

**New item: script-scope channels.** Values built at the top level of `workflows/atacseq.nf`,
outside the `workflow {}` block (`ch_input = file(params.input)`, bamtools and MultiQC config
files, L20-55), are missing from `workflow.channels`. `edges[]` nevertheless references
`ch_input`, and no channel carries `from_param`. Expected: include script-scope constructions
the primary workflow references, with `construct` and `from_param` filled in.

**Confirmation of the `params_delta` numeric drop reported above:** in atacseq's
`conf/test.config`, `max_cpus = 2`, `read_length = 50` and `fingerprint_bins = 100` were
dropped. `read_length` matters here because it drives the MACS2 genome-size computation.
```

### C6. Comment on #673 (source-read posture)

Entries: `reference-data-mold-no-fallback-when-inventory-empty` (friction, minor). Subject:
`content/molds/nextflow-summary-to-galaxy-reference-data/index.md`, revision 5, hash
`b49bae31…5f7f`, unchanged on main.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

Another data point for correction 1, at the extreme. On nf-core/atacseq 2.1.2,
`reference_assets[]` **and** `reference_rebuilds[]` were both empty (resolver gap, see #666).
The Mold's "flag the asset rebuild-unverified rather than re-parsing source files" instruction
then has nothing to flag. Followed literally, it leaves every derived asset undesigned: chrom
sizes, autosomes, include-regions BED, gene and TSS BED.

The phase read `subworkflows/local/prepare_genome.nf` directly and cited it in the brief. A
pipeline-level posture as proposed here would make that legitimate. At minimum, the Mold should
name the empty-inventory case: allow a bounded read of the reference-prep subworkflow named in
`subworkflows[]`, with file and line citations.
```

### C7. Comment on #769 (confirm scope at the start)

Entries: `interface-mold-no-scope-selection-guidance` (gap, minor). Subject:
`content/molds/nextflow-summary-to-galaxy-interface/index.md`, revision 6, hash
`43966773391578490688098c9333f6eb2eaa94574755f5b6554e7f9b72a605c0`, unchanged on main.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

From the interface Mold's side, from a nextflow-to-galaxy run on nf-core/atacseq 2.1.2: that
pipeline has 4 aligners × 2 merge levels plus optional QC stages, and the interface's input and
output set depends entirely on which of them are in scope. `nextflow-summary-to-galaxy-interface`
never says who makes that call. The agent asked the user at phase 3 and recorded every excluded
stage as a `kind: dropped` ledger entry by its own choice.

Whatever the pipeline-level fix here, please also make the interface Mold consume an explicit
scope (from a Workflow Brief, the caller, or a stated default such as "default route, default
aligner"). Require each excluded stage to land as a `kind: dropped` entry, so the scope stays
auditable downstream. Related: #798.
```

### C8. Comment on #654 (branch twins)

Entries: `draft-format-no-guidance-for-repeated-lane` (gap, minor). Subject:
`content/research/galaxy-workflow-draft-format/index.md`. Cast hash
`e9b84eeb50cac23f70837e3ed73afe787213b49c06e82606540433f414b56fec`; main hash `8bb5cad9…` has
changed but still has no twin or repeated-chain guidance. Observed through Mold
`nextflow-summary-to-galaxy-template` revision 10, hash
`77f885d640900cca7dac4a3bbb33308d4d8065e871c919c672487db61caf93ab`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

Twins also arise at **template** time, not only from topology repair. nf-core/atacseq 2.1.2
flips six processes on `meta.single_end` (Trim Galore, bamtools filter, orphan removal,
genomecov, MACS2, featureCounts). The template split reads into PE and SE lanes at input and
emitted flat `pe_*` / `se_*` twins: 30 of 80 steps.

`galaxy-workflow-draft-format` covers subworkflow nesting but no shared-definition idiom. An
inline `run:` subworkflow would be duplicated and walked twice by the loop. So the "create with
obligation" and "implement by copy" corrections proposed here need a home in the draft format
too: a `twin_of` / delta hint on the template side, and a loop rule that copies a resolved step
to its twin. At runtime, one twin pair did diverge for a reason: featureCounts PE_fragments
aborts on SE BAMs (2.1.1), so `pe_featurecounts` and `se_featurecounts` must differ. That is
exactly the enumerated delta this issue asks to record.
```

### C9. Comment on #576 (scalar parameters in test fixtures)

Entries: `test-data-refs-no-carrier-for-computed-scalar-params` (gap, minor). Subject:
`package://@galaxy-foundry/gxwf-foundry#testDataRefsSchema`. Cast schema hash
`534dcb2f44e24a33bd59de2bca8d882af97321c602cf1b66776c22c38b0207a8`, unchanged on main. Observed
through Mold `nextflow-to-test-data` revision 4, hash
`842e097edfb5bfbc37b62a35d5870ee2087df33919212a7965fd70dae799b189`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

The same gap one artifact earlier, in `test-data-refs`. nf-core/atacseq computes `macs_gsize` at
runtime (khmer unique-kmers), so its test profile never declares a value. The Galaxy workflow
takes it as an integer input, so the test needs one. We computed 11,622,260 from the test genome
(distinct canonical 50-mers). But `test-data-refs` carries only dataset fixtures, so the value
went to the open-requirements ledger, not the handoff the test-plan Mold reads.

Expected: let `test-data-refs` carry scalar parameter refs (value + provenance, e.g.
`derived-from-fixture`), and make the test-plan `JobInput` shape for scalars match it, which is
the fix asked for here.
```

### C10. Comment on #743 (`list:paired_or_unpaired` examples)

Entries: `test-conventions-no-paired-or-unpaired-input-example` (gap, minor). Subject:
`content/research/iwc-test-data-conventions/index.md`, hash
`b7ef14132a0b40f626fff98fde44234ce5c848b6a3c255f4748b803c9a44b074`, unchanged on main. Observed
through Mold `implement-galaxy-workflow-test` revision 11, hash
`34855691581889d36265e00178088b8a52a51ee72119329261bca186f7cb480e`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

A working test-file example to seed this. It comes from a nextflow-to-galaxy run on
nf-core/atacseq 2.1.2 that passed on test.galaxyproject.org. The input mixed PE and SE runs.
Inner elements must **not** carry `type` / `collection_type`: adding them failed `validate-tests`
with 60+ `oneOf` errors pointing at the outer input.

    reads:
      class: Collection
      collection_type: list:paired_or_unpaired
      elements:
      - class: Collection
        identifier: OSMOTIC_STRESS_T0_PE_REP1_T1
        elements:
        - class: File
          identifier: forward
          location: https://raw.githubusercontent.com/nf-core/test-datasets/atacseq/testdata/SRR1822153_1.fastq.gz
          filetype: fastqsanger.gz
          hashes: [{hash_function: SHA-1, hash_value: e7304cadcdf9cf9cb108c577c6119d6bc1c5b88b}]
        - class: File
          identifier: reverse
          location: https://raw.githubusercontent.com/nf-core/test-datasets/atacseq/testdata/SRR1822153_2.fastq.gz
          filetype: fastqsanger.gz
          hashes: [{hash_function: SHA-1, hash_value: 9c5406feb1bb1bb6aba00d8341764917b52f6bc1}]
      - class: Collection          # a single-end run
        identifier: OSMOTIC_STRESS_T100_SE_REP1_T1
        elements:
        - {class: File, identifier: unpaired, location: <url>, filetype: fastqsanger.gz}

`iwc-test-data-conventions` has a `list:paired` example but none for `paired_or_unpaired`. A
sibling example with the legal keys on inner collections would have saved the guesswork.
```

### C11. Comment on #644 (`validate-galaxy-workflow` gate)

Entries: `validate-mold-silent-on-connections-flag` (gap, minor). Subject:
`content/molds/validate-galaxy-workflow/index.md`, revision 5, hash
`74e3743fc376f33c1eb37832ab4869c327d48f87e015c7a38597cf4c4ca939cd`, unchanged on main.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

A related ambiguity in the same Mold. The procedure says "run gxwf validate" with no flags, so
which invocation is the terminal gate is left to judgment. On an nf-core/atacseq 2.1.2 workflow
(80 steps), the flags gave opposite results:

- `gxwf validate --strict` (and `draft-validate --concrete --strict-state`) passed.
- `gxwf validate --strict --connections` exited 1 with 18 "invalid" and 20 skipped edges, all
  false positives downstream of `__APPLY_RULES__` (filed separately).

The phase treated `--connections` as advisory, by judgment. Expected: name the gating command
and flags, and say how connection-report findings map to pass or fail. Combined with this issue's
importability gate, the gate would also have caught the frame-colour import rejection (see #580).
```

### C12. Comment on #580 (frame comments rejected by Galaxy import)

Entries: `gxwf-validate-misses-frame-color-enum` (major). Subject: related project, gxwf comment
validation (`@galaxy-tool-util/cli`, https://github.com/jmchilton/galaxy-tool-util-ts). Observed
through Mold `run-workflow-test` revision 8, hash
`6e312c6ee27ef6e45a6ace74087cd28a6509ade11f788a51ee478efce58971b6`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

Another frame field with the same gap, after position and size: **`color`**. A frame authored
with `color: lightblue` passed `gxwf draft-validate --concrete --strict-state` and
`gxwf validate --strict`. Galaxy 27.0.dev0 (test.galaxyproject.org) then rejected the import
with HTTP 400 `err_code 400008`:

    Input should be 'none', 'black', 'blue', 'turquoise', 'green', 'lime', 'orange', 'yellow',
    'red' or 'pink' in ('frame', 'color')

Changing only the colour to `yellow` imported. Suspected upstream: gxwf validates `comments[]`
more loosely than Galaxy's `WorkflowCommentModel`. Expected: validate `comments[]` against
Galaxy's model (colour enum and the other required or enumerated fields) in `validate --strict`
and `draft-validate`. Meanwhile, the Foundry's `galaxy-workflow-comments` note already lists the
palette; the template Mold could tell the author to stay inside it.
```

---

## New-issue drafts

### N1. summarize-nextflow §3.5: no branch for the legacy `SAMPLESHEET_CHECK` samplesheet idiom

Entries: `summarize-nextflow-samplesheet-discovery-no-branch-for-legacy-check` (gap, minor).
Subject: `content/molds/summarize-nextflow/index.md`. Observed revision 18, hash
`fb19fff9162cc36fae916a456cfbbe31a33c4565063a522846c48222d02f7c37`; main hash `d8e67590…` has
changed, and §3.5 still lacks the branch.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
Step 3.5's sample-sheet discovery branches (`schema:` keyword, `samplesheetToList`, `splitCsv`
over `Channel.fromPath(params.X)`) miss the pre-nf-schema nf-core idiom, where:

- `assets/schema_input.json` exists but nothing references it: no `schema:` keyword in
  `nextflow_schema.json`, and no `samplesheetToList`;
- a local `SAMPLESHEET_CHECK` Python process validates the sheet; and
- `splitCsv(header: true)` reads **that process's output**, not the param.

## Evidence
nf-core/atacseq 2.1.2, `subworkflows/local/input_check.nf` L5-23. `foundry summarize-nextflow`
emitted no `sample_sheets[]` entry. The 6 columns were recovered by hand and recorded as
`discovered_via: ad-hoc` with `schema_path: assets/schema_input.json`. The `meta.single_end`
flag is derived by the check script, not by a column.

## Expected
Add a branch (or a rule under `splitCsv`) for `splitCsv` on a process output whose input is the
samplesheet param. Read the sibling `assets/schema_input.json` for columns, and note derived meta
such as `single_end`. This is the shape of most nf-core pipelines released before nf-schema.

Run: nextflow-to-galaxy, Foundry skills 0.2.0, nf-core/atacseq 2.1.2. Related: #771 (the
draft-07 schema form these same pipelines use).
```

### N2. compare-against-iwc-exemplar: the exemplar artifact assumes one nearest workflow

Entries: `iwc-compare-single-exemplar-artifact-for-split-match` (gap, minor). Subject:
`content/molds/compare-against-iwc-exemplar/index.md`, revision 12, hash
`84abb427cbcbae5616ae22e4a7fa803f14350605c246638575b3a32c5ad9c6fb`, unchanged on main.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The procedure and the `iwc-exemplar-gxformat2` artifact assume a single nearest exemplar. IWC
often splits a domain into several workflows that each best match a different sub-graph of the
source pipeline.

## Evidence
nf-core/atacseq 2.1.2. The best per-library match was `epigenetics/atacseq/atacseq`. The best
cross-sample match (consensus peaks via `bedtools_multiintersectbed` + `Filter1` with a composed
`c4 >= N` rule) was `epigenetics/consensus-peaks/consensus-peaks-atac-cutandrun`. Both were
needed; the second closed an open ledger gap outright. To fit one file, the phase wrote
`iwc-exemplar.gxwf.yml` with a non-runnable `steps:` map keyed by source workflow
(`steps.atacseq`, `steps.consensus_peaks`), a shape no schema or downstream Mold describes.

## Expected
Either let the artifact carry several labelled sub-graph slices (one per exemplar, each
naming which part of the design briefs it guides) with a documented shape, or allow one sibling
file per exemplar and say how the template Mold consumes them.

Run: nextflow-to-galaxy, Foundry skills 0.2.0, IWC @ `5bfb694`.
```

### N3. advance-galaxy-draft-step: one step per invocation does not scale; allow per-wrapper batching

Entries: `advance-step-one-per-call-impractical-for-twinned-80-step-draft` (friction, major).
Subject: `content/molds/advance-galaxy-draft-step/index.md`. Observed revision 11, hash
`677bb3288b4b88a5c4d66c878318c4d46bdc15f9ebcb01698ade2100a70ea835`; main hash `12f242dd…` has
changed, with no batch provision.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The Mold advances exactly one step per invocation. On an 80-step draft with 78 drafty steps but
only 35 distinct wrappers, that means 78 iterations, most of them repeating pin, summarize and
validate for a wrapper already resolved one step earlier: PE/SE twins and repeated
samtools/awk/merge steps.

## Evidence
nf-core/atacseq 2.1.2 → Galaxy, phase 7. The run did not follow the one-step contract. It
resolved and summarized each distinct wrapper once against the target toolbox (34 pins + 1
substitute, 3 user-defined tools), concretized all 78 steps in one scripted pass, then ran
`draft-validate --concrete --strict-state` once (11 state errors, one fix round) until
`draft-next-step` reported `draft: false`. The run record shows `iterations: 1`. The resulting
workflow passed on test.galaxyproject.org. #547's profiling (wall clock dominated by turn count,
not tools) suggests the per-step unit is also the costly one.

## Expected
Either a batch mode (resolve per distinct wrapper, implement every step that shares it, validate
once with the same `--concrete --strict-state` gate), or make the harness loop's unit "one
wrapper" rather than "one step". Keep the same failure routing and ledger checks per step.

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```

### N4. advance-galaxy-draft-step: no lightweight path for trivial structural fixes found at implementation time

Entries: `advance-step-in-loop-repairs-without-escalation` (friction, minor). Subject:
`content/molds/advance-galaxy-draft-step/index.md` (revision 11, hash `677bb328…a835`; main has
changed, and step 5 still routes every structural edit to repair).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
Two earlier-step defects surfaced only once real wrapper port types were wired. Each needed a
one-step structural edit. The Mold's only route is "append a blocking entry and escalate to
`repair-galaxy-draft-topology`". The run made the edits in place instead and recorded them as
resolved or dropped ledger entries with `topology_repair.escalations: 0`.

## Evidence
nf-core/atacseq 2.1.2, PE/SE lanes:
1. PE FastQC output is `list:paired`, SE is `list`, and `__MERGE_COLLECTION__` cannot merge
   them. Fixed by inserting one `__FLATTEN__` step.
2. Post-markdup and post-filter flagstats share element identifiers, so MultiQC inputs would
   collide. Fixed by removing two dead-end steps.
Both stayed green under `draft-validate`, and the final workflow passed at runtime.

## Expected
Define a bounded in-loop path for trivial, local structural edits (one inserted collection
operation, or removing a dead-end step with no promoted output), with the same ledger trail and
budget accounting. Or state explicitly that even these must go through repair, so runs behave
consistently. Related: #753 (repair contract), #660.

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```

### N5. gxwf `--strict-state`: misleading diagnostics for a null optional data parameter

Entries: `gxwf-strict-state-null-optional-data-message` (friction, minor). Subject: related
project, `gxwf draft-validate --strict-state` (`@galaxy-tool-util/cli`,
https://github.com/jmchilton/galaxy-tool-util-ts). Observed through `advance-galaxy-draft-step`
(hash `677bb328…a835`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
An unconnected optional data parameter set to `null` in step `state` fails
`gxwf draft-validate --concrete --strict-state` with a message that does not say what to change.
When the parameter sits inside a conditional branch, the error blames the conditional's selector
instead.

## Evidence
11 errors on the first strict pass of an nf-core/atacseq 2.1.2 draft. Examples: FastQC
`contaminants` and MultiQC `image_content_input` set to `null` gave
`Expected never, actual null` / `Expected undefined, actual null`. A conditional holding such a
param reported `Expected "no", actual "yes"` on its selector, although `"yes"` was valid. All 11
cleared by deleting the null keys.

## Suspected upstream
The generated linked-step schema forbids the key outright, and the reported path collapses to the
nearest discriminated union. A gxwf (galaxy-tool-util-ts) issue; filed here with the run context
for forwarding.

## Expected
Report "optional data input must be omitted from state (or connected)" at the parameter's own
path, and do not attribute it to the conditional selector. Meanwhile, the Foundry's
`implement-galaxy-tool-step` guidance could say: omit unconnected optional data params from
`state` rather than writing `null`.
```

### N6. IUC `bedtools_genomecoveragebed`: no `-pc` / `-fs` options

Entries: `iuc-bedtools-genomecov-missing-pc-fs` (wish, minor). Subject: related project,
`toolshed.g2.bx.psu.edu/repos/iuc/bedtools/bedtools_genomecoveragebed/2.31.1+galaxy0`. Observed
through `advance-galaxy-draft-step` (hash `677bb328…a835`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The IUC genomecov wrapper exposes `-bg` and `-scale` but not `-pc` (paired-end fragment coverage)
or `-fs` (fragment size for single-end reads). nf-core ATAC-seq and ChIP-seq pipelines use both
for normalised bigWigs.

## Evidence
nf-core/atacseq 2.1.2 `BEDTOOLS_GENOMECOV` ext.args choose `-pc` (PE) or `-fs` (SE) per library,
with `-scale 1e6/mapped`. The wrapper's parsed inputs (2.31.1+galaxy0) carry neither option. The
Galaxy translation substituted `deeptools_bam_coverage` 4.0.0+galaxy1 (bin size 10, scaleFactor
wired per element), which gives bin-level rather than base-level coverage. That is a recorded
deviation from the source.

## Suspected upstream
galaxyproject/tools-iuc, `tools/bedtools` genomecov wrapper. Filed here with the run context for
forwarding.

## Expected
Add `-pc` and `-fs` to the BAM-input branch. Meanwhile, the Foundry could document bamCoverage
(with a per-element `scaleFactor`) as the substitute for nf-core genomecov steps.
```

### N7. IUC featureCounts: no SAF annotation input

Entries: `iuc-featurecounts-no-saf-annotation` (wish, minor). Subject: related project,
`toolshed.g2.bx.psu.edu/repos/iuc/featurecounts/featurecounts/2.1.1+galaxy3`. Observed through
`advance-galaxy-draft-step` (hash `677bb328…a835`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The featureCounts wrapper's history-annotation branch accepts gff/gtf/gff3 only. SAF (`-F SAF`),
the format nf-core uses to count reads over peak sets, is not accepted.

## Evidence
nf-core/atacseq 2.1.2 `SUBREAD_FEATURECOUNTS` ext.args `-F SAF -O --fracOverlap 0.2` over
consensus peaks. The Galaxy translation reformatted consensus peaks as GTF with a synthetic
feature type and `gene_id` = interval name. It ran correctly (counts matrix and DESeq2 QC
passed), but it is an extra conversion step and a recorded deviation. The same run found that
2.1.1 aborts on SE BAMs in `PE_fragments` mode ("No paired-end reads were detected"), whereas
nf-core's subread 2.0.1 tolerates `-p` there. The Foundry had to split counting into PE and SE
steps.

## Suspected upstream
galaxyproject/tools-iuc `tools/featurecounts`. Filed here with the run context for forwarding.

## Expected
Accept a tabular SAF annotation in the history branch and pass `-F SAF`. Meanwhile, a
pattern-page note: peak-set counting needs SAF→GTF projection, and PE/SE libraries must be
counted in separate steps.
```

### N8. test-data-refs: no state for an optional input the source test deliberately leaves unset

Entries: `test-data-refs-optional-unused-input-forced-unresolved` (friction, minor). Subject:
`package://@galaxy-foundry/gxwf-foundry#testDataRefsSchema` (hash `534dcb2f…07a8`, unchanged on
main). Observed through `nextflow-to-test-data` revision 4 (hash `842e097e…b189`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
An optional workflow input that the selected source test intentionally does not set can only be
written as `resolved: false` / `storage: unresolved`. That is the same encoding as a real gap,
and under the `test-data-resolution` branch rules it routes to `find-test-data` for a search
nobody needs.

## Evidence
nf-core/atacseq 2.1.2 `profile:test` sets no `blacklist`. The Galaxy workflow has an optional
`blacklist_bed` input. `test-data-refs.json` had to mark it unresolved, and the harness had to
override the fall-through by judgment.

## Expected
Add an explicit state (e.g. `resolved: true, storage: not-needed` or a `left_unset_by_source`
reason) that satisfies the ref without a fixture, and tell the branch not to fall through for it.

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```

### N9. galaxy-workflow-test-plan: assertions cannot express a minimum or maximum bound

Entries: `test-plan-tolerance-cannot-express-min-bound` (gap, minor). Subject:
`package://@galaxy-foundry/gxwf-foundry#galaxyWorkflowTestPlanSchema`. Cast hash
`03fc1d58499c4bd5f3fa9556d771a8f24bcc8a387f120bd6eb28fe5f103ffc95`; main `aaa611c5…` has changed
in formatting only, and `Tolerance.kind` is still `delta | delta_frac | lines_diff | none`.
Observed through `nextflow-test-to-galaxy-test-plan` revision 8, hash
`fa769216f621ef25470c9fb907df1278635c0a1e022b647b9462ff7b92469291`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
`AssertionIntent` carries `expected_value` plus a `Tolerance` limited to
`delta | delta_frac | lines_diff | none`. Lower- or upper-bound assertions (`has_size: {min: …}`,
`has_n_lines: {min: …}`) are the natural shape when no upstream expected value exists, and they
can only be written as prose inside `intent`.

## Evidence
nf-core/atacseq 2.1.2 has no nf-test, so every assertion in the plan was intent. Examples are
"library_peaks has at least N lines" and "library_bam is non-trivially sized". The concrete
tests-format file then had to re-derive `min:` values from the prose.

## Expected
Add a bound form, either `min` / `max` on `AssertionIntent` or a `Tolerance.kind: bound` with
`min` / `max` magnitudes, so `implement-galaxy-workflow-test` can map it directly onto
tests-format.

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```

### N10. nextflow-test-to-galaxy-test-plan: no rule for a profile-only candidate (no nf-test)

Entries: `test-plan-mold-silent-on-profile-only-evidence` (gap, minor). Subject:
`content/molds/nextflow-test-to-galaxy-test-plan/index.md`, revision 8, hash `fa769216…9291`,
unchanged on main.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The procedure says to set `source.derived_from: test-evidence` "because this plan is translated
from real nf-test evidence". Many released nf-core pipelines have no nf-test at all, only a
`test` profile. The profile supplies inputs and params but no expected outputs.

## Evidence
nf-core/atacseq 2.1.2 has no `tests/` directory; the selected candidate is `profile:test`
(`kind: profile`, no snapshot). The phase set source `test-evidence`, test case `intent`, plus
the `no-upstream-expected-outputs` warning, all by judgment.

## Expected
State the rule for a profile-only candidate: which `derived_from` applies at source and
test-case level, and that every assertion is then `intent` or `fixture-derived` with the
`no-upstream-expected-outputs` warning. Optionally, point to tightening the assertions from a
first green invocation (`workflow_test_init --from_invocation`).

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```

### N11. gxwf `validate --connections`: cannot infer `__APPLY_RULES__` output, marks all downstream edges invalid

Entries: `gxwf-connections-cannot-infer-apply-rules-output` (defect, major). Subject: related
project, `gxwf validate --connections` (`@galaxy-tool-util/cli`,
https://github.com/jmchilton/galaxy-tool-util-ts). Observed through `validate-galaxy-workflow`
revision 5 (hash `74e3743f…39cd`).

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
`gxwf validate --strict --connections` reports "Cannot determine output type for output" on an
`__APPLY_RULES__` step. It then treats every downstream mapped step as un-mapped, so a correct
workflow gets "invalid" edges and exit code 1.

## Evidence
An nf-core/atacseq 2.1.2 → Galaxy workflow (80 steps) regroups runs into libraries with Apply
Rules (`list_identifiers` columns `[1, 2]`, so the output is `list:list`). `--connections` gave
18 invalid edges ("output is dataset, input expects collection") and 20 skips, all false
positives. The same workflow imported and ran 182/182 jobs green on test.galaxyproject.org.

## Suspected upstream
The connection graph builder in galaxy-tool-util-ts has no output-type rule for
`__APPLY_RULES__`. Filed here with the run context for forwarding.

## Expected
Derive the output `collection_type` from `tool_state.rules.mapping`: N `list_identifiers` columns
give `list` repeated N times, and a `paired_identifier` adds `:paired`. Failing that, mark
downstream edges `unknown`/`skip`, not `invalid`. Meanwhile, `validate-galaxy-workflow` should
treat `--connections` findings downstream of Apply Rules as advisory (see the #644 comment).
```

### N12. nextflow-to-galaxy pipeline: no repair and re-run path after debug

Entries: `pipeline-no-repair-rerun-path-after-debug` (gap, major). Subject:
`content/pipelines/nextflow-to-galaxy/index.md`, revision 5, unchanged in shape on main (still
ends at `debug-galaxy-workflow-output`). Observed through `debug-galaxy-workflow-output`
revision 6, hash `0ea72a26de30b8086e4d11fea09bc269e94320ec97fb317f6c0232cd92841009`.

```markdown
Posted by an AI assistant on Chisomgold's behalf.

## Summary
The pipeline ends at `debug-galaxy-workflow-output`, which classifies a red run and names where
the fix belongs but neither repairs nor re-runs. Any real run that is red on first contact needs
work outside the declared phases to reach green.

## Evidence
nf-core/atacseq 2.1.2 → Galaxy on test.galaxyproject.org needed three attempts:
1. Import rejected (400, frame `color: lightblue`). Debug routed it to the template phase.
2. 176/182 jobs ok; featureCounts `PE_fragments` aborted on 3 SE libraries. Debug routed it to
   template topology (split counting per lane).
3. Pass, 182/182.
Both fixes, their re-validation (`draft-validate`, `validate --strict`, `validate-tests`) and
attempts 2 and 3 all ran inside phase 13, outside any declared phase. They are recorded only in
`workflow-test-result.json` `attempts[]` and the debug report.

## Expected
Add a bounded loop from debug back to the routed phase. Template or loop goes to validate and
run. Use an attempt cap, and carry the debug report into the repair. Alternatively, add an
explicit post-debug repair phase. Each attempt should re-run the static gates. Removals should
stay subject to the #796 / #800 checks, which already assume test-phase routing exists (#800:
"needs test-phase routing, which #753 left out"). Related: #792.

Run: nextflow-to-galaxy, Foundry skills 0.2.0.
```
