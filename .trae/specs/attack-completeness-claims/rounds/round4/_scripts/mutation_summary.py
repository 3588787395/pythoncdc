#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：汇总变异测试读数（按族：mutated / missed / miss-rate）。

判据口径（与 `scripts/pyc_verify.py::evaluate` 同一代码路径）：
  status == 'success'      => **漏检 MISS**（产物语义已错，判据仍判绿）
  status == 'failure'      => 捕获 CAUGHT
  status == 'compile_error'=> 变异产物不可编译（非语义捕获，单列 INVALID）
  status == 'error'        => 判据异常（单列 JUDGE_ERROR）
  'NA'                     => 该产物不适用此变异族（不计入分母）

用法：
  python -X utf8 mutation_summary.py [--json out.json] [--jsonl <file>]
"""
from __future__ import annotations

import argparse
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))

FAM_LABEL = {
    'a_num_int': '(a) 数值字面量 1->2',
    'b_cmp_polarity': '(b) 比较极性 a<b -> a>b',
    'c_del_assign': '(c) 删一条赋值语句',
    'd_int_to_bool': '(d) x=1 -> x=True（纯类型变，值不变）',
    'd_any_int_to_bool': "(d') 任意整数 -> True（类型+可能改值，对照用）",
    'e_str_content': '(e) 改字符串字面量内容',
    'f_stmt_swap': '(f) 交换两条独立语句顺序',
    'g_rename_local': '(g) 改局部标识符名（未被使用时）',
    'g_used_local': "(g') 改被使用的局部标识符名",
    'g2_rename_func': '(g2) 改函数名',
    'h_arg_swap': '(h) 交换两个实参顺序',
    'h_param_order': "(h') 交换两个形参顺序",
    'i_int_to_float': '(i) x=1 -> x=1.0',
    'j_func_docstring': '(j) 改函数 docstring',
    'k_posonly': '(k) 去位置限定符 /',
    'l_except_tuple': '(l) except X -> except (X,)',
    'm_ann_local': '(m) 改函数内局部注解',
    'n_dead_code': '(n) 插入不可达语句',
    'o_handler_body': '(o) 改 handler 体返回值',
    'p_except_type': '(p) 改 except 的异常类型',
    's_decorator_swap': '(s) 交换两个装饰器顺序',
    't_fstring_spec': '(t) 改 f-string 转换/格式说明',
    'u_ann_param': '(u) 改形参注解',
    'v_lambda_default': '(v) 改 lambda 默认值',
    'w_global_stmt': '(w) 插入 global 声明',
    'x_module_docstring': '(x) 改模块 docstring',
    'z_assert_msg': '(z) 改 assert 消息',
}

REQUIRED = ['a_num_int', 'b_cmp_polarity', 'c_del_assign', 'd_int_to_bool',
            'e_str_content', 'f_stmt_swap', 'g_rename_local', 'h_arg_swap']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', default=os.path.join(ROUND4, '_out', 'mutation_summary.json'))
    ap.add_argument('--jsonl', default=os.path.join(ROUND4, '_out', 'mutation_results.jsonl'))
    args = ap.parse_args()

    rows = []
    seen = set()
    with open(args.jsonl, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r['pyc'], r['family'])
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)

    base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
    green = {p for p, r in base.items() if r['status'] == 'success'}
    print('corpus baseline rows = %d ; baseline green = %d ; non-green = %d'
          % (len(base), len(green), len(base) - len(green)))

    stat = collections.defaultdict(collections.Counter)
    misses = collections.defaultdict(list)
    for r in rows:
        if r['family'] == 'BASELINE':
            continue
        if r['pyc'] not in green:
            continue
        st = r['status']
        stat[r['family']]['NA' if st == 'NA' else st] += 1
        if st == 'success':
            stat[r['family']]['MISS'] += 1
            misses[r['family']].append(r)

    order = list(FAM_LABEL)
    fams = sorted(stat.keys(), key=lambda f: order.index(f) if f in order else 999)
    print()
    print('%-20s %8s %8s %8s   %s' % ('family', 'mutated', 'missed', 'rate', 'other'))
    tot_mut = tot_miss = 0
    req_mut = req_miss = 0
    rows_out = []
    for f in fams:
        c = stat[f]
        mutated = c['MISS'] + c['failure'] + c['compile_error'] + c['error']
        missed = c['MISS']
        rate = (missed / mutated) if mutated else 0.0
        other = dict((k, v) for k, v in c.items()
                     if k not in ('MISS', 'failure', 'compile_error', 'error'))
        print('%-20s %8d %8d %7.2f%%   %s'
              % (f, mutated, missed, 100 * rate, other))
        tot_mut += mutated
        tot_miss += missed
        if f in REQUIRED:
            req_mut += mutated
            req_miss += missed
        rows_out.append({'family': f, 'label': FAM_LABEL.get(f, f),
                         'required': f in REQUIRED,
                         'mutated': mutated, 'missed': missed,
                         'miss_rate': round(rate, 4),
                         'caught_failure': c['failure'], 'compile_error': c['compile_error'],
                         'judge_error': c['error'], 'na': c['NA'],
                         'miss_examples': [m['pyc'] for m in misses[f][:8]]})
    print()
    print('REQUIRED-8  mutated=%d missed=%d miss-rate=%.2f%%'
          % (req_mut, req_miss, 100 * req_miss / max(1, req_mut)))
    print('ALL-FAMILY  mutated=%d missed=%d miss-rate=%.2f%%'
          % (tot_mut, tot_miss, 100 * tot_miss / max(1, tot_mut)))

    with open(args.json, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'baseline_total': len(base), 'baseline_green': len(green),
                   'required_families': REQUIRED,
                   'families': rows_out,
                   'required_total_mutated': req_mut, 'required_total_missed': req_miss,
                   'required_miss_rate': round(req_miss / max(1, req_mut), 4),
                   'total_mutated': tot_mut, 'total_missed': tot_miss,
                   'overall_miss_rate': round(tot_miss / max(1, tot_mut), 4)},
                  f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('-> %s' % args.json)


if __name__ == '__main__':
    main()
