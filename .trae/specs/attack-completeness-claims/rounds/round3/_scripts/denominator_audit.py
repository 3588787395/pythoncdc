# -*- coding: utf-8 -*-
"""denominator_audit.py — L1 口径层：分母 128 的正确性审计

复算 tools/kb/syntax_coverage.py 的分母规则，并与「语言权威（Python 3.11 ast 模块）」
独立重算的集合对拍；并模拟解释器漂移（3.12 新增节点）对该规则的影响。

输出 JSON + 控制台报告。
"""
import ast as pyast
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
OUT = ROOT / '.trae' / 'specs' / 'attack-completeness-claims' / 'rounds' / 'round3' / '_out'
OUT.mkdir(parents=True, exist_ok=True)

# ---- 规则副本：与 tools/kb/syntax_coverage.py:80-107 完全一致（用于验证本脚本忠实） ----
SKIP = {'AST', 'mod', 'stmt', 'expr', 'expr_context', 'boolop', 'operator',
        'unaryop', 'cmpop', 'type_ignore', 'pattern', 'typevar',
        'type_param', 'slice'}
DEPRECATED = {'Num', 'Str', 'Bytes', 'NameConstant', 'Ellipsis',
              'AugLoad', 'AugStore', 'Param', 'ExtSlice'}
NON_SYNTAX = {'Interactive', 'Expression', 'FunctionType', 'Suite', 'TypeIgnore'}
STMT_SET = {
    'FunctionDef', 'AsyncFunctionDef', 'ClassDef', 'Return', 'Delete', 'Assign',
    'AugAssign', 'AnnAssign', 'For', 'AsyncFor', 'While', 'If', 'With',
    'AsyncWith', 'Match', 'Raise', 'Try', 'TryStar', 'Assert', 'Import',
    'ImportFrom', 'Global', 'Nonlocal', 'Expr', 'Pass', 'Break', 'Continue'}


def tool_denominator(namespace):
    """按 tools/kb/syntax_coverage.py 的规则，从给定的 ast 命名空间复算分母。"""
    nodes = [n for n in sorted(n for n in dir(namespace) if n[0].isupper()
                               and isinstance(getattr(namespace, n), type)
                               and issubclass(getattr(namespace, n), namespace.AST))
             if n not in DEPRECATED and n not in NON_SYNTAX]
    stmt = sorted({n for n in nodes if n.endswith('Stmt') or n in STMT_SET})
    expr = sorted(set(nodes) - set(stmt) - SKIP)
    mod = sorted(n for n in nodes if n.endswith(('Module', 'Interactive',
                                                 'Expression', 'FunctionType')))
    return sorted(set(stmt) | set(expr) | set(mod)), set(stmt), set(expr), set(mod)


def all_ast_classes(namespace):
    """全部 AST 子类（**不设大小写过滤**）——用于揭示工具规则 `n[0].isupper()` 的排除效应。"""
    return {n for n in dir(namespace) if isinstance(getattr(namespace, n), type)
            and issubclass(getattr(namespace, n), namespace.AST)}


