# Galaxy data-flow brief — nf-core/bamtofastq

*Source: summary-nextflow.json @ aa0150e + nextflow-galaxy-interface.md + nextflow-galaxy-reference-data.md (same run). Channel semantics re-verified by direct inspection of `workflows/bamtofastq.nf`, `subworkflows/local/{prepare_indices,pre_conversion_qc,alignment_to_fastq}/main.nf`, `conf/modules.config`, `modules/local/checkpairedend/main.nf`, and `tests/default.nf.test.snap`. Written 2026-11-09 23:5x local (via `date`).*

Not gxformat2; no tool ids resolved. Abstract operations, collection map/reduce choices, shape-changing placeholders, Galaxy tool needs, confidence, open questions.

## 0. Source shape in one paragraph

Each samplesheet row is one alignment file (BAM or CRAM) with an optional index. The pipeline: repairs missing sample indexes and the missing FASTA fai (PREPARE_INDICES) → runs pre-conversion QC (flagstat/idxstats/stats + FastQC on BAM rows only) → classifies each sample paired vs single-end by samtools flag counting (CHECKPAIREDEND) → routes paired samples through a 4-way `samtools view` flag split → per-sample unmapped merge → collatefastq → concatenate (ALIGNMENT_TO_FASTQ), and single-end samples through one collatefastq whose `other` bucket carries the reads → FastQC + fastq_utils over the merged reads → MultiQC reduction over all reports.

## 1. Galaxy-facing inputs (from interface brief, refined here)

| Input | Shape | Notes |
|---|---|---|
| Input samplesheet | collection `sample_sheet` | **Refinement of the interface brief's `paired_or_unpaired`** — see decision D1 below. Columns: `sample_id` (string, required, `^\S+$`), `file_type` (string, required, restrictions `[bam, cram]`). The alignment file is the element dataset. |
| Fasta reference | data, `format: fasta`, optional | Needed only when a row is CRAM. |
| Fasta index | data, `format: fai`, optional | v1 posture: in-tool rebuild by the consuming samtools wrappers; not a workflow node (decision D2). |
| Controls | `chr` (string, optional), `no_read_QC` (boolean), `no_stats` (boolean), `samtools_collate_fast` (boolean), `reads_in_memory` (int) | Feed `when:` gates and tool parameters only; no dataset edges. |

**Decision D1 — samplesheet variant is `sample_sheet`, not `paired_or_unpaired`.** The interface brief chose `paired_or_unpaired` to give the optional `index` sidecar an inner slot. The v1-consistent default it also recorded (and the ledger entry `sample-sheet-index-column-representation` pinned) is to *drop the index input* and rely on in-tool index building. With the index dropped, each row carries exactly one dataset — the mapping rules in galaxy-sample-sheet-collections pin "path-typed column (one per row) → variant `sample_sheet`". Inner subcollections would be singletons, which `paired_or_unpaired` expresses but does not need. **Primary shape: `sample_sheet`.** Fallback if the per-step loop finds the selected samtools wrappers cannot build indexes in-tool: reopen the ledger entry and switch to `sample_sheet:paired_or_unpaired` with the index as the inner mate. Confidence: high for the drop (posture), medium for wrapper capability (unverified — the gate is already in the ledger).

**Decision D2 — PREPARE_INDICES dissolves into wrapper capability.** Source PREPARE_INDICES does two compute-if-missing things: (a) `SAMTOOLS_INDEX` on rows lacking `.bai`/`.crai`, (b) `SAMTOOLS_FAIDX` when `params.fasta` is supplied without `params.fasta_fai`. Under the in-tool-rebuild posture both become *properties of the consuming wrappers*, not workflow steps: every samtools step that wants an index gets the alignment (or FASTA) and builds it if absent. Consequence: **no PREPARE_INDICES node, no fai-rebuild branch, no `ch_fasta_fai` carrier in the Galaxy draft.** The FASTA input connects directly to the samtools steps that consume a reference. Contingent on wrapper rebuild verification at per-step time (ledger `sample-sheet-index-column-representation`). Confidence: medium-high (posture is corpus-pinned; per-wrapper capability unverified).

