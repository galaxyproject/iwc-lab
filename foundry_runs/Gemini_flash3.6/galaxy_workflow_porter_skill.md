---
name: galaxy-workflow-porter
description: Converts external computational pipelines (Nextflow DSL2, Snakemake, CWL, WDL) into hardened, import-safe Galaxy `.ga` workflow definitions and self-contained interactive visualizers. Handles tool availability audits, soft-binding against HTTP 500 editor crashes, missing tool substitution, and instant in-chat DAG visualization.
---

# Galaxy Workflow Porter & Visualizer Skill (SKILL.md)

A standardized operational manual and prompt guide for translating external data pipelines into hardened, import-safe Galaxy workflow definitions (`.ga` / JSON) that load without backend crashes across disparate Galaxy servers (e.g., Main, Europe, Australia), with built-in instant visual validation.

---

## 1. End-to-End Operational Pipeline

```
[External Pipeline: Nextflow / Snakemake / CWL]
                        │
                        ▼
    Phase 1: Parse Topology & Channel Flow
    • Map inputs/samplesheets to dataset or collection inputs.
    • Map tasks/processes to tool nodes.
    • Trace directed acyclic graph (DAG) connections.
                        │
                        ▼
    Phase 2: Target Galaxy Server Availability Audit
    • Resolve tools against the Main Tool Shed (`toolshed.g2.bx.psu.edu`).
    • Check target instance toolbox (e.g., usegalaxy.org.au, usegalaxy.eu).
    • Segregate native tools from missing/custom modules.
                        │
                        ▼
    Phase 3: Apply Missing Tool Substitution Policy
    • Single dataset stream ──► Core `cat1` ("Concatenate datasets tail-to-head")
    • Collection stream     ──► Core `__MERGE_COLLECTION__` or `__CONCATENATE_DATASET_COLLECTION__`
                        │
                        ▼
    Phase 4: Workflow Hardening (Soft-Binding)
    • Strip brittle Tool Shed `changeset_revision` hashes.
    • Collapse fragile parameter trees to minimalist `tool_state: "{}"`.
    • Wire mandatory inputs explicitly to avoid serialization crashes.
                        │
                        ▼
    Phase 5: Format Assembly & Schema Validation
    • Add root marker: `"a_galaxy_workflow": "true"`.
    • Verify step IDs match key indices (`"0"`, `"1"`, ...).
                        │
                        ▼
    Phase 6: Instant In-Chat Visual Validation
    • Generate a single-file Tailwind + SVG interactive visualizer HTML artifact.
    • Inspect nodes, splines, and step inspector before importing to Galaxy.
```

---

## 2. Hardening & Soft-Binding Rules

Galaxy instances dynamically reconstruct workflow form states upon opening the workflow editor (`GET /api/workflows/{id}/editor`). If a tool revision or parameter mismatch occurs, the backend throws an unhandled exception resulting in **`AxiosError: Request failed with status code 500`**.

### Rule 2.1: Full Repository URIs vs. Short IDs
* **Never use bare short IDs for Tool Shed tools** on production instances (like Galaxy Australia or Europe). The Galaxy toolbox registers tools under their full repository paths.
  * ❌ *Brittle*: `"tool_id": "fastqc"` or `"tool_id": "cutadapt"`
  * ✅ *Robust*: `"tool_id": "toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc"`
* **Core built-in tools** use their exact canonical short IDs (e.g., `"cat1"`, `"Select1"`, `"__MERGE_COLLECTION__"`).

### Rule 2.2: Omit Locked Changeset Revisions
* Do not lock workflow steps to specific 12-character Tool Shed changeset hashes (`tool_shed_repository.changeset_revision`) when creating portable workflows.
* Omitting the specific hash allows the destination Galaxy server to resolve the step against whichever point release or wrapper revision is currently installed locally.

### Rule 2.3: Minimal Safe `tool_state` Pattern
* **Avoid exporting deeply nested parameter trees**, especially dictionaries containing integer indices (e.g., `"__current_case__": 8`). Tool wrapper updates shift conditional branch indices, causing fatal `IndexError` or `KeyError` crashes in Galaxy's form builder.
* **Safe State Formula**:
  * For tools where user defaults suffice:
    ```json
    "tool_state": "{}"
    ```
  * For tools requiring input parameter wiring:
    ```json
    "tool_state": "{\"input_file\": {\"__class__\": \"ConnectedValue\"}}"
    ```

---

## 3. Missing Tool Substitution Matrix

When an external pipeline relies on tools not installed on the destination Galaxy instance (or local demo scripts such as `cowpy`):

| Input Data Topology | Primary Galaxy Replacement Tool | Fallback Galaxy Tool | Parameter Wiring Protocol |
| :--- | :--- | :--- | :--- |
| **Single Dataset** | `cat1`<br>*(Concatenate datasets tail-to-head)* | `Select1`<br>*(Select lines matching pattern)* | Wire upstream dataset directly into `input1` (`ConnectedValue`) to avoid unpopulated parameter errors. |
| **Dataset Collection** | `__MERGE_COLLECTION__`<br>*(Merge Collections)* | `__CONCATENATE_DATASET_COLLECTION__` | Preserves list/paired collection structure through downstream operations. |
| **Pure Metadata / Text** | `cat1` | `data_input` | Mark as optional input if no runtime processing occurs. |

---

## 4. Top-Level Workflow Schema Contract

To pass Galaxy's import filter without triggering `"File does not appear to be a Galaxy workflow (.ga). Missing workflow marker."`, the JSON must adhere to this schema:

