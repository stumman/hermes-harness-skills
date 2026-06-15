#!/usr/bin/env python3
"""Deterministic scorer for Copilot Agent Skills against the anatomy standard.
Usage: score.py <SKILL.md path>   (skill folder = dirname; orphan/dangling checks use it)
Prints a JSON line of metrics + an automatable compliance score (0-100, normalized).
"""
import sys, re, os, json, glob

SIX = {"name","description","argument-hint","user-invocable","disable-model-invocation","context"}
VER  = re.compile(r'v[0-9]+\.[0-9]+\.[0-9]+|iter[0-9]+|—\s*NEW|—\s*UPDATED|version history|release notes', re.I)
BENCH= re.compile(r'[0-9]+%|~?[0-9]+x\b|faster|fewer tool|token savings|benchmark|repro rate|production audits|SWE-bench', re.I)
TODO = re.compile(r'\b(TODO|FIXME|XXX|WIP|implement later|for now)\b')
MKT  = re.compile(r'world-class|state-of-the-art|cutting-edge|blazing|elite|seamless|revolutionary|best-in-class|powerful|ultra', re.I)
DESC_MECH = re.compile(r'\.(py|js|ts|sh)\b|--\w+|\[[A-Z_/]+\]|references/|scripts/|→.*→.*→')

def split(path):
    txt=open(path,encoding="utf-8").read()
    m=re.match(r'^---\n(.*?)\n---\n(.*)$', txt, re.S)
    if not m: return {}, txt, txt
    fm_raw, body = m.group(1), m.group(2)
    fm={}
    for line in fm_raw.splitlines():
        mm=re.match(r'^([A-Za-z_-]+):(.*)$', line)
        if mm: fm[mm.group(1)]=mm.group(2).strip()
    # description may be multi-line (>- or folded); grab full value
    dm=re.search(r'description:\s*(.*?)(?:\n[A-Za-z_-]+:|\Z)', fm_raw, re.S)
    desc=(dm.group(1) if dm else fm.get("description","")).strip().strip('"').strip("'")
    desc=re.sub(r'^[>|]-?\s*','',desc); desc=re.sub(r'\s+',' ',desc).strip()
    return fm, desc, body

def score(path):
    folder=os.path.dirname(path)
    name_expected=os.path.basename(folder)
    fm, desc, body = split(path)
    words=len(body.split()); b=len(body.encode()); toks=b//4
    keys=set(fm.keys()); extra=keys-SIX
    # dangling links
    refs=re.findall(r'(?:\./)?((?:references|scripts)/[A-Za-z0-9._/-]+)', body)
    dangling=[r for r in set(refs) if not os.path.isfile(os.path.join(folder,r))]
    # orphans
    folder_files=[p for p in glob.glob(os.path.join(folder,"**","*"),recursive=True)
                  if os.path.isfile(p) and os.path.basename(p) not in ("SKILL.md",".DS_Store")]
    orphans=[p for p in folder_files if os.path.basename(p) not in body]
    name=fm.get("name","")
    full=open(path,encoding="utf-8").read()

    pts=0; mx=0
    def add(cond,p):
        nonlocal pts,mx; mx+=p; pts+= p if cond else 0
    add(name==name_expected and bool(re.match(r'^[a-z0-9-]{1,64}$',name)), 14)  # identity+regex
    add(len(extra)==0, 8)
    add(not('---' in body[:3]), 0)  # noop placeholder removed
    add("user-invocable: true" not in full and "disable-model-invocation: false" not in full and "context: inline" not in full, 4)
    add(bool(re.search(r'\buse\b',desc,re.I)) and bool(desc.split('.')[0].strip()), 10)
    dl=len(desc); add(dl<=1024 and 120<=dl<=300, 6) if 120<=dl<=300 else add(dl<=1024,3)
    add(not VER.search(desc) and not DESC_MECH.search(desc), 7)
    add(not MKT.search(desc), 4)
    add(words<=500, 8) if words<=500 else (add(words<=1000,5) if words<=1000 else add(toks<=3000,2))
    add(len(dangling)==0, 5)
    add(len(orphans)==0, 5)
    add(not VER.search(full), 3)
    add(not BENCH.search(body), 2)
    add(not TODO.search(body), 2)
    add(not MKT.search(body), 2)
    norm=round(100*pts/mx,1)
    return {"skill":name_expected,"name":name,"desc_chars":dl,"body_words":words,"body_bytes":b,
            "body_est_tokens":toks,"extra_fm_keys":sorted(extra),"dangling":dangling,"orphans":[os.path.relpath(o,folder) for o in orphans],
            "ver_hits":len(VER.findall(full)),"bench_hits":len(BENCH.findall(body)),"mkt_hits":len(MKT.findall(full)),
            "score":norm}

if __name__=="__main__":
    print(json.dumps(score(sys.argv[1])))