Sample rows may repeat `sample_id` (one sample, several runs) in the general case; the source test's two rows (`test`, `test2`) are unique. Galaxy sample_sheet element identifiers must be unique per row — the brief carries the constraint that identifier derivation must disambiguate repeated `sample_id` rows if a user sheet has them (template tier); the test fixture does not exercise this.

## 2. Abstract nodes

Notation: `⇒` maps over the samplesheet-derived per-sample collection. Element identifiers throughout are derived from `sample_id` (`test`, `test2` in the fixture).

| # | Node | In → out | What it must do | Tool need (capability, not id) | Conf |
|---|---|---|---|---|---|
| N1 | Pre-conversion stats | `⇒` alignment (+ ref for CRAM) → 3 txt | samtools flagstat / idxstats / stats, one job per sample, gated by `no_stats` | samtools flagstat/idxstats/stats wrappers; reference optional-in | high |
| N2 | Pre-conversion FastQC | `⇒` **BAM rows only** → html + zip | FastQC, prefix `sample_id.pre_conversion`, gated by `no_read_QC` | fastqc wrapper; prefix/rename control | high |
| N3 | Pairedness classifier | `⇒` alignment (+ ref for CRAM) → per-sample flag verdict | Count paired reads (samtools view `-c -f 1`) vs total; verdict single/paired per sample | **unresolved**: classifier step — either compose from samtools view `-c` + tabular compare + filter, or author a small user-defined tool mirroring CHECKPAIREDEND's head-N logic | medium |
| N4 | Split samples by pairedness | N3 verdict + alignment collection → two collections | Per-element routing (see C1) | collection filter driven by per-element verdict | medium |
| N5 | Flag-split extraction | `⇒` paired samples → 3 unmapped BAM/CRAM variants + 1 mapped BAM/CRAM | Four `samtools view` invocations with ext.args `-b -f1 -F12` (map_map), `-b -f12 -F256` (unmap_unmap), `-b -f4 -F264` (unmap_map), `-b -f8 -F260` (map_unmap); CRAM inputs also emit cram (same step, output type follows input) | samtools view wrapper with flag-filter args; per-alias output naming `${id}.{map_map|unmap_unmap|unmap_map|map_unmap}` | high |
| N6 | Unmapped merge | 3 unmapped variants (same sample) → 1 merged BAM/CRAM | `samtools merge` over the 3 sibling outputs per sample | samtools merge accepting multiple inputs mapped per-sample (identifier-aligned fan-in, see T2) | medium |
| N7 | Collate+extract (mapped, paired) | merged-mapped BAM/CRAM ⇒ → R1/R2 fastq.gz | `samtools collate | samtools fastq` with args2 `-N`; prefix `${id}.mapped` | samtools collatefastq wrapper (or collate + fastq pair) | medium |
| N8 | Collate+extract (unmapped, paired) | merged-unmapped BAM/CRAM ⇒ → R1/R2 fastq.gz | same, prefix `${id}.unmapped` | ditto | medium |
| N9 | Collate+extract (single-end) | single-end samples ⇒ → other + singleton fastq.gz | same tool family; for single-end samples the **`other` bucket carries the reads** (source comment: fastq_singleton was empty — famosab swap); prefix from sample id; publishes as `unmapped_other_reads` | ditto; wrapper must expose the other output | medium |
| N10 | Concatenate mates | mapped R1 + unmapped R1 → `test_1.merged.fastq.gz`; mapped R2 + unmapped R2 → `test_2.merged.fastq.gz` | per-sample concat, mapped-first order matters for content only via ordering of cat operands (md5-stable) | concatenate datasets (tail-to-head), 2 jobs per sample | high |
| N11 | Post-conversion FastQC | per-sample merged mates → html + zip | FastQC once per sample over the sample's mates; rename `sample_id.post_conversion_N`; gated by `no_read_QC` | fastqc wrapper accepting both mates per job (rename `_1/_2`) | medium |
| N12 | fastq_utils info | per-sample merged mates → `sample_id.txt` | **one job per sample over both mates** (snapshot: `test.txt`, `test2.txt` — one per sample, not per mate) | fastq_utils `fastq_info` wrapper; must accept both mates per job or accept per-mate naming deviation (see O2) | medium |
| N13 | MultiQC reduction | all report datasets → 1 html | One reduction over flagstat+idxstats+stats+pre-conversion fastqc html (+ post-conversion html is *not* in the source fan-in) | multiqc wrapper over a merged flat list | high |
| N14 | chr filter (conditional) | alignment ⇒ → chr-filtered alignment | `samtools view -hb <chr>` + re-index; replaces the collection when `chr` set | samtools view + index; whole-collection gate, see C4 | medium |

