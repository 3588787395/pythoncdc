import sys, os, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main/tools/completeness')
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
os.chdir('F:/Downloads/pythoncdc-main')
import semantic_diff as sd
EV = 'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/orandchain_if'
for cid, pyc, prod in [
    ('REAL46-036-v111', 'D:/Python/Lib/site-packages/pandas/core/__pycache__/indexing.cpython-311.pyc', EV + '/indexing_prod_v111.py'),
    ('REAL46-004-v111', 'D:/Python/Lib/__pycache__/enum.cpython-311.pyc', EV + '/enum_prod_v111.py'),
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
    out = EV + '/semantic_%s.json' % cid
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False, default=str, indent=1)
    print(cid, 'status:', res.get('status'),
          'diffs:', len(res.get('diffs', [])),
          [d.get('path', d.get('dimension')) for d in res.get('diffs', [])][:6])
    print('  errors:', res.get('errors'), 'inconclusive:', res.get('inconclusive'))
    print('  json ->', out)
