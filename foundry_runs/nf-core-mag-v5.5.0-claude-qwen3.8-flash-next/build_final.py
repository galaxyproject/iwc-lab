#!/usr/bin/env python3
"""Assemble the final summary-nextflow.json from base.json + hand-authored sections."""
import json, ast

base = json.load(open("/home/abennett/nf-core-mag/base.json"))

TESTDATA = "https://raw.githubusercontent.com/nf-core/test-datasets/refs/heads/mag/"

def norm_default(v):
    if v is None:
        return None
    v = v.strip()
    if v in ("null", '""', "''"):
        return None
    try:
        return ast.literal_eval(v)
    except Exception:
        return v.strip("'\"")

for p in base["params"]:
    p["default"] = norm_default(p["default"])
    if p.get("enum") is None:
        p["enum"] = []

# schema hygiene on deterministic pass output
for pr in base["processes"]:
    for io in pr["inputs"] + pr["outputs"]:
        if io.get("description") is None:
            io["description"] = ""
    m = pr.get("meta")
    if isinstance(m, dict):
        for t in m.get("tools", []):
            if not isinstance(t.get("doi"), str):
                t.pop("doi", None)

for sw in base["subworkflows"]:
    for io in sw.get("inputs", []) + sw.get("outputs", []):
        if io.get("description") is None:
            io["description"] = ""

# ---------------------------------------------------------------- script summaries
SUM = {
"GUNZIP": "Decompress gz/bz2/xz/zst files with the matching tool (gzip/lbzip2 etc.) and link the result.",
"PYPOLCA_RUN": "Polish a long-read assembly with short reads via PyPolca (pypolca polish, --careful by default).",
"PRODIGAL": "Predict prokaryotic coding sequences on assemblies with prodigal -p meta; GFF or table output per val outformat.",
"FIND_CONCATENATE": "Concatenate many (optionally gzipped) files found by name pattern into one output, sidestepping argv limits.",
"CHECKM_QA": "Score bin completeness/contamination with checkm qa against a lineage marker set from lineage_wf.",
"CHECKM_LINEAGEWF": "Place bins on the CheckM reference tree with checkm lineage_wf to find their lineages.",
"BUSCO_BUSCO": "Assess completeness and duplication against BUSCO ortholog lineages with busco run (genome mode here).",
"SEMIBIN_SINGLEEASYBIN": "Bin metagenomic contigs with SemiBin2 single_easy_bin using per-sample BAM depths.",
"UNTAR": "Extract .tar/.tar.gz/.tar.bz2/.tar.xz archives into a per-input directory.",
"MINIMAP2_INDEX": "Build a minimap2 .mmi index from the assembly for long-read alignment.",
"MINIMAP2_ALIGN": "Align long reads to the assembly with minimap2 -ax, sort with samtools, index, and emit stats.",
"PROKKA": "Annotate prokaryotic bins with prokka (metagenome mode; fast/compliance args wired via modules.config).",
"MULTIQC": "Aggregate all collected MultiQC-compatible files into one HTML report plus data dir.",
"SAMTOOLS_INDEX": "Index BAM/CRAM files with samtools index (bai/csi by input type).",
"SAMTOOLS_FAIDX": "Index FASTA with samtools faidx, optionally emitting chromosome sizes.",
"SAMTOOLS_STATS": "Produce per-alignment statistics from BAM with samtools stats.",
"NANOPLOT": "Summarize long-read quality/length distributions with NanoPlot (raw or filtered fastq).",
"COMEBIN_RUNCOMEBIN": "Bin contigs with COMEBin using the assembly plus co-mapped BAM alignments.",
"NANOLYSE": "Remove lambda phage reads from a fastq stream with NanoLyse -r reference.",
"GTDBTK_CLASSIFYWF": "Assign GTDB taxonomy to bins with gtdbtk classify_wf against the GTDB-Tk database.",
"FASTQC": "Per-sample per-lane sequence QC with FastQC; zips collected to MultiQC.",
"CONCOCT_CONCOCTCOVERAGETABLE": "Build the CONCOCT per-contig coverage table from BAM-derived bed/depth input.",
"CONCOCT_CUTUPFASTA": "Cut contigs into equal (overlapping) fragments with cut_up_fasta.py for CONCOCT.",
"CONCOCT_CONCOCT": "Cluster cut-up fragments into bins with concoct clustering on coverage + 4-mer composition.",
"CONCOCT_EXTRACTFASTABINS": "Write one FASTA per CONCOCT cluster with extract_fasta_bins.py (min contig size kept).",
"CONCOCT_MERGECUTUPCLUSTERING": "Merge per-fragment cluster labels back to whole contigs with merge_cutup_clustering.py.",
"GUNC_MERGECHECKM": "Merge GUNC and CheckM QC tables per bin with gunc merge_checkm.",
"GUNC_DOWNLOADDB": "Download a GUNC classification database (progenomes/refseq/...) with gunc download_db.",
"GUNC_RUN": "Detect chimeric/contaminated bins with gunc run on the bin FASTA list.",
"METAMDBG_ASM": "Assemble long reads (ont/hifi mode) with metaMDBG run_mdbg.py; gzip contigs.",
"SEQKIT_STATS": "Per-sequence length statistics of bins with seqkit stats --tabular (used for bin size filtering).",
"FREEBAYES": "Call variants of the mapped reads vs the assembly with freebayes (ploidy/quality args from config).",
"BCFTOOLS_INDEX": "Index a VCF with bcftools index (csi/tabix per args).",
"BCFTOOLS_VIEW": "Filter/convert VCF with bcftools view (variant quality thresholds via config).",
"BCFTOOLS_CONSENSUS": "Apply called variants to the assembly with bcftools consensus to get damage-corrected contigs.",
"CHECKM2_PREDICT": "Predict bin completeness/contamination with checkm2 predict against its quality DB.",
"CHECKM2_DATABASEDOWNLOAD": "Download the CheckM2 quality database for a pinned Zenodo version with aria2c.",
"DASTOOL_DASTOOL": "Cross-map binner outputs and produce refined non-redundant bin sets with DAS Tool.",
"DASTOOL_FASTATOCONTIG2BIN": "Convert per-binner bin FASTAs into DAS Tool scaffold2bin tables.",
"METABAT2_METABAT2": "Bin contigs with MetaBAT2 using the cleaned depth file; bins and unbinned emitted as fastas.",
"METABAT2_JGISUMMARIZEBAMCONTIGDEPTHS": "Compute per-contig depth across one or more BAMs with jgi_summarize_bam_contig_depths.",
"TRIMMOMATIC": "Adapter/quality trim paired or single-end reads with trimmomatic (phred33, standard windows via config).",
"MEGAHIT": "Assemble short reads (per sample or co-assembled group) with megahit, then pigz the contig fasta.",
"NANOQ": "Filter long reads by length/quality and emit stats with nanoq filter.",
"GENOMAD_ENDTOEND": "Identify viruses and proviruses in assemblies with genomad end-to-end (min score via config).",
"GENOMAD_DOWNLOAD": "Download the geNomad protein and nucleotide reference databases.",
"QSV_CAT": "Concatenate CSV/TSV tables with qsv cat; 'rowskey' mode merges on the first column (key-based row union).",
"CATPACK_CONTIGS": "Classify unbinned contigs taxonomically with CAT cat_contigs against the CAT db.",
"CATPACK_PREPARE": "Build a CAT pack database (CAT_prepare) from fasta/names/nodes/acc2tax source files.",
"CATPACK_SUMMARISE": "Roll up CAT/BAT per-contig classifications into per-bin or per-contig lineage summaries.",
"CATPACK_DOWNLOAD": "Download CAT database source files (Nr or GTDB) with CAT_download.",
"CATPACK_ADDNAMES": "Map taxids in bin/contig classification tables to lineage names (cat_add_names, BAT step).",
"CATPACK_BINS": "Classify bins (MAGs) taxonomically with CAT cat_bins against the CAT db.",
"METAEUK_EASYPREDICT": "Predict proteins on eukaryotic bins with metaeuk easy-predict against an mmseqs MetaEuk db.",
"FILTLONG": "Filter long reads by quality/length, optionally guided by matching short reads, with filtlong.",
"CHOPPER": "Trim adapters and quality-filter long reads with chopper filter (can co-remove lambda when given the fasta).",
"FLYE": "Assemble long reads in metagenomic mode with flye (--nano-raw/--nano-hq/--pacbio-* chosen per platform).",
"PORECHOP_ABI": "Trim ONT adapters/barcodes with porechop_abi.",
"PORECHOP_PORECHOP": "Trim ONT adapters with porechop.",
"TIARA_TIARA": "Classify contigs to bacteria/archaea/eukarya/organelle with tiara.",
"FASTP": "Adapter + quality trim reads with fastp (quality/length args from config); merged PE reads out, JSON/HTML to MultiQC.",
"CAT_FASTQ": "Concatenate fastq files (interleaving pairs for PE) into one file per sample.",
"SPADES": "Assemble with spades.py --isolate/--meta in short-read, --hybrid, or --metaspades mode; scaffolds/contigs picked per config.",
"BBMAP_BBNORM": "Normalize short-read coverage with bbnorm.sh (target/min from params) before assembly.",
"MAXBIN2": "Bin contigs with MaxBin2 run_abundance.pl using the reads and a converted abundance profile.",
"PYDAMAGE_FILTER": "Filter pydamage per-contig damage estimates to a MAPD accuracy threshold.",
"PYDAMAGE_ANALYZE": "Estimate aDNA deamination damage per contig with pydamage analyze from BAM.",
"ALE": "Compute assembly likelihood, error rate and GC statistics with ALE from BAM vs assembly.",
"ADAPTERREMOVAL": "Trim adapters and collapse overlapping reads with adapterremoval2 (SE or PE invocation per sample).",
"MMSEQS_DATABASES": "Download a URL database and convert it to mmseqs format for MetaEuk (mmseqs createdb/createindex).",
"SEQTK_MERGEPE": "Interleave paired-end fastq into a single file with seqtk mergepe (symlink passthrough for SE).",
"METABINNER_KMER": "Compute the per-contig k-mer composition profile with MetaBinner get_kmer_frequencies.py.",
"BIN_SUMMARY": "Merge depths/QUAST/GTDB-Tk/CAT/BUSCO/CheckM(2)/pydamage per-bin summaries into bin_summary.tsv.",
"PREPARE_BIGMAG_SUMMARY": "Join bin_summary.tsv with GUNC QC into a BigMag-ready table.",
"RENAME_PREDASTOOL": "Decompress and rename bin FASTAs into DAS-Tool-compatible <binner>_<bins> naming pre-refinement.",
"MAG_DEPTHS": "Compute per-bin per-sample depth tables from MetaBAT2 depth files (get_mag_depths.py).",
"RENAME_POSTDASTOOL": "Rename and recompress DAS Tool outputs into refined bin/unbinned .fa.gz sets.",
"BOWTIE2_ASSEMBLY_ALIGN": "Map one sample's short reads to an assembly with bowtie2 (preset via bowtie2_mode); sorted BAM + alignment log.",
"MAG_DEPTHS_SUMMARY": "Build the per-bin depth summary table from concatenated MAG depth TSVs (get_mag_depths_summary.py).",
"GTDBTK_SUMMARY": "Merge classified and QC-discarded bins into gtdbtk_summary.tsv (gtdbtk_summary.py).",
"BOWTIE2_REMOVAL_BUILD": "Build a bowtie2 index for a host/phiX removal reference fasta.",
"QUAST": "Evaluate an assembly with metaquast.py (reference-free, rna-finding); copy report dir + summary TSV.",
"BOWTIE2_REMOVAL_ALIGN": "Align reads to the host/phiX index and emit the unmapped (non-host) reads via samtools view -f 4.",
"SPLIT_FASTA": "Split an unbinned-contigs fasta; contigs above the length threshold become individual files, shorter ones are discarded.",
"QUAST_BINS": "Evaluate each bin group with metaquast.py and extract per-bin report.tsv rows.",
"SAMTOOLS_UNMAPPED": "Extract mapped and/or unmapped reads from a BAM with samtools view -F4/-f4.",
"BOWTIE2_ASSEMBLY_BUILD": "Build a bowtie2 index for a metagenome assembly (bt2_index_base).",
"METABINNER_BINS": "Extract MetaBinner bin FASTAs from the membership table; emits bins, unbinned, and too-short contigs.",
"TIARA_CLASSIFY": "Roll per-contig Tiara classifications up to per-bin domain calls (domain_classification.R, optparse/tidyverse).",
"METABINNER_METABINNER": "Run MetaBinner binning on length-filtered contigs with k-mer composition + depth inputs.",
"METABINNER_TOOSHORT": "Separate contigs above the min length (sizefiltered) from the too-short remainder for MetaBinner.",
"SUMMARISE_PYDAMAGEBINS": "Aggregate pydamage contig results to per-bin medians and map contigs to bins (summarise_pydamagebins.py).",
"CONVERT_DEPTHS": "Stream MetaBAT2 depth files into per-readset MaxBin2 abundance profiles with bioawk (no on-disk decompression).",
"GTDBTK_DB_PREPARATION": "Unpack a GTDB-Tk database tarball into the directory layout classify_wf expects.",
}
missing = [p["name"] for p in base["processes"] if p["name"] not in SUM]
assert not missing, missing

