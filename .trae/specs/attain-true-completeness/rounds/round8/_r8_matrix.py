# -*- coding: utf-8 -*-
"""R8: 25 行逐行终审矩阵 —— 每行 1 个深层探针 + 9 个负对照，批跑并落 stamp。"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
os.chdir(ROOT)

STAGE = '.trae/specs/attain-true-completeness/test_repros/round8'
LOG = '.trae/specs/attain-true-completeness/rounds/round8'
RV2 = '.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2'

# (行号, 行名, 深层探针 rel, 负对照名)
MATRIX = [
    (1, 'If', RV2 + '/v_b46_face.pyc', 'r707'),
    (2, 'BoolOp', 'test_repros/round7/r7_12_boolop_nest.pyc', 'r708'),
    (3, 'IfExp', 'test_repros/round7/r7_08_ternary_deep_host.pyc', 'rv801'),
    (4, 'Try', 'test_repros/round2/c04_class_try.pyc', 'rv802'),
    (5, 'Raise', 'test_repros/round8/r8_10_expr_cross_stmt.pyc', 'r806'),
    (6, 'Assert', 'test_repros/round8/r8_07_assert_forms.pyc', 'r1004'),
    (7, 'Import', RV2 + '/v_b73_face.pyc', 'r1015'),
    (8, 'Global', 'test_repros/round10/r10_15_global_hosts.pyc', 'r1021'),
    (9, 'global_nonlocal', 'test_repros/round2/x04_try_deep_hosts.pyc', 'rv1032'),
    (10, 'Await', 'test_repros/round4/c4_20_async_five.pyc', 'r707'),
    (11, 'ListComp', 'test_repros/round7/r7_14_boolop_deep_host.pyc', 'r708'),
    (12, 'await_expr', 'test_repros/round3/e12d_g9_awaits.pyc', 'rv801'),
    (13, 'Yield', 'test_repros/round4/rec1_synth_yf9_ctx.pyc', 'rv802'),
    (14, 'Match', 'test_repros/round5/rec1_synth_b122c_noguard_chain2.pyc', 'r806'),
    (15, 'With', 'test_repros/round2/x05_with_deep_hosts.pyc', 'r1004'),
    (16, 'match_statement', 'test_repros/round2/x01_if_deep_hosts.pyc', 'r1015'),
    (17, 'Break', 'test_repros/round2/x10_handler_hosts.pyc', 'r1021'),
    (18, 'Continue', 'test_repros/round10/r10_21_fin_loopctrl.pyc', 'rv1032'),
    (19, 'While', 'test_repros/round2/x01_if_deep_hosts.pyc', 'r707'),
    (20, 'Delete', 'test_repros/round8/r8_04_delete_forms.pyc', 'r708'),
    (21, 'AugAssign', 'test_repros/round8/r8_06_augassign_ops.pyc', 'rv801'),
    (22, 'Return', 'test_repros/round2/x08_stmt_leaves.pyc', 'rv802'),
    (23, 'Slice', 'test_repros/round3/e07_g4_star_slice_containers.pyc', 'r806'),
    (24, 'augmented_assign', RV2 + '/v_b76_face.pyc', 'r1004'),
    (25, 'slice', 'test_repros/round8/r8v8rev3_b104_exprtail_battery.pyc', 'r1015'),
]

NEG = {
    'r707': 'test_repros/round7/r7_07_ternary_nest.pyc',
    'r708': 'test_repros/round7/r7_08_ternary_deep_host.pyc',
    'rv801': 'test_repros/round8/rv8_01_chain3_subscript.pyc',
    'rv802': 'test_repros/round8/rv8_02_with_tryfin_constret.pyc',
    'r806': 'test_repros/round8/r8_06_augassign_ops.pyc',
    'r1004': 'test_repros/round10/r10_04_import_try_cross.pyc',
    'r1015': 'test_repros/round10/r10_15_global_hosts.pyc',
    'r1021': 'test_repros/round10/r10_21_fin_loopctrl.pyc',
    'rv1032': 'test_repros/round10/rv10_32_augassign_variant.pyc',
}

stamp = sys.argv[1] if len(sys.argv) > 1 else 'r8matrix1'
args = []
for no, line, rel, neg in MATRIX:
    args.append('L%02d=%s' % (no, rel))
for i, (name, rel) in enumerate(sorted(NEG.items())):
    args.append('N%02d=%s' % (i + 1, rel))

cmd = [sys.executable, '-X', 'utf8',
       '.trae/specs/attain-true-completeness/rounds/round1/rec1_run.py',
       '--stage', STAGE, '--log', LOG, '--stamp', stamp] + args
print('probes:', len(args), flush=True)
p = subprocess.run(cmd, cwd=ROOT, encoding='utf-8', errors='replace')
out = p.stdout or ''
print('\n'.join([l for l in out.splitlines() if l.strip()][-40:]))
