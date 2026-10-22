#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：语义变异族库（对**产物**注入已知语义错误）。

原则：
  * 只改**产物**（OK.py），不动原始 .pyc、不动判据、不动产品代码；
  * 每个变异都是**语义**错误（可观察行为改变），不是排版/注释/空行改动；
  * 用 CPython `ast` 定位注入点，按 UTF-8 字节偏移做**文本切片替换**，
    变异之外的字节保持原样（避免格式化噪声混入读数）；
  * 每个变异函数返回 (mutated_bytes, site) 或 None（该产物不适用）。

用法：
  python -X utf8 mutation_lib.py <product.py> [family ...]
"""
from __future__ import annotations

import ast
import re


# ── 字节级定位工具 ───────────────────────────────────────────────────────────


def line_starts(data: bytes):
    offs = [0]
    for i, b in enumerate(data):
        if b == 0x0A:
            offs.append(i + 1)
    return offs


class Loc:
    def __init__(self, data: bytes):
        self.data = data
        self.offs = line_starts(data)

    def pos(self, lineno: int, col: int) -> int:
        return self.offs[lineno - 1] + col

    def span(self, node):
        return (self.pos(node.lineno, node.col_offset),
                self.pos(node.end_lineno, node.end_col_offset))

    def seg(self, node) -> bytes:
        s, e = self.span(node)
        return self.data[s:e]

    def line_span(self, node):
        s = self.offs[node.lineno - 1]
        e = self.offs[node.end_lineno] if node.end_lineno < len(self.offs) else len(self.data)
        return s, e


def splice(data: bytes, spans, new_texts) -> bytes:
    """spans: [(start,end)] 按 start 升序且互不重叠；new_texts: 对应替换文本(bytes)。"""
    out = bytearray()
    cur = 0
    for (s, e), t in zip(spans, new_texts):
        out += data[cur:s]
        out += t if isinstance(t, bytes) else t.encode('utf-8')
        cur = e
    out += data[cur:]
    return bytes(out)


def parents_map(tree):
    p = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            p[child] = node
    return p


def in_function(node, pmap) -> bool:
    cur = node
    while cur in pmap:
        cur = pmap[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return True
    return False


def is_docstring(node, pmap) -> bool:
    parent = pmap.get(node)
    if not isinstance(parent, ast.Expr):
        return False
    holder = pmap.get(parent)
    body = getattr(holder, 'body', None)
    return isinstance(body, list) and bool(body) and body[0] is parent


# ── 变异族 ───────────────────────────────────────────────────────────────────


def m_num_int(tree, data, loc, pmap):
    """(a) 数值字面量 1->2：改数值。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool) and node.value != 0:
            old = loc.seg(node)
            if not re.fullmatch(rb'[0-9]+', old):
                continue
            new = str(node.value + 1).encode('utf-8')
            return splice(data, [loc.span(node)], [new]), \
                'int literal %s -> %s' % (old.decode(), new.decode())
    return None


def _negated(node, pmap) -> bool:
    """该常量是否处于一元负号/正号之下（`-1` 的 AST 是 UnaryOp(USub, Constant(1))）。"""
    p = pmap.get(node)
    return isinstance(p, ast.UnaryOp) and isinstance(p.op, (ast.USub, ast.UAdd))


def _bare_const_stmt(node, pmap) -> bool:
    """该常量是否处于「裸常量表达式语句」中（CPython 直接优化掉，指令流里没有它）。"""
    p = pmap.get(node)
    if not isinstance(p, ast.Expr):
        return False
    holder = pmap.get(p)
    body = getattr(holder, 'body', None)
    if not isinstance(body, list) or not body or body[0] is not p:
        return False
    return True


