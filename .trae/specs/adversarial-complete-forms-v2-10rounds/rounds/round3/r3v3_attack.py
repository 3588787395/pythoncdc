#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 3.3 新变体对抗攻击驱动（RV2：compile -> pycdc regen -> pyc_verify batch）。

只读 core/，只写 test_repros/round3/r3v3_* 产物与本目录 r3v3_attack_*.json。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUNDS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUNDS, '..', '..', '..', '..'))
R3 = os.path.join(ROOT, 'test_repros', 'round3')

PROBES = ['r3v3_a_ternary_boolop_cond', 'r3v3_b_compare_chains',
          'r3v3_c_b98_group', 'r3v3_d_interaction', 'r3v3_e_negctl']


def run(cmd, timeout=280):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    index = []
    for stem in PROBES:
        src = os.path.join(R3, stem + '.py')
        pyc = os.path.join(R3, stem + '.pyc')
        rc, out = run([sys.executable, '-c',
                       'import py_compile,sys; py_compile.compile(sys.argv[1], sys.argv[2], doraise=True, optimize=0)',
                       src, pyc])
        if rc != 0:
            print('COMPILE FAIL(src)', stem, out.strip()[-200:])
            continue
        ok = os.path.join(R3, stem + 'OK.py')
        run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        index.append({'path': 'test_repros/round3/%s.pyc' % stem})
    idx_path = os.path.join(HERE, 'r3v3_attack_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    rep = os.path.join(HERE, 'r3v3_attack_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep])
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))
    d = json.load(open(rep, encoding='utf-8'))
    for r in d['rows']:
        print('%-38s %-9s %2d/%-2d' % (os.path.basename(r['pyc']),
                                       r['status'], r['units_success'], r['units_total']))
        for f in r['failures']:
            print('      FAIL', f)


if __name__ == '__main__':
    main()
