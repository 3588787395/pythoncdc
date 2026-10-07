#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 8 修复批位A（识别域）攻击面重放（RV2：compile -> pycdc regen -> pyc_verify batch + 逐文件 single）。

复用 round7/r7v7_attack.py 驱动（只读 core/，只写 test_repros/round7 探针产物 .pyc/*OK.py
与本目录 r8v8fixA_* 证据 JSON）。探针面 = test_repros/round7/ 全部 r7v7_*（攻击）、
n7v7_*（负对照）、r7v7r_*（round7 复核批变体，含 B121 最小复现 r7v7r_b121_whilehdr）。
本副本仅改：①输出前缀 r7v7_ → r8v8fixA_（证据文件名）；②glob 与分类增加 r7v7r_* 面。
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
R7 = os.path.join(ROOT, 'test_repros', 'round7')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    stems = []
    for pat in ('r7v7_*.py', 'n7v7_*.py', 'r7v7r_*.py'):
        for p in sorted(glob.glob(os.path.join(R7, pat))):
            if p.endswith('OK.py'):
                continue
            stems.append(os.path.splitext(os.path.basename(p))[0])

    index = []
    for stem in stems:
        src = os.path.join(R7, stem + '.py')
        pyc = os.path.join(R7, stem + '.pyc')
        rc, out = run([sys.executable, '-c',
                       'import py_compile,sys; py_compile.compile(sys.argv[1], sys.argv[2], doraise=True, optimize=0)',
                       src, pyc])
        if rc != 0:
            print('COMPILE FAIL(src)', stem, out.strip()[-300:])
            continue
        ok = os.path.join(R7, stem + 'OK.py')
        rc, out = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        if rc != 0:
            print('PYCDC FAIL', stem, out.strip()[-200:])
        index.append({'path': 'test_repros/round7/%s.pyc' % stem})

    idx_path = os.path.join(HERE, 'r8v8fixA_probe_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print('index -> %s (%d files)' % (idx_path, len(index)))

    rep_path = os.path.join(HERE, 'r8v8fixA_probe_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep_path])
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))

    rows = []
    for stem in stems:
        pyc = os.path.join(R7, stem + '.pyc')
        if not os.path.isfile(pyc):
            continue
        rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', pyc])
        status, us, ut = None, None, None
        fails = []
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        rows.append({'pyc': 'test_repros/round7/%s.pyc' % stem,
                     'status': status, 'units_success': us, 'units_total': ut,
                     'failures': fails})

    detail_path = os.path.join(HERE, 'r8v8fixA_probe_detail.json')
    with open(detail_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    attack = [r for r in rows if os.path.basename(r['pyc']).startswith('r7v7_')
              and not os.path.basename(r['pyc']).startswith('r7v7r_')]
    neg = [r for r in rows if os.path.basename(r['pyc']).startswith('n7v7_')]
    var = [r for r in rows if os.path.basename(r['pyc']).startswith('r7v7r_')]
    atk_ok = sum(r['units_success'] or 0 for r in attack)
    atk_tot = sum(r['units_total'] or 0 for r in attack)
    neg_ok = sum(r['units_success'] or 0 for r in neg)
    neg_tot = sum(r['units_total'] or 0 for r in neg)
    var_ok = sum(r['units_success'] or 0 for r in var)
    var_tot = sum(r['units_total'] or 0 for r in var)
    print('-> %s  attack units=%d/%d  neg units=%d/%d  r7v7r variants units=%d/%d'
          % (detail_path, atk_ok, atk_tot, neg_ok, neg_tot, var_ok, var_tot))


if __name__ == '__main__':
    main()
