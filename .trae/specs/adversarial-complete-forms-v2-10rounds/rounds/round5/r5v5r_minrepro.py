#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 复核：三最小复现 RV2 独立复跑（先 regen 再 verify）。
r5v5_01(B114) / r5v5_08 + k1 + k2(B115) / r5v5_03 + k4(B116)。
输出 rounds/round5/r5v5r_minrepro.json。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

FILES = [
    ('test_repros/round5/r5v5_01_module_root.pyc', 'B114'),
    ('test_repros/round5/r5v5_08_slice_callsite.pyc', 'B115'),
    ('test_repros/round5/_scratch_r5v5/k1_ifwhile.pyc', 'B115'),
    ('test_repros/round5/_scratch_r5v5/k2_ifwhile_flag.pyc', 'B115'),
    ('test_repros/round5/r5v5_03_annassign.pyc', 'B116'),
    ('test_repros/round5/_scratch_r5v5/k4_bare_ann.pyc', 'B116'),
]


def run(args, timeout=290):
    p = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def main():
    rows = []
    for rel, bug in FILES:
        full = os.path.join(ROOT, rel.replace('/', os.sep))
        ok = full[:-4] + 'OK.py'
        rc1, _ = run([sys.executable, 'pycdc.py', full, '-o', ok], 90)
        rc2, out = run([sys.executable, 'scripts/pyc_verify.py', 'single', full])
        status, us, ut = None, None, None
        fails = []
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        rows.append({'file': rel, 'bug': bug, 'regen_rc': rc1, 'verify_rc': rc2,
                     'status': status, 'units_success': us, 'units_total': ut, 'failures': fails})
        print('%-14s %-46s regen=%s verify=%s %s %s/%s' % (bug, os.path.basename(rel), rc1, rc2,
              status, us, ut), flush=True)
        for f in fails:
            print('     ' + f, flush=True)
    with open(os.path.join(HERE, 'r5v5r_minrepro.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()