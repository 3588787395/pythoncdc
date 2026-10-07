#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round8 位B/位C 复现读数驱动（RV2：先 regen（pycdc -o）再 verify single）。

只读 core/，只写本目录 r8v8fixB_* 证据 JSON。用法：
  python r8v8fixB_repro.py <name1> [name2 ...]   # 跑指定探针
  python r8v8fixB_repro.py --all                  # 跑全部登记探针
输出：r8v8fixB_repro_<stamp>.json（stamp 由调用方经 env R8FB_STAMP 指定，缺省 = reprodump）
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

PROBES = {
    # 位B 目标族
    'B108_main': 'test_repros/round4/c4_06_try_finally_only.pyc',
    'B99_min': 'test_repros/round3/_scratch_b99/b99min.pyc',
    'B104_main': 'test_repros/round4/c4_09_chained_compare.pyc',
    'B105_main': 'test_repros/round4/c4_10_walrus.pyc',
    'B105_call': 'test_repros/round5/r5v5_09_walrus_callsite.pyc',
    'B107_main': 'test_repros/round4/c4_07_multi_target.pyc',
    'B111_main': 'test_repros/round4/c4_19_decorator_args.pyc',
    'B111_cross': 'test_repros/round5/r5v5_12_decorator_cross.pyc',
    'B98_matrix': 'test_repros/round3/e01_g1_b98_matrix.pyc',
    'B98_hosts': 'test_repros/round3/e02_g1_b98_hosts.pyc',
    'B98_resid': 'test_repros/round3/_scratch_b98/resid.pyc',
    'B78_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc',
    'B79_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc',
    'B80_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc',
    'B82_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc',
    'B83_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rvC/rvC_v2.pyc',
    # 位C 目标族
    'B77_face': 'test_repros/round7/r7_08_ternary_deep_host.pyc',
    'B81_face': '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc',
    'B103_main': 'test_repros/round4/c4_04_match_patterns.pyc',
    'B103_guard': 'test_repros/round4/r4v4r_b103_guard.pyc',
    'B102_main': 'test_repros/round4/c4_03_except_star.pyc',
    'B102_except': 'test_repros/round4/r4v4r_b102_except.pyc',
    'B102_deep': 'test_repros/round5/r5v5_14_except_star_deep.pyc',
    'B113_min': 'test_repros/round4/_scratch_m4/comp2.pyc',
    'B113_host': 'test_repros/round4/c4_05_multi_with.pyc',
    'B96_async': 'test_repros/round3/e09b_g6_async_comps.pyc',
    'B112_async': 'test_repros/round4/c4_20_async_five.pyc',
    'B106_main': 'test_repros/round4/c4_12_star_args.pyc',
    'B106_call': 'test_repros/round5/r5v5_07_starargs_callsite.pyc',
    'B106_lam': 'test_repros/round5/r5v5_15_lambda_combo.pyc',
}

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def one(name, rel):
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
    return {'name': name, 'pyc': rel, 'status': status, 'units_success': us,
            'units_total': ut, 'failures': fails}


def main():
    args = sys.argv[1:]
    stamp = os.environ.get('R8FB_STAMP', 'reprodump')
    if args and args[0] == '--all':
        names = list(PROBES)
    else:
        names = args
    rows = []
    for n in names:
        if n not in PROBES:
            print('unknown probe: %s' % n)
            continue
        r = one(n, PROBES[n])
        rows.append(r)
        print('[%-12s] %-8s %s/%s' % (n, r['status'], r['units_success'], r['units_total']), flush=True)
        for f in r['failures']:
            print('    ' + f)
    out = os.path.join(HERE, 'r8v8fixB_repro_%s.json' % stamp)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> units=%d/%d  (%d probes)  %s' % (ok, tot, len(rows), os.path.basename(out)))


if __name__ == '__main__':
    main()
