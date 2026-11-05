# rr-v5r115 REAL46-031 单案权威判官 + 盲区字段比对
import os, sys, json, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r115diag'
PY = 'D:/Python/python.exe'
PYCDC = REPO + '/pycdc.py'
PYC = 'D:/Python/Lib/site-packages/packaging/__pycache__/version.cpython-311.pyc'

sys.path.insert(0, REPO + '/tools/completeness')
sys.path.insert(0, REPO)
os.chdir(REPO)
import semantic_diff as sd

prod = OUT + '/REAL46-031_v115.py'
with open(prod, 'wb') as fo, open(prod + '.err', 'wb') as fe:
    r = subprocess.run([PY, '-I', '-X', 'utf8', PYCDC, PYC], stdout=fo, stderr=fe, cwd=REPO, timeout=300)
case = {"case_id": "REAL46-031", "original": {"pyc": PYC}, "product": {"source": prod},
        "entrypoint": "module", "args": [], "kwargs": {}, "timeout_s": 180, "_base": os.getcwd()}
res = sd.compare_case(case)
json.dump(res, open(OUT + '/semantic_REAL46-031_v115.json', 'w', encoding='utf-8'),
          ensure_ascii=False, default=str, indent=1)
print('decompile rc =', r.returncode, '| status =', res.get('status'), '| diffs =', len(res.get('diffs', [])))

# 盲区递归字段比对
import marshal, py_compile
py_compile.compile(prod, cfile=OUT + '/prod115.pyc', doraise=True)
with open(PYC, 'rb') as f: f.read(16); orig = marshal.load(f)
with open(OUT + '/prod115.pyc', 'rb') as f: f.read(16); prod_c = marshal.load(f)
def walk(code, path, acc):
    acc.append((path, code))
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            walk(c, path + '/' + c.co_name, acc)
oa, pa = [], []
walk(orig, '', oa); walk(prod_c, '', pa)
def norm(c): return tuple('<code:%s>' % x.co_name if hasattr(x, 'co_name') else x for x in c)
bad = []
for (op, oc), (pp, pc) in zip(oa, pa):
    diffs = []
    if oc.co_code != pc.co_code: diffs.append('co_code(%d vs %d)' % (len(oc.co_code), len(pc.co_code)))
    if oc.co_exceptiontable != pc.co_exceptiontable: diffs.append('exctab')
    if oc.co_names != pc.co_names: diffs.append('names')
    if oc.co_varnames != pc.co_varnames: diffs.append('varnames')
    if oc.co_argcount != pc.co_argcount: diffs.append('argcount')
    if oc.co_flags != pc.co_flags: diffs.append('flags')
    if norm(oc.co_consts) != norm(pc.co_consts): diffs.append('consts')
    if diffs: bad.append((op, diffs))
print('field-level diff code objects: %d' % len(bad))
for b in bad[:10]: print('  ', b)
