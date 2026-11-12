#!/usr/bin/env python3
"""Deterministic extraction pass for summary-nextflow.json (nf-core/ampliseq).

Usage: python3 -I summarize_extract.py <src_root> <out_json>
"""
import json, re, sys, os, glob, hashlib

SRC = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]

def read(p):
    with open(os.path.join(SRC, p), encoding='utf-8', errors='replace') as f:
        return f.read()

def strip_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    text = re.sub(r'^\s*//.*$', '', text, flags=re.M)
    return text

def brace_end(text, start):
    """index after matching close brace for the '{' at or after start"""
    i = text.find('{', start)
    depth = 0
    while i < len(text):
        c = text[i]
        if c == '{': depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0: return i + 1
        i += 1
    return len(text)

def dedent(s):
    lines = s.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    while lines and not lines[-1].strip(): lines.pop()
    if not lines: return ''
    ind = min((len(l) - len(l.lstrip())) for l in lines if l.strip())
    return '\n'.join(l[ind:] if len(l) >= ind else l for l in lines)[:4000]

# ---------------- source ----------------
lic = 'MIT'
for name in ('LICENSE', 'LICENSE.md'):
    if os.path.exists(os.path.join(SRC, name)):
        t = read(name)[:2000].lower()
        lic = 'MIT' if 'mit license' in t or 'permission is hereby granted' in t else 'unknown'
config = read('nextflow.config')
man_ver = re.search(r'manifest\s*\{[^}]*?version\s*=\s*[\'"]([^\'"]+)', config, re.S)
sha = os.popen(f'git -C {SRC} rev-parse HEAD').read().strip()
source = {
    "ecosystem": "nf-core",
    "workflow": "ampliseq",
    "url": "https://github.com/nf-core/ampliseq",
    "version": sha,
    "license": lic,
    "slug": "nf-core-ampliseq",
}
warnings = []

# ---------------- params ----------------
schema = json.loads(read('nextflow_schema.json'))
params = []
seen_names = set()
for dname, d in schema.get('$defs', {}).items():
    for pname, p in d.get('properties', {}).items():
        if pname in seen_names or not isinstance(p, dict):
            continue
        seen_names.add(pname)
        ent = {
            "name": pname, "type": str(p.get('type', 'string')),
            "default": p.get('default'),
            "description": p.get('description', ''), "required": False,
            "schema_group": dname,
        }
        if isinstance(p.get('enum'), list): ent['enum'] = p['enum']
        for k in ('format', 'mimetype', 'fa_icon'):
            if isinstance(p.get(k), str): ent[k] = p[k]
        if isinstance(p.get('hidden'), bool): ent['hidden'] = p['hidden']
        params.append(ent)
req = set()
for grp in schema.get('allOf', []):
    for r in grp.get('required', []): req.add(r)
for p in params:
    if p['name'] in req: p['required'] = True
by_name = {p['name']: p for p in params}
# input_fasta required only in the fasta branch (oneOf) - keep required False, note
warnings.append("nextflow_schema.json oneOf makes either --input or --input_fasta required; both marked per-param as non-required.")

# ---------------- sample sheets ----------------
sample_sheets = []
def sheet_entry(param, schema_path, via):
    d = json.loads(read(schema_path))
    props = d['items']['properties']
    cols = []
    for cn, c in props.items():
        fmt = c.get('format')
        kind = 'data' if fmt in ('file-path', 'directory-path', 'path') else 'meta'
        typ = c.get('type')
        col = {
            "name": cn, "type": typ if typ in ('string', 'integer', 'number', 'boolean') else 'string',
            "kind": kind,
            "required": cn in d['items'].get('required', []),
            "pattern": c.get('pattern'), "exists": c.get('exists'),
            "mimetype": c.get('mimetype'), "format": fmt,
            "description": c.get('errorMessage') or c.get('description'),
        }
        if 'default' in c: col['default'] = c['default']
        if isinstance(c.get('enum'), list): col['enum'] = c['enum']
        cols.append(col)
    fmt = 'tsv' if param in ('input','multiregion','pplace_sheet') else 'csv'
    return {
        "param": param, "schema_path": schema_path, "discovered_via": via,
        "format": fmt, "header": True, "columns": cols,
    }
for prm, sp in (('input', 'assets/schema_input.json'),
                ('multiregion', 'assets/schema_multiregion.json'),
                ('pplace_sheet', 'assets/schema_pplace_sheet.json')):
    try:
        sample_sheets.append(sheet_entry(prm, sp, 'nf-schema'))
    except Exception as e:
        warnings.append(f"sample sheet {prm}: {e}")
warnings.append("nf-schema meta annotations present (e.g. input.sample has meta:[sample]); carried via kind=meta.")

# ---------------- profiles ----------------
pi = config.find('profiles')
prof_block = config[brace_end(config, pi) and pi: ]
pb_start = config.find('{', config.find('profiles'))
pb_end = brace_end(config, pb_start)
pb = config[pb_start:pb_end]
profiles = []
i = 1
while i < len(pb) - 1:
    m = re.compile(r'(\w+)\s*\{').search(pb, i)
    if not m: break
    name = m.group(1)
    end = brace_end(pb, m.end() - 1)
    body = strip_comments(pb[m.end():end])
    kinds, signals = [], []
    includes = re.findall(r"includeConfig\s*[\'\"]([^\'\"]+)", body)
    if any('/test' in inc or 'conf/test' in inc for inc in includes) or re.search(r"params\.(input|input_fasta)\s*=\s*[^\s]", body):
        kinds.append('test'); signals.append('include:test-config' if includes else 'sets-input-data')
        if re.search(r'params\.(input|input_fasta)', body): signals.append('sets-input-data')
    if re.search(r'(docker|singularity|podman|charliecloud|shifter|apptainer|conda|mamba|wave)\.enabled|process\.container|process\.conda|process\.arch', body):
        kinds.append('container'); signals.append('container-keys')
    if re.search(r'executor|workDir|clusterOptions|queue', body):
        kinds.append('executor'); signals.append('executor-keys')
    if name in ('debug', 'gitpod'):
        kinds.append('dev'); signals.append('dev-profile-name')
    if not kinds:
        if re.search(r'params\.\w+\s*=', body):
            kinds.append('mode'); signals.append('params-assignment')
        elif re.search(r'max_|cpus|memory|time', body):
            kinds.append('resources'); signals.append('process-directives-only')
        else:
            kinds.append('unknown')
    # gpu profile sets params.use_gpu only -> mode
    profiles.append({"name": name, "kinds": kinds, "source_path": "nextflow.config",
                     "includes": includes, "signals": sorted(set(signals))})
    i = end

