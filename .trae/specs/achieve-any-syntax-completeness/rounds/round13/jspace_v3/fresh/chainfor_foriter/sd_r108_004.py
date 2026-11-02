import sys, os, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main/tools/completeness')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
import semantic_diff as sd
case = {
    "case_id": "REAL46-004-v108",
    "original": {"pyc": "D:/Python/Lib/__pycache__/enum.cpython-311.pyc"},
    "product": {"source": "D:/temp/opencode/cl_layout/r98/enum_prod_v108.py"},
    "entrypoint": "module",
    "args": [], "kwargs": {},
    "timeout_s": 120,
    "_base": os.getcwd(),
}
res = sd.compare_case(case)
print('status:', res.get('status'))
print('diffs:', len(res.get('diffs', [])))
ev = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/chainfor_foriter'
json.dump(res, open(ev + '/semantic_REAL46-004_v108.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str, indent=1)