## 3. Edges and collection semantics

Source → Galaxy edge translation (operator classes from nextflow-operators-to-galaxy-collection-recipes):

| Source edge | Class | Galaxy disposition |
|---|---|---|
| samplesheet → PREPARE_INDICES branch on `index` presence | channel-only (D2) | disappears — in-tool rebuild |
| PRE_CONVERSION_QC ⇒ flagstat/idxstats/stats | Galaxy collection semantics | map N1 over the samplesheet; outputs are `list` collections keyed by sample_id |
| FASTQC bam/cram branch | collection semantics (per-element, user-declared metadata) | placeholder transform T1 |
| CHECKPAIREDEND + join/map into ch_input_new | explicit step + collection semantics | N3 + T2 (verdict join) + C1 split |
| ch_input_new `.branch{single_end}` | explicit (per-element, runtime-derived) | C1 |
| 4× SAMTOOLS_VIEW aliases | Galaxy collection semantics | map N5 over paired-sample collection; 4 parallel per-sample outputs |
| 3× `.join(..., remainder: true)` + mix bam/cram | collection semantics (identifier-keyed fan-in) | T3 — the three unmapped variants are siblings of the same sample; merge maps over them together (identifier-aligned multi-input map). `remainder: true` tolerates an empty variant (e.g. no map_unmap reads) — in Galaxy a missing/empty view output must not break the join; handled inside the merge step's tolerance or by filter-empty cleanup, flagged for per-step attention |
| SAMTOOLS_MERGE_UNMAP + COLLATE_FASTQ_* | collection semantics | N6 → N7/N8, all per-sample |
| `reads_to_concat` join + parity-index split | channel-only (parity trick) | replaced by explicit R1/R2 handling: unzip both collatefastq paired outputs (T4), concat R1 with R1, R2 with R2 (N10) — the source's odd/even index arithmetic is just an implicit unzip; Galaxy does it explicitly |
| CAT_FASTQ | collection semantics | N10; emits flat per-sample merged mates. Internal QC consumers (N11, N12) need the per-sample grouping (see T5); the published output is the flat list |
| `.mix` into ch_reads_post_qc | wiring | merge collections (merged reads + single-end other) → feeds N11, N12 |
| no_read_QC / no_stats gates on tool steps | inline `when:` | C2, C3 |
| `params.chr` block | inline `when:` + pick_value | C4 |
| `.mix` + `.collect` into MULTIQC | wiring + reduction | N13; build one flat list from the report collections (T6); tolerate skipped inputs when QC gated off |
| topic versions / paramsSummary / methodsDescription → collectFile | **dropped** | ledger `multiqc-runner-boilerplate-dropped` |
| MULTIQC report `.map{}.toList()` emit | wiring | unbox to a single dataset output (`multiqc_report`) |

### Conditionals