for p in base["processes"]:
    p["script_summary"] = SUM[p["name"]]

# ---------------------------------------------------------------- source
source = {"ecosystem": "nf-core", "workflow": "mag",
          "url": "https://github.com/nf-core/mag", "version": "5.5.0",
          "license": "MIT", "slug": "nf-core-mag"}

# ---------------------------------------------------------------- profiles
TPROF = lambda n, inc: {"name": n, "kinds": ["test"], "source_path": "nextflow.config",
    "includes": [inc], "signals": ["include:test-config", "sets-input-data", "params-assignment"]}
CONT = lambda n: {"name": n, "kinds": ["container"], "source_path": "nextflow.config",
    "includes": [], "signals": ["container-keys"]}
profiles = [
    {"name": "debug", "kinds": ["dev"], "source_path": "nextflow.config", "includes": [],
     "signals": ["dev-profile-name"]},
    CONT("conda"), CONT("mamba"),
    CONT("docker"),
    CONT("singularity"),
    CONT("podman"), CONT("shifter"),
    CONT("charliecloud"),
    CONT("apptainer"),
    CONT("wave"),
    CONT("arm64"),
    CONT("emulate_amd64"),
    CONT("gpu"),
    TPROF("test", "conf/test.config"),
    TPROF("test_minimal", "conf/test_minimal.config"),
    TPROF("test_full", "conf/test_full.config"),
    TPROF("test_alternatives", "conf/test_alternatives.config"),
    TPROF("test_single_end", "conf/test_single_end.config"),
    TPROF("test_longreadonly", "conf/test_longreadonly.config"),
    TPROF("test_longreadonly_alternatives", "conf/test_longreadonly_alternatives.config"),
    TPROF("test_hybrid", "conf/test_hybrid.config"),
    TPROF("test_assembly_input", "conf/test_assembly_input.config"),
]

# ---------------------------------------------------------------- sample sheets
def sheet(param, schema_path, cols):
    return {"param": param, "schema_path": schema_path, "discovered_via": "samplesheetToList",
            "format": "csv", "header": True, "columns": cols}
def col(name, kind, typ="string", req=False, fmt=None, pat=None, enum=None, exists=None, desc=None):
    return {"name": name, "type": typ, "kind": kind, "format": fmt, "required": req,
            "default": None, "description": desc, "enum": enum or [], "pattern": pat,
            "exists": exists, "mimetype": None}
