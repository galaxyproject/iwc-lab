# Foundry Run Review: Issues & Conversion Findings

**Target Platform:** Galaxy Australia (`usegalaxy.org.au`)  
**Source Pipelines:** `nf-core/demo`, `OceanOmics-amplicon-nf` (QC & Trimming Subworkflow)  
**Date:** March 2025  
**Review Status:** Completed / Issues Cataloged & Mitigated  

---

## 1. Executive Summary

During the translation and deployment of Nextflow DSL2 pipelines to Galaxy Australia, several failure modes were encountered during workflow import and editor rendering (`AxiosError 500`). These were resolved by formulating hardening strategies:
1. Handling uninstalled target tools via native in-tree primitives (`cat1` and collection combiners).
2. Soft-binding workflow definitions by omitting rigid Tool Shed changeset hashes.
3. Sanitizing brittle `tool_state` parameter trees (specifically removing nested `__current_case__` dictionaries).

---

## 2. Issues Discovered & Root Cause Analysis

### Issue 1: Import Rejection (`Missing workflow marker`)
* **Symptom:** Galaxy workflow import rejects file with error: `File does not appear to be a Galaxy workflow (.ga). Missing workflow marker.`
* **Root Cause:** 
  * The root dictionary lacked the exact top-level indicator `"a_galaxy_workflow": "true"`.
  * Uploading markdown-wrapped JSON (` ```json ... ``` `) or malformed text blocks rather than raw JSON.
* **Mitigation:**
  * Enforce standard top-level JSON boilerplate:
    ```json
    "a_galaxy_workflow": "true",
    "format-version": "0.1"
    ```
  * Ensure files are exported directly with the `.ga` extension.

---

### Issue 2: Workflow Editor Canvas Crash (`AxiosError: Request failed with status code 500`)
* **Symptom:** Workflow imports successfully, but clicking **Edit** triggers an unhandled `500 Server Error` on the Galaxy API route `GET /api/workflows/{id}/editor`.
* **Root Cause Mechanisms:**
  1. **Uninstalled Tools:** Tools present in the pipeline (e.g., `cowpy` in `nf-core/demo`, `seqkit` in OceanOmics) are absent from the Galaxy Australia tool registry (`app.toolbox.get_tool() == None`). When the editor attempts to construct input parameter schemas, it encounters an unhandled `AttributeError`.
  2. **Tool Shed Changeset Hash Pinning:** Exporting workflows locked to a specific 12-character `changeset_revision` fails when the host server runs a different point update or revision.
  3. **Brittle Parameter Trees (`__current_case__`):** Serialized `tool_state` structures containing hardcoded conditional case indices (e.g., `software_cond: {"__current_case__": 8}`) crash during form generation when wrapper definitions change between versions.
  4. **Bare Short IDs vs. Full Tool Shed URIs:** On Galaxy Australia, installed Tool Shed tools require their full repository path (e.g., `toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc`). Using bare short IDs (`"fastqc"`) causes tool lookup misses.

---

## 3. Recommended Remediation & Foundry Rules

### Rule A: Missing Tool Substitution Policy
When designing workflows or porting modules absent from the target Galaxy instance:
* **Single-Dataset Streams:** Replace with built-in `cat1` (*Concatenate datasets tail-to-head*).
  * *Constraint:* Must wire an incoming connection into `input1` (`ConnectedValue`) or leave `tool_state: "{}"` to prevent unpopulated parameter errors.
* **Multi-File / Collection Streams:** Replace with built-in `__MERGE_COLLECTION__` (*Merge Collections*) or `__CONCATENATE_DATASET_COLLECTION__`.

### Rule B: Workflow Soft-Binding (Hardening)
To ensure workflows remain portable across arbitrary Galaxy instances:
* **Remove `tool_shed_repository` Blocks:** Omit `changeset_revision` and repository metadata blocks; use only the base Tool Shed URI in `tool_id` and `content_id`.
* **Sanitize `tool_state`:**
  * Default to `tool_state: "{}"` for tool steps. This forces Galaxy's form generator to safely hydrate default values from its local tool XML.
  * For wired parameters, declare only explicit connected inputs:
    ```json
    "tool_state": "{\"input_file\": {\"__class__\": \"ConnectedValue\"}}"
    ```

---

## 4. Pipeline-Specific Resolution Records

### A. `nf-core/demo`
| Pipeline Step | Target Status (Galaxy AU) | Resolution / Mapping |
| :--- | :--- | :--- |
| `FASTQC` | Available | Mapped to `devteam/fastqc/fastqc` |
| `SEQTK_TRIM` | Available | Mapped to `iuc/seqtk/seqtk_trimfq` |
| `COWPY` | **Missing** | Substituted with `cat1` placeholder (`placeholder_cowpy_cat`) |
| `MULTIQC` | Available | Mapped to `iuc/multiqc/multiqc` with sanitized state |

### B. `OceanOmics-amplicon-nf` (QC Subworkflow)
| Pipeline Step | Target Status (Galaxy AU) | Resolution / Mapping |
| :--- | :--- | :--- |
| `FastQC` | Available | Full Tool Shed URI, sanitized `tool_state: "{}"` |
| `Cutadapt` | Available | Full Tool Shed URI, sanitized `tool_state: "{}"` |
| `SeqKit stats` | **Missing** | Substituted with `cat1` placeholder connected to Cutadapt report |
| `MultiQC` | Available | Full Tool Shed URI, sanitized `tool_state: "{}"` |

---

## 5. Artifact Checklist

- [x] Hardened Galaxy Australia `.ga` definitions verified against 500 error scenarios.
- [x] In-tree fallback substitution policy established for single-dataset and collection flows.
- [x] Standalone interactive visualizer generated for DAG pre-import validation.
- [x] Conversion rules codified into `SKILL.md`.