#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**跨作用域覆盖缺口量化**（§5）。

对每个「记录在案的绿产物」计算**装配层特征**（跨函数 / 模块级 / 类级 / 闭包 / 装饰器），
再与变异测试读数交叉，量化：判据在这些装配层上的漏检率。

特征（从**产物源码** AST + **原始 pyc** 的 code object 数计算）：
  multi_func     : 模块内函数定义数 ≥2
  module_stmt    : 模块体有非 def/class/import 的语句（模块级装配）
  class_level    : 存在类定义
  closure        : 存在「嵌套函数引用外层函数局部变量」⇒ 真实闭包捕获
  decorator      : 存在装饰器
  n_codeobj      : 原始 pyc 的 code object 数（1 = 单元级；>1 = 嵌套/跨函数装配）

用法：
  python -X utf8 coverage_scope.py [--jsonl <mutation_results.jsonl>] [--json out.json]
"""
from __future__ import annotations

import argparse
import ast
import collections
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')

sys.path.insert(0, HERE)
import mutation_experiment  # noqa: E402

FEATURES = ['multi_func', 'module_stmt', 'class_level', 'closure', 'decorator']


def features_of(src_path):
    """返回特征字典；解析失败则返回 None。"""
    try:
        tree = ast.parse(open(src_path, 'rb').read())
    except Exception:
        return None
    funcs = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    module_stmt = any(not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                          ast.ClassDef, ast.Import, ast.ImportFrom))
                      for n in tree.body)
    decorator = any(getattr(h, 'decorator_list', None) for h in funcs + classes)

    # 闭包：嵌套函数体内出现「仅由外层函数绑定」的局部名
    closure = False
    for f in funcs:
        outer_bound = set()
        for n in ast.walk(f):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                outer_bound.add(n.id)
        for inner in ast.walk(f):
            if not isinstance(inner, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if inner is f:
                continue
            inner_bound = {n.id for n in ast.walk(inner)
                           if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
            for n in ast.walk(inner):
                if (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                        and n.id in outer_bound and n.id not in inner_bound):
                    closure = True
                    break
            if closure:
                break
        if closure:
            break
    return {'multi_func': len(funcs) >= 2,
            'module_stmt': module_stmt,
            'class_level': bool(classes),
            'closure': closure,
            'decorator': decorator,
            'n_func': len(funcs)}


def n_codeobj(pyc_path):
    """原始 pyc 的 code object 数（不依赖附件，用 marshal 直读）。"""
    import marshal
    try:
        with open(pyc_path, 'rb') as f:
            data = f.read()
        n = 16                       # py3.7+ 头：magic(4)+flags(4)+mtime(4)+size(4)
        code = marshal.loads(data[n:])
    except Exception:
        return None
    cnt = 0

    def walk(c):
        nonlocal cnt
        cnt += 1
        for k in c.co_consts:
            if hasattr(k, 'co_code'):
                walk(k)
    walk(code)
    return cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonl', default=os.path.join(OUT, 'mutation_results.jsonl'))
    ap.add_argument('--json', default=os.path.join(OUT, 'coverage_scope.json'))
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

    feats = {}
    for tag, pyc, prod in mutation_experiment.corpus_from_stamps():
        if pyc not in green:
            continue
        if prod not in feats:
            f = features_of(prod)
            if f is None:
                continue
            f['n_codeobj'] = n_codeobj(pyc)
            feats[pyc] = f
    print('green corpus with features: %d / %d' % (len(feats), len(green)))

    # 语料特征分布
    dist = {k: sum(1 for f in feats.values() if f.get(k)) for k in FEATURES}
    dist['multi_codeobj'] = sum(1 for f in feats.values()
                                if (f.get('n_codeobj') or 1) > 1)
    print('corpus feature distribution:', dist)

    # 每族 × 特征的 漏检率：stat[scope][family][status]
    stat = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for r in rows:
        if r['family'] == 'BASELINE' or r['pyc'] not in green or r['pyc'] not in feats:
            continue
        st = r['status']
        if st == 'NA':
            continue
        f = feats[r['pyc']]
        scopes = ['ALL'] + [k for k in FEATURES if f.get(k)]
        for sc in scopes:
            stat[sc][r['family']][st] += 1
            stat[sc][r['family']]['mutated'] += 1
            if st == 'success':
                stat[sc][r['family']]['MISS'] += 1

    out = {'corpus_features': dist, 'families': {}, 'scopes': {}}
    fams = sorted({fam for sc in stat for fam in stat[sc]})
    print()
    print('%-20s %-16s %8s %8s %8s' % ('family', 'scope', 'mutated', 'missed', 'rate'))
    for sc in ['ALL'] + FEATURES:
        if sc not in stat:
            continue
        line = []
        for fam in fams:
            c = stat[sc].get(fam)
            if not c:
                continue
            m = c['mutated']
            miss = c['MISS']
            rate = miss / m if m else 0.0
            line.append('%-14s %4d/%-4d %6.2f%%' % (fam, miss, m, 100 * rate))
            out['scopes'].setdefault(sc, {})[fam] = {
                'mutated': m, 'missed': miss, 'miss_rate': round(rate, 4)}
        print('%-20s %-16s %s' % (sc, '(%d products)' % sum(
            1 for f in feats.values() if sc == 'ALL' or f.get(sc)), '  '.join(line)))
    with open(args.json, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print('-> %s' % args.json)


if __name__ == '__main__':
    sys.exit(main())