sample_sheets = [
 sheet("input", "assets/schema_input.json", [
   col("sample", "meta", req=True, pat="^\\S+$", desc="Sample identifier; unique per (sample,run)."),
   col("run", "meta", typ="string", pat="^\\S+$", desc="Run identifier; runs of one sample are concatenated before assembly. unique per sample."),
   col("group", "meta", typ="string", req=True, pat="^\\S+$", desc="Co-assembly group."),
   col("short_reads_1", "data", fmt="file-path", pat="^\\S+\\.f(ast)?q\\.gz$", exists=True, desc="R1 fasta/fastq gz. Optional only if long_reads given (anyOf); if given, short_reads_platform is required."),
   col("short_reads_2", "data", fmt="file-path", pat="^\\S+\\.f(ast)?q\\.gz$", exists=True, desc="R2; requires short_reads_1 (dependentRequired)."),
   col("short_reads_platform", "meta", enum=["ILLUMINA","BGISEQ","LS454","ION_TORRENT","DNBSEQ","ELEMENT","ULTIMA","VELA_DIAGNOSTICS","GENAPSYS","GENEMIND","TAPESTRI"], desc="Short-read platform; required when short_reads_1 given."),
   col("long_reads", "data", fmt="file-path", pat="^\\S+\\.f(ast)?q\\.gz$", exists=True, desc="Long reads fasta/fastq gz; requires long_reads_platform; optional only if short_reads_1 given."),
   col("long_reads_platform", "meta", enum=["OXFORD_NANOPORE","OXFORD_NANOPORE_HQ","PACBIO_CLR","PACBIO_HIFI"], desc="Long-read platform; required when long_reads given."),
 ]),
 sheet("assembly_input", "assets/schema_assembly_input.json", [
   col("id", "meta", req=True, pat="^\\S+$"),
   col("group", "meta", typ="string", req=True, pat="^\\S+$"),
   col("assembler", "meta", req=True, pat="MEGAHIT|SPAdes|SPAdesHybrid|Flye|MetaMDBG", desc="Original assembler label; drives short- vs long-read assembly routing."),
   col("fasta", "data", req=True, fmt="file-path", pat="^\\S+\\.(fasta|fas|fa|fna)(\\.gz)?$", exists=True),
 ]),
]

# ---------------------------------------------------------------- workflow
def ch(name, source_, shape, construct, from_param=None, req=False):
    return {"name": name, "source": source_, "shape": shape, "construct": construct,
            "from_param": from_param, "required_runtime": req}
def edge(f, t, via, notes=None):
    return {"from": f, "to": t, "via": via, "notes": notes or ""}
def cond(g, b, aff):
    return {"guard": g, "branch": b, "affects": aff}