def m_int_to_bool(tree, data, loc, pmap):
    """(d) x = 1 -> x=True：**纯类型**语义改变（int 1 -> bool True），值不变。

    只取**值恰为 1** 的整数字面量：这样变异前后 `==` 判定仍为真（`1 == True`），
    差异**只**落在「值的类型」上 ⇒ 判据若漏检，漏的就是纯粹的**值类型盲区**，
    而不是「值变了但恰好可被 `==` 区分」的混合读数。

    同时排除一元负号下的常量（`-1` -> `-True` 仍等于 -1，是**惰性**变异）。
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool) and node.value == 1:
            if _negated(node, pmap):
                continue
            old = loc.seg(node)
            if not re.fullmatch(rb'1', old):
                continue
            return splice(data, [loc.span(node)], [b'True']), \
                'int literal 1 -> True (type-only change)'
    return None


def m_any_int_to_bool(tree, data, loc, pmap):
    """(d') 任意整数字面量 -> True：类型改变**且**可能改值。

    与 (d) 对照用：若被取值 != 1 的字面量，则 `362000 == True` 为假，
    判据抓到的是「值变了」而非「类型变了」⇒ 不可用于度量值类型盲区。
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool) and node.value != 0:
            if _negated(node, pmap):
                continue
            old = loc.seg(node)
            if not re.fullmatch(rb'[0-9]+', old):
                continue
            return splice(data, [loc.span(node)], [b'True']), \
                'int literal %s -> True (type+maybe-value change)' % old.decode()
    return None


def m_int_to_float(tree, data, loc, pmap):
    """(i) x = 1 -> x = 1.0：值**类型**语义改变（int -> float）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool) and node.value != 0:
            old = loc.seg(node)
            if not re.fullmatch(rb'[0-9]+', old):
                continue
            new = old + b'.0'
            return splice(data, [loc.span(node)], [new]), \
                'int literal %s -> %s' % (old.decode(), new.decode())
    return None


def m_str_content(tree, data, loc, pmap):
    """(e) 字符串字面量内容改变（非 docstring、非裸常量语句）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
            if is_docstring(node, pmap):
                continue
            if _bare_const_stmt(node, pmap):
                continue
            seg = loc.seg(node)
            if not seg.startswith((b"'", b'"', b"b'", b'b"', b"f'", b'f"', b"r'", b'r"')):
                continue
            new = node.value + 'X'
            return splice(data, [loc.span(node)], [repr(new).encode('utf-8')]), \
                'str literal %r -> %r' % (node.value[:20], new[:20])
    return None


