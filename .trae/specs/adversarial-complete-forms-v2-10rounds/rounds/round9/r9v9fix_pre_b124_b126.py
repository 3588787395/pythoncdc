#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 续作二段 before 读数：B124 双桶 / B125 / B126 / B123 靶面现值。

RV2：regen 到临时产物再 verify --source（不写 *OK.py，避免 M 态堆积）。
用法：python -X utf8 r9v9fix_pre_b124_b126.py [name ...]   # 缺省全跑
证据：r9v9fix_pre_b124_b126.json。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
OUT = os.path.join(HERE, 'r9v9fix_pre_b124_b126.json')
TMPOUT = r'D:\Temp\opencode\r92_products'

TARGETS = [
    # B124 分析器桶（e05×3 + c4_09::CCMP.m）
    ('e05_g3_compare_chain', 'test_repros/round3/e05_g3_compare_chain.pyc'),
    ('c4_09_chained_compare', 'test_repros/round4/c4_09_chained_compare.pyc'),
    # B124 生成器桶（e10::f_call_ternary_arg + r8_10::r8_x_with_ternary）
    ('e10_g7_call_args', 'test_repros/round3/e10_g7_call_args.pyc'),
    ('r8_10_expr_cross_stmt', 'test_repros/round8/r8_10_expr_cross_stmt.pyc'),
    # B125（b109::nested_loop_else + r5_13::fe_while_deep）
    ('r4v4r_b109_loopelse', 'test_repros/round4/r4v4r_b109_loopelse.pyc'),
    ('r5v5_13_for_else_cross', 'test_repros/round5/r5v5_13_for_else_cross.pyc'),
    # B126（n9_stmt_sweep::assert_deep）
    ('n9v9_stmt_sweep', 'test_repros/round9/n9v9_stmt_sweep.pyc'),
    # B123（exprtail 电池 v3 存量）
    ('b104_exprtail_battery', 'test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc'),
    # B125 门禁对照面（REVIEW §6 位B 门禁：c4_02 14/14 + r9_01/09/10）
    ('c4_02_loop_else', 'test_repros/round4/c4_02_loop_else.pyc'),
    ('r9_01_b2_cont_loopelse', 'test_repros/round9/r9_01_b2_cont_loopelse.pyc'),
    ('r9_09_b55_boundary', 'test_repros/round9/r9_09_b55_boundary.pyc'),
    ('r9_10_b2b3_shrink', 'test_repros/round9/r9_10_b2b3_shrink.pyc'),
]

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\*{3}(\S+): (.*)$', re.M)


def run(cmd, timeout=250):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -1, 'TIMEOUT'


def one(name, rel):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    os.makedirs(TMPOUT, exist_ok=True)
    ok = os.path.join(TMPOUT, name + '_prod.py')
    rc, _ = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    _, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                  'single', full, '--source', ok])
    status, us, ut = None, None, None
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = FAIL_RE.findall(out)
    return {'name': name, 'pyc': rel, 'regen_rc': rc, 'status': status,
            'units_success': us, 'units_total': ut, 'failures': fails}


def main():
    only = set(sys.argv[1:])
    rows = []
    for name, rel in TARGETS:
        if only and name not in only:
            continue
        r = one(name, rel)
        rows.append(r)
        print('[%-22s] %-8s %s/%s fails=%d' % (name, r['status'], r['units_success'],
                                                r['units_total'], len(r['failures'])), flush=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> ' + os.path.basename(OUT))


if __name__ == '__main__':
    main()
