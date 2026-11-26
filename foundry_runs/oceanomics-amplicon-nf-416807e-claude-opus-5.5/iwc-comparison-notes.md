# IWC comparison notes — OceanOmics-amplicon-nf

Produced by `compare-against-iwc-exemplar`. Corpus: `galaxyproject/iwc` @ `9f111cb8661fa446e43f92ec4863e6a66972a91c` (`~/.foundry/iwc`). Inputs: interface, data-flow and reference-data briefs, open-requirements ledger.

## Ranking
| Candidate | Domain | Input topology | Tool families | Confidence |
|---|---|---|---|---|
| `amplicon/dada2/dada2_paired` | amplicon ASV (16S) | `list:paired` fastq | DADA2 chain end-to-end | **Medium — nearest exemplar.** Same domain and topology. Covers plane B only; no primer trimming, ZOTU, LULU, BLAST/LCA or phyloseq. |
| `amplicon/qiime2/*` | amplicon | multiplexed / demux paired | QIIME2 artifacts (qza) | Low. A different toolchain and artifact model. |
| `amplicon/amplicon-mgnify/*` | amplicon rRNA (MGnify v5) | paired, QC + mapseq | trimming, cmsearch, mapseq | Low. Different classifier strategy. |
| `amplicon/multivariable-association-analysis` | downstream stats | phyloseq/tabular | phyloseq_* | Low. Downstream of a phyloseq object, not its construction. |
| `VGP-assembly-v2/Assembly-decontamination-VGP9` | assembly QC | single | `ncbi_blastn_wrapper` 2.16.0 | Low (cross-domain). Useful only as an idiom for blastn against a history DB. |

Corpus-wide idioms the template can rely on: `__BUILD_LIST__` (10 uses), `__MERGE_COLLECTION__` (8), `__RELABEL_FROM_FILE__` (25), `collapse_dataset` (46), cutadapt `lparsons/cutadapt/5.2+galaxy2` (10). **No IWC workflow uses vsearch or LULU**, so planes C and D6 have no corpus precedent.

## Structural diff vs `amplicon/dada2/dada2_paired` (plane B)
| Exemplar | Data-flow brief | Finding | Owner |
|---|---|---|---|
| `Sort samples` (`__APPLY_RULES__` sorting `list:paired` by identifier) before filterAndTrim | none | Add a sort step. DADA2 per-sample outputs are matched by position across forward/reverse and dada/merge steps, and IWC sorts first to make that deterministic. | template |
| `dada2_filterAndTrim` with `paired_cond` (collection input) → `paired_output` + `outtab` | B1 | Matches. Source sets `minLen`/`maxLen`; the exemplar exposes `truncLen`. | tool-step |
| `__UNZIP_COLLECTION__` → forward / reverse lists | B3 (implied) | Make the unzip an explicit node feeding both learnErrors and dada. | template |
| `dada2_learnErrors` ×2 (fwd, rev) | B3 | Matches. | — |
| `dada2_dada` ×2, `batch_cond.batch_select: no` + `pool` from a **string workflow input** (`restrictOnConnections`) | B4 | Matches, and answers **OQ-D1**: pooled inference runs over the whole collection when batch_select=no. The exemplar takes `pool` as a string input, which fits interface `asv_pooled` (`true`/`false`/`pseudo`). | template / interface |
| `dada2_mergePairs` (dadaF, dadaR, derepF, derepR) | B5 | Matches. derep = filtered reads, confirming the DADA2_DEREPLICATE fold (data-flow decision). `minOverlap`/`maxMismatch` already parameters. | tool-step |
| `dada2_makeSequenceTable` → `stable` | B6 | Matches. | — |
| `dada2_removeBimeraDenovo` (`method: consensus`) | B7 | Matches. Source script uses the module default; confirm method during implementation. | tool-step |
| `dada2_seqCounts` repeat over filtTrim/dadaF/dadaR/merged/seqtab/bimera | B9 | Wrapper equivalent of DADA2_TRACKREADS; use it instead of a custom script. | template |
| `dada2_assignTaxonomy` (builtin cached reference) | — (BLAST + LCA instead) | Deliberate divergence. Data tables are discouraged (ref-data posture), and the source classifies with BLAST/LCA/NBC. | — |
| — | B8 `asv_final_outputs` (ASV_n fasta + counts table + lca_input) | No exemplar node. The DADA2 sequence-table → FASTA/table conversion is custom and its formats are load-bearing downstream. | tool-step |
| `dada2_plotQualityProfile` pre/post filter | B2 | Optional report step, consistent. | — |

## Other planes (no domain exemplar)
- **Plane A:** cutadapt is corpus-common, but no IWC amplicon workflow trims primers with linked 5' adapters and `--discard-untrimmed`. Tool-step owns that.
- **Plane C (vsearch ZOTU):** no precedent. The template should keep the source's linear chain.
- **Plane D/E collection idioms:** build-list → map-over → relabel → merge is backed by corpus idioms (`__BUILD_LIST__`, `__RELABEL_FROM_FILE__`, `__MERGE_COLLECTION__`). Relabelling with a suffix needs a relabel mapping file. `__RELABEL_FROM_FILE__` takes a txt/tabular mapping, so a small text step (or `__APPLY_RULES__` regex) must produce `asv → asv_lulucurated`. This is a pattern gap with no IWC example of suffix relabelling.
- **BLAST against an uploaded DB:** VGP9 uses `ncbi_blastn_wrapper` 2.16.0. The `blastdbn` composite/v5 question (ledger `blastdb-v5-composite-upload`) is not answered by the corpus.

## Test-style comparison
The exemplar test (`dada2_paired-tests.yml`) builds a `list:paired` job input from remote zenodo URLs with SHA-1 hashes, keyed on sample identifiers (`F3D0`, …). The interface brief's `reads` input with test URLs from `a4000/test_data` fits that convention.

## Exemplar excerpt (gxformat2) — `amplicon/dada2/dada2_paired`, steps unzip → dada (forward)
Full subgraph: `iwc-exemplar.gxwf.yml` (13 steps, assignTaxonomy removed).
```yaml
inputs:
  - id: Paired input data
    type: collection
    collection_type: list:paired
  - id: Pool samples
    type: string
    restrictOnConnections: true
steps:
  - id: _unlabeled_step_9
    tool_id: __UNZIP_COLLECTION__
    in:
      - id: input
        source: _unlabeled_step_7/paired_output
    out:
      - id: forward
      - id: reverse
  - id: _unlabeled_step_12
    tool_id: toolshed.g2.bx.psu.edu/repos/iuc/dada2_dada/dada2_dada/1.38.0+galaxy1
    in:
      - id: batch_cond|derep
        source: _unlabeled_step_9/forward
      - id: batch_cond|pool
        source: Pool samples
      - id: err
        source: _unlabeled_step_10/errors
    tool_state:
      batch_cond:
        batch_select: "no"
```
