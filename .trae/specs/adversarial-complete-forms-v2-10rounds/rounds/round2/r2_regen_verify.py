#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 2 站桩回归驱动：对索引内每个 pyc 先用当前 HEAD 代码重生成 OK.py（RV2 方法学，
磁盘 OK.py 可能陈旧），再跑 pyc_verify single。只写 OK.py 产物与 out.json；不改任何源码。

用法：python r2_regen_verify.py <index.json> <out.json> [pyc 路径过滤子串...]
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
            continue
        row['regen'] = 'ok'
        rc2, out2 = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                         'single', pyc], ROOT)
        row['verify_rc'] = rc2
        lines = [l for l in out2.strip().splitlines() if l.strip()]
        row['tail'] = lines[-4:]
        results.append(row)
        print('%-9s %s' % ('FAIL' if rc2 else 'MATCH', e['path']), flush=True)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print('-> %s' % out_path)


if __name__ == '__main__':
    main()
