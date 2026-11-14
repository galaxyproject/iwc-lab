# Phase 6 progress — `nextflow-summary-to-galaxy-template`

Run `funcscan-run1`, phase 6 of `pipeline-nextflow-to-galaxy`. Started 2026-11-11.
Output artifact: `galaxy-workflow-draft.gxwf.yml` (+ re-emitted `open-requirements.ledger.yml`).
Nothing outside `funcscan-run1/` and `/tmp/gxy-scratch/` was written; the funcscan clone was
read-only; nothing was installed, downloaded or filed to GitHub.

## 1. Inputs read for this phase

`summary-nextflow.json` (55 processes, 83 tool rows, 220 params — read programmatically for
`_plan_context`), `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md` (61 inputs,
§10.2 promoted outputs), `nextflow-galaxy-data-flow.md` (N1–N82, P1–P12, M1–M7, 11 gates),
`iwc-comparison-notes.md` (§4 idioms, §6 11 routed findings, §8 what it could not settle),
`iwc-exemplar.gxwf.yml` (the only in-boundary file carrying concrete Tool Shed ids),
`open-requirements.ledger.yml` (30 entries / 17 decisions / 4 held BCRs).
Source re-read for wiring only: `workflows/funcscan.nf:60-234`, `subworkflows/local/annotation.nf`.

## 2. The draft dialect, verified before authoring (not assumed)

`gxwf draft-validate --json` was run over 25 minimal drafts in three probe rounds
(`/tmp/gxy-scratch/phase6probe.py`, `phase6probe2.py`, `phase6probe3.py`; all rc/ok recorded).
Rules this phase authors against, each measured rather than inferred:

1. An input's `format` MUST be a **list**. A scalar string is a decode failure (exit 2). The draft
   schema and the format note do not say so.
2. Legal input `type`s: `data`, `collection`, `text`/`string`, `int`/`integer`, `float`, `boolean`,
   `color`, `directory_uri`. `multiple: true` is accepted on `type: data` and on `type: collection`.
   `type: collection` is the variant carrying `collection_type`, `format`, `column_definitions`.
3. A **list-form step that carries a `label` is addressed by its label**, not its `id`. Every step in
   this draft therefore has `id` only (label lives in `_plan_context`), so `outputSource` and
   `in[].source` are unambiguous.
4. Compound `when:` over workflow inputs validates: `&&`, `||`, parentheses, `==` against a string
   literal, `x == false`, and bare `$(inputs.b)` truthiness. `!` was **not** tested and is not used —
   negations are written as `== false` or expanded by De Morgan. Validation is syntactic only; the
   runtime semantics of a compound expression are unverified by this run.
5. A `type: subworkflow` step with `run: {class: GalaxyWorkflowDraft, inputs, outputs, steps}`
   validates, **including `when:` on the container and `when:` on the inner steps referencing the
   subworkflow's own inputs**, and workflow `outputs[]` may bind to a container port.
6. Nested slot ids (`style_cond|type_cond|pick_from_0|value`, `results_0|software_cond|input`) are
   accepted as `in[].id`; a `comments[]` frame may list a subworkflow step in `contains_steps`;
   `out[]` accepts `rename`/`hide`.
7. Tier gate confirmed by negative control: a step with no TODO sentinels that still carries
   `_plan_*` is a semantic error. `--strict*` flags are ignored unless `--concrete` is passed.
   Exit codes: 0 clean, 1 draft/topology/semantic error, 2 decode failure.

## 3. Wrapper-resolution tiers actually reachable inside this run's read boundary

The mold gates resolution on evidence, not on source tendency. Evidence available here is one
converted 22-step IWC slice plus the idioms quoted in the phase 5 notes — so:

- **Resolved: 0 steps.** The only step whose id, changeset *and* authored `state` are all attested
  inside the boundary is `pick_value`, and its authored `state` needs
  `style_cond.__current_case__` / `type_cond.__current_case__` indices, which are wrapper internals
  and are **not** in the excerpt. Inventing them would be fabricating evidence, so `pick_value` steps
  are pinned one tier down with the attested idiom in `_plan_state` instead.
