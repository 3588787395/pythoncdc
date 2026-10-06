#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round6 站桩回归读数驱动（RV2：**先 regen（pycdc -o）再 verify**）。

只读 core/，只写本目录 r6v6_* 证据 JSON。基线沿用 round1/round2/round3 已落地的对照脚本与 JSON，
禁止覆盖 round3/round4/round5 证据（本文件为 r5v5_station.py 的 round6 独立副本，前缀改为 r6v6_）。

用法：python r6v6_station.py <face>
  face ∈ round2face | probe42 | round1face | residual | oldface | quotation
输出（r6v6_ 前缀，格式对齐 r6v6_compare_regress.py 期望）：
  round2face -> r6v6_regress_round2face.json（tail）
  probe42    -> r6v6_regress_probe42.json（tail）
  round1face -> r6v6_full_round1face.json（full）
  residual   -> r6v6_full_residual_a.json + _b.json（full，对半）
  oldface    -> r6v6_full_oldface_a.json + _b.json（full，对半）
  quotation  -> 单验打印
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
    'oldface': (os.path.join(ROUNDS, 'round3', 'r3v2_oldface_baseline.json'), 'keys'),
}


def pyc_list(face):
    path, kind = BASELINE[face]
    d = json.load(open(path, encoding='utf-8-sig'))
    if kind == 'list':
        return [e['pyc'] for e in d]
    if kind == 'rows':
        return [r['pyc'] for r in d['rows']]
    return list(d.keys())


def run(cmd, timeout=290):
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
        dump(os.path.join(HERE, 'r6v6_quotation.json'), [r])
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
        dump(os.path.join(HERE, 'r6v6_full_%s_a.json' % face), rows[:h])
        dump(os.path.join(HERE, 'r6v6_full_%s_b.json' % face), rows[h:])
        print('-> a=%d b=%d' % (len(rows[:h]), len(rows[h:])))
    elif face == 'round1face':
        dump(os.path.join(HERE, 'r6v6_full_round1face.json'), rows)
    else:
        dump(os.path.join(HERE, 'r6v6_regress_%s.json' % face), rows)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s units=%d/%d' % (face, ok, tot))


if __name__ == '__main__':
    main()