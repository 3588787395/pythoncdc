#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round6 REVIEW2 · 独立验证「零可执行代码变更」：剥 docstring 后 AST 等价。

对 core/cfg/region_analyzer.py 与 core/cfg/region_ast_generator.py：
  old = git show HEAD~1:<file>（带 BOM，需 lstrip('\ufeff')）
  new = 工作树文件
剥除 Module/FunctionDef/AsyncFunctionDef/ClassDef 的 body[0] 若为首条 docstring
(Expr(Constant(str)))，再 ast.dump 比对。只读，不改源码。
"""
import ast
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

FILES = ['core/cfg/region_analyzer.py', 'core/cfg/region_ast_generator.py']


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


def dump_norm(src):
    tree = ast.parse(src)
    strip_docstrings(tree)
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def main():
    out = {'files': [], 'all_equal': True}
    for rel in FILES:
        old_bytes = subprocess.run(['git', '-C', ROOT, 'show', 'HEAD~1:%s' % rel],
                                   capture_output=True).stdout
        old_src = old_bytes.decode('utf-8').lstrip('\ufeff')
        with open(os.path.join(ROOT, rel), encoding='utf-8-sig') as f:
            new_src = f.read()
        try:
            old_dump = dump_norm(old_src)
            old_ok = True
        except SyntaxError as e:
            old_dump, old_ok = 'OLD_SYNTAX_ERROR: %s' % e, False
        try:
            new_dump = dump_norm(new_src)
            new_ok = True
        except SyntaxError as e:
            new_dump, new_ok = 'NEW_SYNTAX_ERROR: %s' % e, False
        equal = old_ok and new_ok and (old_dump == new_dump)
        out['files'].append({
            'file': rel, 'old_ok': old_ok, 'new_ok': new_ok,
            'equal': equal, 'verdict': 'AST_EQUAL' if equal else 'AST_DIFF',
        })
        if not equal:
            out['all_equal'] = False
    with open(os.path.join(HERE, 'r6v6r_ast_equal.json'), 'w',
              encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for r in out['files']:
        print('%-40s %s' % (r['file'], r['verdict']))
    print('ALL_EQUAL=%s' % out['all_equal'])
    return 0 if out['all_equal'] else 1


if __name__ == '__main__':
    sys.exit(main())