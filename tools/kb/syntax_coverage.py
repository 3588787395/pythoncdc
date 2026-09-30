# -*- coding: utf-8 -*-
"""syntax_coverage.py — 语法完备占比：程序能处理的 ÷ 完全反编译应能处理的

**分母（应有）** = Python 3.11 `ast` 模块定义的完整语法面 = 语言权威，
与本实现无关，不存在"用实现自身枚举当全集"的循环论证。
另加无独立 ast 节点的语句形态（elif 链 / for-else / 多上下文 with / 异常组 等）
作为扩展语法面。

**分子（实有）** = 程序能产出的节点词汇：
  (a) `core/ast_nodes.py` 的 AST* 类（自有 AST）
  (b) 各生成器里实际构造的 `ast.<Node>` 引用
分子按 (a)+(b) 命中分母节点；未命中者 = 程序无法产出的语法。

输出 docs/refactor/syntax-coverage.json
用法：python -X utf8 tools/kb/syntax_coverage.py
"""
import ast as pyast
import collections
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r'F:\Downloads\pythoncdc-main')
OUT = ROOT / 'docs' / 'refactor' / 'syntax-coverage.json'
GEN_DIRS = [ROOT / 'core' / 'cfg', ROOT / 'parsers', ROOT / 'core']
GEN_FILES_EXTRA = [ROOT / 'core' / 'control_flow.py', ROOT / 'core' / 'astree.py']

# 无独立 ast 节点的语句形态（Python 语法存在但复用现有节点，需单独判实现）
EXTRA_FORMS = {
    'elif_chain': 'if/elif/else 链（ast.If 的 orelse 嵌套）',
    'for_else': 'for/while 的 else 子句（ast.For.orelse）',
    'multi_target_assign': 'a, b = t1, t2（ast.Tuple 目标）',
    'multi_context_with': 'with a as x, b as y（ast.With.items 多项）',
    'augmented_assign': 'x += 1（ast.AugAssign）',
    'walrus': ':= 海象（ast.NamedExpr）',
    'decorator_with_args': '@f(x)（ast.Call 装饰器）',
    'keyword_args': 'f(k=v)（ast.Call keywords）',
    'star_args': 'f(*a, **k)（ast.Starred）',
    'chained_comparison': 'a < b < c（ast.Compare 多个 ops）',
    'star_import': 'from m import *（ast.alias）',
    'relative_import': 'from . import m（ast.ImportFrom level>0）',
    'global_nonlocal': 'global / nonlocal（ast.Global/NestedLocal）',
    'slice': 'a[1:2:3]（ast.Slice）',
    'fstring_conversion': 'f"{x!r:>10}"（JoinedStr FormattedValue）',
    'async_def': 'async def（ast.AsyncFunctionDef）',
    'async_for': 'async for（ast.AsyncFor）',
    'async_with': 'async with（ast.AsyncWith）',
    'await_expr': 'await x（ast.Await）',
    'yield_from': 'yield from（ast.YieldFrom）',
    'nested_comprehension': '多重 for 的推导式（ast.comprehension 多个）',
    'try_finally_only': 'try/finally（ast.Try.finalbody）',
    'except_star': 'except* E（3.11 异常组）',
    'match_statement': 'match/case（ast.Match）',
    'case_guard': 'case p if g（ast.match_case.guard）',
    'class_keyword_pattern': 'case C(x=1)（ast.MatchClass）',
    'mapping_pattern': 'case {k: v}（ast.MatchMapping）',
    'sequence_pattern': 'case [a, b]（ast.MatchSequence）',
    'or_pattern': 'case A | B（ast.MatchOr）',
    'capture_pattern': 'case [x, *rest]（ast.MatchStar）',
    'value_pattern': 'case 1 / case "s"（ast.MatchValue/MatchSingleton）',
}


def collect_files():
    fs = set()
    for d in GEN_DIRS:
        if d.exists():
            for p in d.rglob('*.py'):
                fs.add(p)
    for p in GEN_FILES_EXTRA:
        if p.exists():
            fs.add(p)
    return sorted(fs)