def m_func_docstring(tree, data, loc, pmap):
    """(j) 函数 docstring 内容改变（函数 docstring 在 co_consts[0]，无指令引用）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not holder.body or not isinstance(holder.body[0], ast.Expr):
            continue
        const = holder.body[0].value
        if not (isinstance(const, ast.Constant) and isinstance(const.value, str)):
            continue
        new = const.value + 'Y'
        return splice(data, [loc.span(const)], [repr(new).encode('utf-8')]), \
            'func docstring %r -> %r' % (const.value[:20], new[:20])
    return None


def m_cmp_polarity(tree, data, loc, pmap):
    """(b) 交换布尔比较极性 a<b -> a>b。"""
    sym = {ast.Lt: (b'<', b'>'), ast.Gt: (b'>', b'<'),
           ast.LtE: (b'<=', b'>='), ast.GtE: (b'>=', b'<=')}
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in sym:
            old_s, new_s = sym[type(node.ops[0])]
            left_end = loc.span(node.left)[1]
            right_start = loc.span(node.comparators[0])[0]
            gap = data[left_end:right_start]
            if old_s not in gap:
                continue
            new_gap = gap.replace(old_s, new_s, 1)
            return splice(data, [(left_end, right_start)], [new_gap]), \
                'Compare %s -> %s' % (old_s.decode(), new_s.decode())
    return None


def m_del_assign(tree, data, loc, pmap):
    """(c) 删除一条赋值语句（块内保留至少一条语句，避免 IndentationError）。"""
    for holder in ast.walk(tree):
        body = getattr(holder, 'body', None)
        if not isinstance(body, list) or len(body) < 2:
            continue
        for stmt in body:
            if not isinstance(stmt, ast.Assign):
                continue
            s, e = loc.line_span(stmt)
            seg = data[s:e]
            if not seg.strip() or b'#' in seg.split(b'\n')[0]:
                continue
            if not seg.endswith(b'\n'):
                continue
            rest = b''
            for other in body:
                if other is stmt:
                    continue
                os_, oe = loc.line_span(other)
                rest += data[os_:oe]
            if not rest.strip():
                continue
            return splice(data, [(s, e)], [b'']), 'deleted one Assign stmt'
    return None


def m_stmt_swap(tree, data, loc, pmap):
    """(f) 交换两条相邻**独立**语句的执行顺序。

    「独立」判据：第二条语句不读取第一条语句所赋的名字 ⇒ 交换后语义必然改变，
    且不依赖求值顺序的偶然性（避免**惰性**变异混入读数）。
    """
    def assigned_names(stmt):
        out = set()
        for n in ast.walk(stmt):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                out.add(n.id)
        return out

    def loaded_names(stmt):
        out = set()
        for n in ast.walk(stmt):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                out.add(n.id)
        return out

    for holder in ast.walk(tree):
        body = getattr(holder, 'body', None)
        if not isinstance(body, list):
            continue
        for a, b in zip(body, body[1:]):
            if not (isinstance(a, ast.Assign) and isinstance(b, ast.Assign)):
                continue
            if a.lineno != a.end_lineno or b.lineno != b.end_lineno:
                continue
            if not assigned_names(a):
                continue
            if assigned_names(a) & loaded_names(b):
                continue          # 有数据依赖 ⇒ 非独立语句，跳过
            sa, sb = loc.seg(a), loc.seg(b)
            if b'=' not in sa or b'=' not in sb:
                continue
            pa, pb = loc.span(a), loc.span(b)
            if pa[1] > pb[0]:
                continue
            return splice(data, [pa, pb], [sb, sa]), \
                'swapped two independent Assign stmts'
    return None


def m_rename_local(tree, data, loc, pmap):
    """(g) 改标识符：函数内形参/局部变量一致改名。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = holder.args
        cand = None
        for a in list(getattr(args, 'posonlyargs', [])) + list(args.args) + list(args.kwonlyargs):
            cand = a
            break
        if cand is None or not cand.arg or cand.arg.startswith('__'):
            continue
        old = cand.arg
        new = old + '_mut'
        spans, texts = [], []
        for node in ast.walk(holder):
            if isinstance(node, ast.arg) and node.arg == old:
                spans.append(loc.span(node))
                texts.append(new.encode('utf-8'))
            elif isinstance(node, ast.Name) and node.id == old:
                spans.append(loc.span(node))
                texts.append(new.encode('utf-8'))
        if not spans:
            continue
        spans.sort()
        return splice(data, spans, texts), 'renamed local %r -> %r' % (old, new)
    return None


def m_rename_func(tree, data, loc, pmap):
    """(g2) 改函数名（模块级函数定义 + 其引用）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        old = holder.name
        new = old + '_mut'
        spans = [loc.span(holder)]
        texts = [None]
        # 只替换 def 关键字后的名字：定位到 name 之前的 token
        head = data[loc.span(holder)[0]:loc.span(holder)[1]]
        idx = head.find(old.encode('utf-8'))
        if idx < 0:
            continue
        s = loc.span(holder)[0] + idx
        spans = [(s, s + len(old.encode('utf-8')))]
        texts = [new.encode('utf-8')]
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == old:
                spans.append(loc.span(node))
                texts.append(new.encode('utf-8'))
        spans.sort()
        return splice(data, spans, texts), 'renamed function %r -> %r' % (old, new)
    return None


def m_arg_swap(tree, data, loc, pmap):
    """(h) 交换两个实参顺序。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and len(node.args) >= 2:
            a, b = node.args[0], node.args[1]
            if a.lineno != node.end_lineno or b.lineno != node.end_lineno:
                continue
            if not isinstance(a, (ast.Name, ast.Constant, ast.Attribute)):
                continue
            if not isinstance(b, (ast.Name, ast.Constant, ast.Attribute)):
                continue
            pa, pb = loc.span(a), loc.span(b)
            if pa[1] > pb[0]:
                continue
            return splice(data, [pa, pb], [loc.seg(b), loc.seg(a)]), 'swapped two call args'
    return None


