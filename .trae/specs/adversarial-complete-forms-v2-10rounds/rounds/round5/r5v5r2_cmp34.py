#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 终审（R2）34 集 compare 修复：合并 a/b（含 paths_by_status）后 compare 基线。
输出 r5v5r2_batch34_merged.json（覆盖） + r5v5r2_batch34_compare.txt。
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')


def main():
    a = json.load(open(os.path.join(HERE, 'r5v5r2_batch34_a.json'), encoding='utf-8'))
    b = json.load(open(os.path.join(HERE, 'r5v5r2_batch34_b.json'), encoding='utf-8'))
    m = dict(a)
    m['rows'] = a.get('rows', []) + b.get('rows', [])
    for k in ('files_total', 'units_total', 'units_success'):
        m[k] = a.get(k, 0) + b.get(k, 0)
    m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
    fbs = {}
    for d in (a, b):
        for k, v in d.get('files_by_status', {}).items():
            fbs[k] = fbs.get(k, 0) + v
    m['files_by_status'] = fbs
    pbs = {}
    for d in (a, b):
        for k, v in d.get('paths_by_status', {}).items():
            pbs.setdefault(k, []).extend(v)
    m['paths_by_status'] = pbs
    merged = os.path.join(HERE, 'r5v5r2_batch34_merged.json')
    with open(merged, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print('MERGED units=%s/%s files=%s paths_by_status=%s' % (
        m['units_success'], m['units_total'], m['files_by_status'],
        {k: len(v) for k, v in pbs.items()}), flush=True)
    p = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'compare',
                        '--before', os.path.join(BL, 'small_test_report.json'), '--after', merged],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=130)
    txt = (p.stdout or '') + (p.stderr or '')
    with open(os.path.join(HERE, 'r5v5r2_batch34_compare.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    print(txt, flush=True)


if __name__ == '__main__':
    main()