# ---------------- processes ----------------
def parse_module_meta(module_path):
    """Return (ModuleMeta dict|None, input name->description, output name->description)."""
    p = os.path.join(os.path.dirname(module_path), 'meta.yml')
    if not os.path.exists(os.path.join(SRC, p)): return None, {}, {}
    t = read(p)
    def block(sec):
        m = re.search(rf'^{sec}:[ \t]*\n(?:(?:[ \t]+\S[^\n]*|[ \t]*|#[^\n]*)(?:\n|$))*', t, re.M)
        return m.group(0) if m else ''
    def scalars(sec):
        return [s.strip().strip('"\'') for s in re.findall(r'^[ \t]+-\s*([^\n]+?)\s*$', block(sec), re.M)]
    def desc_of(chunk):
        m = re.search(r'description:\s*[|>]-?\s*\n((?:[ ]{4,}\S(?:.*\n)?)+)', chunk)
        if m: return ' '.join(l.strip() for l in m.group(1).splitlines())[:400]
        m = re.search(r'description:\s*[\'"]?([^\n\'"]+)', chunk)
        return (m.group(1).strip() if m else '')[:400]
    top_desc = ''
    dm = re.search(r'^description:[ \t]*[|>]-?[ \t]*\n((?:[ ]+\S(?:.*\n)?)+)', t, re.M)
    if dm: top_desc = ' '.join(l.strip() for l in dm.group(1).splitlines())[:600]
    else:
        dm = re.search(r'^description:[ \t]*(\S.*)$', t, re.M)
        top_desc = dm.group(1).strip().strip('"\'')[:600] if dm else ''
    tools = []
    for chunk in re.split(r'\n(?= {2}(?:- )?[\w\-]+:)', block('tools')):
        em = re.match(r' {2}(?:- )?([\w\-\.]+)[ \t]*:', chunk)
        if not em: continue
        e = {"name": em.group(1)}
        d = desc_of(chunk)
        if d: e["description"] = d
        for k in ('homepage', 'documentation', 'tool_dev_url', 'identifier'):
            km = re.search(rf'^\s+{k}:[ \t]*(\S.*)$', chunk, re.M)
            if km: e[k] = km.group(1).strip().strip('"\'')
        doi = re.search(r'^\s+doi:[ \t]*(\S.*)$', chunk, re.M)
        if doi: e['doi'] = doi.group(1).strip().strip('"\'')
        lic = re.search(r'^\s+licence:[ \t]*\[([^\]]*)\]', chunk, re.M)
        if lic: e['licence'] = [x.strip().strip('"\'') for x in lic.group(1).split(',') if x.strip()]
        tools.append(e)
    def io_entries(sec):
        out, descs = [], {}
        lines = block(sec).splitlines()
        idx = [i for i, l in enumerate(lines) if re.match(r'^\s{2,8}- (?:- )?[\w\-\.]+:[ \t]*$', l)]
        for j, i in enumerate(idx):
            chunk = '\n'.join(lines[i: idx[j + 1] if j + 1 < len(idx) else len(lines)])
            em = re.match(r'^\s*-\s+(?:-\s+)?([\w\-\.]+):', chunk)
            if not em: continue
            e = {"name": em.group(1), "description": desc_of(chunk)}
            ty = re.search(r'^\s+type:[ \t]*(\S.*)$', chunk, re.M)
            if ty: e['type'] = ty.group(1).strip()
            pat = re.search(r'^\s+pattern:[ \t]*(\S.*)$', chunk, re.M)
            if pat: e['pattern'] = pat.group(1).strip().strip('"\'')
            out.append(e); descs[e['name']] = e['description']
        return out, descs
    ins, insd = io_entries('input')
    outs, outsd = io_entries('output')
    meta = {"description": top_desc, "keywords": scalars('keywords'),
            "authors": scalars('authors'), "maintainers": scalars('maintainers'),
            "tools": tools, "input": ins, "output": outs}
    return meta, insd, outsd

def parse_nftest(text, path):
    """NfTest-shaped record for a module-scoped nf-test file."""
    m = re.search(r'test\(([\'"])(.*?)\1\)\s*\{', text)
    name = m.group(2) if m else os.path.splitext(os.path.basename(path))[0]
    body = text[m.end():brace_end(text, m.end() - 1)] if m else text
    prof = re.search(r'-profile\s+([\w,]+)', text) or re.search(r'^\s*profile\s+[\'"]([\w,]+)', text, re.M)
    po = {}
    wp = re.search(r'when\s*\{\s*params\s*\{(.*?)\}\s*\}', body, re.S)
    if wp:
        for pm2 in re.finditer(r'([\w\.]+)\s*=\s*(.+)', wp.group(1)):
            po[pm2.group(1)] = pm2.group(2).strip().strip('"\'')
    snap = bool(re.search(r'assert\s+snapshot', text))
    fixture = {"captures": ["stable_names"], "helpers": [], "ignore_files": [],
               "ignore_globs": [], "snap_path": path + '.snap'} if snap else None
    mode = 'stub' if re.search(r'stub', text) else 'real'
    return {"name": name, "path": path,
            "profiles": prof.group(1).split(',') if prof else [],
            "params_overrides": po, "execution_mode": mode,
            "assert_workflow_success": bool(re.search(r'assert\s+workflow\.success', text)),
            "snapshot": fixture, "prose_assertions": []}

proc_files = sorted(glob.glob(os.path.join(SRC, 'modules/local/*/main.nf'))) + \
             sorted(glob.glob(os.path.join(SRC, 'modules/nf-core/**/main.nf'), recursive=True))
procs = {}
def section(text, header, nxt):
    m = re.search(rf'^\s*{header}\s*:', text, re.M)
    if not m: return None
    end = len(text)
    for n in nxt:
        m2 = re.search(rf'^\s*{n}\s*:', text[m.end():], re.M)
        if m2: end = min(end, m.end() + m2.start())
    return text[m.end():end].strip()

def io_items(block):
    out = []
    if not block: return out
    # one declaration per (possibly continued) line: join while nesting is open
    # or the line ends with a comma (NF attributes like `optional: true,` / `emit: x,`)
    items = []
    cur = ''
    depth = 0
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith('//'): continue
        cur = (cur + ' ' + line).strip()
        for ch in line:
            if ch in '([{': depth += 1
            elif ch in ')]}': depth -= 1
        if depth <= 0 and not line.endswith(','):
            items.append(cur); cur = ''; depth = 0
    if cur: items.append(cur)
    for it in items:
        it = it.strip()
        if not it: continue
        nm = re.findall(r'(?:path|val|stdin|stdout|env|tuple|val\(|path\()?\s*[\w"\.\*\{\}\/\.\-]+', it)
        # name: last identifier inside path()/val() or bare token
        calls = re.findall(r'(path|val|env|stdin|stdout)\(([^)]*)\)', it)
        names = []
        for kind, arg in calls:
            arg = arg.strip()
            for a in re.split(r'\s+', arg):
                if a.endswith(':') or ':' in a: continue  # named arg like stageAs: / checkIfExists:
                a = a.strip(',')
                if a and re.match(r'^[\w\.\*\{\}/\.\-]+$', a): names.append(a)
        if not names:
            toks = [t for t in re.split(r'[ ,]+', it) if re.match(r'^\w+$', t) and t not in ('tuple',)]
            names = toks[-1:]
        topic = None
        tm = re.search(r'topic:\s*(\w+)', it)
        if tm: topic = tm.group(1)
        shape = re.sub(r'\s+', ' ', it).strip()
        em = re.search(r'emit:\s*(\w+)', it)
        if em: nm = em.group(1)
        elif names: nm = names[-1]
        else: nm = shape
        desc = None
        cm = re.search(r'documentation:\s*[\'"]([^\'"]+)', it)
        if cm: desc = cm.group(1)
        out.append({"name": nm, "shape": shape,
                    "description": desc, "topic": topic})
    return out

