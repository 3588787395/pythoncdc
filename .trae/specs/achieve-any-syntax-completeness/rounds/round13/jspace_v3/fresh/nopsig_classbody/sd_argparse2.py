import sys, os, json
sys.path.insert(0, os.getcwd())
import semantic_diff as sd
case = {
    "case_id": "REAL46-018-probe",
    "original": {"pyc": "D:/Python/Lib/__pycache__/argparse.cpython-311.pyc"},
    "product": {"source": "D:/temp/opencode/cl_layout/r98/argparse_prod_v107.py"},
    "entrypoint": "module",
    "args": [], "kwargs": {},
    "timeout_s": 120,
    "_base": os.getcwd(),
}
res = sd.compare_case(case)
print('status:', res.get('status'))
for d in res.get('diffs', []):
    print('DIM', d.get('dimension'))
    print(json.dumps(d, ensure_ascii=False, default=str)[:1200])
