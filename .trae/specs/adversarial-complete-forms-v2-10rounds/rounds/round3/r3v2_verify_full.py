#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round3 站桩回归全量读数驱动：对索引内每个 pyc 跑 pyc_verify single 并捕获**完整**输出，
解析全部失败单元名与 units 读数，落盘 rows（含 failures 列表）。只读校验，不改任何源码。
用法：python r3v2_verify_full.py <index.json> <out.json>
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')


def run(cmd, cwd, timeout=280):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    idx_path, out_path = sys.argv[1], sys.argv[2]
    entries = json.load(open(idx_path, encoding='utf-8'))
    results = []
    for e in entries:
        rel = e['path'].replace('/', os.sep)
        rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                       'single', rel], ROOT)
        failures, status, us, ut = [], None, None, None
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                failures.append(line.strip())
        row = {'pyc': e['path'], 'verify_rc': rc, 'status': status,
               'units_success': us, 'units_total': ut, 'failures': failures}
        if status is None:
            row['detail'] = out.strip()[-400:]
        results.append(row)
        print('%-9s %s' % (status or 'ERR', e['path']), flush=True)
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print('-> %s' % out_path)


if __name__ == '__main__':
    main()