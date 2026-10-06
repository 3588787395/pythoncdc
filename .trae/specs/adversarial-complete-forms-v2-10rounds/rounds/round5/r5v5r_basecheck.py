#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 复核：变体失败项在【基线副本 9b3eea38】下的独立读数（证明 NEWFAIL=0）。
把变体 pyc 复制进 $env:TEMP/r5v5r_base 树内，用基线自带 pycdc+pyc_verify 复跑，
绝不覆盖当前工作树产物。输出 rounds/round5/r5v5r_baseline_variant.json。
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'
BASE = os.path.join(os.environ.get('TEMP', r'C:\Temp'), 'r5v5r_base')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

VARIANTS = [
    'b114_in_for', 'b114_in_while', 'b114_in_func_for',
    'b115_while_and3', 'b116_closure_bare', 'b116_default',
]


def run(args, cwd, timeout=120):
    p = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=timeout)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def main():
    dst_dir = os.path.join(BASE, 'test_repros', 'round5')
    os.makedirs(dst_dir, exist_ok=True)
    rows = []
    for stem in VARIANTS:
        src = os.path.join(ROOT, 'test_repros', 'round5', 'r5v5r_%s.pyc' % stem)
        dst = os.path.join(dst_dir, 'r5v5r_%s.pyc' % stem)
        shutil.copyfile(src, dst)
        ok = dst[:-4] + 'OK.py'
        rc1, _ = run([sys.executable, 'pycdc.py', dst, '-o', ok], BASE, 90)
        rc2, out = run([sys.executable, 'scripts', 'pyc_verify.py', 'single', dst], BASE, 120)
        status, us, ut = None, None, None
        fails = []
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        rows.append({'variant': stem, 'base_regen_rc': rc1, 'base_verify_rc': rc2,
                     'base_status': status, 'base_units': us, 'base_total': ut, 'base_failures': fails})
        print('%-20s base=%s %s/%s' % (stem, status, us, ut), flush=True)
    with open(os.path.join(HERE, 'r5v5r_baseline_variant.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()