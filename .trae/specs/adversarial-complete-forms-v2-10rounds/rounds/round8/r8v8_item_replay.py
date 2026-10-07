#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 8.1 残余破口清单逐项重放核验驱动（RV2：先 regen 后 verify）。
对清单内每项的最小复现探针亲跑 regen+single，读数与登记对照。
输出 r8v8_item_replay.json。只读 core/，只写本目录证据 JSON。"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
SPEC_ROUNDS1 = os.path.join(ROOT, '.trae', 'specs',
                            'adversarial-complete-forms-v2-10rounds', 'rounds', 'round1')
STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')

# B 项 → 最小复现探针（登记出处见 REVIEW.md §3 表）
ITEMS = [
    ('B78', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b46_face.pyc', 'round1 REVIEW2 §5 / round2 REVIEW §2.3'),
    ('B79', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc', 'round1 REVIEW2 §5 / round2 REVIEW §2.3'),
    ('B80', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b73_face.pyc', 'round1 REVIEW2 §5 / round2 REVIEW §2.3'),
    ('B81', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b74_face.pyc', 'round1 REVIEW2 §5 / round2 REVIEW §2.3'),
    ('B82', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b75_face.pyc', 'round1 REVIEW2 §5 / round2 REVIEW §2.3'),
    ('B83', '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rvC/rvC_v2.pyc', 'round1 REVIEW3 §2 / round2 REVIEW §2.3'),
    ('B98-face', 'test_repros/round3/e01_g1_b98_matrix.pyc', 'round3 REVIEW §4.1'),
    ('B98-face2', 'test_repros/round3/e02_g1_b98_hosts.pyc', 'round3 REVIEW §4.1'),
    ('B98-min', 'test_repros/round3/_scratch_b98/resid.pyc', 'round3 REVIEW §4.1'),
    ('B99-min', 'test_repros/round3/_scratch_b99/b99min.pyc', 'round3 REVIEW §4.1'),
    ('B96', 'test_repros/round3/e09b_g6_async_comps.pyc', 'round3 REVIEW §4.2（round2 B96 承接）'),
    ('B109-residual', 'test_repros/round4/c4_02_loop_else.pyc', 'round4 REVIEW §4.1 / REVIEW2 §4.1'),
    ('B109-residual2', 'test_repros/round4/r4v4r_b109_loopelse.pyc', 'round4 REVIEW2 §4.1'),
    ('B102', 'test_repros/round4/c4_03_except_star.pyc', 'round4 REVIEW §4.1'),
    ('B102-residual', 'test_repros/round4/r4v4r_b102_except.pyc', 'round4 REVIEW2 §4.1'),
    ('B102-residual5', 'test_repros/round5/r5v5_14_except_star_deep.pyc', 'round5 REVIEW §3'),
    ('B103', 'test_repros/round4/c4_04_match_patterns.pyc', 'round4 REVIEW §4.1'),
    ('B103-residual', 'test_repros/round4/r4v4r_b103_guard.pyc', 'round4 REVIEW2 §4.1'),
    ('B110', 'test_repros/round4/c4_05_multi_with.pyc', 'round4 REVIEW §4.1'),
    ('B108', 'test_repros/round4/c4_06_try_finally_only.pyc', 'round4 REVIEW §4.1'),
    ('B107', 'test_repros/round4/c4_07_multi_target.pyc', 'round4 REVIEW §4.1'),
    ('B104', 'test_repros/round4/c4_09_chained_compare.pyc', 'round4 REVIEW §4.1'),
    ('B105', 'test_repros/round4/c4_10_walrus.pyc', 'round4 REVIEW §4.1'),
    ('B105-residual5', 'test_repros/round5/r5v5_09_walrus_callsite.pyc', 'round5 REVIEW §3'),
    ('B106', 'test_repros/round4/c4_12_star_args.pyc', 'round4 REVIEW §4.1'),
    ('B106-residual5', 'test_repros/round5/r5v5_07_starargs_callsite.pyc', 'round5 REVIEW §3'),
    ('B113', 'test_repros/round4/c4_18_nested_comprehension.pyc', 'round4 REVIEW §4.1'),
    ('B113-min', 'test_repros/round4/_scratch_m4/comp2.pyc', 'round4 REVIEW §4.1 最小复现'),
    ('B111', 'test_repros/round4/c4_19_decorator_args.pyc', 'round4 REVIEW §4.1'),
    ('B111-residual5', 'test_repros/round5/r5v5_12_decorator_cross.pyc', 'round5 REVIEW §3'),
    ('B112', 'test_repros/round4/c4_20_async_five.pyc', 'round4 REVIEW §4.1'),
    ('B121', 'test_repros/round7/r7v7r_b121_whilehdr.pyc', 'round7 REVIEW2 §4.2'),
    ('B121-secondary', 'test_repros/round7/r7v7r_b117_f2tail.pyc', 'round7 REVIEW2 §4.2'),
    ('B117-closed-confirm', 'test_repros/round7/r7v7_b2b04.pyc', 'round7 REVIEW §3.1 / REVIEW2 §3a'),
    ('B117-closed-confirm2', 'test_repros/round7/r7v7_x_b2b04_d2.pyc', 'round7 REVIEW2 §3a'),
    ('B118-closed-confirm', 'test_repros/round7/r7v7_b2c03.pyc', 'round7 REVIEW §3.1 / REVIEW2 §3a'),
    ('B118-closed-confirm2', 'test_repros/round7/r7v7_x_b2c03_pure.pyc', 'round7 REVIEW2 §3a'),
    ('B119-closed-confirm', 'test_repros/round7/r7v7_b4a03.pyc', 'round7 REVIEW §3.3 / REVIEW2 §3a'),
    ('B119-closed-confirm2', 'test_repros/round7/r7v7_x_b4a03_pure.pyc', 'round7 REVIEW2 §3a'),
    ('B120-closed-confirm', 'test_repros/round7/r7v7_b4c03.pyc', 'round7 REVIEW §3.3 / REVIEW2 §3a'),
    ('B114-closed-confirm', 'test_repros/round5/r5v5_01_module_root.pyc', 'round5 REVIEW2 §2.1'),
    ('B115-closed-confirm', 'test_repros/round5/r5v5_08_slice_callsite.pyc', 'round5 REVIEW2 §2.1'),
    ('B116-closed-confirm', 'test_repros/round5/r5v5_03_annassign.pyc', 'round5 REVIEW2 §2.1'),
]


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def one(rel):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'), 'single', full])
    tail = [l for l in out.splitlines() if l.strip()]
    status, us, ut = None, None, None
    for line in tail:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in tail if FAIL_RE.match(l)]
    ce = 'COMPILE_ERROR' in out or any('compile' in l.lower() and 'error' in l.lower() for l in tail)
    return {'pyc': rel, 'status': status, 'units_success': us, 'units_total': ut,
            'failures': fails, 'compile_error_hint': ce, 'tail': tail[-6:]}


def main():
    rows = []
    for i, (bid, rel, src) in enumerate(ITEMS, 1):
        r = one(rel)
        r['item'] = bid
        r['registration'] = src
        rows.append(r)
        print('[%d/%d] %-22s %-9s %s/%s %s' % (i, len(ITEMS), bid, r['status'],
              r['units_success'], r['units_total'], os.path.basename(rel)), flush=True)
    with open(os.path.join(HERE, 'r8v8_item_replay.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> dumped r8v8_item_replay.json (%d rows)' % len(rows))


if __name__ == '__main__':
    main()