channels = [
 ch("ch_raw_short_reads", "PIPELINE_INITIALISATION.out.raw_short_reads — channel.fromList(samplesheetToList(input, 'assets/schema_input.json')) mapped to [meta, [sr1, sr2]]",
    "tuple(meta, [path(fastq1), path(fastq2)])", "samplesheetToList", "input", True),
 ch("ch_raw_long_reads", "PIPELINE_INITIALISATION.out.raw_long_reads — samplesheetToList(params.input) mapped to [meta, long_reads]",
    "tuple(meta, path(fastq))", "samplesheetToList", "input", True),
 ch("ch_input_assemblies", "PIPELINE_INITIALISATION.out.input_assemblies — channel.fromList(samplesheetToList(params.assembly_input, 'assets/schema_assembly_input.json'))",
    "tuple(meta, path(fasta))", "samplesheetToList", "assembly_input", True),
 ch("ch_host_fasta", "params.genomes[params.host_genome].fasta -> channel.value(file(...)) else channel.fromPath(params.host_fasta).first() else channel.empty()",
    "path(fasta)", "value", "host_fasta", False),
 ch("ch_host_bowtie2index", "channel.fromPath(host_bowtie2index).first() else channel.empty()",
    "path(dir)", "fromPath", "host_fasta_bowtie2index", False),
 ch("ch_phix_db_file", "channel.value(file(params.phix_reference or assets/data/GCA_002596845.1_ASM259684v1_genomic.fna.gz)) unless params.keep_phix else channel.empty()",
    "path(fasta)", "value", "phix_reference", False),
 ch("ch_lambda_db", "channel.value(file(params.lambda_reference or assets/data/GCA_000840245.1_ViralProj14204_genomic.fna.gz)) unless keep_lambda",
    "path(fasta)", "value", "lambda_reference", False),
 ch("ch_genomad_db", "file(params.genomad_db, checkIfExists: true) else channel.empty()",
    "path(dir)", "file", "genomad_db", False),
 ch("gtdb", "file(params.gtdb_db) unless skip_binqc or skip_gtdbtk else []",
    "path(tar.gz|dir)", "file", "gtdb_db", False),
 ch("ch_metaeuk_db", "channel.value(file(params.metaeuk_db)) or MMSEQS_DATABASES.out.database or channel.empty()",
    "path(dir)", "value", "metaeuk_db", False),
 ch("ch_versions", "channel.empty(), mixed with every module's versions output", "path(versions.yml)", "empty"),
 ch("ch_multiqc_files", "channel.empty(), mixed with all MultiQC report files", "path(report)", "empty"),
 ch("topic_versions", "channel.topic('versions').distinct().branch(versions_file | versions_tuple)", "tuple/process versions", "topic"),
 ch("ch_assemblies_split", "ch_input_assemblies.branch { gzipped | ungzip }", "tuple(meta, path(fasta))", "other"),
 ch("ch_short_reads", "SHORTREAD_PREPROCESSING.out.short_reads", "tuple(meta, [path(fastq)])", "other"),
 ch("ch_short_reads_assembly", "SHORTREAD_PREPROCESSING.out.short_reads_assembly (post-bbnorm)", "tuple(meta, [path(fastq)])", "other"),
 ch("ch_long_reads", "LONGREAD_PREPROCESSING.out.long_reads", "tuple(meta, path(fastq))", "other"),
 ch("ch_shortread_assemblies", "ASSEMBLY.out.shortread_assemblies or gunzip'd ch_input_assemblies filtered to SPADES/SPADESHYBRID/MEGAHIT", "tuple(meta+assembler, path(fasta))", "other"),
 ch("ch_longread_raw_assemblies", "ASSEMBLY.out.longread_assemblies or gunzip'd input filtered to FLYE/METAMDBG", "tuple(meta+assembler, path(fasta))", "other"),
 ch("ch_longread_assemblies", "PYPOLCA_RUN.out.polished mixed with unpolished branch, or ch_longread_raw_assemblies", "tuple(meta, path(fasta))", "other"),
 ch("ch_assemblies", "ch_shortread_assemblies.mix(ch_longread_assemblies)", "tuple(meta, path(fasta))", "other"),
 ch("ch_ale_input", "BINNING_PREPARATION.out.grouped_mappings.join(ch_shortread_assemblies).map pick one bam", "tuple(meta, path(contigs), path(bam))", "other"),
 ch("ch_input_for_postbinning", "raw and/or refined bins+unbins mixed per postbinning_input/exclude_unbins_from_postbinning", "tuple(meta, [path(fa.gz)])", "other"),
 ch("ch_allcontig2binmap", "ch_input_for_postbinning.transpose/map/splitFasta/collectFile -> contig_to_bin_map.tsv", "path(tsv)", "other"),
 ch("ch_collated_versions", "softwareVersionsToYAML(ch_versions) + topic version strings, collectFile", "path(nf_core_mag_software_mqc_versions.yml)", "other"),
]
edges = [
 edge("ch_raw_short_reads", "SHORTREAD_PREPROCESSING", []),
 edge("ch_host_fasta", "SHORTREAD_PREPROCESSING", []),
 edge("ch_host_bowtie2index", "SHORTREAD_PREPROCESSING", []),
 edge("ch_phix_db_file", "SHORTREAD_PREPROCESSING", []),
 edge("ch_raw_long_reads", "LONGREAD_PREPROCESSING", []),
 edge("ch_short_reads", "LONGREAD_PREPROCESSING", ["map", "join"], "filtlong short-read-aided filtering joins by meta.id when params.filtlong_filtering_by_shortreads"),
 edge("ch_lambda_db", "LONGREAD_PREPROCESSING", []),
 edge("ch_host_fasta", "LONGREAD_PREPROCESSING", []),
 edge("ch_short_reads_assembly", "ASSEMBLY", [], "only when !params.assembly_input"),
 edge("ch_long_reads", "ASSEMBLY", [], "only when !params.assembly_input"),
 edge("ch_input_assemblies", "GUNZIP_ASSEMBLYINPUT", ["branch"], "assembly_input branch: gzipped entries decompressed"),
 edge("GUNZIP_ASSEMBLYINPUT.out.gunzip", "ch_assemblies_unzipped", ["mix"]),
 edge("ch_assemblies_unzipped", "ch_shortread_assemblies", ["filter"], "meta.assembler in [SPADES, SPADESHYBRID, MEGAHIT]"),
 edge("ch_assemblies_unzipped", "ch_longread_raw_assemblies", ["filter"], "meta.assembler in [FLYE, METAMDBG]"),
 edge("ch_longread_raw_assemblies", "PYPOLCA_RUN", ["combine", "map", "branch"], "params.run_pypolca only; pairs assembly with own short reads"),
 edge("PYPOLCA_RUN.out.polished", "ch_longread_assemblies", ["mix"]),
 edge("ch_shortread_assemblies", "QUAST", ["mix"], "!params.skip_quast"),
 edge("ch_longread_assemblies", "QUAST", ["mix"], "!params.skip_quast"),
 edge("ch_assemblies", "PRODIGAL", [], "!params.skip_prodigal (gene prediction on all assemblies)"),
 edge("ch_assemblies", "VIRUS_IDENTIFICATION", [], "params.run_virus_identification"),
 edge("ch_genomad_db", "VIRUS_IDENTIFICATION", [], "db supplied; else GENOMAD_DOWNLOAD inside"),
 edge("ch_shortread_assemblies", "BINNING_PREPARATION", [], "guarded: !skip_binning || ancient_dna || !skip_ale"),
 edge("ch_short_reads", "BINNING_PREPARATION", []),
 edge("ch_longread_assemblies", "BINNING_PREPARATION", []),
 edge("ch_long_reads", "BINNING_PREPARATION", []),
 edge("BINNING_PREPARATION.out.grouped_mappings", "ANCIENT_DNA_ASSEMBLY_VALIDATION", [], "params.ancient_dna"),
 edge("BINNING_PREPARATION.out.grouped_mappings", "ALE", ["join", "map"], "!params.skip_ale; joined with ch_shortread_assemblies"),
 edge("BINNING_PREPARATION.out.grouped_mappings", "BINNING", [], "swapped with ANCIENT_DNA_ASSEMBLY_VALIDATION.out.contigs_recalled when ancient_dna && !skip_ancient_damagecorrection"),
 edge("BINNING.out.bins", "DOMAIN_CLASSIFICATION", [], "params.bin_domain_classification; also ch_assemblies and BINNING.out.unbinned"),
 edge("DOMAIN_CLASSIFICATION.out.classified_bins", "ch_input_for_postbinning", ["map"], "adds meta.domain; unclassified default when no domain classification"),
 edge("ch_input_for_postbinning_bins", "BINNING_REFINEMENT", ["filter"], "params.refine_bins_dastool; prokarya-only; contigs from grouped_mappings or aDNA recall"),
 edge("BINNING_REFINEMENT.out.refined_bins", "ch_input_for_postbinning", ["mix"], "per params.postbinning_input (raw/refined/both)"),
 edge("ch_input_for_postbinning", "DEPTHS", ["map", "groupTuple", "combine", "transpose", "groupTuple", "map"], "with BINNING.out.metabat2depths"),
 edge("ch_input_for_postbinning", "ch_allcontig2binmap", ["transpose", "map", "splitFasta", "map", "collectFile"]),
 edge("ch_input_for_postbinning", "BIN_QC", [], "!params.skip_binqc"),
 edge("ch_input_for_postbinning", "QUAST_BINS", ["map"], "!params.skip_quast; bins sorted+flattened"),
 edge("QUAST_BINS.out.quast_bin_summaries", "CONCAT_QUAST_SUMMARY", ["collect", "map"]),
 edge("BIN_QC.out.qc_metrics", "GTDBTK", ["groupTuple", "join", "map"], "bins filtered on completeness/contamination; !skip_gtdbtk && !skip_binqc && any QC tool && gtdb db given"),
 edge("ch_input_for_postbinning_bins", "CATPACK", [], "params.cat_db || params.cat_db_generate; unbins too when cat_classify_unbinned"),
 edge("ANCIENT_DNA_ASSEMBLY_VALIDATION.out.pydamage_results", "BINNING_PYDAMAGE", ["toSortedList"], "params.ancient_dna; with ch_allcontig2binmap"),
 edge("DEPTHS.out.depths_summary", "BIN_SUMMARY", ["ifEmpty"], "joined with quast/gtdbtk/catpack/busco/checkm/checkm2/pydamage summaries (each .ifEmpty([]))"),
 edge("BIN_SUMMARY.out.summary", "PREPARE_BIGMAG_SUMMARY", [], "params.generate_bigmag_file; with BIN_QC.out.gunc_summary"),
 edge("ch_input_for_postbinning", "PROKKA", ["transpose", "map", "filter"], "!params.skip_prokka; bins with domain != eukarya"),
 edge("ch_input_for_postbinning", "METAEUK_EASYPREDICT", ["transpose", "filter", "map"], "params.metaeuk_db || params.metaeuk_mmseqs_db; domain in [eukarya, unclassified]"),
 edge("params.metaeuk_mmseqs_db", "MMSEQS_DATABASES", [], "produces ch_metaeuk_db"),
 edge("ch_versions", "ch_collated_versions", ["mix", "distinct", "branch", "groupTuple", "map", "collectFile"], "softwareVersionsToYAML + topic-versions strings"),
 edge("ch_multiqc_files", "MULTIQC", ["collect", "ifEmpty", "mix", "flatten", "collect", "map"], "adds QUAST reports, workflow summary, methods description"),
 edge("MULTIQC.out.report", "NFCORE_MAG.out.multiqc_report", ["map", "toList"]),
]
conditionals = [
 cond("params.host_fasta || params.host_genome", "alternate", ["BOWTIE2_HOST_REMOVAL_BUILD", "BOWTIE2_HOST_REMOVAL_ALIGN", "LONGREAD_HOSTREMOVAL"]),
 cond("!params.keep_phix", "alternate", ["BOWTIE2_PHIX_REMOVAL_BUILD", "BOWTIE2_PHIX_REMOVAL_ALIGN"]),
 cond("!params.keep_lambda && longread_filtering_tool != 'chopper'", "alternate", ["NANOLYSE"]),
 cond("params.metaeuk_mmseqs_db", "alternate", ["MMSEQS_DATABASES"]),
 cond("!params.assembly_input", "alternate", ["ASSEMBLY", "SHORTREAD_PREPROCESSING (trim/host/phix stages)", "LONGREAD_PREPROCESSING (trim/filter stages)"]),
 cond("params.assembly_input", "alternate", ["GUNZIP_ASSEMBLYINPUT", "ch_shortread_assemblies/ch_longread_raw_assemblies assembly_input branches"]),
 cond("params.run_pypolca", "alternate", ["PYPOLCA_RUN"]),
 cond("!params.skip_quast", "alternate", ["QUAST", "QUAST_BINS", "CONCAT_QUAST_SUMMARY"]),
 cond("!params.skip_prodigal", "alternate", ["PRODIGAL"]),
 cond("params.run_virus_identification", "alternate", ["VIRUS_IDENTIFICATION", "GENOMAD_ENDTOEND", "GENOMAD_DOWNLOAD", "GENOMAD_UNTAR"]),
 cond("!params.skip_binning || params.ancient_dna || !params.skip_ale", "alternate", ["BINNING_PREPARATION", "BOWTIE2_ASSEMBLY_BUILD", "BOWTIE2_ASSEMBLY_ALIGN", "MINIMAP2_ASSEMBLY_INDEX", "MINIMAP2_ASSEMBLY_ALIGN"]),
 cond("params.ancient_dna", "alternate", ["ANCIENT_DNA_ASSEMBLY_VALIDATION", "BINNING_PYDAMAGE", "SUMMARISE_PYDAMAGEBINS"]),
 cond("params.ancient_dna && !params.skip_ancient_damagecorrection", "alternate", ["SAMTOOLS_FAIDX", "FREEBAYES", "BCFTOOLS_INDEX", "BCFTOOLS_VIEW", "BCFTOOLS_CONSENSUS"]),
 cond("!params.skip_ale", "alternate", ["ALE"]),
 cond("!params.skip_binning", "alternate", ["BINNING", "DEPTHS", "MAG_DEPTHS", "MAG_DEPTHS_SUMMARY", "PROKKA (bin branch)", "ch_allcontig2binmap"]),
 cond("params.bin_domain_classification", "alternate", ["DOMAIN_CLASSIFICATION", "TIARA_TIARA", "DASTOOL_FASTATOCONTIG2BIN_TIARA", "TIARA_CLASSIFY", "CONCAT_TIARA_TSV"]),
 cond("params.refine_bins_dastool", "alternate", ["BINNING_REFINEMENT", "RENAME_PREDASTOOL", "DASTOOL_FASTATOCONTIG2BIN", "DASTOOL_DASTOOL", "RENAME_POSTDASTOOL"]),
 cond("!params.skip_binqc", "alternate", ["BIN_QC", "BUSCO_BUSCO", "CHECKM_LINEAGEWF", "CHECKM_QA", "CHECKM2_PREDICT", "CHECKM2_DATABASEDOWNLOAD", "GUNC_RUN", "GUNC_DOWNLOADDB", "GUNC_MERGECHECKM", "BUSCO_UNTAR", "CHECKM_UNTAR"]),
 cond("!params.skip_gtdbtk && !params.skip_binqc && (run_busco || run_checkm || run_checkm2) && params.gtdb_db", "alternate", ["GTDBTK", "GTDBTK_CLASSIFYWF", "GTDBTK_DB_PREPARATION", "GTDBTK_SUMMARY"]),
 cond("params.cat_db || params.cat_db_generate", "alternate", ["CATPACK", "CATPACK_BINS", "CATPACK_ADDNAMES_BINS", "CATPACK_SUMMARISE_BINS", "CATPACK_DOWNLOAD", "CATPACK_PREPARE", "CATPACK_DB_UNTAR"]),
 cond("params.cat_classify_unbinned", "alternate", ["CONCAT_UNBINS", "CATPACK_UNBINS", "CATPACK_ADDNAMES_UNBINS", "CATPACK_SUMMARISE_UNBINS"]),
 cond("!params.skip_binqc || !params.skip_quast || !params.skip_gtdbtk", "alternate", ["BIN_SUMMARY"]),
 cond("params.generate_bigmag_file", "alternate", ["PREPARE_BIGMAG_SUMMARY"]),
 cond("!params.skip_prokka", "alternate", ["PROKKA"]),
 cond("params.metaeuk_db || params.metaeuk_mmseqs_db", "alternate", ["METAEUK_EASYPREDICT"]),
 cond("!params.skip_clipping && !skip_shortread_qc && clip_tool=='fastp'", "alternate", ["FASTP"]),
 cond("clip_tool=='adapterremoval'", "alternate", ["ADAPTERREMOVAL_PE", "ADAPTERREMOVAL_SE"]),
 cond("clip_tool=='trimmomatic'", "alternate", ["TRIMMOMATIC"]),
 cond("params.bbnorm && !params.assembly_input", "alternate", ["BBMAP_BBNORM", "SEQTK_MERGEPE (when coassemble_group)"]),
 cond("!params.skip_fastqc", "alternate", ["FASTQC_RAW", "FASTQC_TRIMMED"]),
 cond("params.coassemble_group", "alternate", ["POOL_SHORT_READS", "POOL_LONG_READS"]),
 cond("!params.skip_spades", "alternate", ["METASPADES"]),
 cond("!params.skip_spadeshybrid && !params.single_end", "alternate", ["METASPADESHYBRID"]),
 cond("!params.skip_megahit", "alternate", ["MEGAHIT"]),
 cond("!params.skip_flye", "alternate", ["FLYE"]),
 cond("!params.skip_metamdbg", "alternate", ["METAMDBG_ASM"]),
 cond("!params.skip_metabat2", "alternate", ["METABAT2_METABAT2", "METABAT2_JGISUMMARIZEBAMCONTIGDEPTHS_SHORTREAD", "METABAT2_JGISUMMARIZEBAMCONTIGDEPTHS_LONGREAD"]),
 cond("!params.skip_maxbin2", "alternate", ["MAXBIN2", "CONVERT_DEPTHS"]),
 cond("!params.skip_concoct", "alternate", ["FASTA_BINNING_CONCOCT"]),
 cond("!params.skip_comebin", "alternate", ["COMEBIN_RUNCOMEBIN"]),
 cond("!params.skip_metabinner", "alternate", ["BINNING_METABINNER", "METABINNER_KMER", "METABINNER_TOOSHORT", "METABINNER_METABINNER", "METABINNER_BINS"]),
 cond("!params.skip_semibin", "alternate", ["SEMIBIN_SINGLEEASYBIN"]),
 cond("params.longread_adaptertrimming_tool=='porechop_abi'", "alternate", ["PORECHOP_ABI"]),
 cond("params.longread_adaptertrimming_tool=='porechop'", "alternate", ["PORECHOP_PORECHOP"]),
 cond("params.longread_filtering_tool=='filtlong'", "alternate", ["FILTLONG"]),
 cond("params.longread_filtering_tool=='nanoq'", "alternate", ["NANOQ"]),
 cond("params.longread_filtering_tool=='chopper'", "alternate", ["CHOPPER"]),
 cond("params.run_checkm && !params.checkm_db", "alternate", ["CHECKM_UNTAR (download from checkm_download_url)"]),
]

