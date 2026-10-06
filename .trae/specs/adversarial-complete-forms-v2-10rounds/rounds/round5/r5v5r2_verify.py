#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round5 终审（R2）：独立复跑。
用法：python r5v5r2_verify.py variants   -> r5v5r2_variant_results.json（32 变体 regen+verify）
      python r5v5r2_verify.py batch34    -> r5v5r2_batch34_{a,b,merged}.json + r5v5r2_batch34_compare.txt
证据前缀 r5v5r2_，不覆盖既有。
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'F:\Downloads\pythoncdc-main'
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(args, timeout=300):
    try:
        p = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', ''


def regen_verify(pyc):
    full = pyc.replace('/', os.sep) if pyc.startswith('F:') else os.path.join(ROOT, pyc.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok], 90)
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', full])
    status, us, ut, fails = None, None, None, []
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
        if FAIL_RE.match(line):
            fails.append(line.strip())
    return {'pyc': pyc.replace('\\', '/'), 'status': status,
            'units_success': us, 'units_total': ut, 'failures': fails}


def do_variants():
    files = sorted(glob.glob(os.path.join(ROOT, 'test_repros', 'round5', 'r5v5r_*.pyc')))
    rows = []
    for i, f in enumerate(files, 1):
        rel = os.path.relpath(f, ROOT).replace(os.sep, '/')
        r = regen_verify(rel)
        rows.append(r)
        print('[%d/%d] %-9s %s/%s %s' % (i, len(files), r['status'], r['units_success'],
              r['units_total'], os.path.basename(f)), flush=True)
    with open(os.path.join(HERE, 'r5v5r2_variant_results.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> variants units=%d/%d files=%d' % (ok, tot, len(rows)))


def do_batch34():
    with open(os.path.join(BL, 'failing_index.json'), encoding='utf-8-sig') as f:
        paths = [e['path'] for e in json.load(f)]
    py = sys.executable
    for i, p in enumerate(paths, 1):
        full = p.replace('/', os.sep)
        ok = full[:-4] + 'OK.py'
        rc, _ = run([py, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok], 90)
        if rc != 0:
            print('  regen rc=%s %s' % (rc, os.path.basename(full)), flush=True)
    reps = []
    for tag, half in zip(('a', 'b'), (paths[:17], paths[17:])):
        out = os.path.join(HERE, 'r5v5r2_batch34_%s.json' % tag)
        if os.path.exists(out):
            os.remove(out)
        rc, txt = run([py, 'scripts/pyc_verify.py', 'batch', '--json', out] + half, 300)
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
    merged = os.path.join(HERE, 'r5v5r2_batch34_merged.json')
    with open(merged, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print('MERGED units=%s/%s files=%s' % (m['units_success'], m['units_total'], m['files_by_status']), flush=True)
    rc, txt = run([py, 'scripts/pyc_verify.py', 'compare',
                   '--before', os.path.join(BL, 'small_test_report.json'), '--after', merged], 130)
    with open(os.path.join(HERE, 'r5v5r2_batch34_compare.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)
    print(txt[-1500:], flush=True)


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'variants'
    if mode == 'variants':
        do_variants()
    else:
        do_batch34()