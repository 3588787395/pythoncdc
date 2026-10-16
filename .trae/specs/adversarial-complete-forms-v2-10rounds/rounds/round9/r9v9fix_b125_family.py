#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作 B125 族面抽验：r9w16 while-else 电池 + b109 邻接面（RV2 临时产物）。

证据 → r9v9fix_b125_family.json。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
OUT = os.path.join(HERE, 'r9v9fix_b125_family.json')
TMPOUT = r'D:\Temp\opencode\r92_products'

TARGETS = [
    ('w16_13_while_else', 'test_repros/round9/r9w16_13_ctl_while_else.py'),
    ('w16_14_while_else_break', 'test_repros/round9/r9w16_14_ctl_while_else_break.py'),
    ('w16_17_else_nested_loop', 'test_repros/round9/r9w16_17_ctl_else_nested_loop.py'),
    ('w16_18_while_else_cont_outer', 'test_repros/round9/r9w16_18_ctl_while_else_cont_outer.py'),
    ('w16_08_while_in_while', 'test_repros/round9/r9w16_08_while_in_while.py'),
    ('w16_05_nested_in_for', 'test_repros/round9/r9w16_05_nested_in_for.py'),
    ('r6_q2_whilehost_ctl', 'test_repros/round6/r6_q2_whilehost_ctl.py'),
    ('r6_q2_whilehost_spec', 'test_repros/round6/r6_q2_whilehost_spec.py'),
]

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')


def run(cmd, timeout=200):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def main():
    rows = []
    for name, rel in TARGETS:
        src = os.path.join(ROOT, rel.replace('/', os.sep))
        if not os.path.exists(src):
            print('[%-26s] SKIP missing' % name, flush=True)
            continue
        os.makedirs(TMPOUT, exist_ok=True)
        pyc = os.path.join(TMPOUT, 'b125_' + name + '_src.pyc')
        subprocess.run([sys.executable, '-c',
                        'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)',
                        src, os.path.abspath(pyc)], check=True)
        ok = os.path.join(TMPOUT, 'b125_' + name + '.py')
        run([sys.executable, os.path.join(ROOT, 'pycdc.py'), os.path.abspath(pyc), '-o', ok])
        out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', os.path.abspath(pyc), '--source', ok])
        status, us, ut = None, None, None
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
        rows.append({'name': name, 'status': status, 'units_success': us,
                     'units_total': ut})
        print('[%-26s] %-8s %s/%s' % (name, status, us, ut), flush=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> ' + os.path.basename(OUT))


if __name__ == '__main__':
    main()
