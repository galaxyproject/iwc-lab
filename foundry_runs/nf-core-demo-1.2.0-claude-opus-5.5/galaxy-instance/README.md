# Importing nf-core/demo into a Galaxy instance

These files are for Galaxy servers that do **not** allow user-defined tools (UDTs). The main deliverable `../galaxy-workflow.gxwf.yml` embeds cowpy as a UDT, and such servers reject it.

## Which file to use

| Your situation | Import this file | Extra setup |
|---|---|---|
| Public server (usegalaxy.eu / .org) or any server where you cannot add tools | `nf-core-demo.no-cowpy.ga` | None. FastQC, seqtk and MultiQC at the pinned versions are already installed on usegalaxy.eu and usegalaxy.org. |
| Your own or institute server where an admin can add one tool | `nf-core-demo.cowpy-tool.ga` | Admin adds `tools/cowpy_say.xml` to the toolbox (see below) |

The `.gxwf.yml` files are the same workflows in Galaxy's YAML (format2) syntax. Galaxy can import either form, and `.ga` is the most widely accepted.

The no-cowpy variant only drops the `cowpy_output` ("nf-core rules!" ASCII art). All QC and trimming outputs are unchanged.

## Import

1. Galaxy → **Workflows** → **Import** → upload the `.ga` file (or paste its URL).
2. If Galaxy reports missing tools, an admin installs these from the main Tool Shed:
   - `devteam/fastqc` revision `2c64fded1286` (FastQC 0.74+galaxy1)
   - `iuc/seqtk` revision `c8fb17965c7d` (seqtk_trimfq 1.5+galaxy0)
   - `iuc/multiqc` revision `94b6bea727ae` (MultiQC 1.35+galaxy5)

## Admin: adding the cowpy tool (cowpy-tool variant only)

1. Copy `tools/cowpy_say.xml` to the server, e.g. `<galaxy>/tools/local/cowpy_say.xml`.
2. Add it to a tool config such as `tool_conf.xml`:
   ```xml
   <section id="local" name="Local tools">
     <tool file="local/cowpy_say.xml"/>
   </section>
   ```
3. The tool runs in the container `community.wave.seqera.io/library/cowpy:1.1.5--3db457ae1977a273`, so the server needs Docker or Singularity/Apptainer job execution.
4. Restart Galaxy (or reload the toolbox).

## Running it

1. Upload your FASTQs (`fastqsanger.gz`).
2. Build a **list of paired-or-unpaired** collection with one element per samplesheet row, named `<sample>_<run>` (e.g. `SAMPLE1_PE_sample1`). Paired rows get forward + reverse; single-end rows get one file.
3. Run the workflow with `reads` = that collection, `skip_trim` (default false) and, optionally, `multiqc_title`.

## Running with the nf-core test data

The nf-core `-profile test` inputs are public URLs (nf-core/test-datasets, viralrecon branch). `nf-core-test-data.urls.tsv` lists the four collection elements and their URLs.

**Option 1: one command (Planemo uploads the data and builds the collection).** Get an API key from the server (User → Preferences → Manage API Key), then:

```bash
planemo run nf-core-demo.no-cowpy.ga nf-core-test-data.job.yml \
  --engine external_galaxy --galaxy_url https://usegalaxy.eu --galaxy_user_key <YOUR_API_KEY> \
  --history_name "nf-core/demo test data"
```

Add `--output_directory results --download_outputs` to also download the outputs.

**Option 2: Galaxy web UI.**
1. Upload → **Paste/Fetch data**, paste the four distinct URLs from the TSV, and set the type to `fastqsanger.gz`.
2. Build a list of paired-or-unpaired datasets:
   - `SAMPLE1_PE_sample1` = sample1_R1 + sample1_R2
   - `SAMPLE2_PE_sample2` = sample2_R1 + sample2_R2
   - `SAMPLE3_SE_sample1` = sample1_R1 alone
   - `SAMPLE3_SE_sample2` = sample2_R1 alone

   The SE elements reuse the R1 files, exactly as the nf-core test samplesheet does.
3. Run the workflow on that collection with `skip_trim` = No.

## Testing locally (optional)

```bash
planemo test nf-core-demo.no-cowpy.gxwf.yml                               # no-cowpy variant
planemo test --extra_tools tools/cowpy_say.xml nf-core-demo.cowpy-tool.gxwf.yml   # cowpy-tool variant
```

Each `*.gxwf-tests.yml` holds two tests (the nf-core `-profile test` case and `skip_trim: true`). Expected files are in `test-data/` (a symlink to `../test-data`).
