#!/usr/bin/env python3
"""Implement the concrete wrapper-resolved steps in the draft.

Wrapper ports/state come from tool-summaries/*.json (galaxy-tool-cache summarize)
and from valid IWC tool_state examples in ~/.foundry/iwc.
"""
import json
import sys

import yaml

DRAFT = sys.argv[1]
d = yaml.safe_load(open(DRAFT))

steps = {s["id"]: s for s in d["steps"]}
order = [s["id"] for s in d["steps"]]


def impl(sid, **fields):
    s = steps[sid]
    for k in list(s):
        if k.startswith("_plan_"):
            del s[k]
    for k, v in fields.items():
        if v is None:
            s.pop(k, None)
        else:
            s[k] = v


CONN = {"__class__": "ConnectedValue"}
RUNTIME = {"__class__": "RuntimeValue"}

# ---------------------------------------------------------------- samtools QC
impl(
    "flagstat",
    tool_id="toolshed.g2.bx.psu.edu/repos/devteam/samtools_flagstat/samtools_flagstat",
    tool_version="2.0.8",
    **{
        "in": [{"id": "input1", "source": "input"}],
        "out": [{"id": "output1"}],
        "state": {"input1": CONN, "output_fmt": "txt"},
    },
)

impl(
    "idxstats",
    tool_id="toolshed.g2.bx.psu.edu/repos/devteam/samtools_idxstats/samtools_idxstats",
    tool_version="2.0.8",
    **{
        "in": [{"id": "input", "source": "input"}],
        "out": [{"id": "output"}],
        "state": {"input": CONN},
    },
)

impl(
    "stats",
    tool_id="toolshed.g2.bx.psu.edu/repos/devteam/samtools_stats/samtools_stats",
    tool_version="2.0.9",
    **{
        "in": [{"id": "input", "source": "input"}],
        "out": [{"id": "output"}],
        "state": {
            "addref_cond": {"addref_select": "no", "__current_case__": 0},
            "cond_region": {"select_region": "no", "__current_case__": 0},
            "cov_threshold": None,
            "coverage_cond": {"coverage_select": "no", "__current_case__": 0},
            "filter_by_flags": {"filter_flags": "nofilter", "__current_case__": 1},
            "gc_depth": None,
            "input": CONN,
            "insert_size": None,
            "most_inserts": None,
            "read_group": None,
            "read_length": None,
            "remove_dups": False,
            "remove_overlaps": False,
            "sparse": False,
            "split_output_cond": {"split_output_selector": "no", "__current_case__": 0},
            "trim_quality": None,
        },
    },
)

# --------------------------------------------------------------- samtools view
VIEW_STATE = {
    "addref_cond": {"addref_select": "no", "__current_case__": 0},
    "input": CONN,
    "mode": {
        "outtype": "selected_reads",
        "__current_case__": 1,
        "filter_config": {
            "cond_region": {"select_region": "no", "__current_case__": 0},
            "cond_rg": {"select_rg": "no", "__current_case__": 0},
            "cond_expr": {"select_expr": "no", "__current_case__": 0},
            "quality": None,
            "library": None,
            "cigarcons": None,
            "inclusive_filter": None,
            "exclusive_filter": None,
            "exclusive_filter_all": None,
            "tag": None,
            "qname_file": RUNTIME,
        },
        "output_options": {
            "reads_report_type": "retained",
            "__current_case__": 0,
            "complementary_output": False,
            "adv_output": {"readtags": [], "collapsecigar": False},
            "output_format": {"oformat": "bam", "__current_case__": 2},
        },
    },
}


def view(sid, inc, exc):
    st = json.loads(json.dumps(VIEW_STATE))
    st["mode"]["filter_config"]["inclusive_filter"] = inc
    st["mode"]["filter_config"]["exclusive_filter"] = exc
    impl(
        sid,
        tool_id="toolshed.g2.bx.psu.edu/repos/iuc/samtools_view/samtools_view",
        tool_version="1.22+galaxy2",
        **{
            "in": [{"id": "input", "source": "input"}],
            "out": [{"id": "outputsam"}],
            "state": st,
        },
    )


view("view_map_map", ["1"], ["4", "8"])
view("view_unmap_unmap", ["4", "8"], ["256"])
view("view_unmap_map", ["4"], ["8", "256"])
view("view_map_unmap", ["8"], ["4", "256"])

# ------------------------------------------------------------------- FastQC
FASTQC_STATE = {
    "adapters": RUNTIME,
    "contaminants": RUNTIME,
    "input_file": CONN,
    "kmers": "7",
    "limits": RUNTIME,
    "min_length": None,
    "nogroup": False,
}


