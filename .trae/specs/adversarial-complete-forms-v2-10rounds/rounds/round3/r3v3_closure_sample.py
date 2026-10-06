#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闭环复核抽验：regen e02/ne01 后 batch verify（只读 core/，只写 test_repros/round3/ 与 round3/r3v3_closure_sample.json）。"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUNDS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUNDS, '..', '..', '..', '..'))
R3 = os.path.join(ROOT, 'test_repros', 'round3')

PROBES = ['e02_g1_b98_hosts', 'ne01_g1_neg']


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
        pyc = os.path.join(R3, stem + '.pyc')
        ok = os.path.join(R3, stem + 'OK.py')
        run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        index.append({'path': 'test_repros/round3/%s.pyc' % stem})
    idx_path = os.path.join(HERE, 'r3v3_closure_sample_index.json')
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    rep = os.path.join(HERE, 'r3v3_closure_sample.json')
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep])
    print('batch rc=%d' % rc)
    print('\n'.join(out.strip().splitlines()[-8:]))
    d = json.load(open(rep, encoding='utf-8'))
    for r in d['rows']:
        print('%-30s %-9s %2d/%-2d' % (os.path.basename(r['pyc']),
                                       r['status'], r['units_success'], r['units_total']))


if __name__ == '__main__':
    main()