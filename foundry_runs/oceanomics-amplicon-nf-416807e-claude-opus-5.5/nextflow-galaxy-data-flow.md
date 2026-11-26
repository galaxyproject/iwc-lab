# Galaxy data-flow brief — OceanOmics-amplicon-nf

Produced by `nextflow-summary-to-galaxy-data-flow`. Inputs: `summary-nextflow.json`, `nextflow-galaxy-reference-data.md`, `nextflow-galaxy-interface.md`, `open-requirements.ledger.yml`. This brief is not gxformat2 and does not choose tools. It states what each step must do and the shapes it uses.

## Identifier model (load-bearing)
- **Sample axis.** The `reads` `list:paired` elements are keyed on `samp_name`. Test rows `12S_simulated-reads` and `16S_simulated-reads` are unique, and both rows are paired, so the forward/reverse members are true mates. Sample identity must survive into read headers for the ZOTU branch (FASTQRELABEL) and into DADA2 sample rows.
- **OTU-set axis.** The source runs everything after denoising once per *string prefix*: `asv`, `zotu` → `+_db1` → `+_lulucurated`. That gives four sets on the default path: `asv_db1`, `zotu_db1`, `asv_db1_lulucurated`, `zotu_db1_lulucurated`. In Galaxy this becomes the **element identifier of parallel `list` collections** that later steps map over together. `_db1` is a constant (`dbname`) and is dropped. The identifiers are `asv`, `zotu`, `asv_lulucurated`, `zotu_lulucurated`, each unique by construction (method × curation). Every source `join` on prefix becomes a multi-input map-over on these matching identifiers (high confidence once the collections are built with the same identifiers in the same order).

## Plane A — read QC and primer trimming (per sample, map over `reads`)
| # | Node | In → Out | Galaxy idiom | Tool need | Conf. |
|---|---|---|---|---|---|
| A1 | `fastqc` | list:paired → list:paired (html, zip) | map-over | FastQC | high |
| A2 | `trim_primers` (CUTADAPT_TRIM_PRIMERS) | list:paired → list:paired fastqsanger.gz | map-over | cutadapt PE: `-g`/`-G` 5' primers built from `fw_primer`+`rv_primer` (GET_PRIMERFILES writes fw, rv and their reverse complements, `;`-separated → multiple adapters), `-e primertrim_error(0)`, `--minimum-length 1`, `--discard-untrimmed`, `--rename "{header}"` | high |
| A3 | `trim_leftover_primers` (CUTADAPT_TRIM_LEFTOVER_PRIMERS) | list:paired → list:paired | map-over | cutadapt again with each 5' and 3' primer, no discard | medium (iterative loop in source; one cutadapt call with all primers as `-g`/`-a`/`-G`/`-A` is the faithful single-pass equivalent) |
| A4 | `multiqc` | FastQC zips (reduce) → html | reduction | MultiQC | high |

GET_PRIMERFILES is plumbing (string → FASTA). It is **subsumed** by passing primer strings straight to cutadapt adapter parameters, so it needs no node.

## Plane B — ASV inference (DADA2; source subworkflow ASV_WORKFLOW)
| # | Node | In → Out | Idiom | Tool need | Conf. |
|---|---|---|---|---|---|
| B1 | `dada2_filter_trim` | A3 list:paired → list:paired + per-sample read-count table | map-over | DADA2 filterAndTrim (`minLen=read_minlen`, `maxLen=read_maxlen`; other args from the module script) | high |
| B2 | `dada2_plot_quality` | B1 → PNG per sample | map-over | DADA2 plotQualityProfile | medium (report-only; optional) |
| B3 | `dada2_learn_errors_fwd/rev` | B1 (all samples, forward / reverse) → error model ×2 | **reduction**; needs unzip of list:paired into forward and reverse lists | DADA2 learnErrors | high |
| B4 | `dada2_sample_inference` | B1 + B3 → per-sample dada objects, fwd/rev | map-over with broadcast error model; `pool` from `asv_pooled` (`true`/`false`/`pseudo`). Pooled inference makes it a reduction | DADA2 dada | medium (pooling forces all-sample processing) |
| B5 | `dada2_merge_pairs` | B4 + B1 → merged per sample | map-over (fwd/rev zipped) | DADA2 mergePairs (`minOverlap`, `maxMismatch`) | high |
| B6 | `dada2_sequence_table` | B5 (all samples) → seq table | **reduction** | DADA2 makeSequenceTable | high |
| B7 | `dada2_remove_chimeras` | B6 → seq table | single | DADA2 removeBimeraDenovo | high |
| B8 | `asv_final_outputs` (DADA2_FINALOUTPUTS) | B7 → `asv.fa`, `asv_final_table.tsv` (ASV id, per-sample counts, ASV_sequence), `lca_input.tsv` (`#ID` + counts) | single | script that renames ASVs `ASV_<n>` and writes the three tables | medium (custom R; the three exact formats are load-bearing for LCA/PHYLOSEQ) |
| B9 | `dada2_track_reads` | B1 csv + B4 + B5 + B7 → table + PNG | single | read-retention table | low (report; optional) |

