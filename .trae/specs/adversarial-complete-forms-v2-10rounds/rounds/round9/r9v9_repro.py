#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round9 复验读数驱动（RV2：先 regen（pycdc -o）再 verify single）。

只读 core/，只写本目录 r9v9_* 证据 JSON（round9 独立副本，禁覆盖 round8 证据）。
用法：
  python r9v9_repro.py <name1> [name2 ...]   # 跑指定探针
  python r9v9_repro.py --all                  # 跑全部 31 登记探针（= r8v8fixB_repro.py 同集）
输出：r9v9_repro_<stamp>.json（stamp 由 env R9V9_STAMP 指定，缺省 = reprodump）
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

PROBES = {
    # round8 位B 目标族（31 登记探针，与 r8v8fixB_repro.py 逐项同集）
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
    # round8 位C 目标族
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
    # ==== round9 抽验扩展（round2-8 各主题面代表探针 + 移交/残余面）====
    # round2 表A 深层宿主 + 零专攻（Module/ClassDef）
    'r2_x01_if_deep': 'test_repros/round2/x01_if_deep_hosts.pyc',
    'r2_x08_stmt_leaves': 'test_repros/round2/x08_stmt_leaves.pyc',
    'r2_x09_funcdef_hosts': 'test_repros/round2/x09_funcdef_hosts.pyc',
    'r2_m09_module_deep': 'test_repros/round2/m09_module_deep_cross.pyc',
    'r2_c12_class_deep': 'test_repros/round2/c12_class_deep_cross.pyc',
    'r2_x04_try_deep': 'test_repros/round2/x04_try_deep_hosts.pyc',
    'r2_x06_match_deep': 'test_repros/round2/x06_match_deep_hosts.pyc',
    # round3 表B 28 探针代表
    'r3_e05_compare_chain': 'test_repros/round3/e05_g3_compare_chain.pyc',
    'r3_e06_op_leaves': 'test_repros/round3/e06_g3_op_leaves.pyc',
    'r3_e07_star_slice': 'test_repros/round3/e07_g4_star_slice_containers.pyc',
    'r3_e08_lambda_deep': 'test_repros/round3/e08_g5_lambda_deep.pyc',
    'r3_e09_comprehensions': 'test_repros/round3/e09_g6_comprehensions.pyc',
    'r3_e10_call_args': 'test_repros/round3/e10_g7_call_args.pyc',
    'r3_e11_fstrings': 'test_repros/round3/e11_g8_fstrings.pyc',
    'r3_e12d_awaits': 'test_repros/round3/e12d_g9_awaits.pyc',
    'r3_e12e_yield_from': 'test_repros/round3/e12e_g9_yield_from.pyc',
    'r3_e12g_await_yield': 'test_repros/round3/e12_g9_await_yield.pyc',
    # round4 表C 20 形态族（31 面未含者）
    'r4_c4_01_elif': 'test_repros/round4/c4_01_elif_chain.pyc',
    'r4_c4_02_loopelse': 'test_repros/round4/c4_02_loop_else.pyc',
    'r4_c4_08_augassign': 'test_repros/round4/c4_08_augassign.pyc',
    'r4_c4_11_keyword': 'test_repros/round4/c4_11_keyword_args.pyc',
    'r4_c4_13_slice': 'test_repros/round4/c4_13_slice.pyc',
    'r4_c4_14_relative': 'test_repros/round4/c4_14_relative_import.pyc',
    'r4_c4_15_star_import': 'test_repros/round4/c4_15_star_import.pyc',
    'r4_c4_16_global': 'test_repros/round4/c4_16_global_nonlocal.pyc',
    'r4_c4_17_fstring': 'test_repros/round4/c4_17_fstring_conv.pyc',
    'r4_c4_18_nested_comp': 'test_repros/round4/c4_18_nested_comprehension.pyc',
    'r4_b100_levels': 'test_repros/round4/r4v4r_b100_levels.pyc',
    'r4_b101_star': 'test_repros/round4/r4v4r_b101_star.pyc',
    'r4_b109_loopelse': 'test_repros/round4/r4v4r_b109_loopelse.pyc',
    # round5 交叉矩阵 + 零专攻（AnnAssign 等）
    'r5_01_module_root': 'test_repros/round5/r5v5_01_module_root.pyc',
    'r5_02_class_body': 'test_repros/round5/r5v5_02_class_body.pyc',
    'r5_03_annassign': 'test_repros/round5/r5v5_03_annassign.pyc',
    'r5_04_elif_cross': 'test_repros/round5/r5v5_04_elif_cross.pyc',
    'r5_06_keywordargs': 'test_repros/round5/r5v5_06_keywordargs_callsite.pyc',
    'r5_08_slice_callsite': 'test_repros/round5/r5v5_08_slice_callsite.pyc',
    'r5_10_fstring_cross': 'test_repros/round5/r5v5_10_fstring_cross.pyc',
    'r5_11_global_nonlocal': 'test_repros/round5/r5v5_11_global_nonlocal_cross.pyc',
    'r5_13_for_else_cross': 'test_repros/round5/r5v5_13_for_else_cross.pyc',
    'r5_b115_battery': 'test_repros/round5/r5v5r_b115_if_while.pyc',
    'r5_b116_bare': 'test_repros/round5/r5v5r_b116_bare.pyc',
    # round6 With/async 族
    'r6_09_with_multimgr': 'test_repros/round6/r6_09_with_multimgr.pyc',
    'r6_15_yield_forms': 'test_repros/round6/r6_15_yield_forms.pyc',
    'r6_05_asyncwith_basic': 'test_repros/round6/r6_05_asyncwith_basic.pyc',
    # round7 守卫族代表
    'r7_b2a01': 'test_repros/round7/r7v7_b2a01.pyc',
    'r7_b3a01': 'test_repros/round7/r7v7_b3a01.pyc',
    'r7_b4c03': 'test_repros/round7/r7v7_b4c03.pyc',
    'r7_b121_whilehdr': 'test_repros/round7/r7v7r_b121_whilehdr.pyc',
    'r7_b117_f2tail': 'test_repros/round7/r7v7r_b117_f2tail.pyc',
    # round8 变体/电池面（REVIEW2 §3/§8 声称域）
    'r8_b102_battery': 'test_repros/round8/r8v8fc_b102_battery.pyc',
    'r8_b96_battery': 'test_repros/round8/r8v8fc_b96_async_battery.pyc',
    'r8_b113_flat_battery': 'test_repros/round8/r8v8fc_b113_flat_battery.pyc',
    'r8_b106_star_battery': 'test_repros/round8/r8v8fc_b106_star_battery.pyc',
    'r8_b102_2eselsefin': 'test_repros/round8/r8v8rev_b102_2eselsefin.pyc',
    'r8_b106_mixed': 'test_repros/round8/r8v8rev_b106_mixed_battery.pyc',
    'r8_b113_doubfor': 'test_repros/round8/r8v8rev_b113_doubfor_battery.pyc',
    'r8_b104_chain4': 'test_repros/round8/r8v8rev_b104_chain4_battery.pyc',
    'r8_b105_walrus': 'test_repros/round8/r8v8rev_b105_walrus_battery.pyc',
    'r8_b107_iso': 'test_repros/round8/r8v8rev_b107_iso_battery.pyc',
    'r8_b107_iso2': 'test_repros/round8/r8v8rev_b107_iso2_battery.pyc',
    'r8_b107_mtarget3': 'test_repros/round8/r8v8rev_b107_mtarget3_battery.pyc',
    'r8_bmatch_or3iso': 'test_repros/round8/r8v8rev_bmatch_or3iso.pyc',
    'r8_bmatch_v1': 'test_repros/round8/r8v8rev_bmatch_v1.pyc',
    'r8_bmatch_v3': 'test_repros/round8/r8v8rev_bmatch_v3.pyc',
    'r8_bmatch_v4': 'test_repros/round8/r8v8rev_bmatch_v4.pyc',
    'r8_bmatch_or4': 'test_repros/round8/r8v8rev3_bmatch_or4_battery.pyc',
    'r8_b104_chain5': 'test_repros/round8/r8v8rev3_b104_chain5_battery.pyc',
    'r8_b104_foror': 'test_repros/round8/r8v8rev3_b104_foror_battery.pyc',
    'r8_b104_opdeep': 'test_repros/round8/r8v8rev3_b104_opdeep_battery.pyc',
    'r8_b104_exprtail': 'test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc',
    'r8_b105_walrus3': 'test_repros/round8/r8v8rev3_b105_walrus3_battery.pyc',
    'r8_b107_mixed4': 'test_repros/round8/r8v8rev3_b107_mixed4_battery.pyc',
    'r8_b81_t2_wildguard': 'test_repros/round8/r8v8fc_b81_t2_wildguard.pyc',
    'r8_b103_or_variants': 'test_repros/round8/r8v8fc_b103_or_variants.pyc',
    # round9 新探针（本轮构建，test_repros/round9/）
    'n9_b104_whilehost': 'test_repros/round9/n9v9_b104_whilehost.pyc',
    'n9_stmt_sweep': 'test_repros/round9/n9v9_stmt_sweep.pyc',
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


def one(name, rel, regen_timeout=120):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    rc_regen, _ = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok],
                      timeout=regen_timeout)
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', full])
    tail = [l for l in out.splitlines() if l.strip()]
    status, us, ut = None, None, None
    for line in tail:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in tail if FAIL_RE.match(l)]
    return {'name': name, 'pyc': rel, 'regen_rc': rc_regen, 'status': status,
            'units_success': us, 'units_total': ut, 'failures': fails}


def main():
    args = sys.argv[1:]
    stamp = os.environ.get('R9V9_STAMP', 'reprodump')
    if args and args[0] == '--all':
        names = [n for n in PROBES if not n.startswith(('r2_', 'r3_', 'r4_', 'r5_',
                                                        'r6_', 'r7_', 'r8_', 'n9_'))]
    else:
        names = args
    rows = []
    for n in names:
        if n not in PROBES:
            print('unknown probe: %s' % n)
            continue
        r = one(n, PROBES[n])
        rows.append(r)
        print('[%-24s] regen_rc=%s %-8s %s/%s' % (n, r['regen_rc'], r['status'],
              r['units_success'], r['units_total']), flush=True)
        for f in r['failures']:
            print('    ' + f)
    out = os.path.join(HERE, 'r9v9_repro_%s.json' % stamp)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> units=%d/%d  (%d probes)  %s' % (ok, tot, len(rows), os.path.basename(out)))


if __name__ == '__main__':
    main()
