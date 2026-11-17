# drift_after.py: 终验——109 条漂移的 10 个 pyc 重跑，对比修复前的 product_sha 与判官状态
import hashlib
import io
import json
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
SRC = os.path.join(REPO, '.trae/specs/achieve-any-syntax-completeness/rounds/round13'
                         '/jspace_v3/fresh/gate_drift/drift_109.json')
OUTDIR = r'D:\temp\opencode\cl_layout\drift2'
OUT = os.path.join(REPO, '.trae/specs/achieve-any-syntax-completeness/rounds/round13'
                         '/jspace_v3/fresh/gate_drift/drift_109_after.json')


def sha16(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    d = json.load(io.open(SRC, encoding='utf-8'))
    rows = d['rows']
    pycs = sorted({r['pyc'] for r in rows})
    print('rows=%d unique_pyc=%d' % (len(rows), len(pycs)))
    per_pyc = {}
    for pyc in pycs:
        rel = pyc.replace('\\', '/')
        name = os.path.basename(rel).replace('.pyc', '.py')
        out = os.path.join(OUTDIR, name)
        r = subprocess.run([PY, '-I', '-X', 'utf8', 'pycdc.py', rel, '-o', out],
                           capture_output=True, cwd=REPO)
        ok = os.path.isfile(out)
        j = ''
        if ok:
            rr = subprocess.run([PY, '-I', '-X', 'utf8', 'scripts/pyc_verify.py', 'single',
                                 rel, '--source', out], capture_output=True, cwd=REPO)
            j = ((rr.stdout or b'').decode('utf-8', 'replace')).strip().splitlines()[-1:] or ['']
            j = j[0].strip()
        per_pyc[rel] = {'product': out if ok else None,
                        'sha16': sha16(out) if ok else None,
                        'judge': j}
        print('%-58s %s | %s' % (os.path.basename(rel), per_pyc[rel]['sha16'], j))

    changed = same = 0
    still_bad = []
    for r in rows:
        rel = r['pyc'].replace('\\', '/')
        cur = per_pyc[rel]['sha16']
        old = (r.get('product_sha') or '')[:16]
        if cur != old:
            changed += 1
        else:
            same += 1
            if r.get('class') == 'a':
                still_bad.append({'entry': r['entry_id'], 'pyc': os.path.basename(rel),
                                  'sha': cur, 'class_before': r.get('class')})
    res = {'rows': len(rows), 'unique_pyc': len(pycs),
           'product_changed_vs_pre_fix': changed, 'product_unchanged': same,
           'still_class_a_with_same_product': len(still_bad),
           'still_bad_sample': still_bad[:20],
           'per_pyc': {k: {'sha16': v['sha16'], 'judge': v['judge']} for k, v in per_pyc.items()}}
    json.dump(res, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'per_pyc'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
