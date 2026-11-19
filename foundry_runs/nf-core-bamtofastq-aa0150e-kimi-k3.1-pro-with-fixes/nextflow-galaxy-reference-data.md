# Galaxy reference-data brief — nf-core/bamtofastq

## Classification and scope

The summary declares two optional path-shaped parameters in **Reference genome options**: `fasta` and its companion index `fasta_fai`. Following the taxonomy's explicit nf-core/bamtofastq example, classify this as a **single asset (FASTA) with a companion FASTA index**. It is not a coordinated independent-reference bundle: the FAI is derived from the FASTA.

There are no `getGenomeAttribute`-derived parameters and no `reference_rebuilds[]` entries. Rebuild behavior is therefore **rebuild-unverified**, not absent. The `genome` parameter is an iGenomes selector, not a dataset. No reference-producing, multi-database, parallel-bundle, or cohort-data classification applies.

## Galaxy inputs

| Source parameter | Galaxy shape | Requiredness | Rationale and losses |
|---|---|---|---|
| `fasta` | Optional `data`, format `fasta` | Required when any CRAM input or CRAM-producing operation needs reference decoding; otherwise optional | Portable user-supplied reference replaces both direct paths and iGenomes-derived paths. Preserve conditional requirement in documentation and tool validation because gxformat2 cannot express required-when-CRAM cleanly. |
| `fasta_fai` | Optional `data`, format `fai` | Optional; must belong to the supplied FASTA when present | Users can supply a prebuilt index. If absent, prefer the selected wrapper's in-tool `samtools faidx` rebuild, but that capability is not verified yet and remains an open requirement. |

Pairing the correct FASTA and FAI is a user obligation visible in input labels and documentation. No cached `dbkey`, `.loc`, or `from_data_table` dependency is introduced.

## Rebuild posture

Use **in-tool rebuild** for a missing FAI if the chosen Galaxy wrapper supports it. This avoids a workflow-tier conditional branch for one lightweight derived index. If no selected wrapper provides that behavior, implementation must either add a workflow-visible `samtools_faidx` step and route its output to all consumers or retain FAI as required for affected CRAM runs; the choice cannot be fabricated at this phase.

## iGenomes key disposition

Do not carry `--genome` as a Galaxy selector. It would require an admin-curated mapping from names to files, contrary to the portability-first reference-data mapping. The explicit FASTA/FAI inputs preserve the scientific capability for user-supplied references but drop automatic iGenomes nickname resolution. This is recorded as a dropped feature in `open-requirements.ledger.yml`.

## Open questions carried forward

1. Which selected Galaxy path will create an FAI when it is missing, and can one rebuilt index fan out to every consumer?
2. Where will CRAM-without-FASTA be rejected clearly, given the lack of conditional workflow-input requiredness?
3. Can tests include both supplied-FAI and absent-FAI CRAM cases, or only the supplied-reference path?