```json
{
  "a_galaxy_workflow": "true",
  "format-version": "0.1",
  "name": "Pipeline Name (Target Server Compatible)",
  "annotation": "High-level summary of pipeline stages and substitutions",
  "creator": [
    {
      "class": "Person",
      "name": "me"
    }
  ],
  "steps": {
    "0": {
      "id": 0,
      "type": "data_collection_input",
      "label": "input_collection",
      "tool_id": null,
      "tool_version": null,
      "tool_state": "{\"collection_type\": \"paired\"}",
      "inputs": [{ "name": "input_collection", "description": "Raw inputs" }],
      "outputs": [],
      "input_connections": {},
      "position": { "left": 150, "top": 200 }
    },
    "1": {
      "id": 1,
      "type": "tool",
      "label": "standard_tool",
      "name": "Tool Name",
      "tool_id": "toolshed.g2.bx.psu.edu/repos/<owner>/<repo>/<tool_name>",
      "content_id": "toolshed.g2.bx.psu.edu/repos/<owner>/<repo>/<tool_name>",
      "tool_version": null,
      "tool_state": "{}",
      "errors": null,
      "inputs": [],
      "outputs": [{ "name": "output_file", "type": "txt" }],
      "input_connections": {
        "input_param": { "id": 0, "output_name": "output" }
      },
      "position": { "left": 450, "top": 200 }
    }
  },
  "tags": ["ported", "pipeline"],
  "uuid": "<rfc4122-uuid4-string>"
}
```

---

## 5. Instant In-Chat Visualizer Specification

To inspect and verify the workflow graph before uploading it to a live Galaxy instance, Gemini can generate a standalone, single-file HTML artifact containing an interactive visual canvas.

### Visualizer Architecture Requirements
1. **Single-File Delivery**: All HTML, JavaScript, and Tailwind CSS (via CDN) contained within one file block.
2. **Interactive Viewport**:
   * Pan across grid via canvas background dragging.
   * Zoom dynamically via mouse wheel or top toolbar controls (`+`, `-`, `Reset`).
   * Drag-and-drop step cards; recalculate Bezier SVG wires dynamically.
3. **Cubic Bezier Splines**:
   * Wires originate from source output ports (right card boundary) to target input ports (left card boundary).
   * Formula:
     $$C(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$
     Where $P_1 = P_0 + (\Delta x \cdot 0.5, 0)$ and $P_2 = P_3 - (\Delta x \cdot 0.5, 0)$.
4. **Node Card Badges**:
   * Green (`emerald`): Data Inputs / Collections.
   * Blue (`sky`): Standard Installed Tools.
   * Amber (`amber`): Soft-Bound Placeholders (`cat1` / `__MERGE_COLLECTION__`).
5. **Inspector Drawer**:
   * Displays Step ID, Tool Shed Content ID, Annotations, Port Connections, and Step JSON.
6. **Full JSON Modal**:
   * Includes one-click clipboard copy of the entire `.ga` payload.

---

## 6. Prompt Engineering Patterns

### Pattern 1: Tool Availability & Target Instance Audit
```text
Audit the following [Nextflow/Snakemake] pipeline script for deployment on Galaxy [Target: e.g., usegalaxy.org.au]:
[PASTE CODE]

Please:
1. Identify all software tools, scripts, and local processes.
2. Check tool availability on the target Galaxy instance.
3. Classify missing tools and propose standard substitutions (cat1 for single files, __MERGE_COLLECTION__ for collections).
```

### Pattern 2: Hardened `.ga` Workflow Generation
```text
Convert the analyzed pipeline into a valid, hardened Galaxy workflow (.ga file):
Constraints:
- Include root markers: "a_galaxy_workflow": "true", "format-version": "0.1".
- Use full Tool Shed URIs without pinned changeset_revision hashes.
- Set tool_state: "{}" (or strictly minimalist ConnectedValue references) to avoid 500 editor crashes.
- Substitute missing tools using the agreed placeholder policy.
- Include the creator block: [{"class": "Person", "name": "me"}].
```

### Pattern 3: Visualizer Generation
```text
Generate a self-contained interactive Galaxy Workflow Visualizer HTML artifact for the following .ga workflow JSON:
[PASTE JSON]

Ensure it includes pan/zoom navigation, Bezier curve spline connections, color-coded node badges (inputs, tools, placeholders), a step inspector sidebar, and a full JSON export modal.
```

---

## 7. Edge Case Troubleshooting Runbook

| Symptom / Error | Root Cause | Immediate Remediation |
| :--- | :--- | :--- |
| **`Missing workflow marker`** during import | Missing `"a_galaxy_workflow": "true"` at root, or file wrapped in markdown fences/text. | Ensure raw JSON has `"a_galaxy_workflow": "true"` at the root key level. |
| **`AxiosError: 500`** on clicking **Edit** | 1. Uninstalled tool ID.<br>2. Pinned non-existent `changeset_revision`.<br>3. Mismatched `__current_case__` in `tool_state`. | 1. Replace uninstalled tool with `cat1`.<br>2. Remove `tool_shed_repository` block.<br>3. Reset `tool_state` to `"{}"`. |
| **`cat1` causes form error** | `input1` parameter declared without an incoming wire (`ConnectedValue`). | Connect an upstream dataset wire to `input1` or set `tool_state: "{}"`. |
| **Collection Type Mismatch** | Paired collection wired into a tool expecting a flat dataset list. | Configure step as collection mapping (batch mode) or insert a collection flattening tool. |
| **Output Name Disconnect** | Nextflow process output name does not match the Galaxy tool wrapper output name (e.g., `report` vs `text_file`). | Inspect Tool Shed wrapper XML for exact `<data name="..." />` or `<collection name="..." />` identifiers. |