def m_posonly(tree, data, loc, pmap):
    """(k) 去掉位置限定符 `/`（只改 co_flags，无字节码差异）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        posonly = list(getattr(holder.args, 'posonlyargs', []))
        if not posonly:
            continue
        last = posonly[-1]
        hstart, hend = loc.span(holder)
        header = data[hstart:hend]
        hend_rel = header.find(b':')
        if hend_rel < 0:
            continue
        last_end = loc.span(last)[1]
        tail = data[last_end:hstart + hend_rel]
        if b'/' not in tail:
            continue
        idx = tail.index(b'/')
        abs_idx = last_end + idx
        return splice(data, [(abs_idx, abs_idx + 1)], [b'']), 'removed positional-only marker'
    return None


def m_except_tuple(tree, data, loc, pmap):
    """(l) except X -> except (X,)：异常类型语义改变。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is not None:
            t = node.type
            if isinstance(t, ast.Name):
                s = loc.seg(t)
                return splice(data, [loc.span(t)], [b'(' + s + b',)']), \
                    'except %s -> except (%s,)' % (s.decode(), s.decode())
    return None


def m_ann_local(tree, data, loc, pmap):
    """(m) 函数内局部注解 int -> str（运行时不求值 => 无字节码）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            if not in_function(node, pmap):
                continue
            return splice(data, [loc.span(node.annotation)], [b'str']), \
                'local annotation -> str'
    return None


def m_dead_code(tree, data, loc, pmap):
    """(n) 在 return 之后插入不可达语句（fix_unreachable 会抹平）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(holder, 'body', None)
        if not body:
            continue
        last = body[-1]
        if not isinstance(last, ast.Return) or last.value is None:
            continue
        s, e = loc.line_span(last)
        return splice(data, [(e, e)], [b'    _dead_mut = 1\n']), 'inserted unreachable stmt'
    return None


def m_handler_body(tree, data, loc, pmap):
    """(o) except handler **体内**的返回值改写（handler 体是否进入判据视野？）。"""
    for holder in ast.walk(tree):
        handlers = getattr(holder, 'handlers', None)
        if not isinstance(handlers, list):
            continue
        for hd in handlers:
            for stmt in hd.body:
                if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) \
                        and isinstance(stmt.value.value, int) and not isinstance(stmt.value.value, bool):
                    return splice(data, [loc.span(stmt.value)],
                                  [repr(stmt.value.value + 1).encode('utf-8')]), \
                        'handler body return %d -> %d' % (stmt.value.value, stmt.value.value + 1)
    return None


def m_except_type(tree, data, loc, pmap):
    """(p) except 的异常类型改名（异常类型别名是否可见？）。"""
    for holder in ast.walk(tree):
        handlers = getattr(holder, 'handlers', None)
        if not isinstance(handlers, list):
            continue
        for hd in handlers:
            t = hd.type
            if isinstance(t, ast.Name):
                return splice(data, [loc.span(t)], [t.id.encode('utf-8') + b'_MUT']), \
                    'except type %s -> %s_MUT' % (t.id, t.id)
    return None