for pf in proc_files:
    rel = os.path.relpath(pf, SRC)
    text = read(rel)
    for m in re.finditer(r'^process\s+([A-Z][A-Z0-9_]+)\s*\{', text, re.M):
        name = m.group(1)
        end = brace_end(text, m.end() - 1)
        body = text[m.end():end]
        cont = re.search(r'^\s*container\s+([\'"])(.*?)\1(?=\s*(?:\n|$))', body, re.M | re.S)
        conda = re.search(r'^\s*conda\s+["\'](.+?)["\']', body, re.M)
        when = re.search(r'^\s*when\s*:\s*$', body, re.M)
        when_txt = None
        if when:
            wend = re.search(r'^\s*(script|shell|exec|output|input|stub)\s*:', body[when.end():], re.M)
            when_txt = body[when.end():when.end() + (wend.start() if wend else 200)].strip()
        pub = re.search(r'^\s*publishDir\s+[^\n]*', body, re.M)
        # stub removal for script excerpt
        sstart = re.search(r'^\s*script\s*:', body, re.M)
        sbody = None
        if sstart:
            send = re.search(r'^\s*stub\s*:', body[sstart.end():], re.M)
            sbody = body[sstart.end(): sstart.end() + (send.start() if send else len(body))]
            sbody = dedent(re.sub(r'^\s*script\s*:', '', sbody.strip()))
        modrel = rel.replace(os.sep, '/')
        meta_m, insd, outsd = parse_module_meta(modrel)
        ins = io_items(section(body, 'input', ['output|script|shell|exec|stub|when|publishDir']))
        outs = io_items(section(body, 'output', ['when|script|shell|exec|stub|publishDir']))
        for io in ins: io['description'] = insd.get(io['name'], '') or ''
        for io in outs: io['description'] = outsd.get(io['name'], '') or ''
        mtests = []
        mdir = os.path.dirname(modrel)
        for tfrel in sorted(glob.glob(os.path.join(SRC, mdir, 'tests', '*.nf.test'))):
            mrel = os.path.relpath(tfrel, SRC).replace(os.sep, '/')
            mtests.append(parse_nftest(read(mrel), mrel))
        procs[name] = {
            "name": name, "aliases": [], "module_path": modrel,
            "meta": meta_m, "module_tests": mtests, "in_subworkflows": [],
            "tool": None, "container": cont.group(2) if cont else None,
            "conda": conda.group(1) if conda else None,
            "inputs": ins,
            "outputs": outs,
            "when": when_txt,
            "script_excerpt": sbody,
            "script_summary": None,
            "publish_dir": (pub.group(0).strip() if pub else None),
        }

# local module envs referenced
def conda_files_used():
    files = set()
    for p in procs.values():
        if p['conda']:
            c = p['conda']
            m = re.search(r'\$\{(moduleDir|projectDir)\}/([\w/\.\-]+\.yml)', c)
            if m:
                rel = m.group(2) if m.group(1) == 'projectDir' else os.path.join(os.path.dirname(p['module_path']), m.group(2))
                files.add(rel.replace(os.sep, '/'))
    return files

# ---------------- includes / aliases + subworkflows ----------------
wf_text = strip_comments(read('workflows/ampliseq.nf'))
main_text = strip_comments(read('main.nf'))
inc_re = re.compile(r'include\s*\{\s*([A-Z][A-Z0-9_]+)(?:\s+as\s+([A-Z][A-Z0-9_]+))?\s*\}\s*from\s*[\'"]([^\'"]+)[\'"]')
includes = []
for f in ('main.nf', 'workflows/ampliseq.nf'):
    for m in inc_re.finditer(strip_comments(read(f))):
        includes.append((m.group(1), m.group(2), f))
sw_files = sorted(glob.glob(os.path.join(SRC, 'subworkflows/local/*/main.nf'))) + \
           sorted(glob.glob(os.path.join(SRC, 'subworkflows/nf-core/*/main.nf')))
subworkflows = []
sw_names = set()
for sf in sw_files:
    rel = os.path.relpath(sf, SRC).replace(os.sep, '/')
    stext_raw = read(rel)
    stext = strip_comments(stext_raw)
    m = re.search(r'^workflow\s+([A-Z][A-Z0-9_]+)\s*\{', stext, re.M)
    if not m: continue
    swname = m.group(1); sw_names.add(swname)
    body_end = brace_end(stext, m.end() - 1)
    body = stext[m.end():body_end]
    calls = sorted(set(re.findall(r'^\s*([A-Z][A-Z0-9_]+)\s*\(', body, re.M)))
    sw_includes = inc_re.findall(stext)
    # calls inside subworkflow: names that are processes or aliased includes
    inc_map = {a or c: c for c, a, _ in sw_includes}
    proc_set = set(procs)
    call_list = sorted({inc_map.get(c, c) for c in calls if inc_map.get(c, c) in proc_set or c in proc_set})
    take = []
    tk = re.search(r'take\s*:(.*?)(?:main|emit)', body, re.S)
    if tk:
        for ln in tk.group(1).splitlines():
            tm = re.match(r'\s*(\w+)', ln)
            if tm and not ln.strip().startswith('//'): take.append(tm.group(1))
    em = re.search(r'emit\s*:(.*?)\Z', body, re.S)
    outs = []
    if em:
        for ln in em.group(1).splitlines():
            om = re.match(r'\s*(\w+)\s*(?:=|=\s*)?(.*)', ln)
            if om and om.group(1): outs.append({"name": om.group(1), "shape": "", "description": "", "topic": None})
    kind = 'pipeline' if call_list else 'utility'
    swpath = rel
    if 'utils_nfcore' in rel and not call_list: kind = 'utility'
    subworkflows.append({"name": swname, "path": swpath, "kind": kind, "aliases": [], "tests": [], "invocations": [],
                         "calls": call_list, "inputs": [{"name": t, "shape": "", "description": "", "topic": None} for t in take],
                         "outputs": outs})