| Source guard | Disposition | Reasoning |
|---|---|---|
| `params.no_stats` → flagstat/idxstats/stats | **C2: three inline `when:` tool steps**, shared boolean input | Source gates three sibling processes on the same flag; no subworkflow boundary in source; cascade short. Skipped steps produce typed nulls → their collection outputs are workflow outputs that read as skipped/empty when gated; test plan asserts accordingly |
| `params.no_read_QC` → FASTQC pre + post | **C3: two inline `when:` tool steps** | Same shape as C2. The pre-conversion fastqc html feeds the MultiQC fan-in, so N13's list-assembly must tolerate the skipped sentinel (collection-merge tools tolerate skipped inputs per the conditional note; `pick_value` not needed — the other fan-in members still run) |
| `params.chr` → SAMTOOLS_CHR + INDEX + rejoin | **C4: transform-or-pass-through** — gate the chr-filter pair with one `when:` on the boolean-ness of `chr`, then `pick_value` (first_non_null) between the filtered and the unfiltered collection. `the_only_non_null` is not usable because exactly one side always runs | Source: `if (params.chr) {...}` inline in the main workflow body, reassigning `ch_input_new` — a pure transform-or-pass-through over the whole collection; conditional note's canonical pattern. The BAM/CRAM dual-emit + mix collapses to one samtools-view output (type follows input) |
| `params.fasta` `.branch` fai rebuild | **dissolved** (D2) | in-tool rebuild posture; no workflow-tier branch |

**C1 — the runtime paired/single split (the load-bearing hard case).** `meta.single_end` is *runtime-derived* (N3), not user-declared, and the two downstream cascades diverge (N5–N10 for paired; N9 for single). Step-level `when:` cannot route per element. Disposition:

- N3 emits a per-sample verdict (txt or tabular).
- T2/T4-family placeholder: filter the sample collection into `single` and `paired` subcollections using the verdict (identifier-driven collection filtering — the verdict file is named `${id}.paired.txt` / `${id}.single.txt`, so element identifiers are derivable from filenames; the rules-DSL identifier-filter recipe is corpus-attested).
- Then the paired cascade maps over the paired collection and the single-end collatefastq maps over the single collection.
- Confidence: **medium**. The predicates are non-trivial (counting fraction of paired reads), which the operator note flags as a review trigger; the shape above is expressible but the exact filter tooling is per-step work. No `pick_value` needed downstream — both branches produce disjoint outputs that never merge back into one input (`other` + merged reads only merge as siblings in the QC fan-in).
- User-review flag: if the verdict-join proves brittle at implement time, the fallback is a user-declared boolean ("all samples are paired") collapsing C1 to a whole-collection route — a semantic narrowing of the source that must be surfaced, not silently taken.

## 4. Shape-changing placeholder transformations (template tier materializes)

| # | Transform | Have → want | Concrete recipe direction | Conf |
|---|---|---|---|---|
| T1 | BAM-only pre-conversion FastQC input | sample_sheet (bam+cram rows) → collection of BAM rows | filter rows by the `file_type` column value (sample-sheet-aware filtering / rules DSL on column) | medium |
| T2 | Verdict join | N3 verdict files + sample collection → verdict-keyed metadata for routing | merge verdict outputs; derive per-element identifier lists; used by C1's split | medium |
| T3 | Unmapped-variant fan-in | 3 per-sample unmapped BAMs (siblings) → one 3-input merge job per sample | identifier-aligned multi-input map (zip by element identifier or multi-input collection mapping into samtools merge) | medium |
| T4 | Mate handling | collatefastq R1/R2 outputs → explicit R1/R2 siblings for concat; per-sample grouping for QC consumers | unzip paired outputs (T4a); **T5**: keep merged reads grouped per sample (list:paired or sample-keyed subcollections) for N11/N12 while publishing the flat list as `merged_reads` | medium |
| T6 | MultiQC fan-in | several report collections → one flat list of datasets | merge collections (tolerating skipped/gated members); plus single-ended `other` reports if present | high |

Collection shape ledger through the flow:

```
sample_sheet (1 alignment/row)
  → map N1 → list(txt) ×3, map N2 → list(html)+list(zip)   [BAM rows only for N2]
  → N3+split → collection(single) + collection(paired)
  → paired: map N5 → per-sample 4 outputs → N6 → N7/N8 (R1/R2 per sample)
            → N10 → per-sample 2 merged mates  → published flat list (4 elements for the fixture)
  → single: map N9 → other per sample        → published flat list
  → N11/N12 over per-sample grouped merged reads (+ other)
  → N13 reduction → single html
```

