# Reference data brief — OceanOmics-amplicon-nf → Galaxy

Source: `summary-nextflow.json` (OceanOmics-amplicon-nf @416807e). Produced by `nextflow-summary-to-galaxy-reference-data`. Consumers: interface, data-flow and template Molds.

**Classification:** *single asset* core (one BLAST nucleotide DB, `dbfiles`), plus an optional *second parallel DB* (`dbfiles2`, only with `blast_twice`), three optional single assets (`aquamaps_db`, `masterlist`, `filter_table`), and several **hidden runtime-fetched references** with no param (NCBI taxdump, WoRMS species list, NBC classifier models, AquaMaps NetCDF). It is not key-expanded: there are no `getGenomeAttribute` params and no `--genome` key. `reference_rebuilds[]` is empty. The one fetch-if-missing branch (`aquamaps_db` absent → `DOWNLOAD_AQUAMAPS`) is a network download, not an index rebuild. `BLAST_MAKEBLASTDB` inside LULU builds a per-run self-DB from the pipeline's own ASVs/ZOTUs. That is intermediate data, not reference data, so it stays a normal workflow step.

**Posture (v1):** explicit Galaxy `data` inputs, no data tables and no `dbkey`. Where the source fetches at run time, surface that reference as an explicit optional input when a Galaxy tool can consume it, and otherwise flag it.

## Per-asset decisions

| Param | Source classification | Required | Galaxy shape | Datatype | Consumers | Notes |
|---|---|---|---|---|---|---|
| `dbfiles` | single asset (prebuilt BLAST v5 volume glob, `Channel.fromPath(...).collect()`) | **yes** (schema `required`) | single `data` input holding a BLAST nucleotide DB | `blastdbn` (composite) | BLAST_BLASTN, LCA (basename only) | Test fixture has 9 v5 volumes (`.ndb .nhr .nin .nog .nos .not .nsq .ntf .nto`) and no source FASTA. `staxids` in the custom outfmt 6 depends on the taxid map embedded in the volumes, so a plain FASTA + `makeblastdb` (no `-taxid_map`) would lose taxids and break LCA. See OQ-1. |
| `dbfiles2` | second parallel DB, gated by `blast_twice` | no | optional `data` input + boolean `blast_twice` | `blastdbn` | BLAST_BLASTN2 | Recommend **not exposing in v1**: it doubles every downstream branch (prefix `_db2`). Record as dropped. |
| `aquamaps_db` | optional single asset with network fetch fallback | no (default `s3://ocom-databases/eDNA/Aquamaps/am.db`, a private bucket) | optional `data` input | `sqlite` | AQUAMAPS | Default is unreachable from public Galaxy. When absent, the source runs DOWNLOAD_AQUAMAPS (R, fetches NetCDF over HTTP), and a Galaxy job generally cannot do that reproducibly. Recommend: an optional input; when unset, skip the AquaMaps branch (no download path). The output is annotation only and not part of the core taxonomy table. |
| `masterlist` | optional single asset | no | optional `data` input | `fasta` | FILT_WITH_MASTERLIST, ADD_BACK_MASTERLIST | Gates two steps (the gxformat2 `when` on an optional input). Low use; candidate for drop in v1. |
| `filter_table` | optional single asset (cohort/study data, not rebuildable) | no (test profile sets it) | optional `data` input | `csv` | PHYLOSEQ | Passed as `[]` when unset. Keep it; the test exercises it. |

## Hidden / runtime-fetched references (no param)

| Reference | Where | Galaxy implication |
|---|---|---|
| NCBI `new_taxdump.zip` → `rankedlineage.dmp` | `bin/runAssign_collapsedTaxonomy.py` (LCA) runs `wget` at run time | LCA needs ranked lineage. Promote it to an explicit `data` input (`rankedlineage.dmp`, tabular) so the run is reproducible and works offline; failing that, the step needs a wrapper with network access. OQ-2. |
| WoRMS species list | hard-coded URL `ch_worms` → LCA_WITH_FISHBASE | Only on the `lca_with_fishbase` alternate. Not in the v1 default path. |
| NCBI taxdump (Fishbase LCA) | `calculateLCAWithFishbase…py` caches/downloads | Same alternate; not in v1. |
| OceanOmics NBC models | baked into `adbennett/ocom_nbc:v1.4` | OCOMNBC has no Galaxy wrapper and its model is container state. It can only run in a container-pinned user-defined tool; otherwise drop it. PHYLOSEQ joins NBC output, so dropping OCOMNBC changes the PHYLOSEQ inputs. OQ-3. |
| AquaMaps NetCDF maps | DOWNLOAD_AQUAMAPS network fetch | Drop (see `aquamaps_db`). |

## Things deliberately not introduced
- No `.loc`/data-table BLAST DB selection (e.g. `ncbi_blastn_wrapper`'s `db_opts: db` built-in). Use `db_opts: histdb` with the uploaded `blastdbn` dataset instead.
- No workflow-tier rebuild for `dbfiles`: no FASTA is available in the fixtures, and the taxid map would be lost.

## Open questions
- **OQ-1 (blastdbn v5 composite):** Galaxy's `blastdbn` composite was defined for v4 file sets (`.nhr .nin .nsq`, optional `.nog .nsd .nsi`). Can the uploaded composite carry the v5 extras (`.ndb .nos .not .ntf .nto`) that hold the taxid map? If not, the alternative is a BLAST DB packaged as a single archive and unpacked in a user-defined tool. This needs verifying during step implementation and against test data.
- **OQ-2:** Accept `rankedlineage.dmp` as a new required workflow input (not a source param), or wrap LCA with network access? Recommend the explicit input. It is reproducible, but it adds a fixture the Nextflow test never supplied.
- **OQ-3:** Is OCOMNBC (container-baked model) carried as a container-pinned user-defined tool or dropped? Defer to the interface/data-flow molds.
- **OQ-4:** Is the test-profile `aquamaps_db` inherited from a private S3 default? Treat it as unset for Galaxy tests.