# NFCORE_AMPLISEQ wrapper in main.nf
mw = re.search(r'workflow\s+NFCORE_AMPLISEQ\s*\{', main_text)
if mw:
    subworkflows.append({"name": "NFCORE_AMPLISEQ", "path": "main.nf", "kind": "pipeline",
                         "aliases": [], "calls": ["AMPLISEQ"], "inputs": [], "outputs": [],
                         "tests": [], "invocations": []})
# aliases from root includes
for canon, alias, f in includes:
    if alias and canon in procs:
        procs[canon]["aliases"].append(alias)
    if alias and canon in sw_names:
        for sw in subworkflows:
            if sw['name'] == canon: sw['aliases'].append(alias)

# ---------------- tools ----------------
# environment.yml files in this pipeline are conda-lock lockfiles (full transitive
# closure). tools[] must list software the pipeline runs, not its dependency closure:
# root deps = meta.yml `tools:` bioconda declarations + lockfile packages whose name
# appears as an executable/library token in the process script. Lockfiles supply pins.
tools = {}
wave_parts = {}
conflict_noted = set()
META_NOISE = {'description', 'documentation', 'doi', 'licence', 'homepage', 'identifier',
              'source', 'title', 'tool_dev_url', 'author', 'year', 'publication', 'args_id',
              'acm_classification', 'categories', 'notes'}
def add_tool(name, version, fields):
    if not name: return
    t = tools.get(name)
    if t is None:
        tools[name] = {"name": name, "version": version, "biocontainer": None,
                       "bioconda": None, "docker": None, "singularity": None, "wave": None}
    else:
        if version and t['version'] and version != t['version']:
            if name not in conflict_noted:
                conflict_noted.add(name)
                warnings.append(f"tool {name} pinned to multiple versions across module envs ({t['version']} / {version}); kept {t['version']}")
        elif version and not t['version']:
            t['version'] = version
        t.update({k: v for k, v in fields.items() if v})

RUNTIME_ONLY = {'python', 'r-base', 'perl', 'bash', 'coreutils', 'grep', 'sed', 'gawk',
                'findutils', 'tar', 'gzip', 'bzip2', 'xz', 'zstd', 'openssl', 'curl',
                'wget', 'make', 'git'}

_env_cache = {}
def env_lock(rel):
    if rel in _env_cache: return _env_cache[rel]
    try:
        env = read(rel)
    except FileNotFoundError:
        warnings.append(f"conda env file missing: {rel}")
        _env_cache[rel] = {}
        return {}
    pkgs = {}
    for m in re.finditer(r'^\s*-\s*(?:[\w\-]+::)?([\w\.\-]+)[=:]{1,2}(\S+?)\s*$', env, re.M):
        pkgs.setdefault(m.group(1), m.group(2).split('=')[0])
    _env_cache[rel] = pkgs
    return pkgs

def env_rel_for(p):
    if not p['conda']: return None
    m = re.search(r'\$\{(moduleDir|projectDir)\}/([\w/\.\-]+\.yml)', p['conda'])
    if not m: return None
    return m.group(2) if m.group(1) == 'projectDir' else os.path.normpath(os.path.join(os.path.dirname(p['module_path']), m.group(2))).replace(os.sep, '/')

def meta_tools_bioconda(module_path):
    p = os.path.join(os.path.dirname(module_path), 'meta.yml')
    if not os.path.exists(os.path.join(SRC, p)): return []
    t = read(p)
    m = re.search(r'^tools:\s*$(.*?)^(?:input:|output:|containers?:)', t, re.M | re.S)
    if not m: return []
    out = []
    for chunk in re.split(r'\n(?= {2}(?:- )?[\w\-]+:)', m.group(1)):
        em = re.match(r'\s*(?:-\s*)?([\w\-]+)\s*:', chunk)
        bm = re.search(r'^\s+bioconda:\s*([^\s#]+)\s*$', chunk, re.M)
        name = None
        if bm and bm.group(1) not in ('null', '~', '""'): name = bm.group(1)
        elif em: name = em.group(1)
        if name and name.lower() not in META_NOISE: out.append(name)
    return out

def norm_variants(pkg):
    pn = pkg.lower()
    return {pn, pn.replace('bioconductor-', ''), pn.replace('-', ''), pn.replace('-', '_'), 'bioconductor-' + pn}

proc_roots = {}
for p in procs.values():
    c = p['container'] or ''
    for url in re.findall(r'[\'"](https?://[^\s\'"]+|quay\.io/[^\s\'"]+|biocontainers/[^\s\'"]+|community[^\s\'"]+)[\'"]', c):
        if url.startswith('https://depot.galaxyproject.org/singularity/'):
            nv = url.rsplit('/', 1)[1]; n, _, v = nv.partition(':')
            add_tool(n, v.split('--')[0], {"singularity": url})
        elif url.startswith('quay.io/biocontainers/'):
            nv = url.rsplit('/', 1)[1]; n, _, v = nv.partition(':')
            add_tool(n, v.split('--')[0], {"biocontainer": url})
        elif url.startswith('biocontainers/'):
            nv = url.rsplit('/', 1)[1]; n, _, v = nv.partition(':')
            add_tool(n, v.split('--')[0], {"biocontainer": url})
        elif 'community.wave.seqera.io/library/' in url:
            lib = url.split('/library/', 1)[1].split(':')[0]
            for part in lib.split('_'):
                if part: wave_parts.setdefault(part, url)
        elif 'community.wave' in url or 'community-cr-prod' in url:
            continue  # Wave blob mirror: content-addressed copy, no package evidence
        else:
            add_tool('unknown', 'unknown', {"docker": url})
            warnings.append(f"unclassified container for {p['name']}: {url}")
    rel = env_rel_for(p)
    env = env_lock(rel) if rel else {}
    inline_pkgs = []
    if p['conda'] and 'bioconda::' in p['conda'] and not rel:
        for dep in re.findall(r'bioconda::([\w\.\-]+)(?:=|==)([\w\.\+]+)', p['conda']):
            add_tool(dep[0], dep[1], {"bioconda": f"bioconda::{dep[0]}={dep[1]}"})
            inline_pkgs.append(dep[0])
    script = p['script_excerpt'] or ''
    toks = {tk.lower() for tk in re.findall(r'[A-Za-z0-9][\w\-\.]*', script)}
    roots = list(meta_tools_bioconda(p['module_path'])) + inline_pkgs
    if p['conda'] and not rel and not inline_pkgs:
        m2 = re.fullmatch(r'(?:[\w\-]+::)?([\w\.\-]+)(?:={1,2}([\w\.\+]+))?', p['conda'])
        if m2:
            add_tool(m2.group(1), m2.group(2), {"bioconda": f"bioconda::{m2.group(1)}" + (f"={m2.group(2)}" if m2.group(2) else "")})
            roots.append(m2.group(1))
        else:
            warnings.append(f"unparsed conda directive on {p['name']}: {p['conda']}")
    for pkg in env:
        if pkg in RUNTIME_ONLY or pkg.startswith('_') or pkg in roots: continue
        if norm_variants(pkg) & toks:
            roots.append(pkg)
    if 'qiime' in toks:
        roots += [pkg for pkg in env if pkg.startswith('q2-') or pkg == 'qiime2']
    roots = [r for r in roots if r.lower() not in META_NOISE]
    mapped = []
    for r in roots:
        if r in env or not env: mapped.append(r); continue
        hit = [pkg for pkg in env if r.lower() in norm_variants(pkg)]
        mapped.append(hit[0] if len(hit) == 1 else r)
    roots = mapped
    if 'r' in roots and any(pkg.startswith(('r-', 'bioconductor-')) for pkg in env):
        roots.remove('r')
    roots = sorted(set(roots))
    proc_roots[p['name']] = roots
    for pkg in roots:
        ver = env.get(pkg)
        fields = {"bioconda": f"bioconda::{pkg}={ver}"} if ver else {"bioconda": f"bioconda::{pkg}"}
        add_tool(pkg, ver, fields)