# ---------------------------------------------------------------- test candidates
def tdref(role, url=None, path=None, filetype=None, desc=None):
    return {"role": role, "path": path, "url": url, "sha1": None, "filetype": filetype, "description": desc}
def expref(role, path, kind, assertions=None, desc=None):
    return {"role": role, "path": path, "url": None, "kind": kind, "description": desc,
            "assertions": assertions or []}
def snap(matches, snap_path, globs=None):
    return {"captures": [
                "workflow.trace.succeeded().size()",
                "nf_core_mag_software_mqc_versions.yml (removeNextflowVersion)"] + matches,
            "helpers": ["getAllFilesFromDir", "removeNextflowVersion"],
            "ignore_files": ["tests/.nftignore"],
            "ignore_globs": globs or [],
            "snap_path": snap_path, "parsed_content": []}
def outset(matches, snap_path):
    return [
      expref("MultiQC report", "multiqc/multiqc_report.html", "file",
             ["snapshot('" + m + "')" for m in matches if m == "multiqc"]),
      expref("pipeline software versions", "pipeline_info/nf_core_mag_software_mqc_versions.yml", "file",
             ["snapshot match of (succeeded_task_count, versions) pair"]),
      expref("whole-outdir snapshot sets", "QC_shortreads/**; Assembly/**; GenomeBinning/**; Annotation/**; Taxonomy/**; multiqc/**",
             "directory-glob",
             ["snapshot match(name, paths) per top-level outdir, ignoring tests/.nftignore entries"] ),
      expref("bin summary", "GenomeBinning/bin_summary.tsv", "file",
             ["content/tsv-row snapshots where asserted by the test"]),
    ]
def cand(tfile, name, profiles_, inputs_, pdelta, matches, globs=None, scope="primary",
         disp="eligible", rationale=""):
    return {"id": f"tests/{tfile}.nf.test::{name}", "kind": "nf-test", "name": name,
            "path": f"tests/{tfile}.nf.test", "effective_profiles": profiles_,
            "params_delta": pdelta, "inputs": inputs_, "outputs": outset(matches, None),
            "execution_mode": "real", "scope": scope, "disposition": disp,
            "rationale": rationale, "assert_workflow_success": True,
            "snapshot": snap(matches, f"tests/{tfile}.nf.test.snap", globs),
            "prose_assertions": []}

