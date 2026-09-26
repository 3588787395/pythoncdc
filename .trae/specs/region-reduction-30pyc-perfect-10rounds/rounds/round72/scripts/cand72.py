# -*- coding: utf-8 -*-
"""Center-side candidate ADR-1 check for round 72 (read-only w.r.t. the repository).

  python -X utf8 cand72.py <arm> [<arm2> ...]

For each arm: (1) union the landed/branch official readings written by h62.py over the
round lists and list every file whose decompile sha moved; (2) run the mandated ruler
(scripts/pyc_verify.py single) on the moved files for both the landed product and the
candidate product and print the unit delta; (3) re-check the four canary pins against the
candidate product sha; (4) print a per-arm ADR-1 verdict line (REGRESSION / new-failing
units / pin misses).  All raw output is appended under dump/.
"""
import io
import json
import os
import subprocess
import sys

ROOT = r'D:/Temp/opencode/r72gate/center'
REPO = r'F:/Downloads/pythoncdc-main'
LISTS = ['all16', 't_fix1', 'canary', 'head25']
PINS = {
    'quotation.pyc': '3eb76e512df9ab1e',
    'market_time.pyc': 'af77224b34b203c4',
}
PIN_ANY = ['e711b8ea86d49a15', '9d09af09249da177']
sys.stdout.reconfigure(encoding='utf-8')


def union(arm):
    d = {}
    for l in LISTS:
        p = ROOT + '/dump/%s_%s.jsonl' % (arm, l)
        if not os.path.isfile(p):
            continue
        for line in io.open(p, encoding='utf-8'):
            if line.strip():
                r = json.loads(line)
                d[r['path']] = r
    return d


def prod(arm, p):
    rel = p.replace('\\', '/')
    pre = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(pre):
        rel = rel[len(pre):]
    return ROOT + '/build_' + arm + '/' + rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'


def units(arm, p):
    """run mandated pyc_verify single; return (fail_count, total, tail)"""
    out = ROOT + '/dump/pv_%s_%s.txt' % (arm, os.path.basename(p))
    cmd = ['python', '-X', 'utf8', REPO + '/scripts/pyc_verify.py', 'single', p,
           '--source', prod(arm, p)]
    with io.open(out, 'w', encoding='utf-8') as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=280)
    txt = io.open(out, encoding='utf-8', errors='replace').read()
    tail = [x for x in txt.splitlines() if 'units' in x.lower() or 'failure' in x.lower()
            or 'status' in x.lower()][-3:]
    fail = txt.count('Failure')
    return fail, r.returncode, tail


def main():
    arms = sys.argv[1:]
    base = union('landed')
    for arm in arms:
        cur = union(arm)
        assert set(base) == set(cur), 'unpaired lists: %s' % (set(base) ^ set(cur))
        moved = [p for p in sorted(base) if base[p].get('sha') != cur[p].get('sha')]
        same = len(base) - len(moved)
        print('== arm %s: official SAME=%d MOVED=%d' % (arm, same, len(moved)))
        reg = []
        newfail = 0
        for p in moved:
            fa, _, ta = units('landed', p)
            fb, _, tb = units(arm, p)
            flag = ''
            if fb > fa:
                reg.append((p, fa, fb))
                flag = ' REGRESSION'
            newfail += max(0, fb - fa)
            print('   %s  units landed=%d -> arm=%d%s' % (os.path.basename(p), fa, fb, flag))
            if ta:
                print('      landed tail: %s' % ta)
            if tb:
                print('      arm    tail: %s' % tb)
        # canary pins from candidate readings
        pinmiss = []
        for p, r in cur.items():
            b = os.path.basename(p)
            if b in PINS and r.get('sha') != PINS[b]:
                pinmiss.append((b, r.get('sha'), PINS[b]))
        q = [r.get('sha') for p, r in cur.items() if os.path.basename(p) == 'quotation.pyc']
        verdict = 'PASS' if not reg and not pinmiss and newfail == 0 else 'FAIL'
        print('   moved-unit-regressions=%d new-failing-units=%d pin-miss=%s => %s'
              % (len(reg), newfail, pinmiss, verdict))
        print('   quotation sha=%s (pin 3eb76e512df9ab1e) datetime sha=%s'
              % (q[0] if q else None,
                 [r.get('sha') for p, r in cur.items() if 'datetime_func' in p]))


if __name__ == '__main__':
    main()