def m_rename_used_local(tree, data, loc, pmap):
    """(g') 改**被使用**的局部变量名（指令流里 LOAD_FAST 的 argval 会变）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        used = set()
        for node in ast.walk(holder):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        cand = None
        for a in list(getattr(holder.args, 'posonlyargs', [])) + list(holder.args.args):
            if a.arg in used:
                cand = a
                break
        if cand is None:
            continue
        old = cand.arg
        new = old + '_mut'
        spans, texts = [], []
        for node in ast.walk(holder):
            if isinstance(node, ast.arg) and node.arg == old:
                spans.append(loc.span(node))
                texts.append(new.encode('utf-8'))
            elif isinstance(node, ast.Name) and node.id == old:
                spans.append(loc.span(node))
                texts.append(new.encode('utf-8'))
        if not spans:
            continue
        spans.sort()
        return splice(data, spans, texts), 'renamed used local %r -> %r' % (old, new)
    return None


def m_param_order(tree, data, loc, pmap):
    """(h') 交换两个**形参**的顺序：调用语义改变，但指令流与 co_varnames 之外的维度可能完全一致。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = list(holder.args.posonlyargs) + list(holder.args.args)
        if len(args) < 2:
            continue
        a, b = args[0], args[1]
        if a.arg == b.arg:
            continue
        pa, pb = loc.span(a), loc.span(b)
        if pa[1] > pb[0]:
            continue
        return splice(data, [pa, pb], [loc.seg(b), loc.seg(a)]), \
            'swapped formal params %r <-> %r' % (a.arg, b.arg)
    return None


def m_decorator_swap(tree, data, loc, pmap):
    """(s) 交换两个装饰器的顺序（装饰器求值/应用顺序是语义）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        decs = holder.decorator_list
        if len(decs) < 2:
            continue
        a, b = decs[0], decs[1]
        pa, pb = loc.span(a), loc.span(b)
        if pa[1] > pb[0]:
            continue
        # 装饰器行首有 '@'，需连同 '@' 一起换位
        sa = loc.line_span(a)
        sb = loc.line_span(b)
        seg_a = data[sa[0]:sa[1]]
        seg_b = data[sb[0]:sb[1]]
        if not seg_a.startswith(b'@') or not seg_b.startswith(b'@'):
            continue
        return splice(data, [(sa[0], sa[1]), (sb[0], sb[1])], [seg_b, seg_a]), \
            'swapped two decorators'
    return None


def m_fstring_spec(tree, data, loc, pmap):
    """(t) 改 f-string 的转换/格式说明（f"{a}" -> f"{a!r}"）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for v in node.values:
                if isinstance(v, ast.FormattedValue) and v.conversion == -1 and v.format_spec is None:
                    span = loc.span(v)
                    seg = data[span[0]:span[1]]
                    if not seg.endswith(b'}'):
                        continue
                    return splice(data, [(span[1] - 1, span[1])], [b'!r}']), \
                        'f-string conversion added (!r)'
    return None


def m_ann_param(tree, data, loc, pmap):
    """(u) 改**形参注解**（注解在 def 时求值并进 __annotations__，不在指令流里）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for a in list(getattr(holder.args, 'posonlyargs', [])) + list(holder.args.args) \
                + list(holder.args.kwonlyargs):
            if a.annotation is None:
                continue
            return splice(data, [loc.span(a.annotation)], [b'str']), \
                'param annotation -> str'
    return None


def m_lambda_default(tree, data, loc, pmap):
    """(v) 改 lambda 的默认值（默认值在 MAKE_FUNCTION 时压栈 → 指令流里可见）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda) and node.args.defaults:
            d = node.args.defaults[0]
            if isinstance(d, ast.Constant) and isinstance(d.value, int) \
                    and not isinstance(d.value, bool):
                return splice(data, [loc.span(d)], [repr(d.value + 1).encode('utf-8')]), \
                    'lambda default %r -> %r' % (d.value, d.value + 1)
    return None


