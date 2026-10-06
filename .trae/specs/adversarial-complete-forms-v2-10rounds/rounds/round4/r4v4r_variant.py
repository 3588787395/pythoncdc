#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round4 复核（Task 4.3）：新变体攻击驱动——HEAD(fa9778a5) vs 修复前(9836400d worktree)。

对每个 r4v4r_* 变体探针：compile -> 两侧各自 pycdc regen（隔离 tmp 目录）-> 各自 pyc_verify single。
区分「误伤（HEAD 比修复前变差/新失败）」与「存量（两侧皆失败）」。
只读两侧 core/，输出 r4v4r_variant_results.json。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
BASE_ROOT = r'd:\Temp\r4v4r_base'
R4 = os.path.join(ROOT, 'test_repros', 'round4')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

PROBES = ['r4v4r_b100_levels', 'r4v4r_b101_star', 'r4v4r_b102_except',
          'r4v4r_b109_loopelse', 'r4v4r_b103_guard']


def run(cmd, cwd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def side_verify(tree_root, pyc, tag):
    tmp = tempfile.mkdtemp(prefix='r4v4r_%s_' % tag)
    try:
        local_pyc = os.path.join(tmp, os.path.basename(pyc))
        shutil.copy2(pyc, local_pyc)
        ok = local_pyc[:-4] + 'OK.py'
        run([sys.executable, os.path.join(tree_root, 'pycdc.py'), local_pyc, '-o', ok], tree_root)
        rc, out = run([sys.executable, os.path.join(tree_root, 'scripts', 'pyc_verify.py'),
                       'single', local_pyc], tree_root)
        status, us, ut, fails = None, None, None, []
        for line in out.splitlines():
            m = STAT_RE.search(line)
            if m:
                status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
            if FAIL_RE.match(line):
                fails.append(line.strip())
        ok_txt = ''
        if os.path.isfile(ok):
            with open(ok, encoding='utf-8', errors='replace') as f:
                ok_txt = f.read()
        return {'status': status, 'units_success': us, 'units_total': ut,
                'failures': fails, 'product': ok_txt[:2000]}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    rows = []
    for stem in PROBES:
        src = os.path.join(R4, stem + '.py')
        pyc = os.path.join(R4, stem + '.pyc')
        rc, out = run([sys.executable, '-c',
                       'import py_compile,sys; py_compile.compile(sys.argv[1], sys.argv[2], doraise=True, optimize=0)',
                       src, pyc], ROOT)
        if rc != 0:
            rows.append({'probe': stem, 'compile_error': out.strip()[-300:]})
            print('COMPILE FAIL', stem, out.strip()[-200:])
            continue
        head = side_verify(ROOT, pyc, 'head')
        base = side_verify(BASE_ROOT, pyc, 'base')
        h_fail = set(head['failures'])
        b_fail = set(base['failures'])
        infl = sorted(h_fail - b_fail)        # HEAD 新增失败 = 误伤（if any）
        healed = sorted(b_fail - h_fail)      # HEAD 修复
        row = {'probe': stem,
               'head': {'status': head['status'], 'units': '%s/%s' % (head['units_success'], head['units_total']),
                        'failures': sorted(h_fail)},
               'base': {'status': base['status'], 'units': '%s/%s' % (base['units_success'], base['units_total']),
                        'failures': sorted(b_fail)},
               'false_negative_units': infl, 'healed_units': healed,
               'verdict': 'MISFIRE' if infl else ('improved' if healed else ('both_fail_same' if h_fail else 'clean'))}
        rows.append(row)
        print('%-22s HEAD=%s BASE=%s infl=%d healed=%d -> %s'
              % (stem, row['head']['units'], row['base']['units'],
                 len(infl), len(healed), row['verdict']), flush=True)
        if stem in ('r4v4r_b100_levels', 'r4v4r_b101_star'):
            os.makedirs(os.path.join(HERE), exist_ok=True)
            with open(os.path.join(HERE, '%s_head_product.txt' % stem), 'w',
                      encoding='utf-8', newline='\n') as f:
                f.write(head['product'])
            with open(os.path.join(HERE, '%s_base_product.txt' % stem), 'w',
                      encoding='utf-8', newline='\n') as f:
                f.write(base['product'])
    with open(os.path.join(HERE, 'r4v4r_variant_results.json'), 'w',
              encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> r4v4r_variant_results.json (%d probes)' % len(rows))


if __name__ == '__main__':
    main()