import sys, os, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main/tools/completeness')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
import semantic_diff as sd
ev = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/chainfor_foriter'
for cid, pyc, prod in [
    ('REAL46-004-v110', 'D:/Python/Lib/__pycache__/enum.cpython-311.pyc', 'D:/temp/opencode/cl_layout/r98/enum_prod_v110.py'),
    ('REAL46-001-v110', 'D:/Python/Lib/__pycache__/dataclasses.cpython-311.pyc', 'D:/temp/opencode/cl_layout/r98/dc_prod_v110.py'),
]:
    case = {
        "case_id": cid,
        "original": {"pyc": pyc},
        "product": {"source": prod},
        "entrypoint": "module",
        "args": [], "kwargs": {},
        "timeout_s": 180,
        "_base": os.getcwd(),
    }
    res = sd.compare_case(case)
    tag = cid.split('-')[1]
    json.dump(res, open(ev + '/semantic_%s_v110.json' % tag, 'w', encoding='utf-8'), ensure_ascii=False, default=str, indent=1)
    print(cid, 'status:', res.get('status'), 'diffs:', len(res.get('diffs', [])), [d.get('path', d.get('dimension')) for d in res.get('diffs', [])][:6])
