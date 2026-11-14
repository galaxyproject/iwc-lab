# Data-flow brief — nf-core/funcscan → Galaxy

- **Run:** `funcscan-run1` · phase 4 (`nextflow-summary-to-galaxy-data-flow`)
- **Source:** `nf-core/funcscan` 4.0.0, commit `aee3dc965eb0c77267435544dda30da858763913`
- **Reads:** `summary-nextflow.json` (22 channels, 27 edges, 13 conditionals, 55 processes, 14 subworkflows), `nextflow-galaxy-interface.md`, `nextflow-galaxy-reference-data.md`, `open-requirements.ledger.yml`; source re-read for wiring: `workflows/funcscan.nf` (458 l) and `subworkflows/local/{annotation,amp,arg,bgc,cazyme,protein_annotation,taxa_class}.nf` (916 l), `conf/modules.config`, `assets/schema_input.json`, `tests/*.snap`
- **Consumers:** `compare-against-iwc-exemplar` (abstract topology + placeholder transformations), `nextflow-summary-to-galaxy-template` (gxformat2 skeleton, step order, `when:` wiring), `advance-galaxy-draft-step` (per-step tool resolution), `nextflow-test-to-galaxy-test-plan`
- **Not this document:** gxformat2, `tool_id`s, parameter values. Tool *needs* are stated as what a step must do; availability is `advance-galaxy-draft-step`'s to discover. Per `galaxy-data-flow-draft-contract`, tool needs and confidence live here; ordering guidance is shared with the template and is offered as a suggestion, not a step list.

## 1. The shape, and the four things that dominate it

Galaxy-side this is **one unbranched trunk, seven gated lanes, one report sink**. The trunk turns four user collections into four aligned per-sample collections of *prepared* artifacts (unpacked, optionally split into a length-filtered variant, optionally newly annotated). Each lane (AMP, ARG, BGC, CAZYME, taxa, protein-annotation, report) consumes some subset of those collections and most of them end there.

Four facts about the source dominate every decision below; each is verified, with sites.

1. **Most of the operator noise is Nextflow's flat-channel tax, and it disappears.** The 27 summary edges carry `map`, `transpose`, `branch`, `mix`, `groupTuple`, `join`, `multiMap`, `filter` — but 15 `.join()`, 7 `.multiMap{}`, 6 `.groupTuple()` and 29 non-versions `.mix()` sites exist because Nextflow re-assembles per-slot streams it had just split apart. Under the interface brief's four aligned `sample_sheet` inputs (§2.1 there) slots stay in separate collections end to end, and **the split/reassemble cycle has no Galaxy counterpart at all** — it becomes multi-input map-over. Class for most of this surface: `channel-only rewiring`.
2. **4 of the 7 screening subworkflows are data sinks.** `AMP`, `ARG`, `BGC`, `CAZYME` contribute only `versions` onward (`funcscan.nf:251,271,297,329,352,376`; `CAZYME` declares no `emit:` block at all — `cazyme.nf:11-75`). Their scientific output reaches the user only through `publishDir`, which is exactly the promotion list in interface §10.2. In the Galaxy graph these lanes have **no outgoing edges**, so nothing downstream can notice if they produce nothing.
3. **18 per-element emptiness filters and 5 data-inspecting gates are not parameter conditionals.** `workflow.conditionals[]`'s 13 rows are all parameter-driven, but the sources also contain 18 `.filter { … isEmpty() }` sites (15 in `funcscan.nf`, 3 in `arg.nf`) — each carrying its own `log.warn` inside the closure, which is why the 8 wiring files hold 23 `log.warn` sites — plus `if` blocks whose condition reads data or input shape instead of a param (across the 8 wiring files: 58 param-based `if`s, 21 data- or shape-based, 1 inspecting an input's shape, 6 tool-selectors; the primary workflow alone has 32 blocks, 16 of each kind). Only **5** of those are real gates (§12's table); the rest are the warning branches inside the filters. Galaxy `when:` is an expression over workflow **inputs**, so both classes — the filters and the 5 gates — fall outside it. This is the class of thing that gets silently dropped, so it gets its own sections (§8, §12) rather than a footnote.
4. **The element identifier is `sample`, and nothing in the source guarantees it is unique.** See §3 — it is the one place where the interface's shape rests on a property the source does not enforce.

**Topology (trunk and lanes).** `[` ] = `when:`-gated; `»` = reduction to a single job; `∅` = no outgoing data edge.

```
input_fasta ─┐                                   ┌─▶ TAXA_CLASS ────────┐ (tsv list)
input_protein├─▶ unpack ×4 ─▶ split/prep ─┬──────┼─▶ PROTEIN_ANNOT ─────┤
input_gbk   ─┘                            │      ├─▶ AMP  [run_amp]  ∅ ─┤
input_gff  ───────────────────────────────┘      ├─▶ ARG  [run_arg]  ∅ ─┼─▶ MULTIQC ─▶ report
        [run_bgc] seqkit min-len ─▶ ANNOTATION ×2┤                      │    ▲
        (long variant, second instance)          ├─▶ BGC  [run_bgc]  ∅ ─┘    │
        gff_type carry-forward ──────────────────┴─▶ CAZYME [cazyme]     ∅ ──┘
                                                 (versions YAML / summary / methods ┘── shim, §14)
```

**Inventory.** **82 named abstract nodes** (§4–§7, `N1`–`N82`): trunk 7, taxa 4, protein-annotation 5, AMP 17, ARG 24, BGC 19, CAZYME 5, report 1 — plus **12 placeholder transformations** (§13), **7 materialised merge points** (§9) and **11 step-level `when:` gates** (§10). The node count excludes the per-consumer emptiness filters that §8 accounts separately (18 sites; one is spelled out as N12, the other 17 are carried by P2), because repeating a filter at each consumer is not distinct work. It also excludes two blocks that look like nodes and are not: the split/reassemble cycle of §4.1, and the 3 literal-meta `combine`s of §11.

## 2. Operator translation, site by site

Classified with `nextflow-operators-to-galaxy-collection-recipes`' four labels. Counts are from a scripted scan of the 8 wiring files (`/tmp/gxy-scratch/dfcount.py`); "→ 0 nodes" means the operator's intent is realised by collection identity or by an optional input, not by a step.

| Nextflow construct | sites | Galaxy recipe | class |
|---|---|---|---|
| `ch_versions.mix(...)` | 70 | no node; provenance is per-job in Galaxy (§14) | channel-only → 0 nodes |
| data `.mix(...)` | 29 | union of identifier-aligned collections; `MERGE_COLLECTIONS` where materialised (§9) | channel-only, sometimes explicit step |
| `.join(...)` | 15 | multi-input map-over on matching identifiers (§5) | collection semantics → 0 nodes |
| `.multiMap{}` | 7 | consumer binds the one slot collection it wants (§5) | channel-only → 0 nodes |
| `.groupTuple()` | 6 | 5 → per-sample list-of-lists (real fan-in, §9); 1 (`by: 0`, versions) → 0 nodes | explicit step / review |
| `channel.empty()`, `[meta, []]` | 25 | **optional step input** (§6) | channel-only → 0 nodes |
| `.filter { … isEmpty() }` | 18 | filter-empty collection step, per consumer (§8) | explicit step |
| `Channel.fromPath(param).first()` | 11 (9 `.first()`) | workflow input, or the rebuild step in its place (§7) | channel-only |
| `.collect()` | 6 | `multiple=true` input → one job (§9) | collection reduction |
| `.combine(...)` | 6 | **3 literal-meta annotates → 0 nodes; 2 file cross-products; 1 value cross-product** (§11) | review |
| `.collectFile(...)` | 5 | concatenated dataset step, or a shim that has no producer (§14) | explicit step / review |
| `.transpose()` | 2 | 1 → per-collection mapping (§4); 1 (`arg.nf:87`) → flatten a nested axis | collection semantics |
| `.branch{}` | 3 | compressed/uncompressed (§4.2); preannotated/fastas (§6); versions `instanceof Path` (§14, review) | review |
| `.map{ new File(...) }` | 1 closure, 2 statements | **a tabular step**: append two `NA` columns (§7 F5) | explicit step (review trigger fired) |
| `channel.topic("versions")` | 1 | no Galaxy carrier (§14) | review |

