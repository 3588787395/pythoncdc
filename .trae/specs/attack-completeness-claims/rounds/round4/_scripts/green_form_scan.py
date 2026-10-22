#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**「绿但形态错」**的量化扫描。

在 416 个被判绿的产物上，统计 judge **无法察觉**的形态损失：
  * 模块级多余 `global` / `nonlocal` 语句（pycdc 发射，模块级为 no-op，字节码零差异）
  * 函数级局部注解丢失（PEP 526 局部注解运行时不求值 → 字节码零差异）
  * 函数 docstring 的值类型（co_consts[0]，无指令引用 → 字节码零差异）
  * 常量 **类型** 漂移（int vs float：值相等但类型不同）
并给出「判据能否察觉」的判定。

用法： python -X utf8 green_form_scan.py
"""
from __future__ import annotations

import ast
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
JSONL = os.path.join(ROUND4, '_out', 'mutation_results.jsonl')


def main():
    rows = []
    seen = set()
    for line in open(JSONL, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        k = (r['pyc'], r['family'])
        if k in seen:
            continue
        seen.add(k)
        rows.append(r)
    base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
    green = sorted(p for p, r in base.items() if r['status'] == 'success')

    stat = collections.Counter()
    examples = collections.defaultdict(list)
    for pyc in green:
        prod = pyc[:-4] + 'OK.py'
        if not os.path.isfile(prod):
            continue
        try:
            tree = ast.parse(open(prod, 'rb').read())
        except SyntaxError:
            stat['not_parseable'] += 1
            continue
        stat['scanned'] += 1
        # 模块级 global/nonlocal（pycdc 的多余发射）
        for n in tree.body:
            if isinstance(n, ast.Global):
                stat['module_level_global'] += 1
                examples['module_level_global'].append(pyc)
                break
        # 局部注解（PEP 526，运行时不求值）
        has_local_ann = False
        for n in ast.walk(tree):
            if isinstance(n, ast.AnnAssign):
                has_local_ann = True
                break
        if has_local_ann:
            stat['has_local_annotation'] += 1
            examples['has_local_annotation'].append(pyc)
        # 函数 docstring
        for h in ast.walk(tree):
            if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
                b = getattr(h, 'body', [])
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                        and isinstance(b[0].value.value, str):
                    stat['has_func_docstring'] += 1
                    examples['has_func_docstring'].append(pyc)
                    break
        # 常量类型
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, float):
                stat['has_float_const'] += 1
                examples['has_float_const'].append(pyc)
                break

    print('scanned green products = %d' % stat['scanned'])
    for k in ('module_level_global', 'has_local_annotation', 'has_func_docstring', 'has_float_const'):
        print('  %-24s %4d  (%.1f%%)  e.g. %s'
              % (k, stat[k], 100.0 * stat[k] / max(1, stat['scanned']),
                 (examples[k][0] if examples[k] else '-')))

    out = {'scanned': stat['scanned'],
           'module_level_global': stat['module_level_global'],
           'has_local_annotation': stat['has_local_annotation'],
           'has_func_docstring': stat['has_func_docstring'],
           'has_float_const': stat['has_float_const'],
           'examples': {k: v[:5] for k, v in examples.items()}}
    with open(os.path.join(ROUND4, '_out', 'green_form_scan.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('-> _out/green_form_scan.json')


if __name__ == '__main__':
    main()
