#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round6 REVIEW2 · 独立复核 I.7 docstring 合规（AST 提取 docstring，非文本粗匹配）。

识别层 region_analyzer.py 10 方法：需含六项（算法依据/归约顺序/唯一归属判定/嵌套处理/
入口引用语义/反编译流程）与 C 条款 C1/C2/C3。
生成层 region_ast_generator.py 9 方法：需含 ①-⑥ 六标号与 C 条款 C1/C2/C3。
只读，输出 r6v6r_docstring_check.json。
"""
import ast
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

ID_FILES = 'core/cfg/region_analyzer.py'
GEN_FILES = 'core/cfg/region_ast_generator.py'
ID_METHODS = ['_identify_loop_regions', '_identify_try_except_regions',
              '_identify_with_regions', '_identify_match_regions',
              '_identify_assert_regions', '_identify_chained_compare_regions',
              '_identify_conditional_regions', '_identify_ternary_regions',
              '_identify_boolop_regions', '_identify_sequence_regions']
GEN_METHODS = ['_generate_loop', '_generate_assert', '_generate_if',
               '_generate_value_context_chain_compare_assign', '_generate_match',
               '_generate_boolop', '_generate_boolop_impl', '_generate_ternary',
               '_generate_basic_region']

ID_ITEMS = ['算法依据', '归约顺序', '唯一归属判定', '嵌套处理', '入口引用语义', '反编译流程']
GEN_ITEMS = ['①', '②', '③', '④', '⑤', '⑥']


def docstrings(path):
    tree = ast.parse(open(path, encoding='utf-8-sig').read())
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            out.setdefault(node.name, ast.get_docstring(node) or '')
    return out


def check(path, methods, items, label):
    ds = docstrings(path)
    rows = []
    all_ok = True
    for m in methods:
        d = ds.get(m, '')
        marks = [it for it in items if it in d]
        has_c = ('C 条款' in d)
        c1, c2, c3 = ('C1' in d), ('C2' in d), ('C3' in d)
        ok = (len(marks) == len(items)) and has_c and c1 and c2 and c3
        all_ok = all_ok and ok
        rows.append({'layer': label, 'method': m, 'doc_len': len(d),
                     'item_marks': marks, 'items_ok': len(marks) == len(items),
                     'has_C_clause': has_c, 'C1': c1, 'C2': c2, 'C3': c3, 'ok': ok})
    return rows, all_ok


def main():
    id_rows, id_ok = check(os.path.join(ROOT, ID_FILES), ID_METHODS, ID_ITEMS, 'identify')
    gen_rows, gen_ok = check(os.path.join(ROOT, GEN_FILES), GEN_METHODS, GEN_ITEMS, 'generate')
    rows = id_rows + gen_rows
    out = {'identify_all_ok': id_ok, 'generate_all_ok': gen_ok,
           'all_ok': id_ok and gen_ok, 'rows': rows}
    with open(os.path.join(HERE, 'r6v6r_docstring_check.json'), 'w',
              encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for r in rows:
        print('%-9s %-45s items=%s C=%s C1/2/3=%s%s%s ok=%s'
              % (r['layer'], r['method'], r['items_ok'], r['has_C_clause'],
                 r['C1'], r['C2'], r['C3'], r['ok']))
    print('ALL_OK=%s' % out['all_ok'])


if __name__ == '__main__':
    main()