The source's DADA2_DEREPLICATE is folded into B4. Galaxy's DADA2 dada step dereplicates internally, which is the modern DADA2 idiom. This is a subsumed node, not a drop.

## Plane C — ZOTU inference (vsearch; source subworkflow ZOTU_WORKFLOW)
| # | Node | In → Out | Idiom | Tool need | Conf. |
|---|---|---|---|---|---|
| C1 | `relabel_reads` (FASTQRELABEL) | A3 list:paired → list:paired, every header `@<samp_name>` | map-over; identifier → header | rewrite FASTQ headers to the element identifier (vsearch derives sample from label) | medium |
| C2 | `merge_pairs_qf` (ADAPTERREMOVAL `--collapse --trimns --trimqualities --minquality 10 --minalignmentlength 6`) | C1 list:paired → list of collapsed fastq | map-over, paired → single | read-pair collapse + quality trim | high |
| C3 | `pool_reads` (FASTQCONCAT) | C2 list → one fastq.gz | **reduction** (concatenate collection) | concatenate datasets | high |
| C4 | `fastq_to_fasta` | C3 → fasta | single | FASTQ→FASTA | high |
| C5 | `derep` | C4 → fasta with sizes | single | vsearch `--derep_fulllength --sizeout` | high |
| C6 | `denoise` | C5 → centroids | single | vsearch `--cluster_unoise --minsize zotu_min_size --centroids` | high |
| C7 | `remove_chimeras_zotu` | C6 → zotu fasta (`zotu<n>` relabel) | single | vsearch `--uchime3_denovo --nonchimeras --relabel zotu` | high |
| C8 | `zotu_table` | C4 + C7 → otutab | single | vsearch `--usearch_global --id zotu_id --otutabout` | high |
| C9 | `zotu_table_format` | C8 + C7 → `zotu_table` (+sequence column) and `lca_input` (`#ID` header, quotes stripped) | single | tabular reformat | medium (exact column contract set by VSEARCH_USEARCHGLOBAL script) |

## Plane D — OTU-set assembly, LULU, BLAST
| # | Node | In → Out | Idiom | Tool need | Conf. |
|---|---|---|---|---|---|
| D1 | `build_fasta_sets` | B8.asv.fa + C7 → list {asv, zotu} | **explicit build-list** (`mix`) | build list | high |
| D2 | `build_table_sets` | B8.asv_final_table + C9.table → list {asv, zotu} | build-list | build list | high |
| D3 | `build_lca_input_sets` | B8.lca_input + C9.lca_input → list {asv, zotu} | build-list | build list | high |
| D4 | `lulu_self_db` (BLAST_MAKEBLASTDB) | D1 → list of blastdbn | map-over | makeblastdb `-parse_seqids -dbtype nucl` | high |
| D5 | `lulu_match_list` (BLAST_MATCHLIST) | D1 + D4 → list of match lists | map-over (matching ids) | blastn `-outfmt "6 qseqid sseqid pident" -qcov_hsp_perc 80 -perc_identity 84` | high |
| D6 | `lulu` | D2 + D5 → curated table list {asv, zotu} | map-over | LULU (`minimum_match = lulu_min_match`) | medium |
| D7 | `lulu_fasta` (GETLULUFASTA) | D1 + D6 → curated fasta list | map-over | subset FASTA by ids in table column 1 | high |
| D8 | `blastn` (BLAST_BLASTN) | D1 + `blast_db` → blast tabular list {asv, zotu} | map-over, broadcast DB | blastn against an uploaded DB with outfmt `6 qseqid sseqid staxids sscinames scomnames sskingdoms pident length qlen slen mismatch gapopen gaps qstart qend sstart send stitle evalue bitscore qcovs qcovhsp`, plus `-task blastn -perc_identity blast_pid -evalue blast_evalue -qcov_hsp_perc blast_qcov -max_target_seqs 99999` | medium (custom columns `sscinames/scomnames/sskingdoms` need taxdb; staxids needs the v5 taxid map — ledger `blastdb-v5-composite-upload`) |
| D9 | `curate_blast` (CURATE_BLASTN_RESULTS) | D7 + D8 → list | map-over | keep BLAST rows whose qseqid is in the curated FASTA | high |

Dropped scatter: `splitFasta(by: 500)` → BLAST chunks → `groupTuple` → CONCAT_BLASTN_RESULTS is a **performance scatter/gather** with no semantic effect, so D8 runs once per set. CONCAT_BLASTN_DEFAULT_RESULTS (default-format text) has no downstream consumer. Neither needs a node.