def fastqc(sid, src):
    st = json.loads(json.dumps(FASTQC_STATE))
    impl(
        sid,
        tool_id="toolshed.g2.bx.psu.edu/repos/devteam/fastqc/fastqc",
        tool_version="0.74+galaxy1",
        **{
            "in": [{"id": "input_file", "source": src}],
            "out": [{"id": "html_file"}, {"id": "text_file"}],
            "state": st,
        },
    )


fastqc("fastqc_pre", "input")
fastqc("fastqc_post_paired", "zip_reads_paired/output")
fastqc("fastqc_post_single", "fastq_single/TODO_other")

# --------------------------------------------------------------- collections
ZIP_STATE = {"input_forward": CONN, "input_reverse": CONN}


def zipcoll(sid, fwd, rev):
    st = json.loads(json.dumps(ZIP_STATE))
    impl(
        sid,
        tool_id="__ZIP_COLLECTION__",
        tool_version=None,
        **{
            "in": [
                {"id": "input_forward", "source": fwd},
                {"id": "input_reverse", "source": rev},
            ],
            "out": [{"id": "output"}],
            "state": st,
        },
    )


zipcoll("zip_unmapped_ab", "view_unmap_unmap/outputsam", "view_unmap_map/outputsam")
zipcoll("zip_unmapped_abc", "merge_unmapped_ab/output", "view_map_unmap/outputsam")
zipcoll("zip_reads_paired", "cat_r1/out_file1", "cat_r2/out_file1")

MERGE_STATE = {
    "bamfiles": CONN,
    "bed_file": RUNTIME,
    "headerbam": RUNTIME,
    "idpg": False,
    "idrg": False,
    "region": None,
    "seed": 1,
}
for sid, src in (
    ("merge_unmapped_ab", "zip_unmapped_ab/output"),
    ("merge_unmapped_abc", "zip_unmapped_abc/output"),
):
    st = json.loads(json.dumps(MERGE_STATE))
    impl(
        sid,
        tool_id="toolshed.g2.bx.psu.edu/repos/iuc/samtools_merge/samtools_merge",
        tool_version="1.22+galaxy2",
        **{
            "in": [{"id": "bamfiles", "source": src}],
            "out": [{"id": "output"}],
            "state": st,
        },
    )

CAT_STATE = {"input1": CONN, "queries": [{"__index__": 0, "input2": CONN}]}
for sid, a, b in (
    ("cat_r1", "fastq_mapped/TODO_forward", "fastq_unmapped/TODO_forward"),
    ("cat_r2", "fastq_mapped/TODO_reverse", "fastq_unmapped/TODO_reverse"),
):
    st = json.loads(json.dumps(CAT_STATE))
    impl(
        sid,
        tool_id="cat1",
        tool_version=None,
        **{
            "in": [
                {"id": "input1", "source": a},
                {"id": "queries_0|input2", "source": b},
            ],
            "out": [{"id": "out_file1"}],
            "state": st,
        },
    )

# ------------------------------------------------------------------- MultiQC
MQ_STATE = {
    "results": [
        {"software_cond": {"software": "fastqc"}},
        {"software_cond": {"software": "fastqc"}},
        {"software_cond": {"software": "fastqc"}},
    ],
    "title": CONN,
    "comment": "",
    "flat": False,
    "export": False,
    "png_plots": False,
}
impl(
    "multiqc",
    tool_id="toolshed.g2.bx.psu.edu/repos/iuc/multiqc/multiqc",
    tool_version="1.35+galaxy5",
    **{
        "in": [
            {"id": "results_0|software_cond|input", "source": "fastqc_pre/html_file"},
            {"id": "results_1|software_cond|input", "source": "fastqc_post_paired/html_file"},
            {"id": "results_2|software_cond|input", "source": "fastqc_post_single/html_file"},
            {"id": "title", "source": "multiqc_title"},
        ],
        "out": [{"id": "html_report"}],
        "state": MQ_STATE,
    },
)

# ------------------------------------------------- topology change: no filter
# __APPLY_RULES__ cannot filter by datatype extension, so the BAM-only
# pre-conversion FastQC step is fed the whole input list instead; recorded in
# the ledger.
d["steps"] = [s for s in d["steps"] if s["id"] != "filter_bam"]

# multiqc_config has no matching input on the selected wrapper.
d["inputs"].pop("multiqc_config", None)

yaml.safe_dump(d, open(DRAFT, "w"), sort_keys=False, default_flow_style=False)
print("rewrote", DRAFT, "steps:", len(d["steps"]))