for t in tools.values():
    if t['name'] in wave_parts and not t['wave']:
        t['wave'] = wave_parts[t['name']]
unmatched_wave = sorted(set(wave_parts) - set(tools))
if wave_parts:
    nwave = sum(1 for p in procs.values() if 'community.wave' in (p['container'] or ''))
    warnings.append(f"Wave containers in {nwave} processes: library names carry package sets without versions (pins taken from the conda env files); wave package names with no tools[] entry are transitive deps: {', '.join(unmatched_wave[:15])}")
all_env = {}
for p in procs.values():
    rlx = env_rel_for(p)
    if rlx:
        for k2, v2 in env_lock(rlx).items(): all_env.setdefault(k2, v2)
still_open = [t['name'] for t in tools.values() if not t['version']]
for t in tools.values():
    if not t['version']: t['version'] = all_env.get(t['name'], '')
never_pinned = [n for n in still_open if not tools[n]['version']]
if never_pinned:
    warnings.append(f"tools with no version pin anywhere in the pipeline's conda envs: {', '.join(never_pinned)}")
tools_l = [t for k, t in sorted(tools.items()) if k != 'unknown']
tools_l += [t for k, t in sorted(tools.items()) if k == 'unknown']
# FK: process tool = its single root dependency, or the one matching the module name
for p in procs.values():
    roots = proc_roots.get(p['name'], [])
    low = p['name'].lower().replace('_', '')
    named = [r for r in roots if r.lower().replace('-', '') in low or low in r.lower().replace('-', '').rstrip('0123456789')]
    p['tool'] = roots[0] if len(roots) == 1 else (named[0] if len(named) == 1 else None)

# ---------------- workflow channels / edges / conditionals ----------------
body_m = re.search(r'workflow\s+AMPLISEQ\s*\{', wf_text)
bstart = brace_end(wf_text, body_m.end() - 1)
wbody = wf_text[body_m.end(): bstart - 1]
channels = []
# a name may be assigned several times (channel.empty() placeholder, then real
# materialisation inside if/else arms): keep the most substantive assignment
INFORMATIVE = {'samplesheetToList': 5, 'splitCsv': 5, 'fromFilePairs': 4, 'fromPath': 4,
               'file': 4, 'files': 4, 'fromList': 3, 'of': 2, 'other': 1, 'topic': 1,
               'value': 0, 'empty': 0}
def parse_channel_src(src):
    construct = None; from_param = None; req_runtime = False
    if 'samplesheetToList(' in src: construct = 'samplesheetToList'
    elif re.search(r'\.splitCsv\(\s*header\s*:\s*true', src): construct = 'splitCsv'
    else:
        fm = re.search(r'channel\.(fromPath|fromFilePairs|fromList|fromText|of|value|empty|topic)\s*\(', src, re.I)
        if fm:
            construct = fm.group(1)[0].lower() + fm.group(1)[1:]
            if construct == 'fromText': construct = 'other'
        elif re.match(r'file\s*\(', src): construct = 'file'
        elif re.match(r'files\s*\(', src): construct = 'files'
    if construct is None: return None
    pm = re.search(r'params\.(\w+)', src)
    if pm and pm.group(1) in by_name and construct not in ('empty', 'of', 'value', 'topic', 'other'):
        from_param = pm.group(1)
    if re.search(r'\.ifEmpty\s*\{\s*error', src):
        req_runtime = True
    shape = 'tuple(meta, [path])' if construct == 'samplesheetToList' else ''
    return {"source": src[:400], "shape": shape, "construct": construct,
            "from_param": from_param, "required_runtime": req_runtime}

assign_order = []
best = {}
for m in re.finditer(r'(ch_\w+)\s*=\s*(channel\.[\w\.]+\s*\([^;]*?\)|[^\n;]+)', wbody):
    nm, src = m.group(1), m.group(2).strip()
    parsed = parse_channel_src(src)
    if parsed is None: continue
    score = INFORMATIVE.get(parsed['construct'], 1)
    if nm not in best:
        assign_order.append(nm); best[nm] = (score, parsed)
    elif score > best[nm][0]:
        best[nm] = (score, parsed)
for nm in assign_order:
    channels.append({"name": nm, **best[nm][1]})
# also channels assigned from process outs or operators (for edges), plus edges
edges = []
seen_edges = set()
def edge(f, t, via=None):
    k = (f, t)
    if k in seen_edges or f == t: return
    seen_edges.add(k)
    edges.append({"from": f, "to": t, "via": via or []})
allnames = set(procs) | sw_names
alias_to_canon = {}
for canon, alias, f in includes:
    if alias: alias_to_canon[alias] = canon
for sw in subworkflows:
    for a in sw['aliases']: alias_to_canon[a] = sw['name']
# process/subworkflow invocations with a leading ch_ argument
for m in re.finditer(r'\b([A-Z][A-Z0-9_]{2,})\s*\(', wbody):
    nm = alias_to_canon.get(m.group(1), m.group(1))
    if nm not in allnames: continue
    args_start = m.end()
    seg = wbody[args_start:args_start + 300]
    # first argument identifier
    am = re.search(r'[\'"]?(\w+)[\'"]?(?:\.out[\w\.]*)?\s*[,\)]', seg)
    if am and am.group(1).startswith('ch_'):
        edge(am.group(1), nm)
    am2 = re.search(r'(\w+)\.out', seg)
    if am2:
        edge(am2.group(1) if am2.group(1) in allnames else am2.group(1), nm)
