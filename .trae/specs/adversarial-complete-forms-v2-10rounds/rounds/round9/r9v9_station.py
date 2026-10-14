#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round9 站桩回归读数驱动（RV2：先 regen（pycdc -o）再 verify）。

只读 core/，只写本目录 r9v9_* 证据 JSON（round9 独立副本，禁覆盖 round8 证据）。
基线 = Round 8 终态：round1face 417/423、round2face 239/251、probe42 177/196、
residual 419/446、oldface 665/692、quotation 152/153。

用法：python r9v9_station.py <face> [a|b]
  face ∈ round2face | probe42 | round1face | residual | oldface | quotation
  a|b = 半片分跑（全 face 超时纪律用；residual/oldface 默认必须分片）
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
        dump(os.path.join(HERE, 'r9v9_quotation.json'), [r])
        return
    plist = pyc_list(face)
    part = sys.argv[2] if len(sys.argv) > 2 else None
    if part in ('a', 'b'):
        h = (len(plist) + 1) // 2
        plist = plist[:h] if part == 'a' else plist[h:]
    elif part and part.startswith('c'):
        # cN:M = 切片（0 基、含首不含尾），用于 300s 分片纪律
        lo_s, hi_s = part[1:].split(':')
        plist = plist[int(lo_s):int(hi_s)]
        part = part.replace(':', '-')
    rows = []
    outpath = None
    if part:
        if face in ('residual', 'oldface', 'round1face'):
            outpath = os.path.join(HERE, 'r9v9_full_%s_%s.json' % (face, part))
        else:
            outpath = os.path.join(HERE, 'r9v9_regress_%s_%s.json' % (face, part))
    for i, pyc in enumerate(plist, 1):
        r = one(pyc)
        rows.append(r)
        print('[%d/%d] %-9s %s/%s %s' % (i, len(plist), r['status'],
              r['units_success'], r['units_total'], os.path.basename(pyc)), flush=True)
        if outpath:
            dump(outpath, rows)  # 增量落盘：超时也保住已测读数
    suffix = ('_%s' % part) if part else ''
    if face in ('residual', 'oldface', 'round1face'):
        dump(os.path.join(HERE, 'r9v9_full_%s%s.json' % (face, suffix)), rows)
    else:
        dump(os.path.join(HERE, 'r9v9_regress_%s%s.json' % (face, suffix)), rows)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s%s units=%d/%d' % (face, suffix, ok, tot))


if __name__ == '__main__':
    main()
