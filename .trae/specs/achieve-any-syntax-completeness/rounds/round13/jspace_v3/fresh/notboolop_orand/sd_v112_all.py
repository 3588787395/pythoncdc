# rr-v5r112 [v112-NOTBOOL] 权威 semantic_diff 复跑 + 基线读数比对
#   001 目标：DIFFERENT -> EQUAL(diffs=[])  004/036：维持 EQUAL
#   019/031：非本轮目标，读数（status + diffs 全签名）须与修复前基线一致
import os, sys, json, subprocess

REPO = 'F:/Downloads/pythoncdc-main'
EV = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/notboolop_orand'
PY = 'D:/Python/python.exe'
PYCDC = REPO + '/pycdc.py'

CASES = [
    ('REAL46-001', 'D:/Python/Lib/__pycache__/dataclasses.cpython-311.pyc', 'EQUAL'),
    ('REAL46-004', 'D:/Python/Lib/__pycache__/enum.cpython-311.pyc', 'EQUAL'),
    ('REAL46-036', 'D:/Python/Lib/site-packages/pandas/core/__pycache__/indexing.cpython-311.pyc', 'EQUAL'),
    ('REAL46-019', 'D:/Python/Lib/__pycache__/ipaddress.cpython-311.pyc', 'BASELINE'),
    ('REAL46-031', 'D:/Python/Lib/site-packages/packaging/__pycache__/version.cpython-311.pyc', 'BASELINE'),
]

# 修复前基线（只读，来自只读诊断阶段）
BASELINE = {
    'REAL46-019': 'D:/temp/opencode/cl_layout/r112diag_a/semantic_diag.json',
    'REAL46-031': 'D:/temp/opencode/cl_layout/r112diag_b/semantic_REAL46-031.json',
    'REAL46-001': 'D:/temp/opencode/cl_layout/r112diag_b/semantic_REAL46-001.json',
}


def sig(res):
    return (res.get('status'), [tuple(sorted(d.items(), key=lambda kv: kv[0]))
                               for d in res.get('diffs', [])])


def main():
    sys.path.insert(0, REPO + '/tools/completeness')
    sys.path.insert(0, REPO)
    os.chdir(REPO)
    import semantic_diff as sd
    summary = []
    for cid, pyc, expect in CASES:
        prod = EV + '/' + cid + '_v112.py'
        with open(prod, 'wb') as fo, open(prod + '.err', 'wb') as fe:
            r = subprocess.run([PY, '-I', '-X', 'utf8', PYCDC, pyc],
                               stdout=fo, stderr=fe, cwd=REPO, timeout=300)
        case = {"case_id": cid, "original": {"pyc": pyc},
                "product": {"source": prod}, "entrypoint": "module",
                "args": [], "kwargs": {}, "timeout_s": 180, "_base": os.getcwd()}
        res = sd.compare_case(case)
        json.dump(res, open(EV + '/semantic_%s_v112.json' % cid, 'w', encoding='utf-8'),
                  ensure_ascii=False, default=str, indent=1)
        n = len(res.get('diffs', []))
        paths = [d.get('path') for d in res.get('diffs', [])]
        if expect == 'BASELINE':
            base = json.load(open(BASELINE[cid], encoding='utf-8'))
            same = (sig(res) == sig(base))
            verdict = 'BASELINE-UNCHANGED' if same else 'BASELINE-CHANGED'
        else:
            verdict = 'OK' if res.get('status') == expect and n == 0 else 'FAIL'
        row = {'case_id': cid, 'decompile_rc': r.returncode,
               'status': res.get('status'), 'n_diffs': n, 'diff_paths': paths,
               'errors': res.get('errors'), 'inconclusive': res.get('inconclusive'),
               'expect': expect, 'verdict': verdict}
        summary.append(row)
        print('%-12s rc=%s status=%-10s diffs=%d %-20s %s' %
              (cid, r.returncode, res.get('status'), n, verdict, paths))
        if expect == 'BASELINE' and verdict == 'BASELINE-CHANGED':
            print('    baseline sig:', sig(base))
            print('    current  sig:', sig(res))
    json.dump(summary, open(EV + '/semantic_v112_all.json', 'w', encoding='utf-8'),
              ensure_ascii=False, default=str, indent=1)
    ok = all(r['verdict'] in ('OK', 'BASELINE-UNCHANGED') for r in summary)
    print('\nALL:', 'PASS' if ok else 'FAIL')


if __name__ == '__main__':
    main()
