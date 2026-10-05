#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 位临时驱动：按索引对 pyc 先 regen OK.py（RV2 方法学）再 pyc_verify single。
用法：python tmp_p3_index_replay.py <index.json> <out.json> [过滤子串...]
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))


def run(cmd, cwd, timeout=280):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    idx_path, out_path = sys.argv[1], sys.argv[2]
    filters = sys.argv[3:]
    entries = json.load(open(idx_path, encoding='utf-8'))
    if filters:
        entries = [e for e in entries if any(f in e['path'] for f in filters)]
    results = []
    for e in entries:
        rel = e['path'].replace('/', os.sep)
        pyc = os.path.join(ROOT, rel)
        ok = pyc[:-4] + 'OK.py'
        rc1, out1 = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok], ROOT)
        row = {'pyc': e['path']}
        if rc1 != 0:
            row['regen'] = 'fail rc=%d' % rc1
            row['detail'] = out1.strip()[-400:]
            results.append(row)
            print('%-9s %s' % ('REGENFAIL', e['path']), flush=True)
            continue
        rc2, out2 = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                         'single', pyc], ROOT)
        row['verify_rc'] = rc2
        lines = [l for l in out2.strip().splitlines() if 'Failure' in l or 'units=' in l]
        row['tail'] = lines
        results.append(row)
        print('%-9s %s | %s' % ('FAIL' if rc2 else 'MATCH', e['path'],
                                '; '.join(l.strip() for l in lines if 'Failure' in l)), flush=True)
    with open(os.path.join(HERE, out_path), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print('-> %s' % out_path)


if __name__ == '__main__':
    main()
