#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**构造级探针**（judge 对每个语义维度的可辨性）。

目的：
  1) 量化 judge 对**每个语义维度**是否真能抓到「注入的已知语义错误」
     （不是「该维度出现在语料里吗」——那是覆盖问题；这是判据问题）；
  2) 覆盖 402 语料里缺失的维度：注解 / docstring / 装饰器 / 闭包 / nonlocal /
     global / 异常别名 / lambda 默认值 / async / match 守卫 / with 序 / del /
     assert 消息 / f-string / 跨函数与模块级装配；
  3) 每条结论都带变异 site，证据可复现（产物与变异产物都落盘）。

流程（与 `.trae/specs/attain-true-completeness/rounds/round1/rec1_run.py` 同源）：
    写探针 .py -> py_compile(3.11) -> pycdc.py -o <base>OK.py -> pyc_verify single（基线）
    -> 注入语义错误 -> pyc_verify single（判定）-> CAUGHT / MISS / COMPILE_ERROR

用法： python -X utf8 construct_probe.py [--only <tag>]
产物： _out/construct_probe.json
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import subprocess
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')
PROBE_DIR = os.path.join(ROUND4, '_probes')
MUT_DIR = os.path.join(ROUND4, '_probes', 'mut')

sys.path.insert(0, HERE)
import mutation_lib  # noqa: E402
from mutation_lib import splice  # noqa: E402


# ── 通用工具 ─────────────────────────────────────────────────────────────────


def docstring_of(holder):
    body = getattr(holder, 'body', None)
    if not isinstance(body, list) or not body:
        return None
    if not isinstance(body[0], ast.Expr):
        return None
    c = body[0].value
    if isinstance(c, ast.Constant) and isinstance(c.value, str):
        return c
    return None


