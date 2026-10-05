#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 3 攻击执行驱动：编译 e*/ne* 探针 → pycdc regen OK.py → pyc_verify batch。
另按 RV2 方法学对 rv3_02/rv3_07（B98 移交复现）以当前 HEAD regen+verify。

用法：python r3_attack_run.py
产物：rounds/round3/v2r3_probe_index.json / v2r3_probe_results.json / v2r3_rv3_repro.json
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
R3 = os.path.join(ROOT, 'test_repros', 'round3')
R2 = os.path.join(ROOT, 'test_repros', 'round2')

PROBES = [
    'e01_g1_b98_matrix', 'e02_g1_b98_hosts', 'e03_g1_b1b_stress', 'ne01_g1_neg',
    'e04_g2_ifexp_deep', 'ne02_g2_neg',
    'e05_g3_compare_chain', 'e06_g3_op_leaves', 'ne03_g3_neg',
    'e07_g4_star_slice_containers', 'ne04_g4_neg',
    'e08_g5_lambda_deep', 'ne05_g5_neg',
    'e09_g6_comprehensions', 'e09b_g6_async_comps', 'ne06_g6_neg',
    'e10_g7_call_args', 'ne07_g7_neg',
    'e11_g8_fstrings', 'ne08_g8_neg',
    'e12_g9_await_yield', 'ne09_g9_neg',
    'e13_g10_walrus', 'ne10_g10_neg',
]


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
            print('COMPILE FAIL', stem, out.strip()[-200:])
            continue
        ok = os.path.join(R3, stem + 'OK.py')
        rc, out = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        if rc != 0:
            print('PYCDC FAIL', stem, out.strip()[-200:])
            continue
        index.append({'path': 'test_repros/round3/%s.pyc' % stem})
    idx_path = os.path.join(HERE, 'v2r3_probe_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print('index -> %s (%d files)' % (idx_path, len(index)))

    rep_path = os.path.join(HERE, 'v2r3_probe_results.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep_path])
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))

    repro = []
    for stem in ('rv3_02_b89_boolop_chain', 'rv3_07_b89_trim_overtrim'):
        pyc = os.path.join(R2, stem + '.pyc')
        ok = os.path.join(R2, stem + 'OK.py')
        rc1, out1 = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        rc2, out2 = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                         'single', pyc])
        lines = [l for l in out2.strip().splitlines() if l.strip()]
        repro.append({'pyc': stem, 'regen_rc': rc1, 'verify_rc': rc2, 'tail': lines[-5:]})
        print('%-30s verify_rc=%d' % (stem, rc2))
        for l in lines:
            if l.startswith('***') or 'status=' in l:
                print('   ', l)
    with open(os.path.join(HERE, 'v2r3_rv3_repro.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(repro, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
