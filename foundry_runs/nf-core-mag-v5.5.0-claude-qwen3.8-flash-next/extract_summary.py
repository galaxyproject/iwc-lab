#!/usr/bin/env python3
"""Deterministic extraction pass for summarize-nextflow on nf-core/mag.

Walks the source tree and emits base.json (processes, tools, params,
subworkflows, aliases, publish dirs) plus digest.txt (compact per-process
review sheet for the LLM-level script_summary pass). No LLM content here.
"""
import json, os, re, sys

SRC = "/home/abennett/nf-core-mag-src"

def rd(p):
    with open(os.path.join(SRC, p), encoding="utf-8") as f:
        return f.read()

# ---------------------------------------------------------------- process parsing
SECTION_RE = re.compile(r"^(\s{0,8})(input|output|when|script|shell|exec|stub):\s*(#.*)?$")

def strip_comments_lines(text):
    out = []
    for line in text.splitlines():
        # crude // comment strip, avoiding :// URLs and http(s)
        m = re.search(r"(?<![:\w])//(?![/:])", line)
        if m:
            line = line[:m.start()]
        out.append(line)
    return "\n".join(out)

def parse_process_blocks(text, relpath):
    """Return list of dicts for each `process NAME { ... }` block."""
    procs = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^process\s+([A-Z0-9_]+)\s*\{", lines[i])
        if m:
            name = m.group(1)
            depth = 1
            j = i + 1
            start = i + 1
            while j < len(lines) and depth:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            body = "\n".join(lines[start:j - 1])
            procs.append(extract_process(name, relpath, body))
            i = j
        else:
            i += 1
    return procs

def grab_directive(body, key):
    """Grab a possibly multi-line quoted directive value (container/conda)."""
    m = re.search(rf"^\s*{key}\s*(['\"])", body, re.M)
    if not m:
        return None
    q = m.group(1)
    rest = body[m.end():]
    # collect until a line that ends with a closing quote of same type (unbalanced check)
    lines = rest.split("\n")
    acc = ""
    for ln in lines:
        acc += ln + "\n"
        if acc.count(q) % 2 == 1:
            break
    val = acc.strip()
    # strip outer quotes
    if val.startswith(q):
        val = val[len(q):]
    if val.endswith(q):
        val = val[:-1]
    return val.strip()

def split_sections(body):
    sec = {"pre": []}
    order = ["pre"]
    cur = "pre"
    stub_mode = False
    for line in body.splitlines():
        m = SECTION_RE.match(line)
        if m and not stub_mode:
            cur = m.group(2)
            if cur == "stub":
                stub_mode = True
            sec.setdefault(cur, [])
            order.append(cur)
            continue
        if stub_mode:
            continue
        sec.setdefault(cur, []).append(line)
    return {k: "\n".join(v) for k, v in sec.items()}

def clean_io_line(line):
    line = re.sub(r"//.*$", "", line).strip().rstrip(",")
    return line

def parse_io(section_text):
    ios = []
    for raw in section_text.splitlines():
        line = clean_io_line(raw)
        if not line:
            continue
        name = None
        topic = None
        mt = re.search(r"topic:\s*([A-Za-z0-9_]+)", line)
        if mt:
            topic = mt.group(1)
            line = line[:mt.start()].rstrip().rstrip(",").strip()
        me = re.search(r"emit:\s*([A-Za-z0-9_]+)", line)
        if me:
            name = me.group(1)
            line = line[:me.start()].rstrip().rstrip(",").strip()
        if not line:
            continue
        shape = re.sub(r"\s+", " ", line)
        if name is None:
            # prefer a path(...) variable, then val(...), else the raw shape
            mp = re.search(r'path\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,|\))', shape)
            if not mp:
                mp = re.search(r'path\s*\(\s*["\']([^"\']+)["\']', shape)
            if not mp:
                mp = re.search(r'\bpath\s+([A-Za-z_][A-Za-z0-9_]*)', shape)
            if not mp:
                mp = re.search(r'val\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:,|\))', shape)
            if not mp:
                mp = re.search(r'\bval\s+([A-Za-z_][A-Za-z0-9_]*)', shape)
            name = mp.group(1) if mp else shape
        ios.append({"name": name, "shape": shape, "description": None, "topic": topic})
    return ios

def dedent(t):
    ls = t.splitlines()
    pads = [len(l) - len(l.lstrip()) for l in ls if l.strip()]
    p = min(pads) if pads else 0
    return "\n".join(l[p:] if l.strip() else "" for l in ls)

def extract_process(name, relpath, body):
    sec = split_sections(body)
    pre = sec.get("pre", "")
    container = grab_directive(pre, "container")
    conda = grab_directive(pre, "conda")
    when = None
    if sec.get("when"):
        when = dedent(sec["when"]).strip()
    inputs = parse_io(sec.get("input", ""))
    outputs = parse_io(sec.get("output", ""))
    script_raw = ""
    for k in ("script", "shell", "exec"):
        if sec.get(k):
            script_raw = sec[k]
            break
    # strip enclosing triple quotes
    s = script_raw
    s = re.sub(r'^\s*"""/?\'?\'?', "", s)
    s = re.sub(r'"""\s*$', "", s)
    s = re.sub(r"^'''''?'?", "", s)
    s = dedent(s).strip()
    if len(s) > 4000:
        s = s[:4000]
    return {
        "name": name, "aliases": [], "in_subworkflows": [],
        "module_path": relpath, "meta": None, "module_tests": [],
        "tool": None, "container": container, "conda": conda,
        "inputs": inputs, "outputs": outputs, "when": when,
        "script_excerpt": s or None, "publish_dir": None,
    }

def load_meta(mod_dir):
    p = os.path.join(SRC, mod_dir, "meta.yml")
    if not os.path.exists(p):
        return None
    import yaml
    try:
        y = yaml.safe_load(rd(mod_dir + "/meta.yml"))
    except Exception:
        return None
    if not isinstance(y, dict):
        return None
    def entries(v):
        out = []
        if isinstance(v, list):
            for e in v:
                if isinstance(e, dict):
                    for k, vv in e.items():
                        if isinstance(vv, dict):
                            ent = {"name": str(k)}
                            for fk in ("description", "pattern", "type", "format", "homepage", "documentation", "doi", "identifier"):
                                ent[fk] = vv.get(fk)
                            out.append({kk: vvv for kk, vvv in ent.items() if vvv is not None})
        return out
    tools = []
    for e in y.get("tools", []) or []:
        if isinstance(e, dict):
            for k, vv in e.items():
                tools.append({"name": str(k), "description": vv.get("description") if isinstance(vv, dict) else None,
                              "doi": vv.get("doi") if isinstance(vv, dict) else None})
    return {"description": y.get("description"), "keywords": y.get("keywords") or [],
            "authors": y.get("authors") or [], "maintainers": y.get("maintainers") or [],
            "tools": tools, "input": entries(y.get("input")), "output": entries(y.get("output"))}

def env_deps(mod_dir):
    p = os.path.join(SRC, mod_dir, "environment.yml")
    if not os.path.exists(p):
        return []
    import yaml
    try:
        y = yaml.safe_load(rd(mod_dir + "/environment.yml"))
    except Exception:
        return []
    return [d for d in (y.get("dependencies") or []) if isinstance(d, str)]

# collect processes from all module files
processes = []
proc_index = {}  # name -> process dict
module_of = {}   # process name -> module dir relpath
for root, dirs, files in os.walk(os.path.join(SRC, "modules")):
    if "main.nf" not in files:
        continue
    rel = os.path.relpath(os.path.join(root, "main.nf"), SRC)
    for pr in parse_process_blocks(rd(rel), rel):
        processes.append(pr)
        proc_index.setdefault(pr["name"], pr)
        module_of[pr["name"]] = os.path.dirname(rel)

# attach meta + env deps
for pr in processes:
    md = module_of[pr["name"]]
    pr["meta"] = load_meta(md)
    pr["_deps"] = env_deps(md)

# ---------------------------------------------------------------- includes & aliases
INC_RE = re.compile(r"include\s*\{\s*([^}]+?)\s*\}\s*from")
aliases_by_canon = {}      # canonical -> [alias]
in_sub_by_proc = {}        # canonical -> [caller workflow names]
sw_files = []
for root, dirs, files in os.walk(SRC):
    if any(seg in root for seg in ("/.git", "/tests", "/modules")):
        continue
    for f in files:
        if f.endswith(".nf"):
            sw_files.append(os.path.relpath(os.path.join(root, f), SRC))
sw_files += [os.path.relpath(os.path.join(root, f), SRC)
             for root, dirs, files in os.walk(os.path.join(SRC, "modules"))
             for f in files if False]  # none; placeholder

def workflow_names_in(relpath):
    return re.findall(r"^workflow\s+([A-Z0-9_]+)\s*\{", rd(relpath), re.M)

include_map = {}  # file -> [(canonical, alias)]
for rel in sw_files:
    text = strip_comments_lines(rd(rel))
    wnames = workflow_names_in(rel)
    caller = wnames[0] if wnames else rel
    for m in INC_RE.finditer(text):
        inner = m.group(1)
        # 'A as B' possibly multiple names 'A, B as C' (rare) -> handle simple forms
        for part in inner.split(","):
            part = part.strip()
            am = re.match(r"([A-Za-z0-9_]+)(?:\s+as\s+([A-Z0-9_]+))?$", part)
            if not am:
                continue
            canon, alias = am.group(1), am.group(2) or am.group(1)
            if not re.match(r"^[A-Z][A-Z0-9_]*$", canon):
                continue  # functions / plugin utils
            include_map.setdefault(rel, []).append((canon, alias))
            if canon != alias:
                aliases_by_canon.setdefault(canon, set()).add(alias)
            if canon in proc_index:
                if caller not in in_sub_by_proc.setdefault(canon, []):
                    in_sub_by_proc[canon].append(caller)

for canon, als in aliases_by_canon.items():
    if canon in proc_index:
        proc_index[canon]["aliases"] = sorted(als)
for canon, callers in in_sub_by_proc.items():
    proc_index[canon]["in_subworkflows"] = sorted(callers)

# ---------------------------------------------------------------- publish dirs (conf/modules.config)
mc = strip_comments_lines(rd("conf/modules.config"))
pub = {}
for m in re.finditer(r"withName:\s*([A-Z0-9_]+)\s*\{", mc):
    aname = m.group(1)
    depth, j = 1, m.end()
    while j < len(mc) and depth:
        depth += mc[j].count("{") - mc[j].count("}")
        j += 1
    blk = mc[m.end():j - 1]
    pdm = re.search(r"publishDir\s*=\s*\[", blk)
    if pdm:
        d, k = 1, pdm.end()
        while k < len(blk) and d:
            d += blk[k].count("[") - blk[k].count("]")
            k += 1
        ptxt = blk[pdm.end():k - 1]
        if "enabled: false" in ptxt and ptxt.count("path:") == ptxt.count("enabled: false"):
            continue
        paths = re.findall(r"path:\s*(\{(?:[^{}]|\{[^{}]*\})*\}|\"[^\"]*\"|'[^']*')", ptxt)
        pats = re.findall(r"pattern:\s*(\"[^\"]*\"|'[^']*')", ptxt)
        if paths:
            pub.setdefault(aname, []).append(
                " + ".join(p.strip("{}\"' ") for p in paths) +
                (" (pattern: " + "; ".join(p.strip() for p in pats) + ")" if pats else ""))
for canon, pr in proc_index.items():
    keys = [canon] + sorted(aliases_by_canon.get(canon, []))
    entries = []
    for k in keys:
        for e in pub.get(k, []):
            tag = "" if k == canon else f"[{k}] "
            entries.append(tag + e)
    if entries:
        pr["publish_dir"] = " ; ".join(entries)

# ---------------------------------------------------------------- subworkflows
SW_DIRS = sorted(
    [os.path.relpath(os.path.join(root, "main.nf"), SRC)
     for root, dirs, files in os.walk(os.path.join(SRC, "subworkflows"))
     if "main.nf" in files]
)
sw_takes = {}
subworkflows_info = []
sw_decl = {}
for rel in SW_DIRS:
    text = rd(rel)
    for m in re.finditer(r"workflow\s+([A-Z0-9_]+)\s*\{", text):
        sw_decl.setdefault(m.group(1), rel)

# pre-pass: collect every subworkflow's take list so invocations can bind by position
for rel in SW_DIRS:
    text = rd(rel)
    for m in re.finditer(r"workflow\s+([A-Z0-9_]+)\s*\{", text):
        nm = m.group(1)
        tm = re.search(r"^\s{4}take:(.*?)(?=^\s{4}(?:main|emit):)", text[m.end():], re.S | re.M)
        tk = []
        if tm:
            for ln in tm.group(1).splitlines():
                ln = re.sub(r"//.*", "", ln).strip()
                if ln:
                    tk.append(ln.split()[0])
        sw_takes[nm] = tk
# MAG's take names (primary workflow; used by the hand-written NFCORE_MAG invocation)
mag_text = rd("workflows/mag.nf")
mm = re.search(r"workflow MAG \{\s*take:(.*?)main:", mag_text, re.S)
sw_takes["MAG"] = [l.split()[0] for l in
                   (re.sub(r"//.*", "", x).strip() for x in mm.group(1).splitlines()) if l]

for rel in SW_DIRS:
    text = rd(rel)
    names = re.findall(r"^workflow\s+([A-Z0-9_]+)\s*\{", text, re.M)
    if not names:
        continue
    for name in names:
        m = re.search(rf"workflow\s+{name}\s*\{{", text)
        depth, j = 1, m.end()
        lines = text[m.end():].split("\n")
        body_lines, dep = [], 1
        for ln in lines:
            dep += ln.count("{") - ln.count("}")
            if dep <= 0:
                break
            body_lines.append(ln)
        body = "\n".join(body_lines)
        clean = strip_comments_lines(body)
        tm = re.search(r"^\s{4}take:(.*?)(?=^\s{4}(?:main|emit):)", body, re.S | re.M)
        take = []
        if tm:
            for ln in tm.group(1).splitlines():
                ln = re.sub(r"//.*", "", ln).strip()
                if ln:
                    take.append(ln.split()[0])
        em = re.search(r"^\s{4}emit:(.*)$", body, re.S | re.M)
        outs = []
        if em:
            for ln in em.group(1).splitlines():
                ln2 = ln.strip()
                if not ln2 or ln2.startswith("//"):
                    continue
                am = re.match(r"([A-Za-z0-9_]+)\s*=\s*([^/]+?)\s*(?://\s*channel:\s*(.*))?$", ln2)
                if am:
                    outs.append({"name": am.group(1),
                                 "shape": re.sub(r"\s+", " ", am.group(2).strip()),
                                 "description": am.group(3), "topic": None})
        # includes for this file
        calls, invocations = [], []
        inc = include_map.get(rel, [])
        inc_lookup = {a: c for c, a in inc}
        inc_lookup.update({c: c for c, a in inc})
        for canon, alias in inc:
            cm = re.search(rf"(?:^|[=\s]){alias}\s*\(", clean, re.M)
            hits = [mm for mm in re.finditer(rf"(?<![\w.]){alias}\s*\(", clean)
                    if not clean[:mm.start()].rstrip().endswith("include")]
            if hits:
                if alias not in calls:
                    calls.append(alias)
                hm = hits[0]
                d, k = 1, hm.end()
                while k < len(clean) and d:
                    d += clean[k].count("(") - clean[k].count(")")
                    k += 1
                argtxt = clean[hm.end():k - 1]
                args, acc2, d2 = [], "", 0
                for chx in argtxt:
                    if chx in "([{":
                        d2 += 1
                    elif chx in ")]}":
                        d2 -= 1
                    if chx == "," and d2 == 0:
                        args.append(acc2.strip()); acc2 = ""
                    else:
                        acc2 += chx
                if acc2.strip():
                    args.append(acc2.strip())
                args = [re.sub(r"\s+", " ", a.split("//")[0].strip()) for a in args if a.strip()]
                bindings = []
                callee_take = sw_takes.get(alias)
                if callee_take is None and alias in proc_index:
                    callee_take = [i["name"] for i in proc_index[alias]["inputs"]]
                if callee_take is None and canon in proc_index:
                    callee_take = [i["name"] for i in proc_index[canon]["inputs"]]
                if callee_take:
                    bindings = [{"take": callee_take[i] if i < len(callee_take) else f"arg{i}",
                                 "argument": a} for i, a in enumerate(args)]
                invocations.append({"caller": alias, "caller_path": rel,
                                    "arguments": args, "bindings": bindings})
        utility_name = name in ("PIPELINE_INITIALISATION", "PIPELINE_COMPLETION")
        utility_path = "/utils_" in "/" + rel
        kind = "utility" if (not calls or utility_name or utility_path) else "pipeline"
        subworkflows_info.append({
            "name": name, "path": rel, "kind": kind, "aliases": [],
            "calls": calls, "inputs": [], "outputs": outs,
            "invocations": invocations, "tests": [],
        })
        sw_takes[name] = take

# NFCORE_MAG wrapper + entrypoint
nfc = {"name": "NFCORE_MAG", "path": "main.nf", "kind": "pipeline", "aliases": [],
       "calls": ["MAG"], "inputs": [], "outputs": [
           {"name": "multiqc_report", "shape": "MAG.out.multiqc_report", "description": "/path/to/multiqc_report.html", "topic": None}],
       "invocations": [{"caller": "MAG", "caller_path": "main.nf",
                        "arguments": ["raw_short_reads", "raw_long_reads", "input_assemblies",
                                       "params.multiqc_config", "params.multiqc_logo",
                                       "params.multiqc_methods_description", "params.outdir"],
                        "bindings": [
                            {"take": "ch_raw_short_reads", "argument": "raw_short_reads"},
                            {"take": "ch_raw_long_reads", "argument": "raw_long_reads"},
                            {"take": "ch_input_assemblies", "argument": "input_assemblies"},
                            {"take": "multiqc_config", "argument": "params.multiqc_config"},
                            {"take": "multiqc_logo", "argument": "params.multiqc_logo"},
                            {"take": "multiqc_methods_description", "argument": "params.multiqc_methods_description"},
                            {"take": "outdir", "argument": "params.outdir"}]}],
       "tests": []}
subworkflows_info.append(nfc)

# fix take inputs for subworkflows (inputs[] field: take names w/ shapes from comments)
for sw in subworkflows_info:
    rel = sw["path"]
    text = rd(rel)
    m = re.search(rf"workflow\s+{sw['name']}\s*\{{", text)
    if not m:
        continue
    tm = re.search(r"^\s{4}take:(.*?)(?=^\s{4}(?:main|emit):)", text[m.end():], re.S | re.M)
    ins = []
    if tm:
        for ln in tm.group(1).splitlines():
            cm = re.match(r"\s*([A-Za-z0-9_]+)\s*(?://\s*channel:\s*(.*))?$", ln)
            if cm:
                ins.append({"name": cm.group(1), "shape": "channel",
                            "description": cm.group(2), "topic": None})
            elif re.sub(r"//.*", "", ln).strip():
                nm = re.sub(r"//.*", "", ln).strip().split()[0]
                ins.append({"name": nm, "shape": "channel", "description": None, "topic": None})
    sw["inputs"] = ins

# ---------------------------------------------------------------- tools
def classify_image(url):
    if not url:
        return None
    if "depot.galaxyproject.org/singularity" in url:
        return "singularity"
    if url.startswith("quay.io/biocontainers/") or "quay.io/biocontainers" in url:
        return "biocontainer"
    if "community.wave.seqera.io" in url or "community-cr-prod.seqera.io" in url or "community-cr-prod" in url:
        return "wave"
    return "docker"

def unquoted_images(directive):
    if not directive:
        return []
    return [s.strip() for s in re.findall(r"['\"]([^'\"]+)['\"]", directive)
            if "://" in s or "seqera.io" in s or "/" in s]

tools = {}
for pr in processes:
    imgs = unquoted_images(pr["container"])
    fields = {"biocontainer": None, "docker": None, "singularity": None, "wave": None}
    for u in imgs:
        f = classify_image(u)
        if f and not fields[f]:
            fields[f] = u
    deps = pr["_deps"]
    chosen = None
    for d in deps:
        if "::" in d:
            dm = re.match(r"^\w*::([A-Za-z0-9_.\-]+?)(=+|>=|==|>|<)(.*)$", d.strip())
            if dm:
                tname, sep, ver = dm.group(1), dm.group(2), dm.group(3)
            else:
                dm = re.match(r"^\w*::([A-Za-z0-9_.\-]+)$", d.strip())
                if not dm:
                    continue
                tname, sep, ver = dm.group(1), None, None
        else:
            dm = re.match(r"^([A-Za-z0-9_.\-]+?)(=+|>=|==|>|<)(.*)$", d.strip())
            if dm:
                tname, sep, ver = dm.group(1), dm.group(2), dm.group(3)
            else:
                dm = re.match(r"^([A-Za-z0-9_.\-]+)$", d.strip())
                if not dm:
                    continue
                tname, sep, ver = dm.group(1), None, None
        tver = ver.split(" ")[0] if ver else "unknown"
        bio = d.strip() if "bioconda" in d else None
        if sep in (">=", "==", ">", "<"):
            # inexact pin: version is unknown, constraint kept verbatim
            entry = tools.setdefault((tname, "unknown"), {
                "name": tname, "version": "unknown",
                "version_constraint": d.strip(), "biocontainer": None, "bioconda": bio,
                "docker": None, "singularity": None, "wave": None,
                "mulled_components": [], "versions": []})
        elif sep == "==" or tver != "unknown":
            exact = tver if sep != "==" else ver.split(" ")[0]
            entry = tools.setdefault((tname, tver), {
                "name": tname, "version": tver, "version_constraint": None,
                "biocontainer": None, "bioconda": bio,
                "docker": None, "singularity": None, "wave": None,
                "mulled_components": [], "versions": [tver] if tver != "unknown" else []})
        else:
            entry = tools.setdefault((tname, "unknown"), {
                "name": tname, "version": "unknown", "version_constraint": None,
                "biocontainer": None, "bioconda": bio,
                "docker": None, "singularity": None, "wave": None,
                "mulled_components": [], "versions": []})
        # attach container fields to matching tool (by name token)
        norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
        for u in imgs:
            if norm(tname) in norm(u):
                f = classify_image(u)
                if f and not entry[f]:
                    entry[f] = u
        if tname not in ("pigz", "pysam", "xopen", "sed", "coreutils", "gzip"):
            chosen = chosen or tname
    # primary tool pick: name appearing in process name, else wave image token, else first
    pn = pr["name"]
    pick = None
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    for d in deps:
        t = re.match(r"^\w+::([A-Za-z0-9_.\-]+)", d)
        if t and norm(t.group(1)) and norm(t.group(1)) in norm(pn):
            pick = t.group(1)
            break
    if not pick and deps:
        t = re.match(r"^\w+::([A-Za-z0-9_.\-]+)", deps[0])
        pick = t.group(1) if t else None
    pr["tool"] = pick

# tools that only have container evidence (no env yml deps) -> derive from image name
for pr in processes:
    if pr["_deps"]:
        continue
    for u in unquoted_images(pr["container"]):
        m = re.match(r"^(?:quay\.io/biocontainers/|docker\.io/biocontainers/)?([A-Za-z0-9._\-]+):([A-Za-z0-9._\-]+)$", u)
        if m and "/" not in m.group(1):
            tname, tver = m.group(1), m.group(2)
            f = classify_image(u)
            entry = tools.setdefault((tname, tver), {
                "name": tname, "version": tver, "version_constraint": None,
                "biocontainer": u if f == "biocontainer" else None, "bioconda": None,
                "docker": u if f == "docker" else None,
                "singularity": u if f == "singularity" else None,
                "wave": u if f == "wave" else None,
                "mulled_components": [], "versions": [tver]})
            break
        wm = re.match(r"^community\.wave\.seqera\.io/library/([A-Za-z0-9._\-]+):(.+)$", u)
        if wm:
            fname = wm.group(1).split("_")[0]
            entry = tools.setdefault((fname, "unknown"), {
                "name": fname, "version": "unknown", "version_constraint": None,
                "biocontainer": None, "bioconda": None, "docker": None,
                "singularity": None, "wave": u, "mulled_components": [], "versions": []})
            break

deps_map = {pr["name"]: pr.pop("_deps") for pr in processes}

# ---------------------------------------------------------------- params
schema = json.loads(rd("nextflow_schema.json"))
# nextflow.config root params block
cfg = rd("nextflow.config")
pb = re.search(r"^params \{(.*?)^\}", cfg, re.S | re.M)
defaults = {}
for m in re.finditer(r"^\s{4}([a-z0-9_]+)\s*=\s*([^#\n]+)", pb.group(1), re.M):
    defaults[m.group(1)] = m.group(2).strip()

params_out = []
seen = set()
def ptype(ty):
    if isinstance(ty, list):
        return "|".join(str(t) for t in ty)
    return str(ty) if ty is not None else "string"

for ref in [d["$ref"].split("/")[-1] for d in schema.get("allOf", []) if "$ref" in d]:
    g = schema["$defs"][ref]
    req = set(g.get("required", []))
    for pname, pdef in g.get("properties", {}).items():
        if pname in seen:
            continue
        seen.add(pname)
        p = {
            "name": pname,
            "type": ptype(pdef.get("type")),
            "default": defaults.get(pname),
            "description": pdef.get("description"),
            "required": pname in req,
            "enum": pdef.get("enum"),
            "format": pdef.get("format"),
            "hidden": pdef.get("hidden", False),
            "mimetype": pdef.get("mimetype"),
            "schema_group": g.get("title", ref),
            "fa_icon": pdef.get("fa_icon"),
            "source_kind": "nextflow_schema",
            "source_expression": None,
            "source_path": "nextflow_schema.json",
        }
        if p["default"] is None and pname in defaults:
            p["default"] = defaults[pname]
        params_out.append(p)
# config-only params not in schema
for pname, dv in defaults.items():
    if pname not in seen:
        params_out.append({"name": pname, "type": "string", "default": dv,
                           "description": None, "required": False, "enum": None,
                           "format": None, "hidden": None, "mimetype": None,
                           "schema_group": None, "fa_icon": None,
                           "source_kind": "params_block",
                           "source_expression": None, "source_path": "nextflow.config"})
params_out.append({"name": "trace_report_suffix", "type": "string",
                   "default": None, "description": "Timestamp suffix for trace/report file names (computed at config load)",
                   "required": False, "enum": None, "format": None, "hidden": True,
                   "mimetype": None, "schema_group": None, "fa_icon": None,
                   "source_kind": "computed",
                   "source_expression": "new java.util.Date().format('yyyy-MM-dd_HH-mm-ss')",
                   "source_path": "nextflow.config"})

base = {
    "processes": processes,
    "tools": sorted(tools.values(), key=lambda t: (t["name"], t["version"])),
    "params": params_out,
    "subworkflows": subworkflows_info,
}
outdir = "/home/abennett/nf-core-mag"
with open(os.path.join(outdir, "base.json"), "w") as f:
    json.dump(base, f, indent=1)

with open(os.path.join(outdir, "digest.txt"), "w") as f:
    for pr in processes:
        desc = (pr["meta"] or {}).get("description")
        td = ((pr["meta"] or {}).get("tools") or [{}])
        tname = td[0].get("name") if td else None
        f.write(f"{pr['name']}\t{pr['module_path']}\tdeps={','.join(deps_map.get(pr['name'], []))}\tmeta={desc}\ttool={tname}\tscript={re.sub(chr(10),' ',(pr['script_excerpt'] or ''))[:160]}\n")

print("processes:", len(processes), "tools:", len(tools), "params:", len(params_out), "subworkflows:", len(subworkflows_info))
missing_meta = [p["name"] for p in processes if not p["meta"]]
print("no meta.yml:", missing_meta)
missing_container = [p["name"] for p in processes if not p["container"]]
print("no container directive:", missing_container)
missing_conda = [p["name"] for p in processes if not p["conda"]]
print("no conda directive:", missing_conda)
