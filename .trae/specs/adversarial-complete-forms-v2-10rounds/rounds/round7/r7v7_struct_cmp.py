#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 7 深层/浅层结构一致性补充证据（C2）：逐函数比对 源码 AST ↔ 反编译产物 AST。

对每个探针（r7v7_*/n7v7_*）：parse 源 .py 与 *OK.py，按函数名（含类方法）配对，
剥 docstring 后 ast.dump 比对。输出 r7v7_struct_cmp.json。

判据地位：pyc_verify（字节等价）为唯一判据；本比对为 C2「深层与浅层产物结构一致」的
补充粒度证据——AST 不等处需人工归类（等价重排 vs 结构破坏），不单独作为破口判据。
"""
import ast
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
R7 = os.path.join(ROOT, 'test_repros', 'round7')


def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body:
                first = body[0]
                if (isinstance(first, ast.Expr)
                        and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str)):
                    node.body = body[1:]
    return tree


def func_map(path):
    with open(path, encoding='utf-8-sig') as f:
        src = f.read()
    tree = strip_docstrings(ast.parse(src))
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = ast.dump(node, annotate_fields=True, include_attributes=False)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out['%s.%s' % (node.name, sub.name)] = ast.dump(
                        sub, annotate_fields=True, include_attributes=False)
    return out


def main():
    stems = []
    for p in sorted(glob.glob(os.path.join(R7, 'r7v7_*.py')) + glob.glob(os.path.join(R7, 'n7v7_*.py'))):
        if p.endswith('OK.py'):
            continue
        stems.append(os.path.splitext(os.path.basename(p))[0])
    rows = []
    n_equal = n_unequal = n_missing = 0
    for stem in stems:
        src_f = os.path.join(R7, stem + '.py')
        ok_f = os.path.join(R7, stem + 'OK.py')
        if not os.path.isfile(ok_f):
            rows.append({'stem': stem, 'error': 'OK.py missing'})
            continue
        try:
            sm = func_map(src_f)
            om = func_map(ok_f)
        except SyntaxError as e:
            rows.append({'stem': stem, 'error': 'SyntaxError: %s' % e})
            continue
        entry = {'stem': stem, 'funcs': {}}
        for name in sorted(set(sm) | set(om)):
            if name not in sm:
                entry['funcs'][name] = 'extra_in_OK'
                n_missing += 1
            elif name not in om:
                entry['funcs'][name] = 'missing_in_OK'
                n_missing += 1
            elif sm[name] == om[name]:
                entry['funcs'][name] = 'equal'
                n_equal += 1
            else:
                entry['funcs'][name] = 'UNEQUAL'
                n_unequal += 1
        rows.append(entry)
    out = {'summary': {'funcs_equal': n_equal, 'funcs_unequal': n_unequal,
                       'funcs_pairing_missing': n_missing}, 'probes': rows}
    path = os.path.join(HERE, 'r7v7_struct_cmp.json')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('funcs equal=%d unequal=%d pairing_missing=%d -> %s'
          % (n_equal, n_unequal, n_missing, path))
    for r in rows:
        bad = {k: v for k, v in r.get('funcs', {}).items() if v != 'equal'}
        if bad or r.get('error'):
            print('  %-22s %s' % (r['stem'], bad or r['error']))


if __name__ == '__main__':
    main()
