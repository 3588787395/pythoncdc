#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 复核：34 小测试集 RV2 独立复跑（先 regen 再 verify，batch 拆两半）。

输入：baseline/failing_index.json（34 pyc）。
流程：对每个 pyc 先 `pycdc.py <pyc> -o <OK.py>` regen（RV2，禁信磁盘陈旧产物），
      再 `pyc_verify.py batch --json` 拆两半执行，合并后与 baseline/small_test_report.json compare。
输出（rounds/round5/）：r5v5r_batch34_a.json / _b.json / _merged.json / _compare.txt
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
CUT = 17


def run(args, timeout, label):
    t0 = time.time()
    try:
        r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        out = (r.stdout or '') + (('\n[stderr] ' + r.stderr) if r.stderr else '')
        rc = r.returncode
    except subprocess.TimeoutExpired:
        rc, out = 'TIMEOUT', '[TIMEOUT] ' + label
    print('=== %s rc=%s %.1fs' % (label, rc, time.time() - t0), flush=True)
    return rc, out


def main():
    with open(os.path.join(BL, 'failing_index.json'), encoding='utf-8-sig') as f:
        paths = [e['path'] for e in json.load(f)]
    py = sys.executable
    # Phase 1: RV2 regen
    for i, p in enumerate(paths, 1):
        full = p.replace('/', os.sep)
        ok = full[:-4] + 'OK.py'
        rc, _ = run([py, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok], 90, 'REGEN%d' % i)
        if rc != 0:
            print('  regen rc=%s %s' % (rc, os.path.basename(full)), flush=True)
    # Phase 2: batch split
    reps = []
    for tag, half in zip(('a', 'b'), (paths[:CUT], paths[CUT:])):
        out = os.path.join(HERE, 'r5v5r_batch34_%s.json' % tag)
        if os.path.exists(out):
            os.remove(out)
        rc, txt = run([py, 'scripts/pyc_verify.py', 'batch', '--json', out] + half, 300, 'BATCH-' + tag.upper())
        print(txt[-500:], flush=True)
        reps.append(out)
    a = json.load(open(reps[0], encoding='utf-8'))
    b = json.load(open(reps[1], encoding='utf-8'))
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
    merged = os.path.join(HERE, 'r5v5r_batch34_merged.json')
    with open(merged, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print('MERGED units=%s/%s files=%s' % (m['units_success'], m['units_total'], m['files_by_status']), flush=True)
    # Phase 3: compare with baseline
    rc, txt = run([py, 'scripts/pyc_verify.py', 'compare',
                   '--before', os.path.join(BL, 'small_test_report.json'),
                   '--after', merged], 130, 'CMP34')
    with open(os.path.join(HERE, 'r5v5r_batch34_compare.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    print(txt[-2500:], flush=True)


if __name__ == '__main__':
    main()