def in_func(node, pmap):
    cur = node
    while cur in pmap:
        cur = pmap[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return True
    return False


# ── 变异族（每个返回 (mutated_bytes, site) 或 None） ─────────────────────────


def mut_annotation_param(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.arg) and n.annotation is not None:
            return splice(data, [loc.span(n.annotation)], [b'str']), 'param annotation -> str'
    return None


def mut_annotation_return(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.returns is not None:
            return splice(data, [loc.span(n.returns)], [b'str']), 'return annotation -> str'
    return None


def mut_annotation_local(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.AnnAssign) and n.annotation is not None:
            return splice(data, [loc.span(n.annotation)], [b'str']), 'local annotation -> str'
    return None


def mut_docstring_module(tree, data, loc, pmap):
    c = docstring_of(tree)
    if c is None:
        return None
    return splice(data, [loc.span(c)], [repr(c.value + 'MUT').encode('utf-8')]), 'module docstring mutated'


def mut_docstring_func(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
            c = docstring_of(h)
            if c is not None:
                return splice(data, [loc.span(c)], [repr(c.value + 'MUT').encode('utf-8')]), \
                    'function docstring mutated'
    return None


def mut_docstring_class(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, ast.ClassDef):
            c = docstring_of(h)
            if c is not None:
                return splice(data, [loc.span(c)], [repr(c.value + 'MUT').encode('utf-8')]), \
                    'class docstring mutated'
    return None


def mut_doc_dunder(tree, data, loc, pmap):
    """pycdc 把模块/类 docstring 还原成 `__doc__ = '...'` 赋值；改它的值。"""
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
                and n.targets[0].id == '__doc__' and isinstance(n.value, ast.Constant):
            return splice(data, [loc.span(n.value)], [repr(n.value.value + 'MUT').encode('utf-8')]), \
                'module __doc__ value mutated'
    for h in ast.walk(tree):
        if isinstance(h, ast.ClassDef):
            for n in h.body:
                if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
                        and n.targets[0].id == '__doc__' and isinstance(n.value, ast.Constant):
                    return splice(data, [loc.span(n.value)],
                                  [repr(n.value.value + 'MUT').encode('utf-8')]), \
                        'class __doc__ value mutated'
    return None


def mut_decorator_order(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(h.decorator_list) >= 2:
            d0, d1 = h.decorator_list[0], h.decorator_list[1]
            s0, s1 = loc.span(d0), loc.span(d1)
            if s0[1] > s1[0]:
                continue
            return splice(data, [s0, s1], [loc.seg(d1), loc.seg(d0)]), 'two decorators swapped'
    return None


def mut_decorator_arg(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in h.decorator_list:
                if isinstance(d, ast.Call) and d.args:
                    a = d.args[0]
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        return splice(data, [loc.span(a)], [repr(a.value + 'B').encode('utf-8')]), \
                            'decorator arg %r -> %r' % (a.value, a.value + 'B')
    return None


def mut_closure_capture(tree, data, loc, pmap):
    """闭包：内层捕获的外层变量改绑到另一个外层变量（语义改变）。"""
    funcs = [h for h in ast.walk(tree) if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for inner in funcs:
        inner_names = {n.id for n in ast.walk(inner) if isinstance(n, ast.Name)}
        for outer in funcs:
            if outer is inner:
                continue
            outer_vars = [n.targets[0].id for n in outer.body
                          if isinstance(n, ast.Assign) and len(n.targets) == 1
                          and isinstance(n.targets[0], ast.Name)]
            if len(outer_vars) < 2:
                continue
            for n in ast.walk(inner):
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in outer_vars:
                    tgt = [v for v in outer_vars if v != n.id][0]
                    return splice(data, [loc.span(n)], [tgt.encode('utf-8')]), \
                        'closure capture %r -> %r' % (n.id, tgt)
    return None


def mut_nonlocal_target(tree, data, loc, pmap):
    """nonlocal 目标改绑到同一外层作用域的另一个变量（语义改变）。

    注：`ast.Nonlocal` 的**直接父节点**就是声明它的函数（`pmap.get(h)`），
    再上一层（`pmap.get(holder)`）才是**外层**函数。
    """
    for h in ast.walk(tree):
        if not isinstance(h, ast.Nonlocal):
            continue
        holder = pmap.get(h)                     # 声明所在的函数
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        outer = pmap.get(holder)                 # 外层函数
        if not isinstance(outer, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        outer_vars = [n.targets[0].id for n in getattr(outer, 'body', [])
                      if isinstance(n, ast.Assign) and len(n.targets) == 1
                      and isinstance(n.targets[0], ast.Name)]
        old = h.names[0]
        cand = [v for v in outer_vars if v != old]
        if not cand:
            continue
        tgt = cand[0]
        spans, texts = [loc.span(h)], [('nonlocal ' + tgt).encode('utf-8')]
        for n in ast.walk(holder):
            if isinstance(n, ast.Name) and n.id == old:
                spans.append(loc.span(n))
                texts.append(tgt.encode('utf-8'))
        pairs = sorted(zip(spans, texts))
        return splice(data, [a for a, _ in pairs], [b for _, b in pairs]), \
            'nonlocal %r -> %r' % (old, tgt)
    return None


def mut_global_target(tree, data, loc, pmap):
    """**函数内**的 global 声明改绑到另一个全局名（语义改变）。

    只改「函数体内」对该名字的使用点，模块级同名定义保持不变。
    """
    module_vars = []
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name):
            module_vars.append(n.targets[0].id)
    for h in ast.walk(tree):
        if not isinstance(h, ast.Global):
            continue
        holder = pmap.get(h)                     # 声明所在的函数
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        old = h.names[0]
        cand = [v for v in module_vars if v != old]
        if not cand:
            continue
        tgt = cand[0]
        spans, texts = [loc.span(h)], [('global ' + tgt).encode('utf-8')]
        for n in ast.walk(holder):
            if isinstance(n, ast.Name) and n.id == old:
                spans.append(loc.span(n))
                texts.append(tgt.encode('utf-8'))
        pairs = sorted(zip(spans, texts))
        return splice(data, [a for a, _ in pairs], [b for _, b in pairs]), \
            'global %r -> %r' % (old, tgt)
    return None


def mut_except_alias(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, ast.ExceptHandler) and h.type is not None:
            t = h.type
            if isinstance(t, ast.Name):
                return splice(data, [loc.span(t)], [t.id.encode('utf-8') + b'_MUT']), \
                    'except type %s -> %s_MUT' % (t.id, t.id)
    return None


def mut_except_tuple_order(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, ast.ExceptHandler) and isinstance(h.type, ast.Tuple) \
                and len(h.type.elts) >= 2:
            e0, e1 = h.type.elts[0], h.type.elts[1]
            s0, s1 = loc.span(e0), loc.span(e1)
            if s0[1] > s1[0]:
                continue
            return splice(data, [s0, s1], [loc.seg(e1), loc.seg(e0)]), 'except tuple order swapped'
    return None


def mut_lambda_default(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Lambda) and n.args.defaults:
            d = n.args.defaults[0]
            if isinstance(d, ast.Constant) and isinstance(d.value, int):
                return splice(data, [loc.span(d)], [repr(d.value + 1).encode('utf-8')]), \
                    'lambda default %r -> %r' % (d.value, d.value + 1)
    return None


def mut_yield_value(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Yield) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, int):
            return splice(data, [loc.span(n.value)], [repr(n.value.value + 1).encode('utf-8')]), \
                'yield value %r -> %r' % (n.value.value, n.value.value + 1)
    return None


def mut_async_await(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Await) and isinstance(n.value, ast.Call) and n.value.args:
            a = n.value.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, int):
                return splice(data, [loc.span(a)], [repr(a.value + 1).encode('utf-8')]), \
                    'await arg %r -> %r' % (a.value, a.value + 1)
    return None


def mut_match_guard(tree, data, loc, pmap):
    sym = {ast.Lt: (b'<', b'>'), ast.Gt: (b'>', b'<'),
           ast.LtE: (b'<=', b'>='), ast.GtE: (b'>=', b'<='),
           ast.Eq: (b'==', b'!='), ast.NotEq: (b'!=', b'==')}
    for n in ast.walk(tree):
        if isinstance(n, ast.match_case) and n.guard is not None and isinstance(n.guard, ast.Compare):
            g = n.guard
            if len(g.ops) != 1 or type(g.ops[0]) not in sym:
                continue
            old_s, new_s = sym[type(g.ops[0])]
            le = loc.span(g.left)[1]
            rs = loc.span(g.comparators[0])[0]
            gap = data[le:rs]
            if old_s not in gap:
                continue
            return splice(data, [(le, rs)], [gap.replace(old_s, new_s, 1)]), 'match guard polarity flipped'
    return None


def mut_with_item_order(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, ast.With) and len(h.items) >= 2:
            i0, i1 = h.items[0], h.items[1]
            s0, s1 = loc.span(i0.context_expr), loc.span(i1.context_expr)
            if s0[1] > s1[0]:
                continue
            return splice(data, [s0, s1], [loc.seg(i1.context_expr), loc.seg(i0.context_expr)]), \
                'two with-items swapped'
    return None


def mut_del_target(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Delete):
            t = n.targets[0]
            if isinstance(t, ast.Name):
                return splice(data, [loc.span(t)], [t.id.encode('utf-8') + b'_MUT']), \
                    'del %s -> %s_MUT' % (t.id, t.id)
    return None


def mut_assert_message(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Assert) and n.msg is not None and isinstance(n.msg, ast.Constant):
            return splice(data, [loc.span(n.msg)], [repr(str(n.msg.value) + 'MUT').encode('utf-8')]), \
                'assert message mutated'
    return None


def mut_fstring_literal(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.JoinedStr):
            for v in n.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    return splice(data, [loc.span(v)], [repr(v.value + 'MUT').encode('utf-8')]), \
                        'f-string literal segment mutated'
    return None


def mut_kwarg_name(tree, data, loc, pmap):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg:
                    return splice(data, [loc.span(kw)], [(kw.arg + '_MUT').encode('utf-8') + b'=1']), \
                        'kwarg name %s -> %s_MUT' % (kw.arg, kw.arg)
    return None


def mut_cross_function_call(tree, data, loc, pmap):
    defs = [h.name for h in ast.walk(tree) if isinstance(h, ast.FunctionDef)]
    if len(defs) < 2:
        return None
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in defs:
            other = [d for d in defs if d != n.func.id][0]
            return splice(data, [loc.span(n.func)], [other.encode('utf-8')]), \
                'call target %s -> %s' % (n.func.id, other)
    return None


def mut_module_const_used(tree, data, loc, pmap):
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = n.value
            if isinstance(v, ast.Constant) and isinstance(v.value, int) and not isinstance(v.value, bool):
                return splice(data, [loc.span(v)], [repr(v.value + 1).encode('utf-8')]), \
                    'module const %r -> %r' % (v.value, v.value + 1)
    return None


def mut_class_attr(tree, data, loc, pmap):
    for h in ast.walk(tree):
        if isinstance(h, ast.ClassDef):
            for n in h.body:
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                    v = n.value
                    if isinstance(v, ast.Constant) and isinstance(v.value, int) \
                            and not isinstance(v.value, bool):
                        return splice(data, [loc.span(v)], [repr(v.value + 1).encode('utf-8')]), \
                            'class attr %r -> %r' % (v.value, v.value + 1)
    return None


def mut_except_type_in_pass_try(tree, data, loc, pmap):
    """try 体只有 pass 时，改 except 的异常类型（handler 体是否已被判据剥掉？）。"""
    for h in ast.walk(tree):
        if isinstance(h, ast.Try) and h.handlers:
            body_stmts = [s for s in h.body if not (isinstance(s, ast.Pass))]
            if body_stmts:
                continue
            hd = h.handlers[0]
            if isinstance(hd.type, ast.Name):
                return splice(data, [loc.span(hd.type)],
                              [hd.type.id.encode('utf-8') + b'_MUT']), \
                    'except type %s -> %s_MUT (try body = pass)' % (hd.type.id, hd.type.id)
    return None


def mut_handler_body_return(tree, data, loc, pmap):
    """改 except handler **体内**的 return 值。"""
    for h in ast.walk(tree):
        if isinstance(h, ast.Try) and h.handlers:
            hd = h.handlers[0]
            for s in hd.body:
                if isinstance(s, ast.Return) and isinstance(s.value, ast.Constant) \
                        and isinstance(s.value.value, int):
                    return splice(data, [loc.span(s.value)],
                                  [repr(s.value.value + 1).encode('utf-8')]), \
                        'handler body return %r -> %r' % (s.value.value, s.value.value + 1)
    return None


def mut_match_binding_order(tree, data, loc, pmap):
    """match 捕获模式的**绑定顺序**交换（case [a, b] -> case [b, a]）。"""
    for n in ast.walk(tree):
        if isinstance(n, ast.match_case) and n.pattern is not None:
            p = n.pattern
            if isinstance(p, ast.MatchSequence) and len(p.patterns) == 2:
                s0, s1 = p.patterns
                if not (isinstance(s0, ast.MatchAs) and isinstance(s1, ast.MatchAs)):
                    continue
                a0, a1 = loc.span(s0), loc.span(s1)
                if a0[1] > a1[0]:
                    continue
                return splice(data, [a0, a1], [loc.seg(s1), loc.seg(s0)]), \
                    'match binding order swapped'
    return None


def mut_fstring_conversion(tree, data, loc, pmap):
    """f-string 转换标志：f\"{a}\" -> f\"{a!r}\"。

    注：3.11 的 `ast.FormattedValue` 位置覆盖**整个 f-string**（不只表达式），
    故闭合 `}` 需在 JoinedStr 文本内自行定位（仅取单花括号的简单形态）。
    """
    for n in ast.walk(tree):
        if isinstance(n, ast.JoinedStr):
            jspan = loc.span(n)
            seg = data[jspan[0]:jspan[1]]
            if seg.count(b'{') != 1 or seg.count(b'}') != 1:
                continue
            if not any(isinstance(v, ast.FormattedValue) and v.conversion == -1
                       for v in n.values):
                continue
            idx = seg.rfind(b'}')
            if idx < 0:
                continue
            abs_idx = jspan[0] + idx
            return splice(data, [(abs_idx, abs_idx + 1)], [b'!r}']), \
                'f-string conversion !r added'
    return None


def mut_side_effect_order(tree, data, loc, pmap):
    """两条**带副作用**的独立表达式语句交换顺序。"""
    for holder in ast.walk(tree):
        body = getattr(holder, 'body', None)
        if not isinstance(body, list):
            continue
        for a, b in zip(body, body[1:]):
            if not (isinstance(a, ast.Expr) and isinstance(b, ast.Expr)):
                continue
            if not (isinstance(a.value, ast.Call) and isinstance(b.value, ast.Call)):
                continue
            if a.lineno != a.end_lineno or b.lineno != b.end_lineno:
                continue
            if not isinstance(a.value.func, ast.Attribute) or not isinstance(b.value.func, ast.Attribute):
                continue
            if a.value.func.attr != b.value.func.attr:
                continue
            pa, pb = loc.span(a), loc.span(b)
            if pa[1] > pb[0]:
                continue
            return splice(data, [pa, pb], [loc.seg(b), loc.seg(a)]), \
                'swapped two side-effect statements'
    return None


def mut_annot_module(tree, data, loc, pmap):
    """**模块级**变量注解（模块级注解在运行时求值 ⇒ 进指令流）。"""
    for n in tree.body:
        if isinstance(n, ast.AnnAssign) and n.annotation is not None:
            return splice(data, [loc.span(n.annotation)], [b'str']), \
                'module annotation -> str'
    return None


def mut_assign_handler_body(tree, data, loc, pmap):
    """对照：try 体有**真实语句**（非 pass）时，handler 体是否进入判据视野。"""
    for h in ast.walk(tree):
        if isinstance(h, ast.Try) and h.handlers:
            hd = h.handlers[0]
            for s in hd.body:
                if isinstance(s, ast.Return) and isinstance(s.value, ast.Constant) \
                        and isinstance(s.value.value, int):
                    return splice(data, [loc.span(s.value)],
                                  [repr(s.value.value + 1).encode('utf-8')]), \
                        'handler body return %d -> %d' % (s.value.value, s.value.value + 1)
    return None


PROBES = [
    ('annot_param', 'def f(a: int) -> int:\n    return a + 1\n', mut_annotation_param),
    ('annot_return', 'def f(a) -> int:\n    return a + 1\n', mut_annotation_return),
    ('annot_local', 'def f():\n    v: int = 1\n    return v\n', mut_annotation_local),
    ('docstring_module', '"""MODULE DOC."""\ndef f():\n    return 1\n', mut_docstring_module),
    ('docstring_func', 'def f():\n    """FUNC DOC."""\n    return 1\n', mut_docstring_func),
    ('docstring_class', 'class C:\n    """CLASS DOC."""\n    def m(self):\n        return 1\n', mut_docstring_class),
    ('doc_dunder', '"""MODULE DOC."""\ndef f():\n    return 1\n', mut_doc_dunder),
    ('decorator_order', 'def d1(f):\n    return f\ndef d2(f):\n    return f\n@d1\n@d2\ndef g():\n    return 1\n', mut_decorator_order),
    ('decorator_arg', 'def deco(tag):\n    def wrap(f):\n        return f\n    return wrap\n@deco("A")\ndef g():\n    return 1\n', mut_decorator_arg),
    ('closure_capture', 'def outer():\n    total = 0\n    other = 5\n    def inner():\n        return total + other\n    return inner\n', mut_closure_capture),
    ('nonlocal_target', 'def outer():\n    c = 0\n    d = 1\n    def inner():\n        nonlocal c\n        c += 1\n    inner()\n', mut_nonlocal_target),
    ('global_target', 'G = 0\nH = 1\ndef bump():\n    global G\n    G += 1\n', mut_global_target),
    ('except_alias', 'class MyErr(Exception):\n    pass\ndef f():\n    try:\n        raise MyErr()\n    except MyErr:\n        return 1\n', mut_except_alias),
    ('except_tuple_order', 'class A(Exception):\n    pass\nclass B(Exception):\n    pass\ndef f():\n    try:\n        pass\n    except (A, B):\n        return 1\n', mut_except_tuple_order),
    ('lambda_default', 'def f():\n    g = lambda x=1: x + 1\n    return g()\n', mut_lambda_default),
    ('yield_value', 'def gen():\n    yield 1\n    yield 2\n', mut_yield_value),
    ('async_await', 'async def f():\n    return await g(1)\nasync def g(x):\n    return x\n', mut_async_await),
    ('match_guard', 'def f(v):\n    match v:\n        case 1 if v > 0:\n            return "a"\n        case _:\n            return "b"\n', mut_match_guard),
    ('with_item_order', 'class A:\n    def __enter__(self):\n        return self\n    def __exit__(self, *a):\n        return False\nclass B(A):\n    pass\ndef f():\n    with A() as a, B() as b:\n        return 1\n', mut_with_item_order),
    ('del_target', 'def f():\n    x = 1\n    del x\n    return 2\n', mut_del_target),
    ('assert_message', 'def f(x):\n    assert x, "boom"\n    return 1\n', mut_assert_message),
    ('fstring_literal', 'def f(a):\n    return f"v={a}"\n', mut_fstring_literal),
    ('kwarg_name', 'def g(x=0):\n    return x\ndef f():\n    return g(x=1)\n', mut_kwarg_name),
    ('cross_function_call', 'def helper():\n    return 1\ndef other():\n    return 2\ndef caller():\n    return helper()\n', mut_cross_function_call),
    ('module_const_used', 'LIMIT = 10\ndef f():\n    return LIMIT\n', mut_module_const_used),
    ('class_attr', 'class C:\n    LIMIT = 10\n    def m(self):\n        return self.LIMIT\n', mut_class_attr),
    ('try_pass_except_type', 'def f():\n    try:\n        pass\n    except ValueError:\n        return 1\n', mut_except_type_in_pass_try),
    ('try_pass_handler_body', 'def f():\n    try:\n        pass\n    except ValueError:\n        return 1\n', mut_handler_body_return),
    ('try_raise_handler_body', 'class E(Exception):\n    pass\ndef f():\n    try:\n        raise E()\n    except ValueError:\n        return 1\n', mut_handler_body_return),
    ('match_binding_order', 'def f(v):\n    match v:\n        case [a, b]:\n            return a - b\n        case _:\n            return 0\n', mut_match_binding_order),
    ('fstring_conversion', 'def f(a):\n    return f"v={a}"\n', mut_fstring_conversion),
    ('side_effect_order', 'def f(acc):\n    acc.append(1)\n    acc.append(2)\n    return acc\n', mut_side_effect_order),
    ('annot_module', 'X: int = 1\ndef f():\n    return X\n', mut_annot_module),
    ('try_assign_handler_body', 'def f():\n    try:\n        x = 1\n    except ValueError:\n        return 1\n', mut_assign_handler_body),
]


def run(cmd, timeout=280):
    p = subprocess.run(cmd, capture_output=True, cwd=ROOT, timeout=timeout,
                       encoding='utf-8', errors='replace')
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def judge_status(pyc, src):
    rc, out = run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', pyc, '--source', src])
    status, units = None, ''
    for line in out.splitlines():
        if '[single] status=' in line:
            seg = line.split('status=', 1)[1].split()
            status = seg[0]
            for tok in seg:
                if tok.startswith('units='):
                    units = tok
    return status, units


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PROBE_DIR, exist_ok=True)
    os.makedirs(MUT_DIR, exist_ok=True)
    results = []
    for tag, src, mutfn in PROBES:
        if args.only and args.only != tag:
            continue
        base = os.path.join(PROBE_DIR, 'cp_' + tag)
        py, pyc, ok = base + '.py', base + '.pyc', base + 'OK.py'
        with open(py, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src)
        py_compile.compile(py, cfile=pyc, doraise=True, optimize=0)
        rc, out = run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        rec = {'tag': tag, 'pyc': os.path.relpath(pyc, ROOT).replace('\\', '/'), 'regen_rc': rc}
        if not os.path.isfile(ok):
            rec['verdict'] = 'NO_PRODUCT'
            results.append(rec)
            print('%-22s NO_PRODUCT (regen_rc=%s)' % (tag, rc))
            continue
        st, units = judge_status(pyc, ok)
        rec['baseline_status'] = st
        rec['baseline_units'] = units
        raw = open(ok, 'rb').read()
        try:
            tree = ast.parse(raw)
        except SyntaxError as e:
            rec['verdict'] = 'PRODUCT_NOT_PARSEABLE'
            rec['detail'] = str(e)
            results.append(rec)
            print('%-22s PRODUCT_NOT_PARSEABLE' % tag)
            continue
        loc = mutation_lib.Loc(raw)
        pmap = mutation_lib.parents_map(tree)
        try:
            res = mutfn(tree, raw, loc, pmap)
        except Exception as exc:
            rec['verdict'] = 'MUTATOR_ERROR'
            rec['traceback'] = traceback.format_exc()[-700:]
            results.append(rec)
            print('%-22s MUTATOR_ERROR %s' % (tag, type(exc).__name__))
            print(rec['traceback'])
            continue
        if not res:
            rec['verdict'] = 'NOT_APPLICABLE'
            results.append(rec)
            print('%-22s NOT_APPLICABLE              baseline=%s' % (tag, st))
            continue
        mut, site = res
        mpath = os.path.join(MUT_DIR, 'cp_%s_mut.py' % tag)
        with open(mpath, 'wb') as f:
            f.write(mut)
        mst, munits = judge_status(pyc, mpath)
        rec['site'] = site
        rec['mut_status'] = mst
        rec['mut_units'] = munits
        rec['verdict'] = 'MISS' if mst == 'success' else ('CAUGHT' if mst == 'failure' else 'NONJUDGE:' + str(mst))
        rec['mutated_file'] = os.path.relpath(mpath, ROOT).replace('\\', '/')
        results.append(rec)
        print('%-22s baseline=%-9s mutated=%-9s %-14s %s'
              % (tag, st, mst, rec['verdict'], site))

    with open(os.path.join(OUT, 'construct_probe.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
        f.write('\n')
    n_miss = sum(1 for r in results if r.get('verdict') == 'MISS')
    n_caught = sum(1 for r in results if r.get('verdict') == 'CAUGHT')
    print('\nconstruct probes: %d  MISS=%d  CAUGHT=%d  other=%d'
          % (len(results), n_miss, n_caught, len(results) - n_miss - n_caught))


if __name__ == '__main__':
    main()