## 5. Datatypes (per nextflow-path-glob-to-galaxy-datatype)

| Edge | format | Confidence |
|---|---|---|
| alignment elements | `bam` / `cram` | high (schema pattern) |
| merged/other/single fastq.gz | `fastqsanger.gz` | high |
| flagstat/idxstats/stats, fastqutils txt | `txt` | medium (report text; `*.txt` is weak evidence per the note) |
| fastqc html / zip | `html` / `zip` | high |
| multiqc report | `html` | high |
| fasta / fai | `fasta` / `fai` | high / high (sidecar posture) |

Index sidecars (bai/crai) are not carried as datasets (D1); the fai is an optional input only (D2).

## 6. Element identifiers vs the source snapshot (feeds fastqc-element-identifiers)

Derived rules, checked against `tests/default.nf.test.snap` stable_names:

| Output | Rule | Fixture names |
|---|---|---|
| merged reads | `${sample_id}_${1|2}.merged.fastq.gz` | `test_1.merged.fastq.gz`, `test2_2.merged.fastq.gz`, … |
| pre-conversion fastqc | `${sample_id}.pre_conversion` + fastqc suffix | `test.pre_conversion_fastqc.html` |
| post-conversion fastqc | `${sample_id}.post_conversion_N` per mate | `test.post_conversion_1_fastqc.html` |
| fastqutils | `${sample_id}.txt` — **one per sample over both mates** | `test.txt`, `test2.txt` |
| samtools reports | `${sample_id}.{flagstat,idxstats,stats}` | `test.flagstat`, … |

The `.merged.fastq.gz` / `.pre_conversion` suffixes come from the source's own ext.prefix idioms; whether Galaxy element identifiers carry them or the wrapper-level filenames carry them is a template/implement choice — but the asserted output *names* must reproduce the snapshot shapes above (checksum evidence exists for merged reads, samtools reports, fastqutils txt).

## 7. Expected outputs and checksum availability (for the test plan)

From the snapshot (default test, 2 paired BAM samples):

- `merged_reads`: 4 elements, **md5s available** (test_1/test_2/test2_1/test2_2) → per-element checksum assertions.
- `flagstat/idxstats/stats`: 2 elements each, **md5s available** → per-element checksums.
- `fastqutils_reports`: 2 elements, **md5s available**.
- `multiqc_report`: html smoke only — the snapshot checksums `multiqc_citations.txt` (inside multiqc_data/), which the runner-boilerplate drop makes content-divergent (see dropped entry).
- `unmapped_other_reads`: **empty for the default test** — corrects the interface brief, which anticipated element_count 2. Evidence: SAMTOOLS_COLLATEFASTQ_SINGLE_END consumes only `ch_single` (`meta.single_end == true`); both fixture samples are paired; the snapshot's stable_names contain no `*other.fq.gz`. Assertion = 0-element/empty or skipped output — a type/count check, logged as such per the test-quality rule. (For single-end samples the other bucket *is* the reads — the no_bai test's test3 exercises it.)
- Pre/post-conversion fastqc html/zip: name-level evidence only (stable_names, no md5) → name/element_count assertions.

## 8. Dropped source work

- **MultiQC runner boilerplate** (3 input streams: collated software-versions YAML, workflow_summary_mqc.yaml, methods_description_mqc.yaml) + `pipeline_info/nf_core_bamtofastq_software_mqc_versions.yml`. Because: these are nf-core-runner artifacts assembled via `collectFile` from Nextflow runtime introspection (`paramsSummaryMap(workflow)`, `softwareVersionsToYAML`), not scientific outputs; Galaxy's MultiQC wrapper supplies its own metadata path. Consequence: `multiqc_citations.txt` content diverges from the source snapshot → its md5 is unassertable in the Galaxy test (smoke only). Recorded as a `dropped` ledger entry.
- **iGenomes key pathway** (`genome`/`igenomes_base`/`igenomes_ignore`): inactive alternate input pathway; dropped under the no-data-tables posture (reference-data brief).