def main():
    # 抽象基类（不直接出现在语法面）
    skip = {'AST', 'mod', 'stmt', 'expr', 'expr_context', 'boolop', 'operator',
            'unaryop', 'cmpop', 'type_ignore', 'pattern', 'typevar',
            'type_param', 'slice'}
    # 3.8 前的废弃别名（3.9+ 已并入 Constant/统一 ctx）——不进语法面，否则虚增分母
    DEPRECATED = {'Num', 'Str', 'Bytes', 'NameConstant', 'Ellipsis',
                  'AugLoad', 'AugStore', 'Param',
                  'ExtSlice'}   # 3.9+ 起 a[b:c, d:e] 由 Tuple 表达
    # compile() 模式根节点 / 非语法面（测试套件、类型检查器专用）
    NON_SYNTAX = {'Interactive', 'Expression', 'FunctionType', 'Suite',
                  'TypeIgnore'}
    # ---------- 分母：Python ast 全节点 ----------
    py311_nodes = [n for n in sorted(n for n in dir(pyast) if n[0].isupper()
                                     and isinstance(getattr(pyast, n), type)
                                     and issubclass(getattr(pyast, n), pyast.AST))
                   if n not in DEPRECATED and n not in NON_SYNTAX]
    stmt_nodes = [n for n in py311_nodes if n.endswith('Stmt') or n in {
        'FunctionDef', 'AsyncFunctionDef', 'ClassDef', 'Return', 'Delete', 'Assign',
        'AugAssign', 'AnnAssign', 'For', 'AsyncFor', 'While', 'If', 'With',
        'AsyncWith', 'Match', 'Raise', 'Try', 'TryStar', 'Assert', 'Import',
        'ImportFrom', 'Global', 'Nonlocal', 'Expr', 'Pass', 'Break', 'Continue'}]
    stmt_nodes = sorted(set(stmt_nodes))
    expr_nodes = sorted(set(py311_nodes) - set(stmt_nodes) - skip)
    match_nodes = sorted(n for n in py311_nodes if n.startswith('Match'))
    mod_nodes = sorted(n for n in py311_nodes if n.endswith(('Module', 'Interactive',
                                                             'Expression', 'FunctionType')))

    denominator_ast = sorted(set(stmt_nodes) | set(expr_nodes) | set(mod_nodes))

    # ---------- 分子：程序能产出的节点 ----------
    own_nodes = set()      # AST* 自有类
    ast_refs = set()       # ast.<Node> 实际构造
    per_file_refs = collections.defaultdict(set)
    for p in collect_files():
        txt = p.read_text(encoding='utf-8', errors='replace')
        for m in re.finditer(r'\bast\.([A-Z]\w+)', txt):
            ast_refs.add(m.group(1))
            per_file_refs[p.name].add(m.group(1))
        for m in re.finditer(r"['\"]([A-Z]\w+)['\"]", txt):
            if m.group(1) in denominator_ast or m.group(1).startswith('Match'):
                ast_refs.add(m.group(1))      # AST 工厂的字符串形式 'If': (...)

    # core/ast_nodes.py 的 AST* 类
    astn = ROOT / 'core' / 'ast_nodes.py'
    if astn.exists():
        t = astn.read_text(encoding='utf-8', errors='replace')
        own_nodes = set(re.findall(r'^class (AST\w+)', t, re.M))

    # own AST* → 对应 python ast 节点（代码生成器终将映射）
    OWN2PY = {
        'ASTBinary': 'BinOp', 'ASTBlock': 'Block', 'ASTCall': 'Call',
        'ASTDecoratorApplication': 'Decorator', 'ASTFor': 'For', 'ASTIfExp': 'IfExp',
        'ASTIf': 'If', 'ASTNodeList': None, 'ASTNode': None, 'ASTStore': None,
        'ASTTry': 'Try', 'ASTWith': 'With', 'ASTFunctionDef': 'FunctionDef',
        'ASTTryStar': 'TryStar',   # 注：词汇存在；except* 的识别/生成经 is_except_star 标记链路（2026-09-29 审计确认）
    }
    own_mapped = {OWN2PY[c] for c in own_nodes if c in OWN2PY and OWN2PY[c]}

    produced = ast_refs | own_mapped
    # 程序自有的复合节点（如 Block/ASTNodeList）不是 python ast 节点，不计入分子
    covered = sorted(n for n in denominator_ast if n in produced)

    uncovered = sorted(n for n in denominator_ast if n not in produced)

    # ---------- 扩展语法面（无独立 ast 节点） ----------
    extra_covered, extra_uncovered = [], []
    all_text = ''.join(p.read_text(encoding='utf-8', errors='replace')
                       for p in collect_files())
    for k, desc in sorted(EXTRA_FORMS.items()):
        hint = {
            'elif_chain': ['elif', 'elif_conditions', 'IfRegion'],
            'for_else': ['else_body', 'LOOP_ELSE'],
            'multi_target_assign': ['ASTStore', 'Tuple'],
            'multi_context_with': ['should_merge_with', 'items'],
            'augmented_assign': ['AugAssign', 'BINARY_OP', 'INPLACE'],
            'walrus': ['NamedExpr', 'COPY'],
            'decorator_with_args': ['Decorator', 'decorator'],
            'keyword_args': ['keywords', 'KW_NAMES'],
            'star_args': ['Starred', 'CALL_FUNCTION_EX', 'UNPACK'],
            'chained_comparison': ['CHAINED_COMPARE', 'Compare'],
            'star_import': ['ImportFrom', 'import_all', 'level'],
            'relative_import': ['level', 'ImportFrom'],
            'global_nonlocal': ['Global', 'Nonlocal', 'STORE_GLOBAL'],
            'slice': ['Slice', 'BUILD_SLICE', 'slice'],
            'fstring_conversion': ['FormattedValue', 'conversion', 'format_spec'],
            'async_def': ['AsyncFunctionDef', 'async'],
            'async_for': ['AsyncFor', 'GET_AITER', 'GET_ANEXT'],
            'async_with': ['AsyncWith', 'BEFORE_ASYNC_WITH'],
            'await_expr': ['Await', 'GET_AWAITABLE', 'SEND'],
            'yield_from': ['YieldFrom', 'GET_YIELD_FROM_ITER', 'is_yield_from_loop'],
            'nested_comprehension': ['multi_for', 'comprehension', 'for_iter_indices'],
            'try_finally_only': ['finally', 'finalbody', 'has_finally'],
            # except* 3.11 判定标记：CHECK_EG_MATCH/PREP_RERAISE_STAR 识别 + is_except_star 生成发射。
            # 注意：PRELOAD_RERAISE 是 3.12 操作码，3.11 里零引用不构成"未实现"证据（2026-09-29 审计纠正）。
            'except_star': ['is_except_star', 'PREP_RERAISE_STAR'],
            'match_statement': ['Match', 'MATCH_', 'MatchRegion'],
            'case_guard': ['guard', 'MatchCase'],
            'class_keyword_pattern': ['MatchClass', 'MatchClass'],
            'mapping_pattern': ['MatchMapping', 'MatchMapping'],
            'sequence_pattern': ['MatchSequence', 'MatchSequence'],
            'or_pattern': ['MatchOr', 'MatchOr'],
            'capture_pattern': ['MatchAs', 'MatchStar'],
            'value_pattern': ['MatchValue', 'MatchValue', 'MatchSingleton'],
        }[k]
        (extra_covered if any(h in all_text for h in hint) else extra_uncovered).append(k)

    n_ast_cov = len(covered)
    n_ast_total = len(denominator_ast)
    n_extra_cov = len(extra_covered)
    n_extra_total = len(EXTRA_FORMS)
    ast_pct = 100.0 * n_ast_cov / n_ast_total
    extra_pct = 100.0 * n_extra_cov / n_extra_total
    total_cov = n_ast_cov + n_extra_cov
    total_all = n_ast_total + n_extra_total
    total_pct = 100.0 * total_cov / total_all

    out = {
        'denominator': {
            'source': 'Python 3.11 ast 模块（语言权威）',
            'ast_node_types': n_ast_total,
            'extra_syntax_forms': n_extra_total,
            'total': total_all,
        },
        'numerator': {
            'source': '程序可产出节点词汇（ast.<Node> 构造引用 + core/ast_nodes.py AST* 类映射）',
            'ast_node_types': n_ast_cov,
            'extra_syntax_forms': n_extra_cov,
            'total': total_cov,
        },
        'coverage_pct': {
            'ast_nodes': round(ast_pct, 2),
            'extra_forms': round(extra_pct, 2),
            'overall': round(total_pct, 2),
        },
        'uncovered_ast_nodes': uncovered,
        'uncovered_extra_forms': extra_uncovered,
        'covered_extra_forms': extra_covered,
        'own_ast_classes': sorted(own_nodes),
    }
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, indent=2))

    print('=== 语法完备占比 ===')
    print('分母(应有): ast 节点 %d + 扩展形态 %d = %d' % (n_ast_total, n_extra_total, total_all))
    print('分子(实有): ast 节点 %d + 扩展形态 %d = %d' % (n_ast_cov, n_extra_cov, total_cov))
    print('占比: ast %.1f%%  扩展 %.1f%%  **总 %.1f%%**' % (ast_pct, extra_pct, total_pct))
    print('\n--- 未覆盖 ast 节点 (%d) ---' % len(uncovered))
    for i in range(0, len(uncovered), 8):
        print('  ' + '  '.join('%-22s' % n for n in uncovered[i:i + 8]))
    print('\n--- 未覆盖扩展形态 (%d) ---' % len(extra_uncovered))
    for k in extra_uncovered:
        print('  %-26s %s' % (k, EXTRA_FORMS[k]))
    print('\nJSON -> %s' % OUT)


if __name__ == '__main__':
    main()