B = TESTDATA
SHEET = lambda s: tdref("input samplesheet", url=B + "mag/samplesheets/" + s, filetype="csv",
                        desc="served via params.pipelines_testdata_base_path, which tests/nextflow.config pins to the 'mag' branch of nf-core/test-datasets")
BUSCO = tdref("BUSCO lineage database", url=B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz", filetype="tar.gz")
GTDBM = tdref("GTDB-Tk mockup database", url=B + "mag/databases/gtdbtk/gtdbtk_mockup_r232_20260507.tar.gz", filetype="tar.gz")
CATDB = tdref("CAT minigut database", url=B + "mag/databases/cat/minigut_cat.tar.gz", filetype="tar.gz")
HOSTF = tdref("host reference (hg38 chr21 region)", url=B + "mag/host_reference/genome.hg38.chr21_10000bp_region.fa", filetype="fa")
PHIXB = tdref("phiX reference (bundled)", path="assets/data/GCA_002596845.1_ASM259684v1_genomic.fna.gz", filetype="fasta.gz",
              desc="shipped in assets/data; used unless params.phix_reference is set")
LAMBD = tdref("lambda reference (bundled)", path="assets/data/GCA_000840245.1_ViralProj14204_genomic.fna.gz", filetype="fasta.gz")

test_candidates = [
 cand("default", "-profile test", ["test"],
      [SHEET("samplesheet.multirun.v4.csv"), BUSCO, GTDBM, CATDB, PHIXB, LAMBD],
      {"input": B + "mag/samplesheets/samplesheet.multirun.v4.csv", "min_length_unbinned_contigs": 1,
       "max_unbinned_contigs": 2, "skip_ale": True, "skip_concoct": True, "skip_comebin": True,
       "skip_metabinner": True, "busco_db": B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz",
       "busco_db_lineage": "bacteria_odb10", "busco_clean": True, "prokka_fast_mode": True,
       "gtdb_db": B + "mag/databases/gtdbtk/gtdbtk_mockup_r232_20260507.tar.gz",
       "cat_db": B + "mag/databases/cat/minigut_cat.tar.gz", "cat_classify_unbinned": True,
       "cat_no_suggestive_asterisks": True, "gtdbtk_min_completeness": 0.01,
       "gtdbtk_place_species": True, "gtdbtk_use_full_tree": True, "megahit_fix_cpu_1": True,
       "spades_fix_cpus": 1, "outdir": "$outputDir"},
      ["qc", "assembly", "binning", "annotation", "taxonomy", "multiqc",
       "content-checks", "tsv-rows", "log-checks"],
      globs=["GenomeBinning/QC/BUSCO/**/{logs,prodigal_output,busco_sequences,hmmer_output}/**",
             "Annotation/Prokka/**/*.tmp.*"],
      scope="primary", disp="selected",
      rationale="canonical whole-pipeline nf-test case in default.nf.test; full science path (QC, SPAdes+MEGAHIT assembly, MetaBAT2/MaxBin2/SemiBin2 binning, BUSCO QC, GTDB-Tk + CAT taxonomy, Prokka annotation) on a small multirun samplesheet"),
 cand("test_minimal", "-profile test_minimal", ["test_minimal"],
      [SHEET("samplesheet.v4.csv")],
      {"input": B + "mag/samplesheets/samplesheet.v4.csv", "skip_clipping": True,
       "skip_adapter_trimming": True, "skip_longread_filtering": True, "skip_spades": True,
       "skip_spadeshybrid": True, "skip_megahit": True, "skip_quast": True, "skip_ale": True,
       "skip_prodigal": True, "skip_binning": True, "skip_metabat2": True, "skip_maxbin2": True,
       "skip_concoct": True, "skip_comebin": True, "skip_metabinner": True, "skip_semibin": True,
       "skip_prokka": True, "skip_binqc": True, "run_busco": False, "outdir": "$outputDir"},
      ["multiqc"], scope="bootstrap-only", disp="deferred",
      rationale="skips every science step (only Flye/MetaMDBG unskipped); asserts multiqc/** only — useful as a smoke test, not as coverage for a translation"),
 cand("test_alternatives", "-profile test_alternatives", ["test_alternatives"],
      [SHEET("samplesheet.v4.csv"), BUSCO],
      {"input": B + "mag/samplesheets/samplesheet.v4.csv", "clip_tool": "trimmomatic",
       "coassemble_group": True, "run_busco": True, "run_checkm2": True,
       "bin_domain_classification": True, "skip_spades": True, "skip_quast": True,
       "skip_ale": True, "skip_prodigal": True, "skip_prokka": True, "skip_gtdbtk": True,
       "skip_maxbin2": True, "skip_concoct": True, "skip_comebin": True, "outdir": "$outputDir"},
      ["qc", "assembly", "binning", "multiqc"],
      rationale="alternative-tool coverage: Trimmomatic clipping, CheckM2 QC, Tiara domain classification, co-assembly by group"),
 cand("test_single_end", "-profile test_single_end", ["test_single_end"],
      [SHEET("samplesheet.single_end.v4.csv"), HOSTF],
      {"input": B + "mag/samplesheets/samplesheet.single_end.v4.csv", "single_end": True,
       "clip_tool": "adapterremoval", "host_fasta": B + "mag/host_reference/genome.hg38.chr21_10000bp_region.fa",
       "ancient_dna": True, "binning_map_mode": "own", "skip_spadeshybrid": True,
       "skip_comebin": True, "skip_metabinner": True, "skip_semibin": True, "skip_ale": True,
       "run_busco": False, "min_length_unbinned_contigs": 1000000, "max_unbinned_contigs": 2,
       "megahit_fix_cpu_1": True, "spades_fix_cpus": 1, "outdir": "$outputDir"},
      ["qc", "assembly", "Ancient_DNA", "binning", "annotation"],
      rationale="single-end + ancient-DNA coverage: AdapterRemoval SE, host removal, pydamage/FreeBayES consensus recall, CheckM QC"),
 cand("test_longreadonly", "-profile longreadonly", ["test_longreadonly"],
      [SHEET("samplesheet.long_read.v4.csv"), HOSTF, BUSCO],
      {"input": B + "mag/samplesheets/samplesheet.long_read.v4.csv",
       "host_fasta": B + "mag/host_reference/genome.hg38.chr21_10000bp_region.fa",
       "busco_db": B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz",
       "busco_db_lineage": "bacteria_odb10", "skip_gtdbtk": True, "skip_concoct": True,
       "skip_comebin": True, "skip_metabinner": True, "skip_semibin": True, "skip_ale": True,
       "outdir": "$outputDir"},
      ["QC_longreads", "assembly", "binning", "annotation"],
      rationale="long-read-only modality: chopper/porechop, Flye + metaMDBG assembly, minimap2 binning preparation"),
 cand("test_longreadonly_alternatives", "-profile longreadonly_alternatives", ["test_longreadonly_alternatives"],
      [SHEET("samplesheet.hybrid.v4.csv"), BUSCO],
      {"input": B + "mag/samplesheets/samplesheet.hybrid.v4.csv",
       "busco_db": B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz",
       "busco_db_lineage": "bacteria_odb10", "longread_adaptertrimming_tool": "porechop",
       "longread_filtering_tool": "nanoq", "run_pypolca": True, "skip_spades": True,
       "skip_spadeshybrid": True, "skip_megahit": True, "skip_metamdbg": True,
       "skip_quast": True, "skip_ale": True, "skip_prodigal": True, "skip_prokka": True,
       "skip_gtdbtk": True, "skip_concoct": True, "skip_comebin": True, "skip_metabinner": True,
       "skip_semibin": True, "outdir": "$outputDir"},
      ["QC_longreads", "assembly", "binning", "multiqc"],
      rationale="alternative long-read tool chain (porechop, Nanoq) plus PyPolca polishing path"),
 cand("test_hybrid", "-profile hybrid", ["test_hybrid"],
      [SHEET("samplesheet.hybrid_coassembly.v4.csv"), HOSTF, BUSCO],
      {"input": B + "mag/samplesheets/samplesheet.hybrid_coassembly.v4.csv",
       "host_fasta": B + "mag/host_reference/genome.hg38.chr21_10000bp_region.fa",
       "busco_db": B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz",
       "busco_db_lineage": "bacteria_odb10", "longread_filtering_tool": "filtlong",
       "skip_spades": True, "skip_megahit": True, "skip_flye": True, "skip_metamdbg": True,
       "skip_gtdbtk": True, "skip_concoct": True, "skip_comebin": True, "skip_metabinner": True,
       "skip_ale": True, "coassemble_group": True, "spadeshybrid_fix_cpus": 2,
       "save_filtered_longreads": True, "outdir": "$outputDir"},
      ["QC_shortreads", "QC_longreads", "assembly", "binning", "annotation"],
      rationale="hybrid SPAdes coverage with Filtlong (short-read-aided) filtering and group co-assembly"),
 cand("test_assembly_input", "-profile assembly_input", ["test_assembly_input"],
      [SHEET("samplesheet.v4.csv"),
       tdref("assembly samplesheet", url=B + "mag/samplesheets/assembly_samplesheet.csv", filetype="csv"),
       BUSCO,
       tdref("GUNC database (minidb)", url=B + "mag/databases/gunc/ci_test.dmnd", filetype="dmnd")],
      {"input": B + "mag/samplesheets/samplesheet.v4.csv",
       "assembly_input": B + "mag/samplesheets/assembly_samplesheet.csv",
       "busco_db": B + "mag/databases/busco/bacteria_odb10.2024-01-08.tar.gz",
       "busco_db_lineage": "bacteria_odb10", "busco_clean": True, "skip_quast": True,
       "skip_prodigal": True, "skip_prokka": True, "skip_gtdbtk": True,
       "skip_concoct": False, "skip_comebin": True, "skip_metabinner": True, "skip_ale": True,
       "skip_semibin": True, "refine_bins_dastool": True, "refine_bins_dastool_threshold": 0.0,
       "postbinning_input": "refined_bins_only", "exclude_unbins_from_postbinning": True,
       "run_gunc": True, "gunc_db": B + "mag/databases/gunc/ci_test.dmnd",
       "metaeuk_mmseqs_db": "Kalamari", "outdir": "$outputDir"},
      ["Assembly", "Annotation", "binning", "multiqc"],
      rationale="assembly_input modality: CONCOCT + DASTool refinement, refined_bins_only post-binning, GUNC QC, MetaEuk via mmseqs db name 'Kalamari'"),
]

test_selection = {"status": "selected",
                  "selected_candidate_id": "tests/default.nf.test::-profile test",
                  "rationale": "default.nf.test is the canonical whole-pipeline case and the only one whose assertions cover the primary science path end to end; test_minimal is multiqc-only (bootstrap), and the remaining cases vary tool choices or input modalities (single-end/aDNA, long-read, hybrid, assembly-input)."}

# ---------------------------------------------------------------- reference assets / rebuilds
def ev(sp, conf, *items):
    return {"source_path": sp, "confidence": conf, "evidence": list(items)}
def rass(param, kind, fmt, req, skind, sexpr, group, used_by, evidence):
    return {"param": param, "asset_kind": kind, "format_hint": fmt, "required": req,
            "source_kind": skind, "source_expression": sexpr, "schema_group": group,
            "used_by": used_by, "evidence": evidence}
reference_assets = [
 rass("gtdb_db", "reference-database", "tar.gz or directory", False, "params_block",
      '"https://data.gtdb.aau.ecogenomic.org/releases/release232/232.0/auxillary_files/gtdbtk_package/full_package/gtdbtk_r232_data.tar.gz"',
      "Taxonomic profiling options", ["GTDBTK", "GTDBTK_CLASSIFYWF"],
      ev("nextflow.config:108", "high", "params.gtdb_db default is the GTDB r232 full package URL",
         "mag.nf wraps it with file(...) unless skip_binqc/skip_gtdbtk")),
 rass("busco_db", "reference-database", "tar.gz or directory", False, "params_block", None,
      "Bin quality check options", ["BIN_QC", "BUSCO_BUSCO", "BUSCO_UNTAR"],
      ev("subworkflows/local/bin_qc/main.nf", "high", "file(params.busco_db); tar.gz -> BUSCO_UNTAR; directory kept as-is",
         "tests set busco_db_lineage=bacteria_odb10")),
 rass("checkm_db", "reference-database", "tar.gz", False, "params_block", None,
      "Bin quality check options", ["BIN_QC", "CHECKM_LINEAGEWF", "CHECKM_QA"],
      ev("subworkflows/local/bin_qc/main.nf", "high",
         "when run_checkm and no checkm_db: [[id:'checkm_db'], file(params.checkm_download_url)] then CHECKM_UNTAR")),
 rass("checkm_download_url", "download-url", "tar.gz", False, "params_block",
      '"https://zenodo.org/records/7401545/files/checkm_data_2015_01_16.tar.gz"',
      "Bin quality check options", ["CHECKM_UNTAR"],
      ev("nextflow.config:170", "high", "default download source for checkm_data_2015_01_16")),
 rass("checkm2_db", "reference-database", "tar.gz", False, "params_block", None,
      "Bin quality check options", ["BIN_QC", "CHECKM2_PREDICT", "CHECKM2_DATABASEDOWNLOAD"],
      ev("subworkflows/local/bin_qc/main.nf", "high", "when run_checkm2 and no checkm2_db: CHECKM2_DATABASEDOWNLOAD(params.checkm2_db_version)")),
 rass("checkm2_db_version", "version-pin", "integer", False, "params_block", "14897628 (Zenodo record id)",
      "Bin quality check options", ["CHECKM2_DATABASEDOWNLOAD"], ev("nextflow.config:174", "high", "Zenodo record pin")),
 rass("gunc_db", "reference-database", "dmnd/tar.gz", False, "params_block", None,
      "Bin quality check options", ["GUNC_RUN", "GUNC_DOWNLOADDB"],
      ev("subworkflows/local/bin_qc/main.nf", "high", "GUNC_DOWNLOADDB(params.gunc_database_type) when no gunc_db given")),
 rass("cat_db", "reference-database", "tar.gz or directory", False, "params_block", None,
      "Taxonomic profiling options", ["CATPACK", "CATPACK_BINS", "CATPACK_DB_UNTAR"],
      ev("subworkflows/local/catpack/main.nf", "high",
         ".tar.gz -> CATPACK_DB_UNTAR; dir -> fromPath; else (cat_db_generate) CATPACK_DOWNLOAD nr + CATPACK_PREPARE builds it (logged as very large)")),
 rass("genomad_db", "reference-database", "tar.gz or directory", False, "params_block", None,
      "Virus identification options", ["VIRUS_IDENTIFICATION", "GENOMAD_ENDTOEND", "GENOMAD_UNTAR", "GENOMAD_DOWNLOAD"],
      ev("subworkflows/local/virus_identification/main.nf", "high", "no db -> GENOMAD_DOWNLOAD().genomad_db")),
 rass("metaeuk_db", "reference-database", "mmseqs db directory", False, "params_block", None,
      "Gene prediction and annotation options", ["METAEUK_EASYPREDICT"],
      ev("workflows/mag.nf:125", "high", "channel.value(file(params.metaeuk_db)) else empty")),
 rass("metaeuk_mmseqs_db", "download-url or db name", "mmseqs db", False, "params_block", None,
      "Gene prediction and annotation options", ["MMSEQS_DATABASES", "METAEUK_EASYPREDICT"],
      ev("workflows/mag.nf:133", "high", "MMSEQS_DATABASES(params.metaeuk_mmseqs_db) -> ch_metaeuk_db; test uses bare name 'Kalamari'")),
 rass("phix_reference", "contaminant-reference", "fasta(.gz)", False, "params_block",
      "default null; bundled fallback file(\"${projectDir}/assets/data/GCA_002596845.1_ASM259684v1_genomic.fna.gz\")",
      "Quality control for short reads options", ["SHORTREAD_PREPROCESSING", "BOWTIE2_PHIX_REMOVAL_BUILD/ALIGN"],
      ev("workflows/mag.nf:91", "high", "bundled copy shipped in assets/data of the repo")),
 rass("lambda_reference", "contaminant-reference", "fasta(.gz)", False, "params_block",
      "default null; bundled fallback file(\"${projectDir}/assets/data/GCA_000840245.1_ViralProj14204_genomic.fna.gz\")",
      "Quality control for long reads options", ["LONGREAD_PREPROCESSING", "NANOLYSE", "CHOPPER"],
      ev("workflows/mag.nf:100", "high", "bundled copy shipped in assets/data of the repo")),
 rass("host_fasta", "host-genome", "fasta(.gz)", False, "params_block", None,
      "Reference genome options", ["SHORTREAD_PREPROCESSING", "LONGREAD_PREPROCESSING", "BOWTIE2_HOST_REMOVAL_*"],
      ev("workflows/mag.nf:70", "high", "params.genomes[params.host_genome].fasta via getGenomeAttribute takes precedence when host_genome set",
         "host_genome resolves through conf/igenomes.config / params.genomes (validation.defaultIgnoreParams=['genomes'])")),
 rass("host_fasta_bowtie2index", "prebuilt-index", "directory", False, "params_block", None,
      "Reference genome options", ["SHORTREAD_PREPROCESSING"],
      ev("subworkflows/local/preprocessing_shortread/main.nf:90", "high",
         "if absent, index is BUILT on the fly by BOWTIE2_HOST_REMOVAL_BUILD")),
 rass("multiqc_config", "config-file", "yaml", False, "params_block", None,
      "MultiQC options", ["MULTIQC"],
      ev("workflows/mag.nf:692", "high", "default file(\"${projectDir}/assets/multiqc_config.yml\")")),
 rass("multiqc_methods_description", "template-file", "yaml", False, "params_block", None,
      "MultiQC options", ["MULTIQC"],
      ev("workflows/mag.nf:682", "high", "default file(\"${projectDir}/assets/methods_description_template.yml\")")),
]
def rebuild(asset, guard, gparams, builder, outputs, fallback=None, sp="workflows/mag.nf", conf="high", *evd):
    return {"asset_param": asset, "guard": guard, "guard_params": gparams, "builder": builder,
            "builder_outputs": outputs, "fallback_for": fallback,
            "evidence": ev(sp, conf, *evd)}
reference_rebuilds = [
 rebuild("host_fasta_bowtie2index", "!params.host_fasta_bowtie2index",
         ["host_fasta", "host_genome"], "BOWTIE2_HOST_REMOVAL_BUILD", ["index"],
         "host_fasta_bowtie2index", "subworkflows/local/preprocessing_shortread/main.nf",
         "high", "bowtie2 index built from host_fasta whenever no prebuilt index is supplied and short reads exist"),
 rebuild("checkm_db", "params.run_checkm && !params.checkm_db", ["run_checkm"],
         "CHECKM_UNTAR (of file(params.checkm_download_url))", ["untar"], "checkm_db",
         "subworkflows/local/bin_qc/main.nf", "high",
         "download + untar of checkm_data_2015_01_16.tar.gz when CheckM is enabled without a db"),
 rebuild("checkm2_db", "params.run_checkm2 && !params.checkm2_db", ["run_checkm2"],
         "CHECKM2_DATABASEDOWNLOAD", ["database"], "checkm2_db",
         "subworkflows/local/bin_qc/main.nf", "high", "downloads by pinned Zenodo version checkm2_db_version"),
 rebuild("gunc_db", "params.run_gunc && !params.gunc_db", ["run_gunc"],
         "GUNC_DOWNLOADDB", ["db"], "gunc_db",
         "subworkflows/local/bin_qc/main.nf", "high", "gunc download_db . -db $db_name (params.gunc_database_type)"),
 rebuild("cat_db", "!params.cat_db && params.cat_db_generate", ["cat_db_generate"],
         "CATPACK_DOWNLOAD + CATPACK_PREPARE", ["database", "taxonomy"], "cat_db",
         "subworkflows/local/catpack/main.nf", "high",
         "downloads CAT nr sources (log-warned as very large) and builds the pack database"),
 rebuild("genomad_db", "!params.genomad_db && params.run_virus_identification", ["run_virus_identification"],
         "GENOMAD_DOWNLOAD", ["genomad_db"], "genomad_db",
         "subworkflows/local/virus_identification/main.nf", "high",
         "geNomad downloads its reference databases when none supplied"),
 rebuild("metaeuk_db", "params.metaeuk_mmseqs_db", ["metaeuk_mmseqs_db"],
         "MMSEQS_DATABASES", ["database"], "metaeuk_db",
         "workflows/mag.nf", "high", "mmseqs createdb/createindex from URL or db name"),
 rebuild("gtdb_db", "gtdb extension == gz", ["gtdb_db"],
         "GTDBTK_DB_PREPARATION", ["db"], None,
         "subworkflows/local/gtdbtk/main.nf", "high",
         "tar.gz db unpacked into directory layout; directory inputs used as-is"),
]

warnings = [
 "Source is a shallow clone of main (rev db7772f, manifest version 5.5.0 — post-release dev line), not a tagged release.",
 "nf-core/mag pins containers as Wave images (community.wave.seqera.io library + community-cr-prod blob) in module container directives; classical quay.io/depot.galaxyproject.org URIs are absent from the source, so tools[].singularity is usually null and tools[].wave holds the library tag instead.",
 "23 modules/local/* processes have no meta.yml; their IO was inferred from the script block (shapes are verbatim channel declarations).",
 "71 module-level nf-test files exist under modules/*/tests/ but were not expanded into processes[].module_tests / subworkflows[].tests: nf-test.config ignores them for the pipeline suite and fixture fetching was not requested.",
 "Workflow edges reconcile operator chains by reading mag.nf; complex inline closures (ch_allcontig2binmap splitFasta/collectFile, PYPOLCA combine/branch, GTDBTK groupKey metrics) are best-effort and carry the argument expressions in subworkflows[].invocations[].bindings for re-checking.",
 "Sample-sheet column 'required' reflects the items.required list only; the schema's anyOf (short_reads_1 OR long_reads) and dependentRequired (R2 requires R1, platform dependencies) rules are recorded in column descriptions instead.",
 "params[].default values are Groovy literals from nextflow.config (normalized: null/false/true/numbers parsed); expression defaults are kept as strings.",
 "Test fixture URLs are recorded, not fetched: remote samplesheets/databases point at the 'mag' branch of nf-core/test-datasets via the pipelines_testdata_base_path override in tests/nextflow.config.",
 "conf/test_full.config declares a full-scale profile (s3 inputs) but no test_full.nf.test exists; test_full stays a profile-level test candidate only (not emitted as nf-test candidate).",
 "PIPELINE_INITIALISATION/PIPELINE_COMPLETION are template utility subworkflows; raw_short_reads/raw_long_reads/input_assemblies channels are built inside PIPELINE_INITIALISATION (samplesheetToList of --input/--assembly_input).",
]

summary = {
 "source": source,
 "params": base["params"],
 "sample_sheets": sample_sheets,
 "profiles": profiles,
 "tools": base["tools"],
 "processes": base["processes"],
 "subworkflows": base["subworkflows"],
 "workflow": {"name": "MAG", "channels": channels, "edges": edges, "conditionals": conditionals},
 "reference_assets": reference_assets,
 "reference_rebuilds": reference_rebuilds,
 "test_candidates": test_candidates,
 "test_selection": test_selection,
 "warnings": warnings,
}
with open("/home/abennett/nf-core-mag/summary-nextflow.json", "w") as f:
    json.dump(summary, f, indent=1)
print("wrote summary-nextflow.json:",
      len(summary["processes"]), "processes,", len(summary["tools"]), "tools,",
      len(summary["params"]), "params,", len(summary["subworkflows"]), "subworkflows,",
      len(summary["test_candidates"]), "test candidates")
