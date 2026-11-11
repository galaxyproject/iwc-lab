# Checklist: Nextflow → Galaxy conversion with Foundry (lessons from nf-core/demo)

Give this file to the agent before it starts. Each item cost at least one failed attempt in the nf-core/demo run.

## 1. Tool versions

- [ ] **Planemo: latest PyPI release** (0.75.48 as of 2026-11-10; check `https://pypi.org/pypi/planemo/json`). Older versions crash with `KeyError: 'tool_id'` on workflows with embedded user-defined tools (UDTs), and only 0.75.48+ grants the UDT execution role automatically. Install it in its own venv: `uv venv -p 3.12 venv && uv pip install planemo`.
- [ ] **Galaxy: current `master`, freshly fetched.** Record the commit (`git rev-parse`) in the test result. An old checkout (`b18269a10f8`, 2026-10-07) caused an import 500 that Galaxy had already fixed (galaxy#24471 / PR #24475). Before treating any Galaxy error as a new bug, search the Galaxy tracker for the exception.
- [ ] **Python ≥ 3.10 for Galaxy.** The host `python3` is 3.9. Pass `--galaxy_python_version 3.12` and put a 3.12 interpreter on `PATH`, e.g. `<uv>/python/cpython-3.12.*/bin`.

## 2. Containers only, no conda

- [ ] Disable conda: `--no_dependency_resolution --no_conda_auto_install --no_conda_auto_init`. With conda, every Tool Shed install failed (conda's shebang picked up Galaxy's venv Python).
- [ ] Use Apptainer/Singularity; there is no Docker on the host. A job conf with `singularity_enabled: true` and `require_container: true`:
  ```yaml
  runners: {local: {load: galaxy.jobs.runners.local:LocalJobRunner, workers: 4}}
  execution:
    default: singularity
    environments:
      singularity:
        runner: local
        singularity_enabled: true
        require_container: true
        singularity_volumes: '$defaults,<workdir>:ro,<data dirs>:ro'
  ```
- [ ] **Prefetch `.sif` images from `https://depot.galaxyproject.org/singularity/`**. Don't let Apptainer convert `docker://` images, which takes more than 10 minutes per image. Derive mulled names with `mulled-hash pkg1=ver,pkg2=ver` from the wrapper's `<requirements>`. For nf-core/demo:
  - `fastqc:0.12.1--hdfd78af_0`
  - `mulled-v2-b8f6f9860663fb4ab74531715c96bb5f4fe84284:5ff5040a455c380ee210cc964f11047f8be16576-0` (seqtk 1.5 + pigz 2.8)
  - `mulled-v2-8374e50c663bfd36021a9219b02d97e9c4baaad5:783e4c36591c28e0c25d1c1084e0a4a5ca32fd17-0` (multiqc 1.35 + python 3.13 + grep 3.12)
- [ ] Container resolvers file:
  ```yaml
  - type: explicit_singularity
  - type: cached_mulled_singularity
    cache_directory: <dir with the depot .sif files>
  ```
- [ ] For nf-core local modules, use the module's own Singularity URL (in `main.nf`). Example, cowpy: `https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/1a/1a1f…/data`.
- [ ] Get wrapper requirements from GitHub (`galaxyproject/tools-iuc` and similar). Tool Shed `raw-file` URLs and the tool cache's `raw_tool_source_path` returned nothing.

## 3. Environment details

- [ ] **Keep `TMPDIR` short (under ~100 chars).** A long scratch path breaks Galaxy's Celery forkserver (`OSError: AF_UNIX path too long`, only visible in the server log), and `__DATA_FETCH__` then hangs forever. Use e.g. `TMPDIR=/data/tmp/<job>/gxtmp`.
- [ ] Don't delete or modify `~/.planemo/` (cached Galaxy repo and venvs). Use a new venv name or `--no_cache_galaxy` instead.
- [ ] **Persistent server instead of per-test boots:** run `planemo serve <workflow> --extra_tools … --job_config_file … --container_resolvers_config_file …` once, then `planemo test --engine external_galaxy --galaxy_url http://127.0.0.1:<port> --galaxy_admin_key test_key --galaxy_user_key <non-admin key>`.
  - `planemo serve` does **not** install the workflow's Tool Shed repos; install them through the admin API (`bioblend toolshed.install_repository_revision`, pinned changesets).
  - For embedded UDTs, create a non-admin user and grant the `user_tool_execute` role (`planemo.galaxy.api.ensure_user_tool_execute`).
- [ ] Stop the server afterwards: kill `planemo serve`, then the gunicorn/celery processes from that Galaxy directory.

## 4. Workflow authoring rules

- [ ] **Comment frames:** always give `position` **and** `size` (Galaxy rejects frames without them), use `color:` not `colour:`, give **every input and step a `position`**, and size each frame around its `contains_steps`. Frames without step positions end up empty after import and break saving in the Galaxy editor (`Input should be a valid number in ('frame','position',0)`).
- [ ] Run `gxwf validate --strict` (or draft-validate `--strict`) in **every** draft iteration, not only at the end.
- [ ] Unconnected optional data inputs: **leave the key out** of the tool state; `null` fails `--strict-state`.
- [ ] Mixed single/paired samplesheets: input `list:paired_or_unpaired` → `__FLATTEN__` (`join_identifier: _`) → per-file tools → MultiQC. Element identifiers become `<element>_forward|reverse|unpaired`.
- [ ] Element identifiers must be unique per row: `<sample>_<run>` (e.g. `SAMPLE3_SE_sample1`), not positional `_1`/`_2`.
- [ ] FastQC → MultiQC: feed FastQC's `text_file` (raw data) to MultiQC with `software: fastqc` (IWC idiom).

## 5. Deliverables: produce both forms

- [ ] An embedded-UDT form, for servers that allow user-defined tools (needs Galaxy 26.1 with galaxy#24475, `enable_beta_tool_formats`, and the user_tool_execute role).
- [ ] **A form without UDTs** (`.ga` + `.gxwf.yml`) for public servers (usegalaxy.*): drop the UDT step, or reference an XML version of the tool by `tool_id`. Convert with `gxwf-to-native` and check with `planemo workflow_lint`.
- [ ] Check that the target server has the exact tool versions: `GET /api/tools/<id>?tool_version=<v>` and look at `.version`. A plain 200 can be a different version.

## 6. Tests

- [ ] nf-test md5 for `*.fastq.gz` is computed over **decompressed** content, and Galaxy compresses with pigz, so a plain `checksum:` will fail. Use `file:` fixtures + `decompress: true` + `compare: diff`. Regenerate the fixtures in the wrapper's own container and check their decompressed md5 against the snapshot.
- [ ] Add a test for every `when:`-gated branch (e.g. `skip_trim: true`). Skipped step outputs are null datasets (`has_text: "null"`).
- [ ] MultiQC md5s don't carry over (version and sample names differ). Compare general-stats values, not hashes.
- [ ] Scalar inputs (booleans, strings) have no slot in the test-data refs or test-plan fixtures. Put them in the test job directly.

## 7. Validation against the real Nextflow run

- [ ] Run the Nextflow pipeline with `-profile test` and keep `results/`.
- [ ] After the Galaxy run, make a per-file comparison: file name, raw bytes, content (decompressed reads, FastQC statistics, MultiQC general stats), files missing on either side, tool-version differences. Foundry doesn't produce this itself.
- [ ] Planemo's `--download_outputs` names files by dataset UUID. Map them back to `<output>/<element_identifier>` through the invocation API.

## 8. Running on a public server (e.g. usegalaxy.be)

- [ ] `planemo run <workflow>.ga <job>.yml --engine external_galaxy --galaxy_url https://usegalaxy.be --galaxy_user_key $KEY --history_name … --output_directory … --download_outputs`
- [ ] Pass the API key only through an environment variable and never write it to files or logs. Ask the user to rotate it afterwards if it was shared in chat.

## 9. Feedback mode

- [ ] Keep `foundry-feedback.ledger.yml` up to date in every phase. At the end, run `report-foundry-run-feedback`, check Foundry main hashes, search existing issues (#580, #576, #726, #730, #743, #762–#765 already cover some of this), and post nothing without the user's confirmation.