def main():
    report = {}
    denom, stmt, expr, mod = tool_denominator(pyast)
    report['tool_denominator_size'] = len(denom)
    report['tool_stmt'] = sorted(stmt)
    report['tool_expr_nonstmt'] = sorted(expr - mod)
    report['tool_mod'] = sorted(mod)

    # ---- 与已发布产物对拍（docs/refactor/syntax-coverage.json） ----
    pub = json.load(io.open(ROOT / 'docs' / 'refactor' / 'syntax-coverage.json',
                            encoding='utf-8'))
    report['published_denominator'] = pub['denominator']
    report['published_numerator'] = pub['numerator']
    report['published_pct'] = pub['coverage_pct']
    report['published_json_has_denominator_node_list'] = any(
        k for k in pub if 'denominator' in k and isinstance(pub[k], list))

    # ---- 独立重算「语言权威面」：逐类判定是否属于语法节点 ----
    every = all_ast_classes(pyast)
    # 抽象基类（含 3.12 名）与编译模式 / 类型检查器专用
    abstract = {n for n in every if n in SKIP}
    legacy_alias = {n for n in every if n in DEPRECATED}
    compile_modes = {n for n in every if n in NON_SYNTAX}
    # 运算符/上下文等「词法类」：不是独立语法构造，而是 BinOp/BoolOp/Compare/UnaryOp/AugAssign 的载荷
    op_bases = ('operator', 'unaryop', 'cmpop', 'boolop')
    ctx_base = 'expr_context'
    token_classes = set()
    ctx_classes = set()
    for n in every:
        cls = getattr(pyast, n)
        if any(issubclass(cls, getattr(pyast, b)) for b in op_bases if hasattr(pyast, b)):
            token_classes.add(n)
        if hasattr(pyast, ctx_base) and issubclass(cls, pyast.expr_context):
            ctx_classes.add(n)
    syntactic = every - abstract - legacy_alias - compile_modes - token_classes - ctx_classes
    report['token_classes_in_denominator'] = sorted(token_classes & set(denom))
    report['ctx_classes_in_denominator'] = sorted(ctx_classes & set(denom))
    report['abstract_bases'] = sorted(abstract)
    report['legacy_aliases'] = sorted(legacy_alias)
    report['compile_modes'] = sorted(compile_modes)
    report['every_ast_class_count'] = len(every)
    report['lowercase_real_syntax_classes_dropped_by_rule'] = sorted(
        n for n in syntactic if not n[0].isupper())
    report['true_syntactic_surface_size'] = len(syntactic)
    report['denominator_minus_true_syntactic'] = sorted(set(denom) - syntactic)
    report['true_syntactic_minus_denominator'] = sorted(syntactic - set(denom))

    # ---- 语义节点（非载荷）细分：把 arguments/arg/keyword/withitem/alias 等单独归类 ----
    helper_nodes = sorted(n for n in denom if n in {
        'arguments', 'arg', 'keyword', 'withitem', 'alias', 'comprehension',
        'ExceptHandler', 'match_case'})

    # ---- 解释器漂移模拟：注入 3.12 节点后重算分母 ----
    class _Fake:  # placeholder
        pass

    class TypeAlias(pyast.AST):
        _fields = ()

    class TypeVar(pyast.AST):
        _fields = ()

    class ParamSpec(pyast.AST):
        _fields = ()

    class TypeVarTuple(pyast.AST):
        _fields = ()

    class TypeParam(pyast.AST):
        _fields = ()
        _field_types = {}

    import types
    ns = types.SimpleNamespace()
    for n in dir(pyast):
        setattr(ns, n, getattr(pyast, n))
    for extra in (TypeAlias, TypeVar, ParamSpec, TypeVarTuple, TypeParam):
        setattr(ns, extra.__name__, extra)
    denom312, _, _, _ = tool_denominator(ns)
    added = sorted(set(denom312) - set(denom))
    report['simulated_312_denominator_size'] = len(denom312)
    report['simulated_312_added'] = added
    report['simulated_312_added_present_in_repo'] = {
        n: any(n in p.read_text(encoding='utf-8', errors='replace')
                for p in (ROOT / 'core').rglob('*.py'))
        for n in added}

    # ---- 扩展形态 31 项的维护属性 ----
    sys.path.insert(0, str(ROOT / 'tools' / 'kb'))
    import syntax_coverage as sc
    report['extra_forms_count'] = len(sc.EXTRA_FORMS)
    report['extra_forms_keys'] = sorted(sc.EXTRA_FORMS)

    # ---- 被 case 规则丢弃的低写真实语法类，是否被 31 扩展形态以「形态」方式补回 ----
    import re as _re
    low = [n for n in report['lowercase_real_syntax_classes_dropped_by_rule']
           if n != 'excepthandler']
    covered_by_form, not_covered = {}, []
    for n in low:
        hit = []
        for k, desc in sc.EXTRA_FORMS.items():
            if _re.search(r'\b' + n + r'\b', desc) or _re.search(
                    r'ast\.' + n + r'\b', desc):
                hit.append(k)
        covered_by_form[n] = hit
        if not hit:
            not_covered.append(n)
    report['lowercase_syntax_dropped'] = low
    report['dropped_but_recovered_as_extra_form'] = covered_by_form
    report['dropped_and_never_recovered'] = not_covered

    out = OUT / 'denominator_audit.json'
    io.open(out, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(report, ensure_ascii=False, indent=2))

    print('== 分母复算 ==')
    print('tool rule denominator size      :', len(denom))
    print('published json denominator       :', pub['denominator'])
    print('published json numerator         :', pub['numerator'])
    print('published json coverage_pct      :', pub['coverage_pct'])
    print('published json 含分母节点清单?   :', report['published_json_has_denominator_node_list'])
    print()
    print('== 语言权威面独立重算 (py%s) ==' % '.'.join(map(str, sys.version_info[:3])))
    print('ast 中 AST 子类总数(不设大小写过滤)  :', len(every))
    print('真正语法节点面(剔除基类/别名/模式/运算符/ctx):', len(syntactic))
    print('其中小写命名、被 n[0].isupper() 规则丢弃 :',
          report['lowercase_real_syntax_classes_dropped_by_rule'])
    print('分母里多出的非语法节点            :', len(report['denominator_minus_true_syntactic']))
    print('  其中运算符/比较/布尔词法类      :', len(report['token_classes_in_denominator']))
    print('  其中 ctx 类(Load/Store/Del)     :', len(report['ctx_classes_in_denominator']))
    print('语言面里但分母缺的节点            :', report['true_syntactic_minus_denominator'])
    print('分母里但语言面没有的节点          :', len(report['denominator_minus_true_syntactic']))
    print()
    print('== 3.12 漂移模拟 ==')
    print('注入 TypeAlias/TypeVar/ParamSpec/TypeVarTuple 后分母 :', len(denom312))
    print('新增节点                            :', added)
    print('新增节点在 core/** 出现?             :', report['simulated_312_added_present_in_repo'])
    print()
    print('JSON ->', out)


if __name__ == '__main__':
    main()