`via[]` in the summary records operator names only, so `combine` cannot be told apart from `combine` without reading the site — hence the split above, and feedback entry `operator-via-records-no-arity-or-key-so-review-triggers-cannot-fire`.

## 3. Element identifiers

The procedure requires identifiers taken from source output names and checked against the source's own test rows.

- **Identifier = the `sample` column**, which nf-schema annotates `meta: ["id"]` (`assets/schema_input.json`), so `meta.id` throughout the sources and `{meta.id}_…` in every `ext.prefix` (`modules.config`: `${meta.id}_long`, `${meta.id}_cleaned.faa`). Snapshot evidence for the fixture rows: `tests/test_preannotated.nf.test.snap` asserts on `sample_1.txt`, `sample_2.txt`, `sample_3.txt`, `sample_1.align.daa.tsv`, `sample_1.normalized.tsv`, and `tests/*.snap` contains `sample_1_overview.tsv` / `sample_2_overview.tsv`. So the fixture sheet has **3 rows, ids `sample_1…sample_3`**, and the per-sample output names are `{id}_{suffix}` — no mate suffixes anywhere (funcscan takes contigs, not reads), so nothing here is a `paired` axis.
- **What makes an element unique — and the honest answer.** `sample` is the only candidate key, and the source does **not** require it to be unique: `uniqueItems: true` sits on the array of row objects (`schema_input.json`), so it rejects two *identical rows*, not two rows sharing a `sample`. Two rows with the same `sample` and different `fasta` pass nf-schema, are merged by `groupTuple()` (`funcscan.nf:84`), and then `files.find { … }` (`:86-89`) keeps only the **first** match per slot — silently discarding the rest. Galaxy `sample_sheet` element identifiers must be distinct, so this translation **tightens** the constraint: a sheet that launches in Nextflow today and quietly loses data becomes a validation error. Stated as a tightening, not a loss; the interface's prose help must say it. Ledger: `sample-column-uniqueness-assumed-not-enforced`.
- **`category` is a second axis, not an identifier.** `meta + [category: 'all'|'long']` (`funcscan.nf:70,108`) is a routing tag only; `meta.id` stays the bare sample id, and the filename prefix `${meta.id}_long` carries the distinction to the tool. §5 works through what that costs.
- **Sparse membership is the normal case, not an edge case.** In that same snapshot, `ampir` has files for 2 of 3 samples and dbCAN `*_overview.tsv` for 2 of 3. So per-stage collections legitimately have fewer elements than the input sheet, and per-tool collections fewer still (§9's arity problem).

## 4. Trunk stage A — unpack and slot preparation

Source: `funcscan.nf:69-100`.

| N | abstract node | input shape → output shape | needs a tool that | src |
|---|---|---|---|---|
| N1 | unpack FASTA sheet | `sample_sheet` → `list` (fasta), ids = `sample` | pass a gzipped dataset through or inflate it | `:69-77` |
| N2 | unpack protein sheet | same | same | `:69-77` |
| N3 | unpack GBK sheet | same | same | `:69-77` |
| N4 | unpack GFF sheet | same; `gff_type` column must survive | same | `:69-77` |

**4.1 `transpose` + `groupTuple` + extension sniffing → per-collection mapping.** The source flattens each row's four slots into four tagged events (`:70-71`), gunzips the compressed ones, then reassembles the row by `groupTuple()` and **filename-extension sniffing**: `files.find { it.toString().tokenize('.').last().matches('fasta|fas|fna|fa') }` (`:86`) plus `.endsWith('.faa')` / `matches('gff|gff3')` / `matches('gbk|gbff')`, with `[]` filling any slot not found (`:90-93`). Under four aligned collections, membership *is* the slot label: `sample_3 ∈ input_gbk` needs no extension test. **All of `:70-96` becomes four independent map-overs → zero reshape nodes.** Gain: the ambiguity of extension sniffing is gone (`.fasta` in both the FASTA and the protein column resolves cleanly by sheet). Loss: nothing, provided the sheets stay aligned (§6).

**4.2 The compressed/uncompressed `branch` (`:72-75`) has no Galaxy per-element equivalent.** `it[1].toString().endsWith('.gz')` routes one file at a time. Galaxy has no per-element branch, and whether a mapped tool step can consume a registered auto-compressed datatype (`fasta.gz`, `gff3.gz` — `nextflow-path-glob-to-galaxy-datatype` §Compression rules confirms they are legal datatypes) is a **per-tool** fact no packaged note carries. Three constructions:

| option | nodes | cost |
|---|---|---|
| **(recommended) one pass-through-or-inflate step per sheet, unconditional** | 4 | the wrapper must inflate-if-gzipped and otherwise copy; Galaxy-side this is a "transform or pass through" over files, and the corpus pattern of that name is about *values* — needs confirming at `advance-galaxy-draft-step` |
| restrict the four input columns to uncompressed types | 0 | user-visible interface change (phase 3's column patterns allow `(\.gz)?`); a user with `.fasta.gz` decompresses first |
| conditional per-element decompression | — | not available |

Recommendation: option 1, because it preserves the source's accepted input set and puts the complexity in a wrapper rather than in the user's form. Interface delta recorded in §17; ledger: `per-element-branch-has-no-galaxy-carrier`.

**4.3 Where the trunk's slot collections go.** After A there are four identifier-aligned `list`s (`prepared_fasta`, `prepared_protein`, `prepared_gbk`, `prepared_gff`) — the Galaxy spelling of `ch_intermediate_input`'s tuple, held as four collections rather than one five-wide tuple, matching interface §11's "several aligned `list`s rather than a `list:record`".

## 5. Trunk stage B — the long-contig variant and the `category` axis

Source: `funcscan.nf:104-137`; `modules.config:94-105`.

| N | abstract node | input → output | needs a tool that | src |
|---|---|---|---|---|
| N5 | keep contigs ≥ `bgc_mincontiglength` | `list` fasta → `list` fasta, same ids | selects sequence records by length (`seqkit seq --min-len`) | `:105`, `modules.config:106` |

N5 is gated `run_bgc_screening` and is the **only** node that axis needs; the hard part is that `ch_input_for_annotation` is then `fastas ∪ long-variant` (`:106-115`), i.e. the *same sample twice with the same id*, and the two copies must stay distinguishable because they are separated again downstream (`filter{meta.category != 'long'}` at `:140`, `== 'long'` at `:166`) and sent to **different consumers**: everything except BGC takes the full-FASTA copy, BGC takes the long copy, and both take the pre-annotated rows (`:154-174`). Galaxy cannot hold two elements with one identifier.

| option | how | cost | confidence |
|---|---|---|---|
| **(recommended) two ANNOTATION subworkflow instances** | instance "full" over `prepared_fasta`, gated by the annotation guard; instance "long" over N5's output, additionally gated by `run_bgc_screening`. Each carries its own four slot collections, both keyed by the plain sample id | costs a *step* (a subworkflow step invoked twice), not a body. Requires that gxformat2 allow the same subworkflow as two steps — unverified against the packaged notes; if it does not, fall back to (b) or duplicate the body | medium |
| (b) relabel the long copy `{sample}__long`, one instance | matches what the source already writes into the *filename* (`${meta.id}_long`) | the identifier is user-visible: every BGC per-sample output is keyed `sample__long`, so a strip-back relabel step is mandatory on every promoted BGC output (`relabel-via-rules-and-find-replace`) | medium |
| (c) `list:list` with outer axis = category | one ANNOTATION instance mapped over the inner axis | the outer axis has exactly one member when `run_bgc_screening` is false, so a boolean input would change every downstream collection *shape*, and the two streams overlap (pre-annotated rows belong to both) so no partition exists | low — recommend rejecting |

Also in this range: `SEQKIT_SEQ_LENGTH`'s own emptiness guard (`:109-114`) drops samples with **no** long contigs, with a `log.warn`. So a sample can legitimately be absent from the BGC lane while present everywhere else; §8 treats the mechanism, and it is a test-plan fact (a 3-sample fixture may yield a 2-sample BGC lane).

## 6. Trunk stage C — pre-annotated rows, and "optional input"

Source: `funcscan.nf:97-100, 139-161, 224-228`.

| N | abstract node | input → output | notes |
|---|---|---|---|
| N6 | split rows that arrived annotated | `list` → `list` (subset) | membership test, not file inspection |
| N7 | split rows that need annotation | complement of N6 | — |

- **The predicate is derivable from membership.** `branch { preannotated: gff != [] \|\| gbk != [] ; fastas: true }` (`:97-100`) asks whether a slot was filled. Because nf-schema's `dependentRequired` couples `gff → protein → gbk`, in practice `preannotated ⟺ sample ∈ input_gbk`. Implement it as the union of the GBK and GFF sheets (`filter-by-list`), which is faithful even if the coupling is not enforced on the Galaxy side (interface §2.1 already logged that the coupling cannot be expressed across four collections). `fastas: true` is the fall-through arm, so it is the complement of N6 — not "every row", which is the trap in reading that line alone.
- **`channel.empty()` and `[meta, []]` mean "optional input".** 25 sites. Two shapes: a lane's input set to empty (`ch_taxonomy_tsv = channel.empty()` at `:193`, `ch_interproscan_tsv = faas.map{ [meta,[]] }` at `:225-227`), and an unused tool slot (`ARG(fastas, [], tsvs)` at `:281`, `MMSEQS_CREATETSV(db, [[:],[]], db)` at `taxa_class.nf:54`, `PROKKA(fasta, [], [])`, `ANTISMASH_ANTISMASH(gbks, db, [])`). In Galaxy each is **an optional input on the consuming step**, and the else-arm that fabricates an empty-dataset-per-sample stream becomes **zero nodes**. Consequence to carry into the template: the AMP subworkflow's `tsvs` (taxonomy) and `tsvs_interpro` inputs, and ARG's `annotations` input, must be *optional* typed inputs, because three of the four arms hand them nothing.
- **The `meta + [gff_type: 'prodigal']` mutation (`:143-149`) is a sample-sheet column carry-forward.** It stamps newly-annotated samples with `gff_type = 'prodigal'` ("dbcan does not distinguish pyrodigal and prodigal", per the source comment) so that `RUNDBCAN_EASYCGC`/`EASYSUBSTRATE` can take `val(gff_type)` per element; pre-annotated samples bring their own `gff_type` from the input sheet. Because `column_definitions` and `columns` do **not** propagate through map-over (`galaxy-sample-sheet-collections`, "carry-forward must be explicit … `__SAMPLE_SHEET_TO_TABULAR__` or rules DSL `add_column_from_sample_sheet_index``), the GFF collection feeding CAZYME needs a **column re-attachment step** whose value depends on which stream the sample came from — constant for annotated rows, sheet-sourced for pre-annotated rows. Two producers, one target column: placeholder **P7** (§13), confidence medium on the mechanism (named recipe, page not packaged) and high that the requirement is real (`cazyme.nf:44` drops a sample whose `meta.gff_type` is missing).

## 7. Lanes

`when:` expressions are written as `$(inputs.…)` terms so the template can lift them; `guard(X)` = the X column of the interface's input list.

**7.1 TAXA_CLASS** — gate `run_taxa_classification`. Source `taxa_class.nf`.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N8 | resolve mmseqs reference DB | *input* `mmseqs_db` **or** download step → single `File` | download+unpack a named mmseqs DB from `mmseqs_db_id` | `:25-33` |
| N9 | build per-sample query DB | `list` fasta → `list` **directory** | `mmseqs createdb` | `:37` |
| N10 | assign taxonomy | N9 `list` + N8 global → `list` directory | search + LCA against the reference DB | `:41` |
| N11 | per-sample TSV | N10 + N9 (aligned) → `list` tabular | dump hit table | `:46-56` |

N8 is the recurring **DB-or-rebuild fork** (11 `reference_rebuilds[]`, 9 `.first()` sites) — a `pick_value` over {workflow input, gated builder step} with the builder gated on "input is empty". `join`+`multiMap` at `:46-51` → 0 nodes (two aligned collections). N9/N10 outputs are **directories**: open question §19.

**7.2 PROTEIN_ANNOTATION** — gate `run_protein_annotation`. Source `protein_annotation.nf`.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N12 | drop empty FAA elements | `list` → `list` (subset) | — (collection filter) | `funcscan.nf:200-205` |
| N13 | strip gap characters | `list` faa → `list` faa | remove `*`, whitespace, tab and `.` residues from protein records (`--gap-letters '* \t.' --remove-gaps`) | `:207`, `modules.config:107-118` |
| N14 | resolve InterProScan DB | input **or** download pinned URL → `File` | fetch+unpack the pinned `interproscan-5.72-103.0` tarball | `:22-30` |
| N15 | InterProScan | `list` faa + N14 → `list` tsv (+xml/gff3/json) | domain/family search over proteins | `:32` |
| N16 | **pad two `NA` columns** | `list` tabular → `list` tabular | append two constant trailing columns to every row | `:37-44` |

N16 is the one **Groovy closure that rewrites file bytes** in the pipeline (`new File(tsv).readLines().collect { (line.split('\t') + ['NA','NA']).join('\t') }`), present because "INTERPROSCAN 5.72-103.0 only includes 13 columns and not 15 which ampcombi expects" (source comment, `:36`). The recipes note lists exactly this as a review trigger, and it is invisible in the summary: it is subworkflow Groovy, not a process, so no `script_excerpt` carries it. Class **explicit Galaxy step** — tabular (`tabular-compute-new-column` / `column_maker` is the nearest named recipe), mapped over the sample list. **Naming note for the template:** `SEQKIT_SEQ_FILTER` is *not* an emptiness filter (N13) despite its name, and this section's names should record effects, not the source's labels.

**7.3 AMP** — gate `run_amp_screening`. Source `amp.nf`; takes fastas, faas, tsvs, gbks, tsvs_interpro.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N17 | AMPlify predict | `list` faa → `list` tsv | AMP prediction from protein seqs | `:44-47` |
| N18 | MACREL contigs | `list` fasta → `list` gz(2) | AMP/orf discovery from contigs | `:52-53` |
| N19, N20 | unpack MACREL prediction / ORFs | `list` gz → `list` | inflate | `:54-55` |
| N21 | AMPIR | `list` faa → `list` tsv | AMP inference, model+minlength | `:65` |
| N22 | HMM models → identified list | `multiple: true` upload → `list`, ids = filename minus `.hmm[.gz]` | — (identifier derivation) | `:79-83` |
| N23 | hmmsearch, **sample × model** | `list` faa × N22 → `list:list` | profile search, optional alignment/target/domain tables | `:85-94` |
| N24 | unpack hmmsearch output | `list:list` → `list:list` | inflate | `:96` |
| N25 | **drop the model axis** | `list:list` → `list`, ids = sample | — (flatten after fan-out) | `:98-100` |
| N26 | **gather per-sample hit tables** | up to 4 sibling `list`s → `list:list` (sample × tool) | — (see §9) | `:105-115` |
| N27 | resolve AMPcombi DB | input **or** download by `amp_ampcombi_db_id` → `File` | fetch DRAMP/APD/UniRef100 | `:118-126` |
| N28 | AMPcombi2 parsetables | N26 + faa(s) + gbk(s) + interpro(s) per sample → `list` tsv | collate + DB-hit | `:119-125` |
| N29 | AMPcombi2 complete | `»` all N28 tsvs → single tsv | merge per-sample tables | `:137` |
| N30 | keep table only if it has data rows | single tsv → single tsv or absent | — (row-count test, §12) | `:138` |
| N31 | AMPcombi2 cluster | N29 → single tsv | cluster AMP sequences | `:143` |
| N32 | merge taxonomy | N31 + taxa TSV list `»` → single tsv | join taxonomy into the summary rows | `:156` |
| N33 | bgzip the merged summary | single tsv → single `tabular.gz` | compress, name `…summary_taxonomy` | `:159-162` |

N26 is the workflow's hardest shape (§9). N22's identifier derivation is free in Galaxy *if* a `multiple: true` upload names elements from filenames — marked medium, verify at implementation.

**7.4 ARG** — gate `run_arg_screening`. Source `arg.nf`; five lanes, each `tool → hAMRonization`, three of them also `→ argnorm`.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N34, N35 | AMRFinderPlus DB / run | input or update step; `list` fasta → `list` report | NMCR-AMR gene search | `:40-52` |
| N36, N37 | fARGene classes → axis; run | comma string from `arg_fargene_hmmmodel` → **tool parameter**, not a collection; `list` fasta → `list` | HMM-class AMP/ARG search | `:68-82` |
| N38 | unpack fARGene class axis | `list:list` → `list` (per sample) | — (`transpose()`) | `:87` |
| N39, N40, N41 | CARD: untar / annotate / resolve | hard-coded `https://card.mcmaster.ca/latest/data` or the user's DB → `File` | unpack CARD; build the processed CARD | `:95-117` |
| N42 | RGI | `list` fasta + N41 → `list` tsv | ARG search (mode from `arg_rgi_data`) | `:119` |
| N43, N44 | DeepARG DB / predict | input or download; `list` faa + model → `list` tsv(2) | ARG classification | `:129-152` |
| N45, N46 | ABRicate DB dir / run | optional override dir; `list` fasta → `list` report | blast-vs-DB AMR screen | `:172-173` |
| N47-N51 | hAMRonization ×5 (amrfinderplus, fargene, rgi, deeparg, abricate) | each lane's report `list` → harmonised tsv `list` | map tool columns onto the hAMRonized schema | `:55,87,123,159,176` |
| N52-N54 | argnorm ×3 (amrfinderplus, deeparg, abricate) | empty-guarded harmonised tsv → normalised tsv | normalise ARG names/coverage | `:60-61,164-165,181-182` |
| N55 | hAMRonization **summarize** | `»` all N47-N51 tsvs across tools **and** samples → single tsv | concatenate harmonised tables | `:187-194` |
| N56, N57 | merge taxonomy; bgzip | N55 + taxa list `»` → single tsv → `tabular.gz` | join taxonomy; compress | `:200-208` |

`arg.nf:180` makes N54 conditional on `arg_abricate_db_id ∈ {ncbi, resfinder, argannot, megares}` — a gate on an *input value*, so expressible as `when:`. That is also the case interface §4 flagged as "a `select` loses the free-string case": if the input is free text, the `when:` needs the enum membership test, and a non-list value silently skips argnorm (as it does in the source).

**7.5 BGC** — gate `run_bgc_screening`; **only lane fed by stage B's long variant**. Source `bgc.nf`.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N58, N59, N60 | antiSMASH DB: untar `.tar.gz` / use directory / download — three arms, one `File` | one `File` | unpack; fetch | `:39-50` |
| N61 | antiSMASH | `list` gbk + N58-60 → `list` (gbk_results, gbk_input dir, zip/html/json) | BGC detection+sidenote annotation | `:52` |
| N62 | gather antiSMASH per-sample files | 2 ports → `list:list` per sample | — (`mix`+`groupTuple`+flatten) | `:55-60` |
| N63, N64 | DeepBGC DB / pipeline | input or download; `list` gbk → `list` tsv/gbk/png | BGC classification | `:75-88` |
| N65 | GECCO run | `list` gbk → `list` gbk+clusters | BGC prediction | `:93-99` |
| N66 | GECCO gather | 2 ports → `list:list` | — | `:100-105` |
| N67 | GECCO convert | N65 clusters+gbk (joined) → `list` | reformat clusters (`convertmode`/`convertformat`) | `:109-116` |
| N68 | **select Big-SCRY input** | up to 2 producers → `list` | — (3-arm input select, `pick_value` cascade) | `:125-133` |
| N69 | pool all BGC gbk **across samples** | `»` → single multi-file job input | — (flatten + collect) | `:135-138` |
| N70, N71 | Big-SCRY DB / run | input or download; N69 → single output | align BGCs to MIBiG | `:140-148` |
| N72 | BGC hmmsearch | `list` faa × models (same cross-product as AMP N23) | profile search | `:152-177` |
| N73 | comBGC | `list:list` per sample → `list` tsv | merge BGC calls per sample | `:191` |
| N74 | concatenate comBGC tables | `list` tsv → single tsv (`keepHeader`) | row-append with one header | `:196/199` |
| N75, N76 | merge taxonomy; bgzip | N74 + taxa list `»` → single tsv → `tabular.gz` | join; compress | `:205-212` |

**Dead wiring, deliberately not translated:** `bgc.nf:182-189` joins `ch_bgcresults_for_combgc` to `fastas` with `remainder: true` and filters it to emit a `log.warn` — **the resulting channel is never read**, and `COMBGC` is called on the unfiltered channel (`:191`). Zero nodes, and the "no BGC hits for sample X" notice has nowhere to go (§8). Two more `remainder: false` joins at `:64-65` are ordinary inner joins; `remainder` is one of the operator parameters the summary does not record.

**7.6 CAZYME** — gate `run_cazyme_screening`; **no emits at all**. Source `cazyme.nf`.

| N | node | input → output | tool must | src |
|---|---|---|---|---|
| N77 | dbCAN DB | input **or** download → `File` | fetch dbCAN HMM sets | `:24-33` |
| N78 | dbCAN annotation | `list` faa + N77 → `list` tsv | HMM-substrate assignment | `:37` |
| N79 | drop rows lacking gff/gff_type | joined `list` → subset | — (metadata-presence filter) | `:43-49` |
| N80 | EasyCGC | faa `list` + gff `list`(+`gff_type`) + N77 → `list` overview tsv + cgc gff | CGC calling | `:57-61` |
| N81 | EasySubstrate | same inputs → `list` | substrate annotation | `:67-71` |

N79 is a per-element filter on **metadata**, not content (`!gff || !meta.gff_type`, warn-and-skip) → class explicit step / review; it depends on P7 having run.

## 8. Emptiness: three states, eighteen filters, and the lost warnings

The source distinguishes three things Galaxy collapses:

| state | Nextflow spelling | count | Galaxy spelling |
|---|---|---|---|
| slot not supplied | `[]`, tested as `file != []` | guards at 15 sites | **element absent** from that collection |
| file present, zero content | `file.isEmpty()`, i.e. `Path.isEmpty()` | same 18 `.filter` sites | element whose dataset is 0 bytes → filter-empty step |
| file present, no *records* | `tsv.countLines() > 1` (`amp.nf:138`) | 1 | a header-only dataset — **not** caught by filter-empty |

Each of the 18 filters is *per consumer* and re-warns per consumer (`faas` before InterProScan, before AMP, before ARG, before BGC, before CAZYME; `gbks` before AMP and BGC; taxonomy tsvs before AMP/ARG/BGC; harmonised tsvs before argnorm). Faithfully that is **18 filter steps**, not one shared one — the same collection is filtered differently depending on who consumes it, and the source's comments say so ("When adding new tool that requires FAA, make sure to update conditions in funcscan.nf", `amp.nf:33-35`, `bgc.nf:32`, `cazyme.nf:17-19`). The corpus recipe is `collection-cleanup-after-mapover-failure`; the third state has no named recipe.

**What is lost with each:** 23 `log.warn` sites, all of the form "sample X produced an empty Y, so stage Z will not run for it". Galaxy has no user-visible per-element skip notice, so a sample missing from one lane's output is unexplained. This is a real usability loss, not cosmetic — it is how the source explains a partial result. Recommendation: the template should not try to reconstruct the warnings; the test plan should assert lane membership per lane, and §19 carries "explain-absent-sample" as an open question. Ledger: `per-element-skip-warnings-have-no-galaxy-surface`.

## 9. Fan-in and reduction — the arity problem, stated plainly

Six `groupTuple`, six `.collect()`, and 29 data `.mix` sites concentrate into seven materialised merge points. Four of them combine **optionally-gated contributors**, so the number of inputs varies with the shape-control inputs:

| # | merge | contributors | arity | downstream consumption |
|---|---|---|---|---|
| M1 | AMP hits → AMPcombi (`amp.nf:105`) | AMPlify, MACREL-pred, AMPIR, hmmsearch(flattened) | 1–4 | per-sample **list** (multiple files per job) |
| M2 | ARG harmonised → summarize (`arg.nf:187-192`) | up to 5 tool lanes, each × N samples | 1–5, ×samples | `»` one job |
| M3 | BGC calls → comBGC (`bgc.nf:70,88,106,182`) | antiSMASH, DeepBGC, GECCO | 1–3 | per-sample list |
| M4 | Big-SCRY input (`bgc.nf:125-138`) | antiSMASH gbk_results, GECCO-convert | 1–2 | `»` one job |
| M5 | MACREL ORFs into AMP's faa (`amp.nf:60`) | faa, macrel orfs | 1–2 | per-sample union |
| M6 | MultiQC input (`funcscan.nf:441`) | versions shim, workflow summary, methods description, ANNOTATION QC files | 3–4 | `»` one job |
| M7 | taxa list for the three `merge_taxonomy_*` | one collection, meta dropped | 1 | `»` one job per table |

**Why M1/M3 are hard.** The natural Galaxy primitive for "for each sample, the files these N tools produced" is a zip or an Apply-Rules build — and both assume a **fixed** input count. Galaxy `when:`-skipped steps yield typed-null outputs, and a zip over a skipped collection is not attested anywhere in the packaged notes. The source, by contrast, gets variable arity for free: a skipped tool's channel stays `channel.empty()` and `groupTuple` simply sees fewer files. Three candidate constructions, all named in `galaxy-collection-patterns`:

1. **(recommended)** relabel each contributor's elements `{sample}__{tool}` (`relabel-via-rules-and-find-replace`) → `__MERGE_COLLECTIONS__` (concatenation of collections, which tolerates a skipped input far better than a zip) → split the compound identifier into two axes (`collection-split-identifier-via-rules`) → `list:list` (sample × tool) for the `multiple=true` per-sample input. Four placeholder steps per merge, ×2 (M1, M3) = 8.
2. `__APPLY_RULES__` with `zip` over all contributors and `when:`-tolerant nulls — cleanest if it tolerates skips; untested.
3. Give AMPcombi/comBGC a `multiple=true` input and **feed the merged flat `list` without the sample axis**, only if the wrapped tool re-derives sample identity from filenames. It does in the source (`ext.prefix = ${meta.id}_…`), so this may work for comBGC; it cannot work for AMPcombi, which also needs per-sample faa/gbk/interpro alignment.

Confidence **low** on all three, because the pattern pages that carry the construction details are not in this bundle (§18). This is the single item I most want `compare-against-iwc-exemplar` to settle by citation: a corpus workflow that gathers N optionally-produced collections per sample. Ledger: `variable-arity-fan-in-has-no-attested-galaxy-recipe`.

**M2/M4/M6/M7 are easy and attested** — "Collection reduction" / `collect()` → `multiple=true` input, High confidence in `nextflow-to-galaxy-channel-shape-mapping`; `__FLATTEN__` for the meta-dropping `.map { it[1] }` idiom. Note M2 and M4 cross the **sample** axis, not just the tool axis: one hAMRonization-summarize job and one Big-SCRY job for the whole run, so a Galaxy test cannot assert per-sample on those two tables (§3 of interface's testability list already implies it; this is the mechanism).

**Identifier discipline for nested dot-product.** N28 consumes four `list:list` collections (sample × {hits | faa | gbk | interpro}) in one invocation. `galaxy-sample-sheet-collections` attests dot-product between two *identically structured* sample sheets; a four-way dot-product over **nested** collections is beyond what any packaged note states. Flagged as low confidence and as an open question — it decides whether AMPcombi is one step or four.

## 10. Parameter conditionals → `when:` gates

All 13 `workflow.conditionals[]` rows are guards over inputs, so all 13 are expressible in `when:` — but the pipeline needs **11 step-level gates, not 13**, and two of those 11 come from source lines the summary never recorded. Row by row (source lines verified against `workflows/funcscan.nf`; the taxa-positive arms are `else if` on their own line, `:253/:299/:354`):

| # | summary guard | src | becomes |
|---|---|---|---|
| 1 | `run_bgc_screening` → SEQKIT_SEQ_LENGTH | `:104` | gate on N5 |
| 2 | `(run_arg && !arg_skip_deeparg) \|\| run_amp \|\| run_bgc \|\| run_cazyme` → ANNOTATION | `:126` | gate on **both** ANNOTATION instances (§5) |
| 3 | `run_taxa_classification` → TAXA_CLASS | `:183` | gate on N8–N11 |
| 4 | `run_protein_annotation` → SEQKIT_SEQ_FILTER, PROTEIN_ANNOTATION | `:199` | gate on N12–N16 |
| 5, 6 | `run_amp && !taxa` / `&& taxa` → AMP | `:238` / `:253` | **1** gate on `run_amp` |
| 7, 8 | `run_arg && !taxa` / `&& taxa` → ARG | `:277` / `:299` | **1** gate on `run_arg` |
| 9 | `arg_skip_deeparg` → ARG | `:278` / `:300` | **0** gates (dissolves, below) |
| 10, 11 | `run_bgc && !taxa` / `&& taxa` → BGC | `:335` / `:354` | **1** gate on `run_bgc` |
| 12 | `run_cazyme_screening` → CAZYME | `:382` | gate on N77–N81 |
| 13 | wide ANNOTATION guard → ANNOTATION | `:436` | gate on the ANNOTATION→MultiQC edge (§14) |
| — | *not in the summary*: gff_type stamp | `:143` | gate on the P7 constant-producer |
| — | *not in the summary*: long-input channel | `:163` | gate on the BGC-input wiring |

Two rows collapse twice over (rows 5/6, 7/8, 10/11 → 3 gates, saving 3), one row dissolves entirely (row 9), giving 13 → 9 gates, plus the two unrecorded source guards = **11**. The inner `!arg_skip_*` / `!bgc_skip_*` / `!amp_skip_*` / `dbcan_skip_*` lane gates and the 11 DB-or-rebuild forks sit *inside* the lanes and are not part of `workflow.conditionals[]`; they are enumerated in §7 and are additional gates.

- **Why rows 5/6, 7/8, 10/11 collapse.** The two arms are the same subworkflow call with the same arguments, differing only in whether the taxonomy input carries an extra emptiness filter. Galaxy: one `when: $(inputs.run_amp_screening)` step whose optional taxa input is P2-filtered. Interface §5's "run_taxa_classification forks every screening branch into a `<X>`/`<X>+taxonomy` pair" is an artefact of reading `if`/`else if` pairs as branches; the fork is real **only** for the three `merge_taxonomy_*` steps (`amp.nf:150-164`, `arg.nf:198-209`, `bgc.nf:203-214`), for comBGC's `collectFile` `storeDir`, and for which table the promoted summary label binds to (§15).
- **Why row 9 dissolves.** `params.arg_skip_deeparg` as a top-level guard (`:278,300`) is the **"pass an empty channel to skip inner work"** idiom: `ARG(fastas, [], tsvs)`. Galaxy does not need it — the ARG body already gates each lane on its own `arg_skip_*` (`arg.nf:40,50,67,93,129,140,171`), and interface §5 exposes all 16 toggles. So this row becomes **0 gates** and the corresponding ARG input becomes optional (§6). Keeping both the empty-collection trick *and* the inner gates would double-gate the same thing.
- **Why the two unrecorded guards still need gates.** `:143` decides whether `gff_type = 'prodigal'` is stamped onto newly-annotated samples, and `:163` decides whether the long-contig input channel exists at all. Neither is dropped by the summary by accident: `conditionals[].affects[]` is a list of **process** names, and both guards affect a channel and a metadata field rather than invoking a process, so there is nothing to attribute them to and no warning is emitted. A reader working from `summary-nextflow.json` alone would translate neither. Feedback: `conditionals-detector-attributes-only-to-processes-so-channel-guards-vanish`.

**Two ANNOTATION guards, not one.** `:126` decides whether ANNOTATION runs at all; `:436` decides whether its MultiQC files reach the report, with a *wider* AMP clause (`amp_run_hmmsearch || !amp_skip_amplify || !amp_skip_ampir`). The template must not reuse one expression for both.

## 11. Cross-product fan-outs — two of them, resolved differently

| site | what it crosses | Galaxy resolution |
|---|---|---|
| `amp.nf:86`, `bgc.nf:168` | `list` faa × **HMM model files** (uploaded list) | a genuine second collection axis: every sample × every model. `list:list` via Apply Rules, or a two-level map-over. Results are then flattened back onto the sample axis (N25). Confidence low — the recipes note says unkeyed `combine` has little corpus uptake and prefers review |
| `arg.nf:71` | `list` fasta × **10 class names from a comma-joined string param** | **not a collection axis.** The values come from `params.arg_fargene_hmmmodel.tokenize(',')`, and interface §4 already exposes that as a `select multiple` input. Galaxy: one fARGene step per sample whose tool parameter carries the selected classes; the per-(sample,class) jobs the source creates collapse into one job per sample, and the `.transpose()` at `:87` (which exists only to undo the fan-out) becomes 0 nodes. Confidence medium-high |

That difference is why the operator-name-only `via[]` list matters (§2): both are `.combine(`, and only the second one is free.

**Literal-meta `combine` (3 sites: `amp.nf:159`, `arg.nf:204`, `bgc.nf:209`).** `channel.of(['id': 'hamronization_combined_report']).combine(<one dataset>)` just names a single dataset so a bgzip step can prefix it. In Galaxy: the step's own output naming, or a rename — **0 nodes**, and a warning to the template not to read these as fan-outs.

## 12. Gates over derived values — the class `when:` cannot state

Five guards read data or input *shape* rather than an input value. Each is listed with the closest corpus construction and exactly what that construction cannot do.

| site | guard | nearest construction | gap |
|---|---|---|---|
| `amp.nf:133` | `ch_summary_count == 0 \|\| == 1` — file count of AMPcombi parsetables outputs, gating N29, N31, and the taxa merge | `conditional-gate-on-nonempty-result` (corpus-backed, "four shim steps", verified against Galaxy `release_25.1`) | the shim derives **emptiness** (0 vs ≥1). The source's threshold is **≤1**, i.e. "one table is also useless" — not expressible by that shim |
| `amp.nf:138` | `tsv.countLines() > 1` on one dataset (header-only ⇒ skip clustering) | filter-empty | a header-only TSV is not empty; needs a row-count test feeding a gate |
| `bgc.nf:39` | uploaded antiSMASH DB `.extension == 'gz'` vs `.isDirectory()` → untar / use / download | three-way producer select | Galaxy cannot gate on an input dataset's datatype or "is a directory" through `when:`; **the shape choice must be made at authoring time**, so §17 forces it |
| `arg.nf:109` | `!rgi_db.contains("card_database_processed")` — a **substring of the uploaded file's name** decides whether CARD gets processed | same | same; also untestable if Galaxy renames on upload |
| `cazyme.nf:44` | `!gff \|\| !meta.gff_type` | filter-by-column-value over the sheet's tabular form | per-element, so it is a filter step (N79), not a gate — fine once P7 exists |

The first two are the ones a reviewer should look at, because they encode *scientific* skip logic ("no hits ⇒ don't cluster"), not plumbing. Any of them could instead be handled by making the tool tolerate empty input and always running the step — cheaper, and it changes the source's behaviour (antiSMASH-style tools do fail on empty input, so not universally available). Recommendation: model N29/N31 as **ungated** steps whose wrapper tolerates an empty/1-row input, and record the divergence; keep the ≤1 test as a ledger obligation rather than inventing a shim whose attested form cannot express the threshold. Ledger: `data-derived-gate-needs-nonemptiness-threshold`, `input-datatype-cannot-gate-a-step`.

**And the derived-boolean problem, once.** The ANNOTATION tool-choice guard (`annotation.nf:29`) is an OR over **six** inputs, including a *silent override* of the user's `annotation_tool` value with a `log.warn` (`:32-37`: "Switching annotation tool to: Pyrodigal … GBK format is incompatible with antiSMASH, DeepBGC, and GECCO"). `galaxy-conditionals-patterns` gives the corpus idiom `when: $(inputs.when)` — a boolean that arrives as a **workflow input** — and the note that defines `when:` describes it as an expression over **workflow inputs**; nothing here says whether a `when:` may reference another step's output. Under that reading the derived boolean must be re-typed verbatim on every gated step: 6 pyrodigal steps (2 compute + 4 gunzip) carry it and 6 prodigal steps carry its negation conjoined with `annotation_tool == "prodigal"`, i.e. **12 `when:` strings per ANNOTATION instance, 24 across the two instances of §5** — and only 8 distinct expressions, since the source's other two arms are plain equality guards (`:55` prokka, `:74` bakta, plus the `:75` DB-build fork). Counted across the whole workflow the same reading costs roughly 26 step-level `when:` strings and 12 distinct expressions: 24 in the two ANNOTATION instances, the 11 gates of §10 (one per gated step, the seqkit node sharing the long-ANNOTATION expression), and ~1 behind pick_value. Both figures are a *cost estimate, not a correctness argument* — they are what the no-derived-gate reading would force, and if §19.3 comes back "step outputs are legal in `when:`", one shared upstream boolean collapses all 24 to 12 references to one value. A cheap alternative that dodges the question entirely: hoist the tool-selection override into the **interface** (an enumerated `annotation_tool` whose `prodigal` option is dropped, or whose help states that prodigal runs as pyrodigal when BGC/AMP screening is on) so no gate has to encode the derived test at all — that is an interface delta (§17.7) and the source's `log.warn` announcing the override is then lost, which is the same loss §8 already records for 23 other warnings. Feedback: `conditionals-note-gives-no-construction-for-a-derived-gate`.

## 13. Placeholder transformations

Shape/semantics steps the data flow says are necessary; the template materialises them and `advance-galaxy-draft-step` picks the built-in. Named recipes come from the collection/conditionals/tabular MOCs; **every one carries "page not packaged" confidence** (§18), which is why the column is *named recipe*, not *verified construction*.

| P | transformation | shape in → out | named recipe | needed by |
|---|---|---|---|---|
| P1 | element-identifier sync across the four input sheets | 4 sheets, possibly disjoint → aligned subsets | `sync-collections-by-identifier` | every multi-slot consumer (N28, N61, N73, N80…) |
| P2 | filter-empty per consumer (18×) | `list` → subset `list` | `collection-cleanup-after-mapover-failure` | §8 |
| P3 | relabel with a tool tag | `list` → `list`, ids `{sample}__{tool}` | `relabel-via-rules-and-find-replace` | M1, M3 |
| P4 | concatenate collections of same-key elements | n × `list` → flat `list` | `__MERGE_COLLECTIONS__` | M1, M3, M6 |
| P5 | split compound identifier into two axes | flat `list` → `list:list` (sample × tool) | `collection-split-identifier-via-rules` | M1, M3, N23 |
| P6 | drop an axis | `list:list` → `list` | `collection-flatten-after-fanout` | N25, N38, M7 |
| P7 | re-attach `gff_type` after map-over | `list` gff + (constant ∪ sheet column) → `sample_sheet`-with-column | `add_column_from_sample_sheet_index` / `__SAMPLE_SHEET_TO_TABULAR__` | N80, N81, N79 |
| P8 | build the pooled-across-samples input | `list` → one multi-file bundle | `collection-build-named-bundle` | M2, M4 |
| P9 | collection of tables → one table (keep one header) | `list` tsv → single tsv | `tabular-concatenate-collection-to-table` | N74 (`keepHeader: true`) |
| P10 | strip a `{sample}__long`-style suffix from promoted outputs | `list` → `list` | `regex-relabel-via-tabular` | only if §5 option (b) is taken |
| P11 | gate on collection emptiness / row count | collection or dataset → boolean | `conditional-gate-on-nonempty-result` | §12 rows 1–2; **cannot express ≤1** |
| P12 | singleton wrap of the merged summary tables | single dataset → named element | `collection-unbox-singleton` (inverse use) | N33, N57, N76 output naming |

## 14. Versions and MultiQC plumbing — where this brief says *no*

- **70 `ch_versions.mix(…)` sites → zero nodes.** Each nf-core module emits `versions.yml` and the pipeline concatenates them through `softwareVersionsToYAML(...).mix(topic_versions_string).collectFile(storeDir: "…/pipeline_info", name: 'nf_core_funcscan_software_mqc_versions.yml', sort: true, newLine: true)` (`:414-421`). In Galaxy versions are known **per job**, and there is no workflow-level versions channel; no packaged note describes a Galaxy carrier. So **interface §10.2's promoted `versions` output has no producer node as specified** — an interface delta (§17), not something the template can wire.
- **`channel.topic("versions").distinct().branch { versions_file: entry instanceof Path ; versions_tuple: true }` (`:397-402`)** mixes two *kinds* of value in one channel — file paths from module emissions and `(process, tool, version)` triples from other helpers — and routes them by `instanceof`. Galaxy has no heterogeneous channel to split, and the distinction only exists because the Nextflow helper accepts both. 0 nodes; recorded so nobody tries.
- **`paramsSummaryMap(workflow, parameters_schema: …)` → `paramsSummaryMultiqc(…)` → `collectFile('workflow_summary_mqc.yaml')`** (`:427-429`) and **`methodsDescriptionText(…)` → `collectFile('methods_description_mqc.yaml')`** (`:430-434`) are nf-schema/plugin **functions over the live workflow object**, not steps. Galaxy would need a step that knows the resolved parameter set and run metadata. Same class of problem as the versions YAML.
- **What the MultiQC report actually contains** — verified, because it changes the test plan: `ch_multiqc_files` starts empty (`:60`) and receives exactly four things — the collated versions YAML (`:426`), `workflow_summary_mqc.yaml` (`:429`), `methods_description_mqc.yaml` (`:434`), and conditionally `ANNOTATION.out.multiqc_files` (`:437`, Prokka/Bakta `*_mqc.txt`, under the *wider* `:436` guard). **No per-tool `multiqc` output port is collected anywhere else**: `grep -n "\.out\.multiqc" workflows/funcscan.nf` returns that one line, and of the seven local subworkflows only `annotation.nf` mentions multiqc at all — AMP, ARG, BGC, CAZYME, taxa and protein-annotation emit no QC fragment to collect. So `multiqc_report.html` is: software versions + parameter summary + methods text + Prokka/Bakta stats, and nothing about AMP/ARG/BGC/CAZYME/taxa results. Its only parameter is `--title` from `multiqc_title` (`modules.config:21-28`). Interface §10.3's refusal to judge a run by this report is right, and now the reason is concrete: **there is almost nothing in it.** Phase 9 must not treat it as a scientific checkpoint, and N82 (the MULTIQC step) is worth keeping mainly because the source emits it and users expect it.
- **N82** = MultiQC: input `list` of report fragments (`multiple=true`) + config (bundled in the wrapper, interface §7) + optional logo + title → single `html`. Class: collection reduction, high confidence.

## 15. Workflow inputs and outputs, from the data-flow side

**Inputs** are interface's 61; nothing here adds one, and §17 lists the three that changed shape. Data-flow requirements on them: `input_gff`'s `gff_type` must be reachable at N80/N81 (P7); `input_gbk` and `input_gff` are the *only* evidence for N6's membership test; the 15 optional DB inputs each own a P-fork at the head of a lane (11 rebuilds), so **each must be an input to a `pick_value` step, not directly to the tool step**, or the rebuild step cannot be bypassed; `bgc_mincontiglength` is not in interface's 61 and is needed by N5 — see §17.

**Outputs** — the promoted set is interface §10.2; what this phase adds is the *binding*:

| output | binds to node | note |
|---|---|---|
| `multiqc_report` | N82 | see §14 for what it proves |
| `versions` | — | **no node produces it** (§14, §17) |
| `amp_summary_table`, `amp_cluster_table` | N29, N31 | N31 may be skipped by §12's gate |
| `arg_hamronization_table` | N57 when `run_taxa_classification`, else N55 | two producers, confirmed at `arg.nf:194` vs `:204-208` — interface §10.1(3) |
| `bgc_combgc_table` | N75 when taxa on, else N74 | same shape of problem |
| `cazyme_overview`, `cazyme_cgc` | N80 | CAZYME has no emits; these are the only route out |
| `taxa_taxonomy_table` | N11 | |
| `interproscan_table` | **N16, not N15** | the pipeline hands AMP the *padded* table (`protein_annotation.nf:51` emits `ch_interproscan_tsv_modified`); promoting N15 would publish a table AMPcombi rejects |
| `annotation_result` | N28-adjacent pick_value ports | unresolved per interface §10.4(1); per-port pick_values are the merge points, so one label per producer port is the only shape that binds |
| `input_unpacked` (optional) | N1-N4 | interface §10.3; source deliberately does not publish gunzip |

## 16. Confidence

| claim | conf | basis |
|---|---|---|
| Split/reassemble operators (`join`, `multiMap`, `groupTuple`-reassemble, `transpose`) → 0 nodes under four aligned collections | **High** | sites in §2/§4/§5 read individually; each relies only on identifier alignment, which P1 exists to enforce |
| `channel.empty()`/`[meta,[]]` → optional step input (25 sites) | High | the take/emit signature of every affected subworkflow was read |
| 6 taxa conditionals collapse to 3 gates; `arg_skip_deeparg` top-level guard → 0 gates | High | arm bodies are identical modulo one filter (`:238-272`, `:277-330`) |
| Trunk nodes N1-N7 (unpack, long filter, membership split) | High | direct source lines |
| Lane node inventories (§7) | Medium-high | read from subworkflow bodies; `ext.args`/`prefix` from `modules.config`; per-tool port lists not re-verified against each module's `meta.yml` |
| ANNOTATION as a subworkflow step, instantiated twice | **Medium** | matches the conditionals note's subworkflow evidence (source boundary, wide cascade, narrow interface), rests on "one subworkflow may be called twice", unverified |
| M1/M3 variable-arity gather (P3→P4→P5) | **Low** | three candidate constructions, none attested; pattern pages missing |
| Nested 4-way dot-product at N28 | **Low** | notes attest 2-way dot-product on identical sample sheets only |
| Sample × HMM-model cross-product (§11) | Low | recipes note: unkeyed `combine` → review, little corpus uptake |
| fARGene class axis → tool parameter | Medium-high | values are a param string; interface already chose `select multiple` |
| Two `NA` columns is a real tabular step (N16) | High | the closure is quoted, its rationale is a source comment |
| MultiQC contains only versions/summary/methods/(Prokka|Bakta) | High | exhaustive grep of `ch_multiqc_files` and `out.multiqc` |
| Data-derived gates (§12) have no clean Galaxy construction | Medium | negative claim about a target whose full module set is not enumerated in the packaged notes |

## 17. Interface deltas this phase forces (for phase 6 and a phase-3 re-read)

1. **`versions` cannot be an output as specified** (§14). Either drop it, or promote per-step `versions.yml` outputs (N-count of them), or accept a custom "collect versions" step with no attested recipe. Interface §10.2's row is not implementable as written.
2. **`bgc_mincontiglength`** is consumed by N5 (`modules.config:103-105`) and is **not** among interface's 61 inputs — it is one of the 133 pinned knobs, and interface §5/§6's effect test is about *shape* controls; a length threshold changes which **samples** a lane screens, so by the same test it should be promoted. Recommend adding it as a numeric input; ledger `bgc-mincontiglength-affects-lane-membership`.
3. **antiSMASH DB shape must be fixed now** (§12 row 3): the untar-vs-directory-vs-download choice is a runtime file inspection in the source. Pick one (recommend "uploaded `.tar.gz`, N58 always untars", matching `db-inputs-as-uploaded-archives`) so N58-N60 become 1 gate + 1 step instead of an unrepresentable 3-way select.
4. **RGI CARD processedness** (`arg.nf:109`) needs either a boolean input ("my CARD is already processed") or unconditional N40. Recommend the boolean; it replaces a filename-substring test with an explicit user statement, and it is the only way to keep the rebuild-or-not choice.
5. **`.gz` in the four sample-sheet patterns** (§4.2): keep and pay 4 pass-through steps, or drop and change the form.
6. **`interproscan_table` binds to N16** (§15) — interface §10.2 names `INTERPROSCAN / tsv`, which is the wrong producer.
7. **`annotation_tool` may need an extra option or a help-text warning** (§12). The source silently overrides `prodigal → pyrodigal` whenever BGC/AMP screening is on; if that test is kept in the workflow it must be re-typed on 12 steps per ANNOTATION instance, whereas stating it on the input (or dropping `prodigal` from the enum for those runs) removes it from every gate. Cost of the interface route: the source's `log.warn` announcing the switch is lost, like the other 23.

## 18. What this brief could not verify, and why

The four pattern MOCs in this bundle (`galaxy-collection-patterns`, `galaxy-conditionals-patterns`, `galaxy-tabular-patterns`, `galaxy-interval-patterns`) instruct the reader to "Open the linked operation page for tool parameters and examples", and each names 13–19 concrete pattern pages. **None of them is packaged** — not in this mold's bundle, and not anywhere in the installed skill tree (the 9 pattern directories across 9 bundles contain only the 4 MOCs; `galaxy-collection-tools` and `galaxy-apply-rules-dsl`, the two notes those MOCs point at for tool settings, ship only in `implement-galaxy-tool-step`'s bundle). So every P-row in §13 is a *named* recipe whose construction I could not read, which is why §13's column heading is "named recipe" rather than a concrete operation + parameters, and why §16's M1/M3 confidence is low even though the recipe names are corpus-backed. Filed as `pattern-moc-links-pages-not-packaged-in-any-bundle`.

## 19. Open questions carried forward

1. Can one subworkflow be invoked as two steps? Decides §5's recommendation.
2. Do `multiple: true` uploads and `__MERGE_COLLECTIONS__` yield filename-derived element identifiers? Decides N22 and P3/P4.
3. Does `when:` accept a step output, or only inputs? Decides §12's derived-gate cost: 24 repeated `when:` strings against 12 references to one shared value.
4. What is a per-sample **directory** collection (`list` of mmseqs DBs, N9/N10) in Galaxy terms — usable, exportable, promotable? No packaged note addresses directory collections.
5. How does a variable-arity per-sample gather actually get built (§9)? Phase 5's job, by citation.
6. Where do "sample X was skipped by stage Y" notices go (§8)?
7. Does a skipped (typed-null) collection poison a zip/dot-product? §9, §13.
8. Is `sample_sheet` → map-over → `sample_sheet` output *shape-preserving* enough that N4's `gff_type`-carrying collection reaches N80 without P7? P7 assumes not.

## 20. Ledger changes emitted with this brief

**`open-requirements.ledger.yml`** — 25 entries / 16 decisions / 16 discoveries after this phase (was 16 / 10 / 8); re-emitted in full, YAML-parsed clean, every cross-reference and `evidence[]` id resolving. Appended **8 discoveries**: `four-of-seven-screening-subworkflows-are-data-sinks`, `most-of-the-edge-list-is-a-split-then-reassemble-cycle`, `emptiness-is-tested-per-consumer-and-the-warning-dies-there`, `interproscan-output-is-rewritten-by-groovy-before-anyone-uses-it`, `dead-wiring-in-the-bgc-warning-block`, `multiqc-report-carries-no-screening-results`, `versions-collation-and-parameter-summary-have-no-galaxy-producer`, `two-gating-decisions-are-channel-level-not-process-level`. Appended **9 gaps**: `sample-column-uniqueness-assumed-not-enforced`, `per-element-branch-has-no-galaxy-carrier`, `per-element-skip-warnings-have-no-galaxy-surface`, `variable-arity-fan-in-has-no-attested-galaxy-recipe` (blocking for phase 5), `nested-collection-dot-product-unattested`, `data-derived-gate-needs-nonemptiness-threshold`, `input-datatype-cannot-gate-a-step`, `bgc-mincontiglength-affects-lane-membership`, `directory-collection-semantics-unattested`. Appended **6 decisions**: `per-collection-mapping-replaces-split-and-reassemble`, `optional-inputs-replace-empty-channel-idiom`, `taxa-conditional-pairs-collapse-to-three-gates`, `annotation-instantiated-per-contig-variant` (medium), `fargene-class-axis-becomes-a-tool-parameter`, `gz-inputs-kept-with-pass-through-unpack-steps`. **Notes added on 7 inherited entries** — `db-directory-input-shape-unsettled`, `wrapper-rebuild-capability-unverified`, `multi-db-pick-list-no-galaxy-exemplar`, `hmm-models-required-when-branch-enabled`, `samplesheet-row-coupling-unexpressible`, `conditional-output-producer-unexpressible`, `published-only-results-need-explicit-promotion` — narrowing each without closing it. **Nothing closed**; every other entry passed through with provenance intact.

**`foundry-feedback.ledger.yml`** — 5 new entries: `pattern-moc-links-pages-not-packaged-in-any-bundle`, `conditionals-note-gives-no-construction-for-a-derived-gate`, `operator-via-records-no-arity-or-key-so-review-triggers-cannot-fire`, `sample-sheet-note-never-states-that-element-identifiers-must-be-unique`, `conditionals-detector-attributes-only-to-processes-so-channel-guards-vanish`. Ledger holds 15 entries, all `open`. §18 is the first entry's evidence; §12, §2, §3 and §10 carry the other four.
