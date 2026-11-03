import sys, os, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main/tools/completeness')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
import semantic_diff as sd
case = {
    "case_id": "REAL46-001-probe",
    "original": {"pyc": "D:/Python/Lib/__pycache__/dataclasses.cpython-311.pyc"},
    "product": {"source": "D:/temp/opencode/cl_layout/r98/dc_prod_v108.py"},
    "entrypoint": "module",
    "args": [], "kwargs": {},
    "timeout_s": 180,
    "_base": os.getcwd(),
}
res = sd.compare_case(case)
print('status:', res.get('status'))
for d in res.get('diffs', []):
    print('DIM', d.get('dimension'), '|', d.get('path'), '|', d.get('kind'))
    print('   orig:', str(d.get('original'))[:100])
    print('   prod:', str(d.get('product'))[:100])