def m_global_stmt(tree, data, loc, pmap):
    """(w) 给「赋值了模块级名字」的函数插入 global 声明（作用域语义改变）。"""
    for holder in ast.walk(tree):
        if not isinstance(holder, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        assigned = set()
        for node in ast.walk(holder):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                assigned.add(node.id)
        if not assigned:
            continue
        name = sorted(assigned)[0]
        hstart = loc.span(holder)[0]
        # 在函数体第一条语句前插入 `global name`
        body = holder.body
        first = body[0]
        ls = loc.line_span(first)
        indent = data[ls[0]:ls[0] + (len(data[ls[0]:ls[1]]) - len(data[ls[0]:ls[1]].lstrip()))]
        ins = indent + ('global %s\n' % name).encode('utf-8')
        return splice(data, [(ls[0], ls[0])], [ins]), 'inserted global %r' % name
    return None


def m_assert_msg(tree, data, loc, pmap):
    """(z) 改 assert 的消息（消息是 LOAD_CONST → 指令流里可见）。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and node.msg is not None:
            if isinstance(node.msg, ast.Constant) and isinstance(node.msg.value, str):
                new = node.msg.value + 'Z'
                return splice(data, [loc.span(node.msg)], [repr(new).encode('utf-8')]), \
                    'assert msg %r -> %r' % (node.msg.value[:20], new[:20])
    return None


def m_module_docstring(tree, data, loc, pmap):
    """(x) 改模块 docstring（只进 co_consts[0]，无指令引用）。"""
    if not tree.body:
        return None
    first = tree.body[0]
    if not isinstance(first, ast.Expr):
        return None
    c = first.value
    if not (isinstance(c, ast.Constant) and isinstance(c.value, str)):
        return None
    new = c.value + 'W'
    return splice(data, [loc.span(c)], [repr(new).encode('utf-8')]), \
        'module docstring %r -> %r' % (c.value[:20], new[:20])


def m_kwparam_rename(tree, data, loc, pmap):
    """(g2) **保证语义**的标识符改写：改「被以关键字实参调用」的形参名。

    局部变量改名往往是**语义惰性**的（名字不进指令流 ⇒ 改不改都一样），
    那样得到的「漏检」不能算判据盲区。本族改的是**以关键字实参传入的形参**：
    改完后调用点会抛 TypeError ⇒ 语义必然改变 ⇒ 漏检即为真盲区。
    """
    defs = {}
    for h in ast.walk(tree):
        if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.setdefault(h.name, h)
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name):
            continue
        fn = defs.get(n.func.id)
        if fn is None:
            continue
        args = (list(getattr(fn.args, 'posonlyargs', [])) + list(fn.args.args)
                + list(fn.args.kwonlyargs))
        names = {a.arg for a in args}
        for kw in n.keywords:
            if not kw.arg or kw.arg not in names:
                continue
            old, new = kw.arg, kw.arg + '_mut'
            spans, texts = [], []
            for a in args:
                if a.arg == old:
                    spans.append(loc.span(a))
                    texts.append(new.encode('utf-8'))
            ks = loc.span(kw)[0]
            spans.append((ks, ks + len(old.encode('utf-8'))))
            texts.append(new.encode('utf-8'))
            pairs = sorted(zip(spans, texts))
            return splice(data, [a for a, _ in pairs], [b for _, b in pairs]), \
                'kw-param %r -> %r' % (old, new)
    return None


MUTATIONS = {
    'a_num_int': m_num_int,
    'b_cmp_polarity': m_cmp_polarity,
    'c_del_assign': m_del_assign,
    'd_int_to_bool': m_int_to_bool,
    'd_any_int_to_bool': m_any_int_to_bool,
    'e_str_content': m_str_content,
    'f_stmt_swap': m_stmt_swap,
    'g_rename_local': m_rename_local,
    'g_used_local': m_rename_used_local,
    'g2_rename_func': m_rename_func,
    'g3_kwparam_rename': m_kwparam_rename,
    'h_arg_swap': m_arg_swap,
    'h_param_order': m_param_order,
    'i_int_to_float': m_int_to_float,
    'j_func_docstring': m_func_docstring,
    'k_posonly': m_posonly,
    'l_except_tuple': m_except_tuple,
    'm_ann_local': m_ann_local,
    'n_dead_code': m_dead_code,
    'o_handler_body': m_handler_body,
    'p_except_type': m_except_type,
    's_decorator_swap': m_decorator_swap,
    't_fstring_spec': m_fstring_spec,
    'u_ann_param': m_ann_param,
    'v_lambda_default': m_lambda_default,
    'w_global_stmt': m_global_stmt,
    'x_module_docstring': m_module_docstring,
    'z_assert_msg': m_assert_msg,
}

# 任务要求的 8 类（§4 报告主表口径）：
#   (a) 数值 1->2 / (b) 比较极性反转 / (c) 删赋值 / (d) x=1->x=True
#   (e) 改字符串 / (f) 交换两条独立语句序 / (g) 改标识符 / (h) 交换实参序
REQUIRED_FAMILIES = ['a_num_int', 'b_cmp_polarity', 'c_del_assign', 'd_int_to_bool',
                     'e_str_content', 'f_stmt_swap', 'g_rename_local', 'h_arg_swap']


def apply_mutation(name, data: bytes):
    """返回 (mutated_bytes, site) 或 (None, None)。"""
    try:
        tree = ast.parse(data)
    except SyntaxError:
        return None, 'PARSE_ERROR'
    loc = Loc(data)
    pmap = parents_map(tree)
    try:
        res = MUTATIONS[name](tree, data, loc, pmap)
    except Exception as exc:
        return None, 'MUTATOR_ERROR:%s' % type(exc).__name__
    return res if res is not None else (None, None)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    raw = open(sys.argv[1], 'rb').read()
    for fam in (sys.argv[2:] or list(MUTATIONS)):
        mut, site = apply_mutation(fam, raw)
        print('%-18s %s' % (fam, site or '-'))
        if mut:
            print('    ', mut.split(b'\n')[0][:120])
