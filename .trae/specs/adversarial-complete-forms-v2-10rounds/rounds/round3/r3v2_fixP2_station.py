#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round3 FIX 位2 站桩回归读数驱动（只读 core/，只写本目录 r3v2_* 证据 JSON）。

与既有 r3v2_verify_full.py 的区别：**先 regen（pycdc -o）再 verify**——因为
pyc_verify 只读同名 *OK.py 产物、不会重新反编译；任何源码改动后必须先重建产物。

用法：python r3v2_fixP2_station.py <face>
  face ∈ round2face | probe42 | round1face | residual | oldface | quotation
输出文件名与格式对齐既有 r3v2_compare_regress.py 的期望：
  round2face -> r3v2_regress_round2face.json（tail）
  probe42    -> r3v2_regress_probe42.json（tail）
  round1face -> r3v2_full_round1face.json（full）
  residual   -> r3v2_full_residual_a.json + r3v2_full_residual_b.json（full，对半）
  oldface    -> r3v2_full_oldface_a.json + r3v2_full_oldface_b.json（full，对半）
  quotation  -> 单验打印
每条记录同时携带 tail（原始输出行）与 status/units_success/units_total/failures，
两种读取器（load_list_tail / load_list_full）均可解析。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUNDS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUNDS, '..', '..', '..', '..'))
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

BASELINE = {
    'round2face': (os.path.join(ROUNDS, 'round2', 'r2_regress_replay.json'), 'list'),
    'probe42': (os.path.join(ROUNDS, 'round2', 'r2_probe_results.json'), 'list'),
    'round1face': (os.path.join(ROUNDS, 'round1', 'r1_sentry_replay.json'), 'rows'),
    'residual': (os.path.join(ROUNDS, 'round1', 'r1_residual_replay.json'), 'rows'),
    'oldface': (os.path.join(HERE, 'r3v2_oldface_baseline.json'), 'keys'),
}


def pyc_list(face):
    path, kind = BASELINE[face]
    d = json.load(open(path, encoding='utf-8-sig'))
    if kind == 'list':
        return [e['pyc'] for e in d]
    if kind == 'rows':
        return [r['pyc'] for r in d['rows']]
    return list(d.keys())


def run(cmd, timeout=280):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def one(pyc):
    rel = pyc.replace('\\', '/')
    if rel.startswith('F:/Downloads/pythoncdc-main/'):
        rel = rel[len('F:/Downloads/pythoncdc-main/'):]
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', full])
    tail = [l for l in out.splitlines() if l.strip()]
    status, us, ut = None, None, None
    for line in tail:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in tail if FAIL_RE.match(l)]
    return {'pyc': pyc.replace('\\', '/'), 'verify_rc': rc, 'status': status,
            'units_success': us, 'units_total': ut, 'failures': fails, 'tail': tail[-8:]}


def dump(path, rows):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


def main():
    face = sys.argv[1]
    if face == 'quotation':
        pyc = os.path.join(ROOT, 'site-packages', 'fly', 'data', 'quotation.pyc')
        r = one(pyc)
        print(r['status'], r['units_success'], r['units_total'])
        print('\n'.join(r['failures']))
        return
    plist = pyc_list(face)
    rows = []
    for i, pyc in enumerate(plist, 1):
        r = one(pyc)
        rows.append(r)
        print('[%d/%d] %-9s %s/%s %s' % (i, len(plist), r['status'],
              r['units_success'], r['units_total'], os.path.basename(pyc)), flush=True)
    if face in ('residual', 'oldface'):
        h = (len(rows) + 1) // 2
        dump(os.path.join(HERE, 'r3v2_full_%s_a.json' % face), rows[:h])
        dump(os.path.join(HERE, 'r3v2_full_%s_b.json' % face), rows[h:])
        print('-> a=%d b=%d' % (len(rows[:h]), len(rows[h:])))
    elif face == 'round1face':
        dump(os.path.join(HERE, 'r3v2_full_round1face.json'), rows)
    else:
        dump(os.path.join(HERE, 'r3v2_regress_%s.json' % face), rows)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s units=%d/%d' % (face, ok, tot))


if __name__ == '__main__':
    main()