## Plane E — four-set fan-in, LCA, NBC, phyloseq, filtering
| # | Node | In → Out | Idiom | Tool need | Conf. |
|---|---|---|---|---|---|
| E1 | `relabel_curated` | D6, D7, D9 → same lists with identifiers suffixed `_lulucurated` | **identifier relabel** | relabel collection identifiers (suffix) | medium |
| E2 | `merge_sets` | {D3 ∪ E1(D6)} → `lca_tables`; {D8 ∪ E1(D9)} → `blast_sets`; {D1 ∪ E1(D7)} → `fasta_sets`; {D2 ∪ D2-relabelled} → `otu_tables` — each list of 4 | **merge collections** | merge collections | medium. Source quirk: the `_lulucurated` phyloseq set reuses the *uncurated* OTU table (`ch_otu_table.mix(ch_otu_table.map{ prefix+"_lulucurated" })`). Kept faithfully. |
| E3 | `lca` | lca_tables + blast_sets + fasta_sets + `taxonomy_lineage` → LCA table, intermediate, taxa_raw, taxa_final | map-over (3 matching lists + broadcast) | runAssign_collapsedTaxonomy.py with `lca_qcov lca_pid lca_diff`; must read `taxonomy_lineage` instead of wget | medium (custom script; ledger `lca-taxdump-runtime-download`) |
| E4 | `lca_dedup` (REMOVE_DUPS) | E3.lca → list | map-over | drop duplicate rows by column 8, strip quotes | high |
| E5 | `nbc` (OCOMNBC) | fasta_sets → NBC table list | map-over | OceanOmics naive Bayes classifier (models in container `adbennett/ocom_nbc:v1.4`) | low (ledger `ocomnbc-container-baked-model`). PHYLOSEQ hard-requires its columns (`Gene`, `Genus.prediction`, `Species.score` …) |
| E6 | `phyloseq` | otu_tables + E4 + E5 + `sample_metadata` + optional `filter_table` → phyloseq rds + final_taxa | map-over (3 lists + 2 broadcasts) | R/phyloseq script (merge, filter_table exclusions, LCA column) | medium (custom R; metadata rows keyed on `samp_name` column) |
| E7 | `flag_length` (FLAG_OTUS_OUTSIDERANGE) | E6.rds → rds + tsv | map-over | flag OTUs outside `[asv_min_length, asv_max_length]` | medium |
| E8 | `proportional_filter` | E7.rds + E6.final_taxa + E3.taxa_final → filtered_taxa, final_taxa, final_otu, stats, rds | map-over (3 matching lists) | R proportional abundance filter | medium |

## Conditional disposition
Every guard is fixed at the source default (interface brief), so the v1 workflow has **no `when:` steps**. `filter_table` is the only optional input. It is a broadcast optional data input to E6, and the source script already branches on `file.exists`.

## Workflow outputs → nodes
`fastqc_html`=A1, `multiqc_report`=A4, `asv_fasta`/`asv_table`=B8, `asv_track_reads`=B9, `zotu_fasta`=C7, `zotu_table`=C9, `lulu_curated_table`=D6, `blast_results`=E2.blast_sets, `lca_table`=E4, `phyloseq_object`=E8.rds, `final_taxa`=E8.final_taxa, `filtered_otu_table`=E8.final_otu.

## Unresolved tool needs (for discovery)
cutadapt (PE, multiple 5'/3' adapters); DADA2 filterAndTrim / learnErrors / dada / mergePairs / makeSequenceTable / removeBimeraDenovo; DADA2-table → ASV fasta + count tables; FASTQ header rewrite; AdapterRemoval collapse; dataset concatenation; FASTQ→FASTA; vsearch derep / cluster_unoise / uchime3_denovo / usearch_global; makeblastdb; blastn with custom outfmt 6 and an uploaded DB; LULU; FASTA subset by id list; tabular row filter by id list; collection build / merge / relabel; LCA (custom); duplicate-row removal; NBC (custom, container model); phyloseq construction (custom R); OTU length flag (custom R); proportional filter (custom R); FastQC; MultiQC.

## Open questions
- **OQ-D1:** Is pooled DADA2 inference (`asv_pooled`, default true) expressible with the Galaxy DADA2 dada wrapper over a collection? If not, the test override `asv_pooled=false` keeps per-sample semantics.
- **OQ-D2:** The source BLAST outfmt requests `sscinames scomnames sskingdoms`, which need NCBI `taxdb.btd/bti`. Those files are not in the test DB volumes (output `N/A`). Does LCA depend on those columns, or only on `staxids` + the lineage file?
- **OQ-D3:** DADA2_FINALOUTPUTS fails with fewer than two samples, and the test has exactly two. Keep that guard.