## 9. Unresolved tool needs (capability statements for discovery/authoring)

1. **Pairedness classifier** (N3): count paired-vs-total reads per alignment, emit per-sample verdict. Composable (samtools view `-c` ×2 + arithmetic + filter) or a small authored tool. CRAM needs `--reference`.
2. **Verdict-driven collection split** (C1/T2): filter a collection into two by per-element verdict.
3. **Sample-sheet column filter** (T1): filter sample_sheet rows by `file_type == bam`.
4. **Multi-input per-sample merge** (N6/T3): samtools merge over 3 identifier-aligned sibling collections.
5. **Multi-mate single-job steps** (N11/N12): fastqc/fastq_info wrappers that take a sample's mates in one job (rename + single report per sample).
6. **samtools wrapper in-tool index rebuild** (D2 gate): build bai/crai/fai when absent.

Each is a capability need, not a tool verdict — discovery reports what exists; authoring is the fallback.

## 10. Confidence summary

- High: N1, N10, N13 wiring, datatypes, output naming rules, checksum availability.
- Medium: N5–N9 (wrapper arg/naming fidelity), N11/N12 (multi-mate single-job), C1 split (per-element routing), T1–T6 materialization, D1/D2 contingent on wrapper verification.
- Low: none carried as nodes; C1's fallback (user-declared pairedness boolean) is a narrowing that would need review if it comes to that.

## 11. Handoff notes

- **To compare-against-iwc-exemplar**: the abstract topology is a per-sample QC+convert fan-out with one reduction; expect divergence from IWC's typical list:paired-reads front end — the input is alignments, not reads. The chr transform-or-pass-through and the runtime paired/single split have no obvious IWC sibling; flag both.
- **To nextflow-summary-to-galaxy-template**: honor source subworkflow boundaries (PRE_CONVERSION_QC, ALIGNMENT_TO_FASTQ) as Galaxy subworkflows or grouped step sections — aesthetic call per the conditional note; no `when:` rides these boundaries. Materialize C2/C3/C4 gates, the T-transform placeholders, and the identifier rules of §6. The `merged_reads` workflow output is the flat list; QC consumers need T5's grouped form.
- **To advance-galaxy-draft-step**: the wrapper-capability gates (D1 fallback, D2 rebuild, multi-mate N11/N12, N6 multi-input) are exactly the checks the per-step loop must run before wiring; treat their failure as a topology repair trigger, not a parameter patch.

## 12. Open questions

1. Can the selected samtools wrappers rebuild bai/crai/fai in-tool (gates D1/D2)? — per-step tier.
2. Does the fastq_utils wrapper run once per sample over both mates (matching `test.txt` naming), or only per file? Fallback naming deviation must be surfaced to the test plan. — per-step tier.
3. Is the C1 verdict-driven split robust enough in Galaxy's rules-DSL/filter tooling, or does the pairedness-boolean fallback get exercised? — template/implement tier.
4. For CRAM rows, does the chosen samtools view/stats wrapper thread `--reference` cleanly? — per-step tier (fixture is BAM-only; CRAM paths go untested by the default test — noted for scope honesty).

## 13. Ledger updates

- **Carried open**: `sample-sheet-index-column-representation` (D1's gate), `fastqc-element-identifiers` (progress recorded in §6; concrete wiring still template/implement).
- **Appended**: `single-paired-runtime-branch-representation` (C1's placeholder + fallback), `fastqutils-per-sample-invocation` (N12 naming gate), `multiqc-runner-boilerplate-dropped` (kind: dropped).
- **Discovery recorded**: `unmapped-other-empty-for-default-test` (corrects the interface brief's element_count-2 anticipation).

**Feedback pass**: no feedback. All notes consumed were load-bearing and sufficient; the two corrections in this brief (empty `other` for the default test, per-sample fastqutils invocation) came from reading the *source*, not from gaps or contradictions in the packaged references. No Foundry asset showed a defect in this phase.