- **Identity-pinned: concrete `tool_id`, `tool_version: TODO`, no `state`, no
  `tool_shed_repository`, `_plan_*` kept** — `pick_value` (all select/cascade steps), `multiqc`
  (id quoted in `iwc-comparison-notes.md` §4), and the five ids whose *operation* also matches:
  `prodigal`, `amrfinderplus`, `abricate`, `argnorm`. Every concrete id the emitter writes is
  self-checked at build time against the two attestation files; an id found in neither fails the build.
- **Deferred (`tool_id: TODO`): everything else** — 16 tool families absent from all 133 corpus
  workflows (antismash, ampcombi, ampir, amplify, bigslice, dbcan, deeparg, deepbgc, fargene, gecco,
  hamronization, hmmer, macrel, prokka, pyrodigal, rgi, seqkit, tabix, gunzip/untar/download), the
  eight reshape steps whose operation pages are link targets the bundle does not carry (§6,
  correction 3), and the mmseqs2 steps: the *family* is attested
  but the attested wrapper is `mmseqs2_easy_linclust_clustering` (clustering) while funcscan needs
  `createdb` / `taxonomy` / `createtsv`, so reusing that id would be a false match.
  `_plan_context` carries the module path, pinned version, bioconda/biocontainer rows, `ext.args`,
  `publishDir` and the source's own port names pulled from `summary-nextflow.json`.

## 4. Topology calls this phase made (each with its evidence)

1. **61 interface inputs kept, plus one forced addition.** `arg_rgi_db_is_processed` (`boolean`,
   default `false`) is added because `arg.nf:109` decides whether to run `RGI_CARDANNOTATION` by
   substring-testing the *uploaded file's name*, which no `when:` expression can read. The
   alternative (always process, 61 inputs) is written into that step's `_plan_state` so phase 7 can
   flip it in two lines. This is the only interface change the template forces.
2. **`bgc_mincontiglength` stays pinned, at the real default 3000** (pulled from `params[]`), inside
   `long_contigs._plan_state`. Promoting it is `brief_change_recommendations/promote-bgc-mincontiglength`,
   still `held-for-operator-decision`, so the interface is not changed here.
3. **ANNOTATION = two embedded subworkflow steps** (`annotation_full`, `annotation_long`), each
   carrying the four-arm body (pyrodigal / prodigal / prokka / bakta) and five per-port
   `pick_value` steps. Two subworkflow steps were chosen over 30 duplicated flat steps: probe T1
   proves an inner step can carry `when:` over an inner input, and the exemplar's embedded
   subworkflow is exactly the "lane body you can gate" idiom. There is no by-reference subworkflow
   call in this format, so "one body, two instances" costs two copies either way; nesting keeps the
   graph legible. Phase 5 §8 (corpus instantiates a subworkflow once) is carried as the risk.
4. **Derived annotation-tool override written verbatim from `annotation.nf:29`.** Phase 4 could only
   describe it as "an OR over six inputs"; the exact expression is now in the draft on each arm's
   steps. The `else if (prodigal)` arm is De Morgan-expanded using only probe-proven operators:
   `tool == "prodigal" && ( run_bgc == false || (skip_antismash && skip_deepbgc && skip_gecco) ) && run_amp == false`.
   The held BCR `annotation-tool-override-belongs-on-the-form` is left untouched; this draft is the
   "keep it in the gates" option, and it is now copy-pasteable if the operator chooses the other.
5. **Per-port pick_value dissolves `conditional-output-producer-unexpressible`.** Interface §10.4(1)
   could not bind one `annotation_result` label to four alternative producers. Because every emitted
   slot is already a `pick_value` over the four arms, one label per logical output binds to the pick
   port: `annotation_faa`, `annotation_fna`, `annotation_gbk`, `annotation_gff`.
6. **Variable-arity fan-in was rewritten while wiring it — this item is the corrected version.**
   The phase-5 decision (`heterogeneous-fan-in-uses-named-optional-slots-plus-pick-value`) said
   "fixed named optional slots on the consumer, no gather steps", and an earlier pass of this note
   claimed M1/M3/M4/M5 added nothing. Source evidence overruled that: `AMPCOMBI2_PARSETABLES` takes
   six positional ports and its hits arrive as *one* port carrying 1–4 files per sample through
   `groupTuple().join(faa).join(gbk).join(interpro).multiMap`, which is a collection axis, not four
   slots. As emitted, M1 is four steps (`relabel_amp_hits` → `merge_amp_hits` → `split_amp_hit_ids` →
   `nest_amp_hits`) and M3 is the same quartet for the BGC callers; M2 is one named bundle
   (`bundle_arg_reports`), M4/M5 are `merge_bigslice_input` → `bundle_bigslice_input`. Fixed optional
   slots survived where they are actually right: the database ports and the optional per-lane inputs.
   The trunk unions *are* materialised (faa, fna, gbk, gff, plus the two long-contig variants) because
   ~15 consumers share them. Ledger decision
   `variable-arity-fan-in-materialised-as-a-reshape-quartet` records the change; the merge hop is the
   one piece with no packaged recipe (§6, correction 3).
