#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 位临时驱动：对指定 pyc 先 regen OK.py（RV2 方法学）再 pyc_verify single。
用法：python tmp_p3_replay.py <out.json> <pyc 路径子串...>
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
    out_path = sys.argv[1]
    filters = sys.argv[2:]
    base = os.path.join(ROOT, 'test_repros', 'round2')
    names = []
    for f in filters:
        for fn in sorted(os.listdir(base)):
            if fn.endswith('.pyc') and f in fn and fn not in names:
                names.append(fn)
    results = []
    for fn in names:
        pyc = os.path.join(base, fn)
        ok = pyc[:-4] + 'OK.py'
        rc1, out1 = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok], ROOT)
        row = {'pyc': fn}
        if rc1 != 0:
            row['regen'] = 'fail rc=%d' % rc1
            row['detail'] = out1.strip()[-400:]
            results.append(row)
            print('%-6s %s regen-fail' % ('REGENFAIL', fn), flush=True)
            continue
        rc2, out2 = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                         'single', pyc], ROOT)
        row['verify_rc'] = rc2
        lines = [l for l in out2.strip().splitlines() if l.strip()]
        row['tail'] = lines
        results.append(row)
        print('%-6s %s' % ('FAIL' if rc2 else 'MATCH', fn), flush=True)
        for l in row['tail']:
            if 'Failure' in l or 'MISSING' in l.upper():
                print('       ', l.strip(), flush=True)
    with open(os.path.join(HERE, out_path), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print('-> %s' % out_path)


if __name__ == '__main__':
    main()
