# -*- coding: utf-8 -*-
"""R8: 组合级 25 号终表 + 口径差 3 号（B52/B53/B11-R2）实跑，并出逐项判定。"""
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
T = 'test_repros/'

# 组合号 → 探针 rel 列表
COMBOS = [
    ('B46t', [T + 'round7/r7_07_ternary_nest.pyc']),
    ('B48r', [T + 'round7/r7_08_ternary_deep_host.pyc']),
    ('B74', [RV2 + '/v_b74_face.pyc']),
    ('B65', [T + 'round8/rv8_01_chain3_subscript.pyc']),
    ('B71', [RV2 + '/v_b71_face.pyc']),
    ('B73', [T + 'round10/r10_04_import_try_cross.pyc']),
    ('B75', [T + 'round10/r10_15_global_hosts.pyc']),
    ('B76', [RV2 + '/v_b76_face.pyc']),
    ('B50', [RV2 + '/v_b50_face.pyc']),
    ('B42', [T + 'round7/r7_01_ternary_args_index.pyc', T + 'round7/r7_04_ternary_binop_compare.pyc',
             T + 'round7/r7_05_ternary_comprehension.pyc']),
    ('B43', [T + 'round7/r7_10_chain_compare_calls.pyc']),
    ('B44', [T + 'round7/r7_11_boolop_mixed.pyc', T + 'round7/r7_12_boolop_nest.pyc']),
    ('B47', [T + 'round7/r7_06_ternary_lambda_await.pyc']),
    ('B49', [T + 'round7/r7_08_ternary_deep_host.pyc']),
    ('B51', [T + 'round7/rv7_02_compare_chain_ternary.pyc']),
    ('B56', [T + 'round8/r8_07_assert_forms.pyc', T + 'round8/r8_10_expr_cross_stmt.pyc']),
    ('B57', [T + 'round8/r8_10_expr_cross_stmt.pyc']),
    ('B58', [T + 'round8/r8_10_expr_cross_stmt.pyc']),
    ('B59', [T + 'round8/r8_09_deep_host_combo.pyc']),
    ('B60', [T + 'round8/r8_09_deep_host_combo.pyc']),
    ('B61', [T + 'round8/r8_09_deep_host_combo.pyc', T + 'round8/r8_11_deep_host_combo2.pyc']),
    ('B62', [T + 'round7/r7_14_boolop_deep_host.pyc']),
    ('B63', [T + 'round8/rv8_02_with_tryfin_constret.pyc']),
    ('B69', [T + 'round9/rv9_01_b68_nonfin_tail.pyc']),
    ('B70', [T + 'round9/rv9_02_b66_with_nest.pyc']),
    ('B52', [T + 'round7/rv7_02_compare_chain_ternary.pyc']),
    ('B53', [T + 'round7/rv7_04_dict3_ternary.pyc']),
    ('B11R2', [T + 'round4/r4_or4_and2.pyc']),
]

stamp = sys.argv[1] if len(sys.argv) > 1 else 'r8combo1'
args = []
plan = []
for combo, rels in COMBOS:
    for i, rel in enumerate(rels):
        name = '%s_%d' % (combo, i)
        args.append('%s=%s' % (name, rel))
        plan.append((combo, name))

cmd = [sys.executable, '-X', 'utf8',
       '.trae/specs/attain-true-completeness/rounds/round1/rec1_run.py',
       '--stage', STAGE, '--log', LOG, '--stamp', stamp] + args
print('probes:', len(args), flush=True)
subprocess.run(cmd, cwd=ROOT, encoding='utf-8', errors='replace')

path = os.path.join(LOG, 'rec1_probes_%s.json' % stamp)
data = json.load(open(path, encoding='utf-8'))
by_name = {e['name']: e for e in data}
agg = {}
for combo, name in plan:
    e = by_name.get(name)
    if e is None:
        agg.setdefault(combo, [0, 0, []])
        continue
    a = agg.setdefault(combo, [0, 0, []])
    a[0] += e.get('units_success') or 0
    a[1] += e.get('units_total') or 0
    for f in (e.get('failures') or []):
        a[2].append(f.replace('***<module>.', '').split(':')[0])
print('=== combo verdicts ===')
for combo, (s, t, fails) in agg.items():
    print('%-6s %3d/%-3d %s' % (combo, s, t, ('RED: ' + ','.join(fails)) if fails else 'GREEN'))
