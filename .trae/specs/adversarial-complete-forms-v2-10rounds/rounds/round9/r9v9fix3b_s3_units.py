#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round9 整改（任务 9.3b，REVIEW2 R-1 方案 a）：§3 四单元 + probe 门禁复跑驱动。

内容 = n9_stmt_sweep 6/6、r8_07 10/11、r8_10 9/12、x08 6/8 + probe_for_assert /
probe_break_raise 门禁。RV2：regen（pycdc -o）到临时目录，verify single --source。
只读 core/，证据 r9v9fix3b_s3_units.json。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
TMPOUT = r'D:\Temp\opencode\r9fix3b\products'

UNITS = [
    ('n9_stmt_sweep', 'test_repros/round9/n9v9_stmt_sweep.pyc'),
    ('r8_07_assert_forms', 'test_repros/round8/r8_07_assert_forms.pyc'),
    ('r8_10_expr_cross_stmt', 'test_repros/round8/r8_10_expr_cross_stmt.pyc'),
    ('x08_stmt_leaves', 'test_repros/round2/x08_stmt_leaves.pyc'),
    ('probe_for_assert', r'D:\Temp\opencode\probe_for_assert.pyc'),
    ('probe_break_raise', r'D:\Temp\opencode\probe_break_raise.pyc'),
]

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=250):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def one(name, rel):
    full = rel if os.path.isabs(rel) else os.path.join(ROOT, rel.replace('/', os.sep))
    os.makedirs(TMPOUT, exist_ok=True)
    ok = os.path.join(TMPOUT, 'fix3b_' + name + 'OK.py')
    rc_regen, _ = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', full, '--source', ok])
    tail = [l for l in out.splitlines() if l.strip()]
    status, us, ut = None, None, None
    for line in tail:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in tail if FAIL_RE.match(l)]
    return {'name': name, 'pyc': rel, 'regen_rc': rc_regen, 'verify_rc': rc,
            'status': status, 'units_success': us, 'units_total': ut,
            'failures': fails}


def main():
    rows = []
    for name, rel in UNITS:
        r = one(name, rel)
        rows.append(r)
        print('[%-22s] regen_rc=%s %-8s %s/%s' % (name, r['regen_rc'], r['status'],
              r['units_success'], r['units_total']), flush=True)
        for f in r['failures']:
            print('    ' + f)
    out = os.path.join(HERE, 'r9v9fix3b_s3_units.json')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> ' + os.path.basename(out))


if __name__ == '__main__':
    main()
