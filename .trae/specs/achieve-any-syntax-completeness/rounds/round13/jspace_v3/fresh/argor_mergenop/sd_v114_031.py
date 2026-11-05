# rr-v5r114 REAL46-031 单案权威 semantic_diff（v114 产品）
import os, sys, json, subprocess

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r114diag'
PY = 'D:/Python/python.exe'
PYCDC = REPO + '/pycdc.py'
PYC = 'D:/Python/Lib/site-packages/packaging/__pycache__/version.cpython-311.pyc'

sys.path.insert(0, REPO + '/tools/completeness')
sys.path.insert(0, REPO)
os.chdir(REPO)
import semantic_diff as sd

prod = OUT + '/REAL46-031_v114.py'
with open(prod, 'wb') as fo, open(prod + '.err', 'wb') as fe:
    r = subprocess.run([PY, '-I', '-X', 'utf8', PYCDC, PYC],
                       stdout=fo, stderr=fe, cwd=REPO, timeout=300)
case = {"case_id": "REAL46-031", "original": {"pyc": PYC},
        "product": {"source": prod}, "entrypoint": "module",
        "args": [], "kwargs": {}, "timeout_s": 180, "_base": os.getcwd()}
res = sd.compare_case(case)
json.dump(res, open(OUT + '/semantic_REAL46-031_v114.json', 'w', encoding='utf-8'),
          ensure_ascii=False, default=str, indent=1)
print('decompile rc =', r.returncode)
print('status =', res.get('status'), '| diffs =', len(res.get('diffs', [])))
for d in res.get('diffs', []):
    print('DIFF:', json.dumps(d, ensure_ascii=False)[:220])
print('errors:', res.get('errors'))