7. **The 18 per-consumer emptiness filters collapse to 7 filter steps** over the shared streams
   (fasta, faa, gbk, gff, the two BGC-only streams, taxa tsv) plus one metadata filter
   (`filter_cazyme_inputs`, N79, different predicate). The 18 sites differ only in their `log.warn`
   text, which has no Galaxy surface (`per-element-skip-warnings-have-no-galaxy-surface`).
8. **`versions` is not promoted** — no producer exists (§14 of the data-flow brief) and
   `brief_change_recommendations/versions-output-has-no-producer` is held. `multiqc_report` is made
   computable from the only real producers (the Prokka/Bakta `out.txt` ports via each ANNOTATION
   body's `pick_mqc`), and the three fragments the source collects but nothing here can produce
   (versions YAML, parameter summary, methods text) are recorded as **blocking** ledger entries.
9. **`interproscan_table` binds to the two-`NA`-column padding step** (`pad_interproscan_columns`),
   not to InterProScan, per the data-flow §15 binding.
10. **antiSMASH DB shape fixed at authoring time**: uploaded `.tar.gz`, always untarred
    (`pick_antismash_db` → `untar_antismash_db`), per data-flow §17.3 — a `when:` cannot test an
    input's datatype.
11. **N29/N31 (AMPcombi complete/cluster) are left ungated.** The source gates them on
    "fewer than two parsetables" and "more than one line", neither of which `conditional-gate-on-nonempty-result`
    can express; per data-flow §12 the threshold becomes a wrapper obligation, recorded in
    `_plan_state` and in `data-derived-gate-needs-nonemptiness-threshold`.
12. **Step-level gates are written as `when:` expressions, not pick_value chains**, except where the
    value itself must fall through (DB-or-rebuild selects). Phase 5 finding 3 measured the corpus's
    two-step inversion idiom; using it for ~30 gates would add ~60 steps to express what one
    expression states, and the expression form validates. Cost stated honestly: the corpus never
    writes a compound `when:` by hand, so this is an untested-by-corpus use of a construct the
    validator accepts.

## 5. Source finding made while settling the trunk (not in any upstream brief)

`funcscan.nf:97-100` is `branch { preannotated: gff != [] || gbk != []; fastas: true }`. Rows that
carry a gff or gbk land in `preannotated`; `ch_input_for_annotation` is fed from `fastas` (`:106`,
`:118`); and `ch_prepped_input = …mix(ch_intermediate_input.preannotated)` (`:154-155`, and `:167` for
the long stream) mixes the pre-annotated copies back in. Whether that is a partition or a duplication
turns on one question this run could not settle: **does the map form's `fastas: true` act as a
catch-all, or as an always-true condition that emits every row?** An early draft of this note and of
the two select steps' `_plan_context` asserted the second (non-exclusive) reading as Nextflow's
behaviour. That assertion was not verified — no Nextflow runtime was available and no downloads were
permitted — so it is now written as *unresolved* everywhere it appears.

The two readings differ in the artifact, not just on paper: under the complement reading each sample is
annotated once, while under the non-exclusive reading a pre-annotated sample is annotated *and* mixed
back, reaching each lane twice under one identifier, which is not representable as one Galaxy
collection element. Phase 4 §6 read the line as a complement ("`fastas: true` is the fall-through
arm").

This draft implements the complement reading: `select_to_annotate` / `select_to_annotate_long` remove
the GBK/GFF-sheet members from the annotation input. Reasons, corrected after checking
`assets/schema_input.json`: the source comment at `:139` ("Mix back the preannotated samples with the
newly annotated ones") implies the author expected the two labels to partition the rows; the
four-sheet interface already assumes disjoint streams; and the non-exclusive reading collides on
element identifiers. One earlier reason is **withdrawn** — `dependentRequired` does *not* support the
complement reading: it requires `sample`+`fasta` on every row and only couples `protein`↔`gbk` and
`gff`→`protein`, so a pre-annotated row is schema-legal *with* a FASTA either way. The divergence is
stated on both select steps, and the ledger carries it as
`discoveries/branch-label-readings-conflict-for-preannotated-rows` +
`entries/preannotated-complement-reading-diverges-from-source` (blocking for the test phases) +
`brief_change_recommendations/preannotated-rows-must-say-whether-they-are-re-annotated` (held). A
`-profile test_preannotated` fixture row carrying fasta+protein+gbk is what settles it.

## 6. Emission and validation log (final)

The emitter is eight small modules in `/tmp/gxy-scratch/p6/` (written to the operator's "split it
into small files, `py_compile` after each" instruction; the earlier single-file
`/tmp/gxy-scratch/phase6draft.py` was abandoned and left untouched): `p6_kit.py` (attested ids,
`when:` helpers, gates, step constructors, evidence pull from `summary-nextflow.json`),
`p6_iface.py` (inputs, promoted outputs, frame text), `p6_trunk.py` (unpack/trunk/ANNOTATION body/
unions/taxa/protein lanes), `p6_lanes.py` (AMP, ARG, BGC, CAZYME, MultiQC), `p6_frames.py` (stage
frames derived from the step list), `p6_steps.py`, `p6_emit.py` (self-checks + YAML write),
`p6_main.py` (driver). All eight `py_compile` clean; run as
`python3 -I /tmp/gxy-scratch/p6/p6_main.py <run-dir>`, which refuses to write if any self-check
fails.

**Emitted artifact** — `galaxy-workflow-draft.gxwf.yml`, 4046 lines:

| measure | value |
|---|---|
| inputs / promoted outputs | 62 / 14 |
| outer steps | 95 (84 Deferred, 9 Identity-pinned, 2 subworkflow containers) |
| inner steps (the two ANNOTATION bodies) | 38 (24 Deferred, 14 Identity-pinned) |
| gated steps / edges / comment frames | 94 / 232 / 10 |
| TODO sentinels / `_plan_*` steps | 505 / 133 |
| Resolved steps | 0 |

**Checks that passed**

- Emitter self-checks (things gxwf cannot see): every `in[].source` and `outputSource` resolves to a
  port its producer really registers, every `$(inputs.X)` names an input of the *enclosing* workflow,
  every concrete `tool_id` is quoted verbatim inside the run directory, container ports match their
  body's ports, frame coverage equals the step set exactly, no step uses `tool_state`, no duplicate
  ids.
- `gxwf draft-validate --json` → exit 0, `ok: true`, and 0 structure / 0 topology / 0 semantic
  diagnostics / 0 warnings. Its survey reports 505 TODOs across 133 step paths, 38 of them nested
  inside the two subworkflows, so the nesting is visible to the tool.
- `gxwf draft-next-step` walks the real draft and picks `arg_untar_card` with its six TODO work items;
  a separate probe draft (`/tmp/gxy-scratch/p6/probe_subwf.yml`) confirmed the loop returns a nested
  path (`["container","deep"]`), so grouping 38 steps into subworkflows does not hide them from
  phase 7. This closes the question the mold's `draft-next-step` sidecar asks.
- Read boundary held: `git -C ~/Desktop/bioHackthon/nf-core-funcscan status --porcelain`
  is empty; today's writes are this note, the draft and `open-requirements.ledger.yml`.

**Computability pass → ledger deltas.** `open-requirements.ledger.yml` 1416 → 1881 lines:
discoveries 19→23, entries 30→36, decisions 17→23, brief-change recommendations 4→6 (both new ones
`held-for-operator-decision`, so the phase-3 brief and the four held rows are byte-unchanged), plus a
phase-6 paragraph appended to the notes of 7 inherited entries. No status changed: nothing a wrapper
or a real run answers could be answered here. Blocking for phase 7:
`db-or-rebuild-fork-cannot-gate` (12 consumer steps must rebuild on absence),
`multiqc-input-fragments-have-no-producer` (versions YAML, parameter summary, methods text),
`arg-summary-producer-is-input-dependent` (three promoted outputs change datatype with
`run_taxa_classification`). Blocking for the test phases:
`preannotated-complement-reading-diverges-from-source`. Recorded but not blocking:
`directory-output-has-no-dataset-carrier`, `no-step-reached-resolved-tier`.

**Three corrections made during the phase, all of them against my own first pass**

1. `amp_cluster_table` was promoted from `ampcombi_cluster` alone. The source publishes the
   taxonomy-merged bgzip of that same table when `run_taxa_classification` is on
   (`amp.nf:156-162`, and `conf/modules.config:675-686` voids the plain publish in exactly that
   case), so the plain-only binding was neither shape the interface brief allows. Fixed: new
   `pick_amp_cluster_table` (identity-pinned `pick_value`), output rebound, and
   `amp_summary_table` now states that promoting it is strictly more than the source publishes.
2. `Kit.PV()` overwrote the caller's `note`, so the three summary picks shipped without the
   conditional-producer rationale that motivated them. Fixed in the constructor; the text is now in
   the draft.
3. Overstatement corrected: this note and the draft's `_plan_context` said the collection/tabular
   "pattern pages are not packaged". Wrong as written — `references/patterns/galaxy-collection-patterns.md`
   and `galaxy-tabular-patterns.md` **are** packaged, and they name tools (`column_maker`, `Filter1`,
   `tp_easyjoin_tool`/`tp_multijoin_tool`, `datamash_ops`, `query_tabular`, `Cut1`, `tp_grep_tool`).
   What is missing is the layer below: every operation page is a `[[link]]` with no file in the
   bundle, and `galaxy-sequence-patterns` — which the tabular MOC calls the dominant sequence seam —
   is absent entirely. The artifact was improved accordingly: 13 Deferred steps now carry a
   "packaged recipe:" line naming the MOC entry and its suggested tool, and the two
   `__MERGE_COLLECTIONS__` steps carry a "packaged gap:" line for the one hop with no name anywhere
   in the bundle (combining N sibling collections whose membership differs because a gated producer
   emitted nothing).

## 7. Where this stopped, and what is NOT done

Phase 6 stopped on the operator's instruction at the end of the correction pass. Open, in the order
someone picking this up would want them:

1. **The ledger still carries the overstated wording from correction 3.** The script that would have
   replaced those two fields (`/tmp/gxy-scratch/p6/patch6.py`: rewrite
   `entries/no-step-reached-resolved-tier.note`,
   `decisions/variable-arity-fan-in-materialised-as-a-reshape-quartet.rationale`, append a
   correction note to `entries/variable-arity-fan-in-has-no-attested-galaxy-recipe`) was **not run** —
   the operator stopped the run before it executed. The corrected facts are in §6 above; the ledger
   text has not been caught up to them.
2. **No phase-6 feedback entries were appended.** `foundry-feedback.ledger.yml` still holds 21
   entries and roster row 6 is still `status: running` with no `feedback_checked`. Eight candidates
   cleared the bar this phase: the undocumented `^TODO(_[A-Za-z0-9_]+)?$` sentinel-shape rule (a
   hyphenated semantic hint is a semantic error); `format` must be a list and nothing says so; the
   label-addresses-the-step rule is unstated; no packaged construction guidance for a `pick_value`
   cascade (`__current_case__`), which is the reason 0 steps reach Resolved; packaged pattern MOCs
   whose operation pages are all dead links, and no `galaxy-sequence-patterns` at all; no MOC entry
   for the N-way unequal-membership collection merge; `--strict*` silently ignored without
   `--concrete`; `draft-next-step` has no `--json` flag (JSON is the default, and
   `--output-format json` invites the wrong one).
3. **`foundry-run.yml` phase 6 still says `running` with `artifacts: []`,** and the run stays
   `running`. Both records need the phase-6 row (draft + ledger artifacts, note) before anything
   downstream reads this run honestly; that is harness-owned state and the operator's stop instruction
   said not to start new work, so it was left untouched rather than closed unilaterally.
4. **Not attempted, correctly out of phase 6's scope:** phase 7 (`advance-galaxy-draft-step`) was not
   started; no wrapper was resolved, downloaded or installed; no GitHub issue filed; the four
   held-for-operator-decision brief-change recommendations remain held and byte-unchanged, and the
   draft's `bgc_mincontiglength` pin (3000) and unpromoted `versions` output both assume that.