# assignments ch_x = PROC.out... or ch_x = ch_y.op
for m in re.finditer(r'(ch_\w+)\s*=\s*(\w+)(\.out)?', wbody):
    nm, src = m.group(1), m.group(2)
    src_canon = alias_to_canon.get(src, src)
    if src_canon in allnames and m.group(3):
        edge(src_canon, nm)
    elif src.startswith('ch_'):
        pass
# conditionals
conditionals = []
lines = wbody.splitlines()
depth_at = []
d = 0
for i, ln in enumerate(lines):
    d += ln.count('{') - ln.count('}')
    depth_at.append(d)
for m in re.finditer(r'^(\s*)if\s*\(\s*(!?\s*params\.[\w\.\s!=<>&\|\'\w:\+\-]+?)\s*\)', wbody, re.M):
    indent = len(m.group(1))
    guard = m.group(2).strip()
    start_line = wbody[:m.start()].count('\n')
    dd = depth_at[start_line]
    end_line = start_line
    for j in range(start_line + 1, len(lines)):
        if depth_at[j] <= dd:
            end_line = j; break
    block = '\n'.join(lines[start_line:end_line + 1])
    aff = sorted({alias_to_canon.get(x, x) for x in re.findall(r'\b([A-Z][A-Z0-9_]{2,})\s*\(', block)
                  if alias_to_canon.get(x, x) in allnames})
    if aff:
        conditionals.append({"guard": guard, "branch": "default", "affects": aff})

# ---------------- test candidates ----------------
def parse_profile_conf(name):
    path = f'conf/{name}.config'
    delta = {}
    includes = []
    if os.path.exists(os.path.join(SRC, path)):
        t = strip_comments(read(path))
        includes = re.findall(r"includeConfig\s*[\'\"]([^\'\"]+)[\'\"]", t)
        for m in re.finditer(r'params\.([\w\.]+)\s*=\s*(.+)', t):
            delta[m.group(1)] = m.group(2).strip().strip('"\'')
        # assignments inside a `params { ... }` block carry no params. prefix
        for pm in re.finditer(r'params\s*\{', t):
            pb = t[pm.end(): brace_end(t, pm.end() - 1)]
            for am in re.finditer(r'^\s*([\w\.]+)\s*=\s*(.+)$', pb, re.M):
                delta.setdefault(am.group(1), am.group(2).strip().strip('"\''))
            for im in re.finditer(r'includeConfig\s*[\'"]([^\'"]+)[\'"]', pb):
                if im.group(1) not in includes: includes.append(im.group(1))
    return delta, includes, path

test_candidates = []
for tf in sorted(glob.glob(os.path.join(SRC, 'tests/*.nf.test'))):
    rel = os.path.relpath(tf, SRC).replace(os.sep, '/')
    t = read(tf)
    suite_profile = re.search(r'^\s*profile\s+[\'"]([^\'"]+)[\'"]', t, re.M)
    for m in re.finditer(r'test\(([\'"])(.*?)\1\)\s*\{', t):
        tname = m.group(2)
        end = brace_end(t, m.end() - 1)
        body = t[m.end():end]
        cmd = re.search(r'cmd\s+[\'"]([^\'"]+)[\'"]', body)
        eff = []
        if suite_profile: eff += [p for p in suite_profile.group(1).split(',')]
        if cmd:
            cm = re.search(r'-profile\s+([\w,]+)', cmd.group(1))
            if cm: eff = [p for p in cm.group(1).split(',')]
        eff = list(dict.fromkeys(eff))
        wp = re.search(r'when\s*\{\s*params\s*\{(.*?)\}\s*\}', body, re.S)
        delta = {}
        for p in eff:
            d2, incs, _ = parse_profile_conf(p if p.startswith('test') else 'test')
            delta.update(d2)
        if wp:
            for pm2 in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', wp.group(1)):
                delta[pm2.group(1)] = pm2.group(2)
        inputs = []
        tdp = by_name.get('pipelines_testdata_base_path')
        tdp_base = (tdp or {}).get('default') or 'https://raw.githubusercontent.com/nf-core/test-datasets/ampliseq/'
        tdp_base = str(tdp_base).strip('"\'')
        for key in ('input', 'input_fasta', 'metadata', 'multiregion', 'pplace_sheet'):
            if key in delta:
                v = delta[key]
                role = "sample-sheet" if 'input' in key else key
                filetype = 'tsv' if v.endswith(('.tsv', '.csv')) else 'auto'
                if 'pipelines_testdata_base_path' in v:
                    suffix = re.search(r'[\'"]([^\'"]+)', v)
                    suffix = suffix.group(1) if suffix else v
                    ft2 = 'tsv' if suffix.endswith(('.tsv', '.csv')) else 'auto'
                    inputs.append({"path": None, "url": tdp_base + suffix, "role": role,
                                   "filetype": ft2, "sha1": None,
                                   "description": "remote nf-core test-data (pipelines_testdata_base_path + suffix)"})
                    continue
                pth = v
                if v.startswith('$projectDir/'): pth = v[len('$projectDir/'):]
                elif v.startswith('../'): pth = os.path.dirname(rel) + '/' + v
                inputs.append({"path": pth.replace('/../', '/'), "url": None, "role": role, "filetype": filetype, "sha1": None})
        snap_m = re.search(r'assert\s+snapshot\((.*?)\)\.match\(\)', body, re.S)
        snapshot = None
        caps = []
        helpers = []
        iglobs = []
        if snap_m:
            args = snap_m.group(1)
            if 'removeNextflowVersion' in args: caps.append('versions_yml'); helpers.append('removeNextflowVersion')
            if 'getAllFilesFromDir' in args or 'stable_path' in args: caps.append('stable_paths'); helpers.append('getAllFilesFromDir')
            for ig in re.findall(r"ignore:\s*\[([^\]]*)\]", args):
                iglobs += [g.strip().strip("'") for g in ig.split(',') if g.strip()]
            caps.append('stable_names')
        prose = []
        if re.search(r'assert\s+path\("[^"]+"\)\.(csv|readLines|text)', body): prose.append('content assertions on specific output files')
        succ = bool(re.search(r'assert\s+workflow\.success', body))
        snap_path = rel + '.snap'
        exec_mode = 'real'
        ref_scale = 'full' in tname.lower() or 'test_full' in eff
        scope = 'reference-scale' if ref_scale else 'primary'
        disp = 'deferred' if ref_scale else 'eligible'
        toutputs = []
        for op in sorted(set(re.findall(r'path\("\$outputDir/([^"]+)"\)', body))):
            toutputs.append({"role": "expected-output-file", "path": op, "url": None,
                             "kind": None, "description": None, "assertions": []})
        cand = {
            "id": f"{rel}::{tname}", "kind": "nf-test", "name": tname, "path": rel,
            "effective_profiles": eff, "params_delta": delta, "inputs": inputs,
            "outputs": toutputs, "execution_mode": exec_mode, "scope": scope,
            "disposition": disp, "rationale": f"whole-pipeline nf-test case from {rel}",
            "assert_workflow_success": succ,
            "snapshot": {"captures": caps, "helpers": helpers, "ignore_files": [],
                         "ignore_globs": iglobs, "snap_path": snap_path} if snap_m else None,
            "prose_assertions": prose,
        }
        test_candidates.append(cand)

