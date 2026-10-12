#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round7 绔欐々鍥炲綊璇绘暟椹卞姩锛圧V2锛?*鍏?regen锛坧ycdc -o锛夊啀 verify**锛夈€?
鍙 core/锛屽彧鍐欐湰鐩綍 r8v8rev_* 璇佹嵁 JSON銆傚熀绾挎部鐢?round1/round2/round3 宸茶惤鍦扮殑瀵圭収鑴氭湰涓?JSON锛?绂佹瑕嗙洊 round3/round4/round5/round6 璇佹嵁锛堟湰鏂囦欢涓?r6v6_station.py 鐨?round7 鐙珛鍓湰锛屽墠缂€鏀逛负 r8v8rev_锛夈€?
鐢ㄦ硶锛歱ython r8v8rev_station.py <face>
  face 鈭?round2face | probe42 | round1face | residual | oldface | quotation
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
        dump(os.path.join(HERE, 'r8v8rev_quotation.json'), [r])
        return
    plist = pyc_list(face)
    # 鍙€夊垎鐗囧弬鏁帮紙鈮?00s 鍛戒护绾緥锛夛細r8v8rev_station.py <face> a|b 浠呰窇鍗婄墖锛岃惤鐩樺搴?_a/_b JSON
    part = sys.argv[2] if len(sys.argv) > 2 else None
    if part in ('a', 'b'):
        h = (len(plist) + 1) // 2
        plist = plist[:h] if part == 'a' else plist[h:]
    rows = []
    for i, pyc in enumerate(plist, 1):
        r = one(pyc)
        rows.append(r)
        print('[%d/%d] %-9s %s/%s %s' % (i, len(plist), r['status'],
              r['units_success'], r['units_total'], os.path.basename(pyc)), flush=True)
    if face in ('residual', 'oldface'):
        h = (len(plist) + 1) // 2 if part not in ('a', 'b') else len(plist)
        if part == 'a':
            dump(os.path.join(HERE, 'r8v8rev_full_%s_a.json' % face), rows)
        elif part == 'b':
            dump(os.path.join(HERE, 'r8v8rev_full_%s_b.json' % face), rows)
        else:
            dump(os.path.join(HERE, 'r8v8rev_full_%s_a.json' % face), rows[:h])
            dump(os.path.join(HERE, 'r8v8rev_full_%s_b.json' % face), rows[h:])
        print('-> a=%d b=%d' % (h, len(plist) - h))
    elif face == 'round1face':
        dump(os.path.join(HERE, 'r8v8rev_full_round1face.json'), rows)
    else:
        dump(os.path.join(HERE, 'r8v8rev_regress_%s.json' % face), rows)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> %s units=%d/%d' % (face, ok, tot))


if __name__ == '__main__':
    main()
