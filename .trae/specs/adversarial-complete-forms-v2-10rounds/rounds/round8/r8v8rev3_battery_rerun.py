#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[r8v8rev3] Round8 整改终审 B 部：变体电池 RV2 单验复跑（regen + verify single）。

只读 core/、只写 rounds/round8/r8v8rev3_* 证据 JSON；不覆盖任何既有证据。
用法：python r8v8rev3_battery_rerun.py <group>   # group = main | bmatch
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
PROBES_DIR = os.path.join(ROOT, 'test_repros', 'round8')

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$', re.M)

MAIN = [
    'r8v8rev_b104_chain4_battery',
    'r8v8rev_b105_walrus_battery',
    'r8v8rev_b107_iso_battery',
    'r8v8rev_b107_iso2_battery',
    'r8v8rev_b107_mtarget3_battery',
    'r8v8rev_bmatch_v3',
    'r8v8rev_bmatch_or3iso',
]
BMATCH = [
    'r8v8rev_bmatch_guards_battery',
    'r8v8rev_bmatch_nestnoguard',
    'r8v8rev_bmatch_v1',
    'r8v8rev_bmatch_v4',
]


def run_one(name, regen_timeout=120, verify_timeout=150):
    pyc = os.path.join(PROBES_DIR, name + '.pyc')
    ok = os.path.join(PROBES_DIR, name + 'OK.py')
    rec = {'probe': name}
    try:
        os.remove(ok)
    except OSError:
        pass
    p = subprocess.run([sys.executable, 'pycdc.py', pyc, '-o', ok],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=regen_timeout)
    rec['regen_rc'] = p.returncode
    if p.returncode != 0:
        rec['regen_stderr_tail'] = (p.stderr or '')[-400:]
    ok_exists = os.path.isfile(ok)
    ok_size = os.path.getsize(ok) if ok_exists else 0
    rec['ok_size'] = ok_size
    if not ok_exists or ok_size == 0:
        rec['verify'] = 'SKIPPED (no regen output)'
        return rec
    v = subprocess.run([sys.executable, 'scripts/pyc_verify.py', 'single', pyc],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=verify_timeout)
    m = STAT_RE.search(v.stdout or '')
    if m:
        rec['verify'] = f'status={m.group(1)} units={m.group(2)}/{m.group(3)}'
    else:
        rec['verify'] = 'NOSTAT'
        rec['verify_stdout_tail'] = (v.stdout or '')[-400:]
    fails = FAIL_RE.findall(v.stdout or '')
    if fails:
        rec['fail_units'] = fails[:10]
    return rec


def main():
    group = sys.argv[1] if len(sys.argv) > 1 else 'main'
    names = MAIN if group == 'main' else BMATCH
    results = []
    for n in names:
        try:
            r = run_one(n)
        except subprocess.TimeoutExpired as e:
            r = {'probe': n, 'verify': 'REGEN_TIMEOUT(>%ds) HANG' % (e.timeout or 0)}
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))
        sys.stdout.flush()
    out = os.path.join(HERE, 'r8v8rev3_battery_rerun_%s.json' % group)
    json.dump({'group': group, 'results': results},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('saved', out)


if __name__ == '__main__':
    main()