default_cands = [c for c in test_candidates if c['path'] == 'tests/default.nf.test' and c['disposition'] == 'eligible']
if default_cands:
    sel = default_cands[0]
    sel['disposition'] = 'selected'
    test_selection = {"status": "selected", "selected_candidate_id": sel['id'],
                      "rationale": "tests/default.nf.test '-profile test' is the primary default-scenario whole-pipeline case; other tests are scenario variants."}
else:
    test_selection = {"status": "needs-scope-choice", "selected_candidate_id": None,
                      "rationale": "no default.nf.test candidate"}

# script_summary: terse deterministic line from the excerpt's first real command
NF_STOP = {'if', 'else', 'for', 'while', 'do', 'then', 'fi', 'esac', 'case', 'def',
           'val', 'tuple', 'path', 'emit', 'return', 'true', 'false', 'String', 'int',
           'boolean', 'new', 'try', 'catch', 'println', 'script:', 'when:', '"""'}
def summarize(p):
    ex = p.get('script_excerpt') or ''
    fallback = None
    for ln in ex.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(('#', '//', '"""', '$', 'def ', 'cat <<EOF')): continue
        toks = ln.replace('"', ' ').replace("'", ' ').split()
        if not toks: continue
        t0 = toks[0].replace('$', '')
        if re.match(r'^[\w\.]+\s*(?:=|<-)', ln) or (len(toks) > 1 and toks[1] in ('=', '<-')):
            continue  # Groovy/R assignment, not a command
        if t0.lower() in NF_STOP or not re.match(r'^[a-zA-Z][\w\.\-]*$', t0) or '(' in t0:
            continue
        rest = [t for t in toks[1:3] if re.match(r'^[a-zA-Z][\w\.\-]*$', t)][:1]
        line = f"invokes {t0}" + (f" ({rest[0]})" if rest else "")
        if p.get('tool') and p['tool'].replace('-', '').startswith(t0.lower().replace('-', '')):
            return line
        fallback = fallback or line
    return fallback
# LLM pass over the verbatim script_excerpt fields: reviewed one-liners for the
# local R/QIIME/duckdb modules where no leading shell command identifies the job.
LLM_SUMMARIES = {
 "BUILD_ASV_ANNOTATIONS": "inline R script: joins barrnap, decontam and per-database taxonomy results into a per-ASV annotation table",
 "CONSOLIDATE_TAXONOMY": "inline R script: merges per-database taxonomy tables into one consensus/LCA taxonomy at the chosen rank levels",
 "DADA2_ADDSPECIES": "inline R (dada2 addSpecies): appends species-level assignments from reference matches to the taxonomy table",
 "DADA2_DENOISING": "inline R (dada2 denoiseSingle/DenoisePaired): infers ASVs and builds the sequence table",
 "DADA2_ERR": "inline R (dada2 learnErrors): learns error models and writes per-sample quality stats",
 "DADA2_FILTNTRIM": "inline R (dada2 filterAndTrim): quality-filters/trims reads to filtered FASTQ plus stats",
 "DADA2_MERGE": "inline R (dada2 mergePairs): merges paired ASVs into an ungapped alignment plus stats",
 "DADA2_QUALITY": "inline R (dada2/ShortRead plotQualityProfile): per-position quality profile plots",
 "DADA2_RMCHIMERA": "inline R (dada2 removeBimeraDenovo): removes chimeric ASVs from the sequence table",
 "DADA2_SPLITREGIONS": "inline R (dada2 cutPrimers): cuts primer-defined amplicon regions out of sequences per region mapping",
 "DADA2_STATS": "inline R script: concatenates filter/merge/denoising stats tables into a per-sample summary",
 "DADA2_TAXONOMY": "inline R (dada2 assignTaxonomy): classifies ASVs against the reference databases, per-database taxonomy tables",
 "DECONTAM": "inline R (decontam isContaminant): flags sequence contaminants and emits the not-contaminant list",
 "DUCKDB_TABLE2PARQUET": "inline duckdb: reads a TSV table via read_csv and COPYs it to Parquet",
 "FILTER_LEN": "inline R (Biostrings): drops ASVs outside the min/max length bounds",
 "FILTER_SAMPLES": "inline R script: filters samples out of the ASV table driven by the metadata sheet",
 "FILTER_SEQUENCES_ABUNDANCES": "inline R (Biostrings): drops ASVs below the min/max abundance thresholds",
 "FILTER_SSU": "inline R (Biostrings): keeps only barrnap-annotated SSU (rRNA kingdom) ASVs",
 "FORMAT_PPLACETAX": "inline R script: converts pplacer EPA likelihood-weight ratios into a per-ASV taxonomy table",
 "FORMAT_TAXONOMY_SINTAX": "shell: normalises the reference taxonomy to gzip'd sintaxdb.fa.gz (gzip magic sniffed, custom DBs copied)",
 "FORMAT_TAXONOMY_VSEARCH_LCA": "shell: normalises the reference taxonomy to gzip'd sintaxdb.fa.gz for vsearch lca",
 "FORMAT_TAXRESULTS_KRAKEN2": "inline R script: parses the Kraken2 kreport into a per-ASV taxonomy table",
 "HMMER_FORMATTSV": "shell/awk: reshapes HMMER tblout/domtblout output into per-query TSV tables",
 "HMMER_HMMRANK": "duckdb SQL: ranks HMMER hits per query into a best-hit TSV",
 "MERGE_STATS": "inline R script: joins two DADA2 per-sample stats tables by sample id",
 "PHYLOSEQ": "inline R (phyloseq): builds and exports a phyloseq object from ASV and taxonomy tables",
 "SIDLE_ALIGN": "QIIME2 CLI: qiime sidle align (regional alignment of reference sequences)",
 "SIDLE_DBEXTRACT": "QIIME2 CLI: qiime sidle db-extract (extract full-length database to the amplicon region)",
 "SIDLE_DBFILT": "QIIME2 CLI: qiime sidle db-filter (permissive pre-filtering of the reference database)",
 "SIDLE_DBRECON": "QIIME2 CLI: qiime sidle db-reconstruct (region args assembled in Groovy from the per-region maps)",
 "SIDLE_FILTTAX": "inline R script: removes a filtered ID set from a reference taxonomy table",
 "SIDLE_IN": "QIIME2 CLI: qiime tools import of sample sequences/tables into qza for q2-sidle",
 "SIDLE_INDB": "QIIME2 CLI: qiime tools import of database sequences into qza",
 "SIDLE_INDBALIGNED": "QIIME2 CLI: qiime tools import of aligned database sequences into qza",
 "SIDLE_SEQRECON": "QIIME2 CLI: qiime sidle seq-reconstruct (full-length ASV sequence reconstruction)",
 "SIDLE_TABLERECON": "QIIME2 CLI: qiime sidle table-reconstruct (per-region tables merged back to full length)",
 "SIDLE_TAXRECON": "QIIME2 CLI: qiime sidle tax-reconstruct (taxonomy reconstruction across regions)",
 "SIDLE_TREERECON": "QIIME2 CLI: qiime sidle tree-reconstruct (phylogenetic tree reconstruction, needs SEPP)",
 "SIDLE_TRIM": "QIIME2 CLI: qiime sidle seq-trim (trims sequences to the region length)",
 "SUMMARY_REPORT": "inline R script: assembles the per-database summaries into the report abstract inputs",
 "SUMMARY_TABLE_COUNTS": "inline R script: pivots the ASV table into long-format per-sample counts",
 "SUMMARY_TABLE_TAXONOMY": "inline R script: emits the per-database/per-classifier taxonomy summary TSV",
 "TREESUMMARIZEDEXPERIMENT": "inline R (TreeSummarizedExperiment): builds a tree+ASV-table SE from the ASV table and taxonomy",
}
for p in procs.values():
    p['script_summary'] = LLM_SUMMARIES.get(p['name']) or summarize(p) or 'script body without a recognisable leading command (ext-args driven)'

# in_subworkflows: denormalized FK from subworkflow calls
canon_alias = {}
for p in procs.values():
    canon_alias[p['name']] = p['name']
    for a in p['aliases']: canon_alias[a] = p['name']
for sw in subworkflows:
    for c in sw['calls']:
        pn = canon_alias.get(c)
        if pn and sw['name'] not in procs[pn]['in_subworkflows']:
            procs[pn]['in_subworkflows'].append(sw['name'])

# ---------------- reference assets / rebuild rules ----------------
# outdir is an output location and input_fasta is a reads-as-input dataset:
# both are interface params, not reference data
sheet_params = {s['param'] for s in sample_sheets} | {'outdir', 'input_fasta'}
def asset_kind(n):
    if n.endswith('_fai') or '_fai' in n: return 'fasta_index'
    if 'primer' in n: return 'primer_fasta'
    if 'tree' in n: return 'newick_tree'
    if 'taxonomy' in n or 'barrnap' in n or ('ref' in n and 'db' in n) or 'silva' in n or 'greengenes' in n or 'itsone' in n or 'rdp' in n: return 'database'
    if 'fasta' in n or n.endswith(('.fa', '.fasta')): return 'fasta'
    if 'metadata' in n or 'sheet' in n: return 'reference_sheet'
    return 'reference_file'
chan_by_param = {}
for c in channels:
    if c['from_param']: chan_by_param.setdefault(c['from_param'], []).append(c['name'])
def consumers(param, max_hops=3):
    frontier = set(chan_by_param.get(param, []))
    found = set()
    for _ in range(max_hops):
        nxt = set()
        for e in edges:
            if e['from'] in frontier:
                tgt = e['to']
                if tgt in procs or tgt in sw_names: found.add(tgt)
                else: nxt.add(tgt)
        frontier = nxt - found
        if not frontier: break
    return sorted(found)
reference_assets = []
for prm in params:
    n = prm['name']
    if n in sheet_params or prm.get('format') not in ('file-path', 'directory-path', 'path'):
        continue
    reference_assets.append({
        "param": n, "asset_kind": asset_kind(n),
        "format_hint": prm.get('format'), "required": False,
        "source_kind": "nextflow_schema",
        "source_expression": f"params.{n}",
        "schema_group": prm.get('schema_group'),
        "used_by": consumers(n),
        "evidence": {"source_path": "nextflow_schema.json", "confidence": "high",
                     "evidence": [f"declared with format: {prm.get('format')} in schema group {prm.get('schema_group')}"]},
    })
reference_rebuilds = []
tags = sorted(set(re.findall(r'DOWNLOAD_REFERENCE_(\w+)\s*\(', wbody)))
for tag in tags:
    call = re.search(rf'(.*\n)?[^\n]*DOWNLOAD_REFERENCE_{tag}\s*\(', wbody)
    cand_param = tag.lower() + '_ref_taxonomy'
    if tag.endswith('_TREE'):
        cand_param = tag[:-5].lower() + '_ref_taxonomy'
    if cand_param not in by_name:
        alts = [q['name'] for q in params if q['name'].endswith('_ref_taxonomy') and tag.lower().replace('_', '').replace('_tree', '') in q['name'].replace('_', '')]
        cand_param = alts[0] if alts else cand_param
    reference_rebuilds.append({
        "asset_param": cand_param,
        "guard": f"{cand_param} set && params.ref_taxonomy_storage",
        "guard_params": [cand_param, 'ref_taxonomy_storage'],
        "builder": f"DOWNLOAD_REFERENCE_{tag}",
        "builder_outputs": ["db"],
        "fallback_for": None,
        "evidence": {"source_path": "workflows/ampliseq.nf", "confidence": "medium",
                     "evidence": [re.search(rf'[^\n]*DOWNLOAD_REFERENCE_{tag}\s*\([^\n]*', wbody).group(0).strip()[:200]]},
    })
warnings.append("reference_rebuilds: the *_ref_taxonomy params are database *selectors* (names keyed into params.*_ref_databases maps from conf/ref_databases.config), not file paths; when params.ref_taxonomy_storage is set the DOWNLOAD_REFERENCE_* modules materialize them into the work directory.")
warnings.append("channel registry records single-line materialisations (most substantive assignment per name); channels derived from operator chains or multi-line ternaries (e.g. ch_reads = ch_reads_result.passed) appear in workflow.edges[] but not in channels[].")
warnings.append("edges[] are first-argument heuristics from invocation sites in workflows/ampliseq.nf; downstream data-flow work should reconcile them against the source's operator chains.")

summary = {
    "source": source, "params": params, "sample_sheets": sample_sheets,
    "profiles": profiles, "tools": tools_l, "processes": sorted(procs.values(), key=lambda x: x['name']),
    "subworkflows": subworkflows,
    "workflow": {"name": "AMPLISEQ", "channels": channels, "edges": edges, "conditionals": conditionals},
    "reference_assets": reference_assets, "reference_rebuilds": reference_rebuilds,
    "test_candidates": test_candidates, "test_selection": test_selection,
    "warnings": warnings,
}
with open(OUT, 'w') as f:
    json.dump(summary, f, indent=1)
print("processes:", len(procs), "tools:", len(tools_l), "subworkflows:", len(subworkflows),
      "channels:", len(channels), "edges:", len(edges), "conditionals:", len(conditionals),
      "tests:", len(test_candidates), "params:", len(params))
