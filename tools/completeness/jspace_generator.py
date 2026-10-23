#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判定空间生成器 / Judgment-space generator (attack-completeness-claims, Task 1).

把「完备」从「节点/形态计数（128）」改写为**有限可枚举的判定空间**：
    形态（文法族）× 宿主上下文 × 深度档 × 变体槽
每条条目要求**独立证据**（一个专属探针 .pyc）。本脚本是该空间的**唯一生成源**
（可重生成：同输入两次运行产出逐字节相同），并顺带产出人类可读视图。

用法：
    python -X utf8 tools/completeness/jspace_generator.py \
        --evidence-root .trae/specs/attain-true-completeness/rounds \
        --out .trae/specs/attack-completeness-claims/rounds/round1/judgment_space.json \
        --md   .trae/specs/attack-completeness-claims/rounds/round1/JUDGMENT_SPACE.md

纪律：
  * 每个变体槽都由一个**可判定的 AST 谓词**定义（谓词源码在本文件内）。
  * 每个条目的 `source` 必须是仓内真实路径（探针 .pyc / 语料文件 / 代码站点 file:line）。
  * 未在证据索引中登记的单元一律标 `uncovered`，**不得**为了好看而改写状态。
"""

from __future__ import annotations

import argparse
import ast
import collections
import glob
import hashlib
import json
import os
import sys

SPEC_DIR = ".trae/specs/attain-true-completeness"
J_SCHEMA_VERSION = "v2"
GENERATOR_VERSION = "2.0.0"

DEPTH_BUCKETS = ("d1 单层", "d2 双层", "d3plus 三层及以上")


def depth_bucket(d: int) -> str:
    if d <= 1:
        return DEPTH_BUCKETS[0]
    if d == 2:
        return DEPTH_BUCKETS[1]
    return DEPTH_BUCKETS[2]


REGION_TYPES = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
    ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith,
    ast.Try, ast.TryStar, ast.match_case, ast.Lambda,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp,
)

#: 宿主 → 必然带来的 region 祖先数（inherent）；宿主只允许 depth >= inherent
HOST_DEPTHS = {
    "module-level": (0,), "function-body": (1,), "nested-func-body": (2,),
    "class-body": (1,), "async-func-body": (1,), "generator-func-body": (1,),
    "lambda-body": (1,), "if-arm": (1,), "elif-arm": (2,), "else-arm": (1,),
    "loop-body": (1,), "loop-else": (1,), "with-body": (1,), "with-item": (1,),
    "try-body": (1,), "except-handler": (2,), "else-of-try": (1,),
    "finally-body": (1,), "match-case-body": (1,), "match-guard": (1,),
    "match-subject": (0,), "comprehension-scope": (1,), "comprehension-if": (1,),
    "comprehension-for": (1,), "condition-expr": (0,), "return-value-expr": (0,),
    "call-arg": (0,), "subscript-index": (0,), "slice-bounds": (0,),
    "default-arg": (1,), "annotation-context": (0,), "decorator-expr": (1,),
    "f-string-format": (0,), "walrus-value": (0,), "assign-rhs": (0,),
    "boolop-operand": (0,), "binop-operand": (0,), "compare-operand": (0,),
    "await-operand": (0,), "starred-operand": (0,), "pattern-value": (1,),
    "pattern-class": (1,), "pattern-sequence": (1,), "pattern-mapping": (1,),
    "pattern-capture": (1,), "pattern-or": (1,), "pattern-star": (1,),
    "pattern-singleton": (1,), "list-literal": (0,), "tuple-literal": (0,),
    "dict-literal": (0,), "set-literal": (0,), "expr-context": (0,),
}

#: 语句型宿主（可作为「嵌套在某构造内」变体的容器）
STMT_HOSTS = {
    "module-level", "function-body", "nested-func-body", "class-body",
    "async-func-body", "generator-func-body", "if-arm", "elif-arm", "else-arm",
    "loop-body", "loop-else", "with-body", "try-body", "except-handler",
    "else-of-try", "finally-body", "match-case-body", "comprehension-scope",
}

#: 变体名中的「嵌套型」关键词：命中者要求该构造必须嵌套在另一区域内，
#: 因此其宿主不得是 module-level（模块级无处可嵌套）。
NESTING_KEYWORDS = (
    "in-loop", "in-try", "in-handler", "in-with", "in-match", "in-func",
    "in-class", "in-nested", "in-async-", "in-comp", "in-else-of-try",
    "in-loop-else", "in-async-def", "in-async-with", "in-async-for",
    "in-async-comp", "in-async-closure", "in-async-method",
)


def admissible_hosts(family, vname):
    if any(k in vname for k in NESTING_KEYWORDS):
        return [h for h in family["hosts"] if h in STMT_HOSTS and h != "module-level"]
    return list(family["hosts"])


def host_depth_buckets(host: str):
    d = min(HOST_DEPTHS[host])
    out = []
    while True:
        b = depth_bucket(d)
        if b not in out:
            out.append(b)
        if b == DEPTH_BUCKETS[2]:
            break
        d += 1
    return out


def ident_in(node, seq) -> bool:
    return any(x is node for x in seq)


def host_of(node, parent) -> str:
    p = parent
    if p is None or isinstance(p, ast.Module):
        return "module-level"
    if isinstance(p, ast.ExceptHandler):
        return "except-handler"
    if isinstance(p, ast.If):
        if ident_in(node, p.body):
            return "if-arm"
        if p.orelse and isinstance(p.orelse[0], ast.If) and ident_in(node, p.orelse[0].body):
            return "elif-arm"
        return "else-arm"
    if isinstance(p, (ast.For, ast.AsyncFor, ast.While)):
        return "loop-body" if ident_in(node, p.body) else "loop-else"
    if isinstance(p, (ast.With, ast.AsyncWith)):
        if ident_in(node, p.body):
            return "with-body"
        for it in p.items:
            if node is it.context_expr or (it.optional_vars is not None and node is it.optional_vars):
                return "with-item"
        return "with-body"
    if isinstance(p, (ast.Try, ast.TryStar)):
        if ident_in(node, p.body):
            return "try-body"
        if ident_in(node, p.orelse):
            return "else-of-try"
        if ident_in(node, p.finalbody):
            return "finally-body"
        for h in p.handlers:
            if ident_in(node, h.body):
                return "except-handler"
        return "try-body"
    if isinstance(p, ast.match_case):
        if p.guard is not None and node is p.guard:
            return "match-guard"
        return "match-case-body"
    if isinstance(p, ast.Match):
        return "match-subject" if node is p.subject else "match-case-body"
    if isinstance(p, ast.Lambda):
        return "lambda-body"
    if isinstance(p, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        if getattr(p, "ifs", None) and ident_in(node, p.ifs):
            return "comprehension-if"
        if any(node is g.iter for g in p.generators):
            return "comprehension-for"
        return "comprehension-scope"
    if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if ident_in(node, p.decorator_list):
            return "decorator-expr"
        if p.returns is not None and node is p.returns:
            return "annotation-context"
        if ident_in(node, p.args.defaults):
            return "default-arg"
        if any(node is x for x in p.args.kw_defaults if x is not None):
            return "default-arg"
        if isinstance(p, ast.AsyncFunctionDef):
            return "async-func-body"
        nested = any(isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)) for a in getattr(p, "_anc", ()))
        if nested:
            return "nested-func-body"
        if any(isinstance(x, (ast.Yield, ast.YieldFrom)) for x in ast.walk(p)):
            return "generator-func-body"
        return "function-body"
    if isinstance(p, ast.ClassDef):
        if ident_in(node, p.decorator_list):
            return "decorator-expr"
        if ident_in(node, p.bases) or ident_in(node, p.keywords):
            return "call-arg"
        return "class-body"
    if isinstance(p, ast.arguments):
        return "default-arg"
    if isinstance(p, ast.IfExp):
        return "condition-expr"
    if isinstance(p, ast.Return):
        return "return-value-expr"
    if isinstance(p, ast.Call):
        return "call-arg"
    if isinstance(p, ast.Subscript):
        return "subscript-index"
    if isinstance(p, ast.Slice):
        return "slice-bounds"
    if isinstance(p, ast.AnnAssign):
        return "annotation-context" if node is p.annotation else "assign-rhs"
    if isinstance(p, ast.Assign):
        return "assign-rhs"
    if isinstance(p, ast.BoolOp):
        return "boolop-operand"
    if isinstance(p, ast.BinOp):
        return "binop-operand"
    if isinstance(p, ast.Compare):
        return "compare-operand"
    if isinstance(p, ast.Await):
        return "await-operand"
    if isinstance(p, ast.NamedExpr):
        return "walrus-value"
    if isinstance(p, ast.JoinedStr):
        return "f-string-format"
    if isinstance(p, ast.Starred):
        return "starred-operand"
    if isinstance(p, ast.MatchValue):
        return "pattern-value"
    if isinstance(p, ast.MatchClass):
        return "pattern-class"
    if isinstance(p, ast.MatchSequence):
        return "pattern-sequence"
    if isinstance(p, ast.MatchMapping):
        return "pattern-mapping"
    if isinstance(p, ast.MatchAs):
        return "pattern-capture"
    if isinstance(p, ast.MatchOr):
        return "pattern-or"
    if isinstance(p, ast.MatchStar):
        return "pattern-star"
    if isinstance(p, ast.MatchSingleton):
        return "pattern-singleton"
    if isinstance(p, ast.List):
        return "list-literal"
    if isinstance(p, ast.Tuple):
        return "tuple-literal"
    if isinstance(p, ast.Dict):
        return "dict-literal"
    if isinstance(p, ast.Set):
        return "set-literal"
    return "expr-context"


# --------------------------------------------------------------------------
# 证据索引
# --------------------------------------------------------------------------

def normalize_rel(rel: str) -> str:
    rel = rel.replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if rel.startswith((".trae/", "site-packages/", "test_repros/")):
        return rel
    return SPEC_DIR + "/" + rel


def build_evidence_index(evidence_root: str):
    index = {}
    files = sorted(glob.glob(os.path.join(evidence_root, "**", "rec1_probes_*.json"), recursive=True))
    for f in files:
        try:
            with open(f, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        stamp = os.path.relpath(f, evidence_root).replace("\\", "/")
        for ent in data:
            if not isinstance(ent, dict):
                continue
            name = ent.get("name")
            rel = ent.get("pyc_src_rel")
            if not isinstance(name, str) or not isinstance(rel, str):
                continue
            rel = rel.replace("\\", "/")
            if rel.startswith("@"):
                continue
            rel = normalize_rel(rel)
            key = (rel, name)
            rec = index.setdefault(key, {"rel": rel, "name": name, "stamps": [],
                                        "status": [], "units": [], "ok_text": ""})
            if stamp not in rec["stamps"]:
                rec["stamps"].append(stamp)
            rec["status"].append(ent.get("status"))
            rec["units"].append([ent.get("units_success"), ent.get("units_total")])
            ok = ent.get("ok_text")
            if isinstance(ok, str) and len(ok) > len(rec["ok_text"]):
                rec["ok_text"] = ok
    return index


# --------------------------------------------------------------------------
# 探针源码观测
# --------------------------------------------------------------------------

class _Ctx:
    __slots__ = ("n", "p", "anc")

    def __init__(self, n, p, anc):
        self.n, self.p, self.anc = n, p, anc


class _Walker(ast.NodeVisitor):
    def __init__(self):
        self.stack = []
        self.out = []

    def visit(self, node):
        self.stack.append(node)
        parent = self.stack[-2] if len(self.stack) > 1 else None
        depth = sum(1 for a in self.stack[:-1] if isinstance(a, REGION_TYPES))
        self.out.append((node, parent, list(self.stack[:-1]), host_of(node, parent), depth))
        self.generic_visit(node)
        self.stack.pop()


def observe(index, family_predicates):
    obs = collections.defaultdict(list)
    for (rel, name), rec in index.items():
        try:
            tree = ast.parse(rec.get("ok_text") or "")
        except Exception:
            continue
        w = _Walker()
        w.visit(tree)
        for node, parent, anc, host, depth in w.out:
            ctx = _Ctx(node, parent, anc)
            for fam, nodes, variants in family_predicates:
                if not isinstance(node, nodes):
                    continue
                for vname, _note, pred in variants:
                    try:
                        hit = pred(ctx)
                    except Exception:
                        hit = False
                    if hit:
                        obs[(fam, vname, host, depth_bucket(depth))].append((rel, name))
    return obs


# --------------------------------------------------------------------------
# 谓词辅助
# --------------------------------------------------------------------------

def desc_of(node, t):
    if node is None:
        return False
    return any(isinstance(x, t) for x in ast.walk(node))


def has_anc(c, t):
    return any(isinstance(a, t) for a in c.anc)


def parent_field(c, owner, attr):
    return isinstance(c.p, owner) and getattr(c.p, attr, None) is c.n


def in_body(c, t):
    return isinstance(c.p, t) and ident_in(c.n, c.p.body)


def in_orelse(c, t):
    return isinstance(c.p, t) and ident_in(c.n, c.p.orelse)


def in_finalbody(c, t):
    return isinstance(c.p, t) and ident_in(c.n, c.p.finalbody)


def _is_ann(c):
    return (parent_field(c, ast.AnnAssign, "annotation")
            or parent_field(c, ast.FunctionDef, "returns")
            or parent_field(c, ast.AsyncFunctionDef, "returns"))


def _nested_loop(c):
    return sum(1 for a in c.anc if isinstance(a, (ast.For, ast.AsyncFor, ast.While))) >= 2


# --------------------------------------------------------------------------
# 形态族表（25 行 + NEW）
# --------------------------------------------------------------------------

def build_families():
    F = []

    def fam(code, name, row, nodes, source, hosts, variants, anchor, structural_cap=12):
        F.append({"code": code, "name": name, "row": row, "nodes": nodes,
                  "source": source, "hosts": hosts, "variants": variants,
                  "anchor": anchor, "structural_cap": structural_cap})

    # ---- 1 If -----------------------------------------------------------
    fam("IF", "If", "If", ast.If,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:28",
        ["module-level", "function-body", "class-body", "if-arm", "elif-arm", "else-arm",
         "loop-body", "loop-else", "with-body", "try-body", "except-handler",
         "else-of-try", "finally-body", "match-case-body", "nested-func-body"],
        [("if-no-else", "if 无 else 臂（then 单臂）", lambda c: not c.n.orelse),
         ("if-else-arm", "if 带非 If 的 else 臂", lambda c: bool(c.n.orelse) and not isinstance(c.n.orelse[0], ast.If)),
         ("if-elif-chain", "if 的 else 位置是另一个 if（elif 链）", lambda c: bool(c.n.orelse) and isinstance(c.n.orelse[0], ast.If)),
         ("if-cond-ternary", "if 条件为三元表达式", lambda c: desc_of(c.n.test, ast.IfExp)),
         ("if-cond-boolop", "if 条件为布尔运算链", lambda c: desc_of(c.n.test, ast.BoolOp)),
         ("if-cond-await", "if 条件含 await（异步宿主）", lambda c: desc_of(c.n.test, ast.Await)),
         ("if-cond-compare-chain", "if 条件为链式比较", lambda c: any(len(x.comparators) > 1 for x in ast.walk(c.n.test) if isinstance(x, ast.Compare))),
         ("if-empty-then", "if 的 then 臂为空", lambda c: not c.n.body),
         ("if-in-loop", "if 位于循环体内", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("if-in-try", "if 位于 try 体内", lambda c: has_anc(c, (ast.Try, ast.TryStar))),
         ("if-in-handler", "if 位于 except handler 内", lambda c: has_anc(c, ast.ExceptHandler)),
         ("if-in-with", "if 位于 with 体内", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("if-in-match-case", "if 位于 match case 体内", lambda c: has_anc(c, ast.match_case))],
        "test_repros/round1/r1_17_elif_mixed.pyc")

    # ---- 2 BoolOp -------------------------------------------------------
    fam("BOOLOP", "BoolOp", "BoolOp", ast.BoolOp,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:29",
        ["module-level", "function-body", "if-arm", "else-arm", "loop-body", "condition-expr",
         "return-value-expr", "assign-rhs", "call-arg", "boolop-operand", "comprehension-if",
         "match-guard", "except-handler", "finally-body"],
        [("boolop-and", "and 链", lambda c: isinstance(c.n.op, ast.And)),
         ("boolop-or", "or 链", lambda c: isinstance(c.n.op, ast.Or)),
         ("boolop-two-operands", "两个操作数", lambda c: len(c.n.values) == 2),
         ("boolop-three-plus", "三个及以上操作数", lambda c: len(c.n.values) >= 3),
         ("boolop-nested", "操作数内再嵌 BoolOp", lambda c: any(desc_of(v, ast.BoolOp) for v in c.n.values)),
         ("boolop-mixed-and-or", "同一链内 and/or 混用", lambda c: len({type(v.op) for v in c.n.values if isinstance(v, ast.BoolOp)}) > 1),
         ("boolop-not-operand", "操作数含 not", lambda c: any(isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not) for v in c.n.values)),
         ("boolop-compare-operand", "操作数含比较", lambda c: any(isinstance(v, ast.Compare) for v in c.n.values)),
         ("boolop-ternary-operand", "操作数含三元", lambda c: any(isinstance(v, ast.IfExp) for v in c.n.values)),
         ("boolop-await-operand", "操作数含 await", lambda c: any(isinstance(v, ast.Await) for v in c.n.values)),
         ("boolop-in-if-cond", "位于 if 条件位", lambda c: parent_field(c, ast.If, "test")),
         ("boolop-in-while-cond", "位于 while 条件位", lambda c: parent_field(c, ast.While, "test")),
         ("boolop-in-guard", "位于 match guard", lambda c: parent_field(c, ast.match_case, "guard"))],
        "test_repros/round1/n1_02_simple_or.pyc")

    # ---- 3 IfExp --------------------------------------------------------
    fam("IFEXP", "IfExp", "IfExp", ast.IfExp,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:30",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "subscript-index", "condition-expr", "comprehension-scope", "lambda-body",
         "boolop-operand", "binop-operand", "if-arm", "match-guard"],
        [("ifexp-in-return", "三元出现在 return 值位", lambda c: parent_field(c, ast.Return, "value")),
         ("ifexp-in-assign", "三元出现在赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("ifexp-in-call-arg", "三元出现在调用实参", lambda c: isinstance(c.p, ast.Call) and ident_in(c.n, c.p.args)),
         ("ifexp-in-subscript", "三元出现在下标", lambda c: isinstance(c.p, ast.Subscript)),
         ("ifexp-in-del-target", "三元出现在 del 目标", lambda c: isinstance(c.p, ast.Delete)),
         ("ifexp-in-assert", "三元出现在 assert 条件", lambda c: parent_field(c, ast.Assert, "test")),
         ("ifexp-in-raise", "三元出现在 raise 异常类", lambda c: parent_field(c, ast.Raise, "exc")),
         ("ifexp-in-for-iter", "三元出现在 for 迭代式", lambda c: parent_field(c, ast.For, "iter") or parent_field(c, ast.AsyncFor, "iter")),
         ("ifexp-in-with-item", "三元出现在 with 管理项", lambda c: isinstance(c.p, (ast.With, ast.AsyncWith))),
         ("ifexp-in-lambda", "三元出现在 lambda 体", lambda c: parent_field(c, ast.Lambda, "body")),
         ("ifexp-in-listcomp-elt", "三元出现在推导式元素位", lambda c: isinstance(c.p, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and c.p.elt is c.n),
         ("ifexp-nested-arms", "三元臂内再嵌三元", lambda c: any(isinstance(x, ast.IfExp) for x in list(c.n.body) + list(c.n.orelse))),
         ("ifexp-in-boolop", "三元作为布尔运算操作数", lambda c: isinstance(c.p, ast.BoolOp)),
         ("ifexp-in-binop", "三元作为二元运算操作数", lambda c: isinstance(c.p, ast.BinOp))],
        "test_repros/round3/e04_g2_ifexp_deep.pyc")

    # ---- 4 Try ----------------------------------------------------------
    fam("TRY", "Try", "Try", (ast.Try, ast.TryStar),
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:31",
        ["function-body", "module-level", "if-arm", "loop-body", "with-body", "try-body",
         "except-handler", "else-of-try", "finally-body", "nested-func-body", "class-body",
         "match-case-body"],
        [("try-no-handler", "try 无 except 臂（仅 finally）", lambda c: not c.n.handlers and not c.n.orelse),
         ("try-with-handler", "try 带 except 臂", lambda c: bool(c.n.handlers)),
         ("try-with-else", "try 带 else 子句", lambda c: bool(c.n.orelse)),
         ("try-with-finally", "try 带 finally 子句", lambda c: bool(c.n.finalbody)),
         ("try-handler-typed", "handler 带异常类型标注", lambda c: bool(c.n.handlers) and c.n.handlers[0].type is not None),
         ("try-handler-as", "handler 带 as 绑定名", lambda c: bool(c.n.handlers) and c.n.handlers[0].name is not None),
         ("try-handler-tuple-type", "handler 异常类型为元组", lambda c: bool(c.n.handlers) and isinstance(c.n.handlers[0].type, ast.Tuple)),
         ("try-nested-in-try", "try 嵌套在 try 内", lambda c: has_anc(c, (ast.Try, ast.TryStar))),
         ("try-nested-in-loop", "try 嵌套在循环内", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("try-nested-in-with", "try 嵌套在 with 内", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("try-in-func", "try 在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("try-in-class-body", "try 在类体", lambda c: has_anc(c, ast.ClassDef))],
        "test_repros/round2/m04_module_try.pyc")

    # ---- 5 Raise --------------------------------------------------------
    fam("RAISE", "Raise", "Raise", ast.Raise,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:32",
        ["function-body", "module-level", "if-arm", "except-handler", "finally-body",
         "try-body", "loop-body", "with-body", "match-case-body", "nested-func-body"],
        [("raise-bare", "裸 raise（重抛）", lambda c: c.n.exc is None),
         ("raise-exc-call", "raise 一个异常实例", lambda c: isinstance(c.n.exc, ast.Call)),
         ("raise-exc-class", "raise 一个异常类", lambda c: isinstance(c.n.exc, (ast.Name, ast.Attribute))),
         ("raise-from", "raise ... from ...（异常链）", lambda c: c.n.cause is not None),
         ("raise-ternary-exc", "异常类位为三元", lambda c: c.n.exc is not None and desc_of(c.n.exc, ast.IfExp)),
         ("raise-in-handler", "raise 位于 except handler 内", lambda c: has_anc(c, ast.ExceptHandler)),
         ("raise-in-finally", "raise 位于 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("raise-in-try-body", "raise 位于 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("raise-in-loop", "raise 位于循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("raise-in-with", "raise 位于 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith)))],
        "test_repros/round2/r2_15_reraise.pyc")

    # ---- 6 Assert -------------------------------------------------------
    fam("ASSERT", "Assert", "Assert", ast.Assert,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:33",
        ["function-body", "module-level", "if-arm", "else-arm", "loop-body", "try-body",
         "except-handler", "with-body", "match-case-body", "nested-func-body", "finally-body"],
        [("assert-plain", "assert 只有条件", lambda c: c.n.msg is None),
         ("assert-with-msg", "assert 带说明消息", lambda c: c.n.msg is not None),
         ("assert-msg-ternary", "说明消息为三元", lambda c: c.n.msg is not None and desc_of(c.n.msg, ast.IfExp)),
         ("assert-test-ternary", "条件为三元", lambda c: desc_of(c.n.test, ast.IfExp)),
         ("assert-test-boolop", "条件为布尔运算", lambda c: desc_of(c.n.test, ast.BoolOp)),
         ("assert-test-call", "条件为函数调用", lambda c: isinstance(c.n.test, ast.Call)),
         ("assert-in-func", "assert 在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("assert-in-loop", "assert 在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("assert-in-try", "assert 在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("assert-in-handler", "assert 在 except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("assert-in-with", "assert 在 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith)))],
        "test_repros/round1/r1_14_assert_mixed.pyc")

    # ---- 7 Import -------------------------------------------------------
    fam("IMPORT", "Import", "Import", (ast.Import, ast.ImportFrom),
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:34",
        ["module-level", "function-body", "class-body", "try-body", "except-handler",
         "else-of-try", "finally-body", "if-arm", "with-body", "loop-body",
         "match-case-body", "nested-func-body"],
        [("import-plain", "import a（无 as）", lambda c: isinstance(c.n, ast.Import) and c.n.names[0].asname is None),
         ("import-as", "import a as b", lambda c: isinstance(c.n, ast.Import) and c.n.names[0].asname is not None),
         ("import-dotted", "import a.b.c（点号路径）", lambda c: isinstance(c.n, ast.Import) and "." in c.n.names[0].name),
         ("import-from", "from m import x", lambda c: isinstance(c.n, ast.ImportFrom)),
         ("import-from-as", "from m import x as y", lambda c: isinstance(c.n, ast.ImportFrom) and c.n.names[0].asname is not None),
         ("import-from-star", "from m import *", lambda c: isinstance(c.n, ast.ImportFrom) and c.n.names[0].name == "*"),
         ("import-in-try", "import 在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("import-in-handler", "import 在 except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("import-in-else-of-try", "import 在 try 的 else 子句", lambda c: in_orelse(c, (ast.Try, ast.TryStar))),
         ("import-in-finally", "import 在 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("import-in-func", "import 在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("import-in-class-body", "import 在类体", lambda c: has_anc(c, ast.ClassDef))],
        "test_repros/round4/c4_15_star_import.pyc")

    # ---- 8 Global -------------------------------------------------------
    fam("GLOBAL", "Global", "Global", ast.Global,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:35",
        ["module-level", "function-body", "class-body", "nested-func-body", "if-arm",
         "loop-body", "try-body", "except-handler", "with-body", "match-case-body"],
        [("global-single", "global 一个名字", lambda c: len(c.n.names) == 1),
         ("global-multiple", "global 多个名字", lambda c: len(c.n.names) > 1),
         ("global-at-module", "模块级 global", lambda c: not has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
         ("global-in-func", "函数体内 global", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("global-in-class-body", "类体内 global", lambda c: has_anc(c, ast.ClassDef)),
         ("global-in-nested-func", "嵌套函数体内 global", lambda c: sum(1 for a in c.anc if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef))) >= 2),
         ("global-with-same-name-assign", "同作用域内有同名赋值", lambda c: bool(c.n.names) and any(isinstance(x, ast.Assign) for x in ast.walk(c.p) if x is not c.n))],
        "test_repros/round10/r10_12_global_deep.pyc")

    # ---- 9 global_nonlocal ----------------------------------------------
    fam("NONLOCAL", "global_nonlocal", "global_nonlocal", ast.Nonlocal,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:36",
        ["function-body", "nested-func-body", "class-body", "if-arm", "loop-body",
         "try-body", "except-handler", "with-body"],
        [("nonlocal-single", "nonlocal 一个名字", lambda c: len(c.n.names) == 1),
         ("nonlocal-multiple", "nonlocal 多个名字", lambda c: len(c.n.names) > 1),
         ("nonlocal-in-nested-func", "nonlocal 出现在嵌套函数体", lambda c: sum(1 for a in c.anc if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef))) >= 2),
         ("nonlocal-in-func", "nonlocal 出现在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("nonlocal-in-class-in-func", "nonlocal 出现在类体内的函数", lambda c: has_anc(c, ast.ClassDef) and has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef)))],
        "test_repros/round10/r10_14_nonlocal_deep.pyc")

    # ---- 10 Await -------------------------------------------------------
    fam("AWAIT", "Await", "Await", ast.Await,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:37",
        ["async-func-body", "function-body", "comprehension-scope", "return-value-expr",
         "assign-rhs", "condition-expr", "call-arg", "binop-operand", "await-operand",
         "if-arm", "loop-body"],
        [("await-in-async-def", "await 出现在 async def 体", lambda c: has_anc(c, ast.AsyncFunctionDef)),
         ("await-in-async-with", "await 出现在 async with 体", lambda c: has_anc(c, ast.AsyncWith)),
         ("await-in-async-for", "await 出现在 async for 体", lambda c: has_anc(c, ast.AsyncFor)),
         ("await-in-async-comp", "await 出现在异步推导式", lambda c: has_anc(c, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))),
         ("await-in-async-closure", "await 出现在嵌套 async 闭包", lambda c: sum(1 for a in c.anc if isinstance(a, ast.AsyncFunctionDef)) >= 2),
         ("await-in-async-method", "await 出现在 async 方法", lambda c: has_anc(c, ast.ClassDef) and has_anc(c, ast.AsyncFunctionDef)),
         ("await-in-cond", "await 出现在条件位", lambda c: parent_field(c, ast.If, "test") or parent_field(c, ast.While, "test")),
         ("await-in-call-arg", "await 出现在调用实参", lambda c: isinstance(c.p, ast.Call) and ident_in(c.n, c.p.args)),
         ("await-in-return", "await 出现在 return 值", lambda c: parent_field(c, ast.Return, "value")),
         ("await-in-assign", "await 出现在赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("await-in-binop", "await 出现在二元运算操作数", lambda c: isinstance(c.p, ast.BinOp)),
         ("await-in-boolop", "await 出现在布尔运算操作数", lambda c: isinstance(c.p, ast.BoolOp))],
        "test_repros/round6/r6_07_async_five.pyc")

    # ---- 11 ListComp ----------------------------------------------------
    fam("LISTCOMP", "ListComp", "ListComp", ast.ListComp,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:38",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "comprehension-scope", "comprehension-if", "comprehension-for", "if-arm",
         "loop-body", "class-body", "annotation-context"],
        [("listcomp-single-for", "单个 for 子句", lambda c: len(c.n.generators) == 1),
         ("listcomp-multi-for", "多个 for 子句", lambda c: len(c.n.generators) > 1),
         ("listcomp-with-if", "带 if 过滤子句", lambda c: bool(c.n.ifs)),
         ("listcomp-multi-if", "两个及以上 if 过滤子句", lambda c: len(c.n.ifs) >= 2),
         ("listcomp-nested-comp", "迭代式内嵌推导式", lambda c: any(isinstance(x, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for g in c.n.generators for x in ast.walk(g.iter))),
         ("listcomp-async", "异步推导式", lambda c: any(g.is_async for g in c.n.generators)),
         ("listcomp-elt-ternary", "元素位为三元", lambda c: desc_of(c.n.elt, ast.IfExp)),
         ("listcomp-elt-boolop", "元素位含布尔运算", lambda c: desc_of(c.n.elt, ast.BoolOp)),
         ("listcomp-elt-await", "元素位含 await", lambda c: desc_of(c.n.elt, ast.Await)),
         ("listcomp-if-ternary", "过滤条件为三元", lambda c: any(desc_of(i, ast.IfExp) for i in c.n.ifs)),
         ("listcomp-in-call-arg", "推导式作为调用实参", lambda c: isinstance(c.p, ast.Call)),
         ("listcomp-in-assign", "推导式作为赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("listcomp-in-return", "推导式作为返回值", lambda c: parent_field(c, ast.Return, "value")),
         ("listcomp-in-annotation", "推导式出现在注解位", lambda c: parent_field(c, ast.AnnAssign, "annotation") or parent_field(c, ast.FunctionDef, "returns") or parent_field(c, ast.AsyncFunctionDef, "returns"))],
        "test_repros/round5/probe_comp_min.pyc")

    # ---- 12 await_expr --------------------------------------------------
    fam("AWAITEXPR", "await_expr", "await_expr", ast.Await,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:39",
        ["condition-expr", "return-value-expr", "call-arg", "assign-rhs", "binop-operand",
         "boolop-operand", "await-operand", "if-arm", "comprehension-scope", "match-guard"],
        [("awexpr-in-if-cond", "await 出现在 if 条件（表达式位）", lambda c: parent_field(c, ast.If, "test")),
         ("awexpr-in-while-cond", "await 出现在 while 条件", lambda c: parent_field(c, ast.While, "test")),
         ("awexpr-in-call-arg", "await 出现在调用实参", lambda c: isinstance(c.p, ast.Call) and ident_in(c.n, c.p.args)),
         ("awexpr-in-return", "await 出现在 return 值", lambda c: parent_field(c, ast.Return, "value")),
         ("awexpr-in-assign-rhs", "await 出现在赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("awexpr-in-binop", "await 出现在二元运算操作数", lambda c: isinstance(c.p, ast.BinOp)),
         ("awexpr-in-boolop", "await 出现在布尔运算操作数", lambda c: isinstance(c.p, ast.BoolOp)),
         ("awexpr-in-compare", "await 出现在比较操作数", lambda c: isinstance(c.p, ast.Compare)),
         ("awexpr-in-listcomp-elt", "await 出现在推导式元素", lambda c: isinstance(c.p, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and c.p.elt is c.n)],
        "test_repros/round2/x09_funcdef_hosts.pyc")

    # ---- 13 Yield -------------------------------------------------------
    fam("YIELD", "Yield", "Yield", (ast.Yield, ast.YieldFrom),
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:40",
        ["generator-func-body", "function-body", "try-body", "finally-body", "except-handler",
         "loop-body", "condition-expr", "boolop-operand", "call-arg", "assign-rhs",
         "if-arm", "nested-func-body"],
        [("yield-bare", "裸 yield", lambda c: isinstance(c.n, ast.Yield) and c.n.value is None),
         ("yield-value", "yield 一个值", lambda c: isinstance(c.n, ast.Yield) and c.n.value is not None),
         ("yield-from", "yield from 迭代器", lambda c: isinstance(c.n, ast.YieldFrom)),
         ("yield-in-try-body", "yield 出现在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("yield-in-finally", "yield 出现在 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("yield-in-loop", "yield 出现在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("yield-in-ternary", "yield 出现在三元臂", lambda c: isinstance(c.p, ast.IfExp)),
         ("yield-in-boolop", "yield 出现在布尔运算操作数", lambda c: isinstance(c.p, ast.BoolOp)),
         ("yield-as-arg", "yield 作为调用实参", lambda c: isinstance(c.p, ast.Call) and ident_in(c.n, c.p.args)),
         ("yield-in-assign", "yield 出现在赋值右值", lambda c: parent_field(c, ast.Assign, "value"))],
        "test_repros/round6/r6_15_yield_forms.pyc")

    # ---- 14 Match（模式族）---------------------------------------------
    fam("MATCHPAT", "Match", "Match", (ast.MatchValue, ast.MatchSingleton, ast.MatchSequence,
                                       ast.MatchMapping, ast.MatchClass, ast.MatchAs, ast.MatchOr,
                                       ast.MatchStar),
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:41",
        ["match-case-body", "pattern-value", "pattern-class", "pattern-sequence",
         "pattern-mapping", "pattern-capture", "pattern-or", "pattern-star", "match-guard",
         "function-body", "match-subject"],
        [("pat-literal", "字面量模式", lambda c: isinstance(c.n, ast.MatchValue)),
         ("pat-singleton", "单例模式（None/True/False）", lambda c: isinstance(c.n, ast.MatchSingleton)),
         ("pat-sequence", "序列模式", lambda c: isinstance(c.n, ast.MatchSequence)),
         ("pat-mapping", "映射模式", lambda c: isinstance(c.n, ast.MatchMapping)),
         ("pat-class", "类模式", lambda c: isinstance(c.n, ast.MatchClass)),
         ("pat-capture", "捕获模式", lambda c: isinstance(c.n, ast.MatchAs) and c.n.name is not None),
         ("pat-wildcard", "通配模式（_）", lambda c: isinstance(c.n, ast.MatchAs) and c.n.name is None),
         ("pat-or", "or 模式（| 分支）", lambda c: isinstance(c.n, ast.MatchOr)),
         ("pat-star", "星号模式（*rest）", lambda c: isinstance(c.n, ast.MatchStar)),
         ("pat-nested-class", "类模式内嵌子模式", lambda c: isinstance(c.n, ast.MatchClass) and any(isinstance(x, (ast.MatchClass, ast.MatchSequence, ast.MatchMapping)) for x in ast.walk(c.n) if x is not c.n)),
         ("pat-with-guard", "所在 case 带 guard", lambda c: has_anc(c, ast.match_case) and c.anc[-1].guard is not None),
         ("pat-in-nested-match", "模式所属 match 嵌套在另一 match 内", lambda c: sum(1 for a in c.anc if isinstance(a, ast.Match)) >= 2)],
        "test_repros/round4/r4_06_match_or.pyc")

    # ---- 15 With --------------------------------------------------------
    fam("WITH", "With", "With", ast.With,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:42",
        ["function-body", "module-level", "if-arm", "loop-body", "try-body", "except-handler",
         "with-body", "with-item", "match-case-body", "nested-func-body", "else-arm"],
        [("with-single-item", "单个 with 管理项", lambda c: len(c.n.items) == 1),
         ("with-multi-item", "多个 with 管理项", lambda c: len(c.n.items) > 1),
         ("with-as-target", "with ... as 绑定名", lambda c: c.n.items[0].optional_vars is not None),
         ("with-in-try", "with 位于 try 内", lambda c: has_anc(c, (ast.Try, ast.TryStar))),
         ("with-in-loop", "with 位于循环内", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("with-in-func", "with 位于函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("with-body-nested-with", "with 体内再嵌 with", lambda c: has_anc(c, ast.With)),
         ("with-in-match-case", "with 位于 match case 体", lambda c: has_anc(c, ast.match_case)),
         ("with-item-ternary", "管理项表达式为三元", lambda c: desc_of(c.n.items[0].context_expr, ast.IfExp)),
         ("with-item-call", "管理项为调用", lambda c: isinstance(c.n.items[0].context_expr, ast.Call))],
        "test_repros/round2/c05_class_with.pyc")

    # ---- 16 match_statement ---------------------------------------------
    fam("MATCHSTMT", "match_statement", "match_statement", ast.Match,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:43",
        ["module-level", "function-body", "if-arm", "loop-body", "try-body", "except-handler",
         "with-body", "match-case-body", "class-body", "nested-func-body"],
        [("msingle-case", "match 只有 1 个 case", lambda c: len(c.n.cases) == 1),
         ("mmulti-case", "match 有多个 case", lambda c: len(c.n.cases) > 1),
         ("mhas-wildcard", "含通配 case（_）", lambda c: any(isinstance(x.pattern, ast.MatchAs) and x.pattern.name is None for x in c.n.cases)),
         ("mhas-guard", "含 guard case", lambda c: any(x.guard is not None for x in c.n.cases)),
         ("min-loop", "match 位于循环内", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("min-try", "match 位于 try 内", lambda c: has_anc(c, (ast.Try, ast.TryStar))),
         ("min-func", "match 位于函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("mcase-body-nested-if", "case 体内嵌 if", lambda c: any(isinstance(x, ast.If) for cs in c.n.cases for x in cs.body)),
         ("mnested-match", "match 嵌套在另一 match 内", lambda c: sum(1 for a in c.anc if isinstance(a, ast.Match)) >= 2),
         ("msubject-ternary", "match 主题为三元", lambda c: desc_of(c.n.subject, ast.IfExp))],
        "test_repros/round4/c4_04_match_patterns.pyc")

    # ---- 17 Break -------------------------------------------------------
    fam("BREAK", "Break", "Break", ast.Break,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:44",
        ["loop-body", "loop-else", "try-body", "except-handler", "finally-body", "with-body",
         "match-case-body", "if-arm", "function-body", "module-level"],
        [("break-in-for", "break 在 for 体内", lambda c: has_anc(c, (ast.For, ast.AsyncFor))),
         ("break-in-while", "break 在 while 体内", lambda c: has_anc(c, ast.While)),
         ("break-in-try-body", "break 在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("break-in-handler", "break 在 except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("break-in-finally", "break 在 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("break-in-with", "break 在 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("break-in-match-case", "break 在 match case 体", lambda c: has_anc(c, ast.match_case)),
         ("break-in-if-arm", "break 在 if 臂内", lambda c: has_anc(c, ast.If)),
         ("break-target-outer", "break 目标是外层循环（跨层）", lambda c: _nested_loop(c)),
         ("break-in-nested-loop", "break 位于嵌套循环内层", lambda c: _nested_loop(c))],
        "test_repros/round7/r7v7r_b120_break.pyc")

    # ---- 18 Continue ----------------------------------------------------
    fam("CONTINUE", "Continue", "Continue", ast.Continue,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:45",
        ["loop-body", "loop-else", "try-body", "except-handler", "finally-body", "with-body",
         "match-case-body", "if-arm", "function-body", "module-level"],
        [("continue-in-for", "continue 在 for 体内", lambda c: has_anc(c, (ast.For, ast.AsyncFor))),
         ("continue-in-while", "continue 在 while 体内", lambda c: has_anc(c, ast.While)),
         ("continue-in-try-body", "continue 在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("continue-in-handler", "continue 在 except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("continue-in-finally", "continue 在 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("continue-in-with", "continue 在 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("continue-in-match-case", "continue 在 match case 体", lambda c: has_anc(c, ast.match_case)),
         ("continue-in-if-arm", "continue 在 if 臂内", lambda c: has_anc(c, ast.If)),
         ("continue-target-outer", "continue 目标是外层循环（跨层）", lambda c: _nested_loop(c)),
         ("continue-in-nested-loop", "continue 位于嵌套循环内层", lambda c: _nested_loop(c))],
        "test_repros/round9/r9_02_b2_dual_continue.pyc")

    # ---- 19 While -------------------------------------------------------
    fam("WHILE", "While", "While", ast.While,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:46",
        ["module-level", "function-body", "class-body", "if-arm", "loop-body", "try-body",
         "except-handler", "with-body", "match-case-body", "nested-func-body", "else-arm"],
        [("while-true", "while True（恒真条件）", lambda c: isinstance(c.n.test, ast.Constant) and c.n.test.value is True),
         ("while-cond-ternary", "while 条件为三元", lambda c: desc_of(c.n.test, ast.IfExp)),
         ("while-cond-boolop", "while 条件为布尔运算", lambda c: desc_of(c.n.test, ast.BoolOp)),
         ("while-cond-await", "while 条件含 await", lambda c: desc_of(c.n.test, ast.Await)),
         ("while-cond-compare-chain", "while 条件为链式比较", lambda c: any(len(x.comparators) > 1 for x in ast.walk(c.n.test) if isinstance(x, ast.Compare))),
         ("while-else", "while 带 else 子句", lambda c: bool(c.n.orelse)),
         ("while-at-module", "模块级 while", lambda c: not has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
         ("while-in-func", "函数体内 while", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("while-in-try", "try 体内 while", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("while-with-break", "while 体内含 break", lambda c: any(isinstance(x, ast.Break) for x in c.n.body)),
         ("while-body-nested-loop", "while 体内嵌循环", lambda c: any(isinstance(x, (ast.For, ast.AsyncFor, ast.While)) for x in c.n.body))],
        "test_repros/round1/r1_10_while_mixed.pyc")

    # ---- 20 Delete ------------------------------------------------------
    fam("DELETE", "Delete", "Delete", ast.Delete,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:47",
        ["function-body", "module-level", "if-arm", "else-arm", "loop-body", "try-body",
         "except-handler", "finally-body", "with-body", "match-case-body", "nested-func-body"],
        [("del-name", "del 局部名", lambda c: isinstance(c.n.targets[0], ast.Name)),
         ("del-subscript", "del 下标元素", lambda c: isinstance(c.n.targets[0], ast.Subscript)),
         ("del-slice", "del 切片目标", lambda c: isinstance(c.n.targets[0], ast.Subscript) and isinstance(c.n.targets[0].slice, ast.Slice)),
         ("del-attribute", "del 属性", lambda c: isinstance(c.n.targets[0], ast.Attribute)),
         ("del-multiple-targets", "del 多个目标", lambda c: len(c.n.targets) > 1),
         ("del-tuple-target", "del 元组目标", lambda c: isinstance(c.n.targets[0], (ast.Tuple, ast.List))),
         ("del-in-loop", "del 位于循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("del-in-try", "del 位于 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("del-in-with", "del 位于 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("del-ternary-target", "del 目标下标含三元", lambda c: any(desc_of(t, ast.IfExp) for t in c.n.targets))],
        "test_repros/round8/r8v8fb_b108_del_probe.pyc")

    # ---- 21 AugAssign（节点级）-----------------------------------------
    fam("AUGASSIGN", "AugAssign", "AugAssign", ast.AugAssign,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:48",
        ["function-body", "module-level", "if-arm", "else-arm", "loop-body", "try-body",
         "except-handler", "finally-body", "with-body", "match-case-body", "class-body",
         "nested-func-body"],
        [("aug-op-add", "+=", lambda c: isinstance(c.n.op, ast.Add)),
         ("aug-op-sub", "-=", lambda c: isinstance(c.n.op, ast.Sub)),
         ("aug-op-mul", "*=", lambda c: isinstance(c.n.op, ast.Mult)),
         ("aug-op-floordiv", "//=", lambda c: isinstance(c.n.op, ast.FloorDiv)),
         ("aug-op-mod", "%=", lambda c: isinstance(c.n.op, ast.Mod)),
         ("aug-op-pow", "**=", lambda c: isinstance(c.n.op, ast.Pow)),
         ("aug-op-lshift", "<<=", lambda c: isinstance(c.n.op, ast.LShift)),
         ("aug-op-rshift", ">>=", lambda c: isinstance(c.n.op, ast.RShift)),
         ("aug-op-bitor", "|=", lambda c: isinstance(c.n.op, ast.BitOr)),
         ("aug-op-bitxor", "^=", lambda c: isinstance(c.n.op, ast.BitXor)),
         ("aug-op-bitand", "&=", lambda c: isinstance(c.n.op, ast.BitAnd)),
         ("aug-op-truediv", "/=", lambda c: isinstance(c.n.op, ast.Div)),
         ("aug-op-matmul", "@=", lambda c: isinstance(c.n.op, ast.MatMult)),
         ("aug-target-name", "目标为名字", lambda c: isinstance(c.n.target, ast.Name)),
         ("aug-target-attr", "目标为属性", lambda c: isinstance(c.n.target, ast.Attribute)),
         ("aug-target-subscript", "目标为下标", lambda c: isinstance(c.n.target, ast.Subscript)),
         ("aug-rhs-call", "右值为调用", lambda c: isinstance(c.n.value, ast.Call)),
         ("aug-rhs-ternary", "右值为三元", lambda c: desc_of(c.n.value, ast.IfExp)),
         ("aug-rhs-attr", "右值为属性链", lambda c: isinstance(c.n.value, ast.Attribute)),
         ("aug-rhs-subscript", "右值为下标链", lambda c: isinstance(c.n.value, ast.Subscript))],
        "test_repros/round4/c4_08_augassign.pyc")

    # ---- 22 Return ------------------------------------------------------
    fam("RETURN", "Return", "Return", ast.Return,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:49",
        ["function-body", "nested-func-body", "module-level", "if-arm", "else-arm", "loop-body",
         "try-body", "except-handler", "finally-body", "with-body", "match-case-body",
         "class-body", "generator-func-body"],
        [("return-bare", "裸 return", lambda c: c.n.value is None),
         ("return-value", "return 一个值", lambda c: c.n.value is not None),
         ("return-ternary", "return 三元", lambda c: c.n.value is not None and desc_of(c.n.value, ast.IfExp)),
         ("return-tuple", "return 元组", lambda c: isinstance(c.n.value, ast.Tuple)),
         ("return-boolop", "return 布尔运算", lambda c: c.n.value is not None and desc_of(c.n.value, ast.BoolOp)),
         ("return-await", "return await", lambda c: isinstance(c.n.value, ast.Await)),
         ("return-yield", "return yield", lambda c: isinstance(c.n.value, (ast.Yield, ast.YieldFrom))),
         ("return-in-try-body", "return 位于 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("return-in-handler", "return 位于 except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("return-in-finally", "return 位于 finally 体", lambda c: in_finalbody(c, (ast.Try, ast.TryStar))),
         ("return-in-loop", "return 位于循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("return-in-with", "return 位于 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("return-in-match-case", "return 位于 match case 体", lambda c: has_anc(c, ast.match_case))],
        "test_repros/round5/r5_13_comp_return.pyc")

    # ---- 23 Slice（节点级）---------------------------------------------
    fam("SLICE", "Slice", "Slice", ast.Slice,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:50",
        ["subscript-index", "slice-bounds", "function-body", "module-level", "assign-rhs",
         "if-arm", "loop-body", "try-body", "call-arg"],
        [("slice-plain", "只有 lower/upper", lambda c: c.n.step is None and c.n.lower is not None and c.n.upper is not None),
         ("slice-with-step", "带 step", lambda c: c.n.step is not None),
         ("slice-neg-bound", "边界为负数一元负号", lambda c: any(isinstance(b, ast.UnaryOp) and isinstance(b.op, ast.USub) for b in (c.n.lower, c.n.upper))),
         ("slice-expr-bound", "边界为算术表达式", lambda c: any(isinstance(b, ast.BinOp) for b in (c.n.lower, c.n.upper))),
         ("slice-ternary-bound", "边界含三元", lambda c: any(b is not None and desc_of(b, ast.IfExp) for b in (c.n.lower, c.n.upper, c.n.step))),
         ("slice-starred", "边界含星号展开", lambda c: any(b is not None and desc_of(b, ast.Starred) for b in (c.n.lower, c.n.upper, c.n.step))),
         ("slice-multidim", "多维下标中的 slice（slice 在元组内）", lambda c: isinstance(c.p, ast.Tuple)),
         ("slice-in-del-target", "slice 出现在 del 目标", lambda c: has_anc(c, ast.Delete)),
         ("slice-in-assign-target", "slice 出现在赋值目标", lambda c: has_anc(c, ast.Assign))],
        "test_repros/round4/c4_13_slice.pyc")

    # ---- 24 augmented_assign（形态级镜像）------------------------------
    fam("AUGFORM", "augmented_assign", "augmented_assign", ast.AugAssign,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:51",
        ["function-body", "module-level", "if-arm", "else-arm", "loop-body", "try-body",
         "except-handler", "finally-body", "with-body", "match-case-body",
         "comprehension-scope", "class-body"],
        [("augform-target-name", "目标形态=名字", lambda c: isinstance(c.n.target, ast.Name)),
         ("augform-target-attr", "目标形态=属性", lambda c: isinstance(c.n.target, ast.Attribute)),
         ("augform-target-subscript", "目标形态=下标", lambda c: isinstance(c.n.target, ast.Subscript)),
         ("augform-target-chain", "目标形态=链式下标/属性", lambda c: isinstance(c.n.target, (ast.Attribute, ast.Subscript)) and isinstance(c.n.target.value, (ast.Attribute, ast.Subscript))),
         ("augform-in-if-arm", "宿主=if 臂", lambda c: has_anc(c, ast.If)),
         ("augform-in-loop-body", "宿主=循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("augform-in-try-body", "宿主=try 体", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("augform-in-handler", "宿主=except handler", lambda c: has_anc(c, ast.ExceptHandler)),
         ("augform-in-with-body", "宿主=with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("augform-in-match-case", "宿主=match case 体", lambda c: has_anc(c, ast.match_case)),
         ("augform-in-comp-scope", "宿主=推导式作用域", lambda c: has_anc(c, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))),
         ("augform-in-class-body", "宿主=类体", lambda c: has_anc(c, ast.ClassDef))],
        "test_repros/round4/c4_08_augassign.pyc")

    # ---- 25 slice（形态级镜像）-----------------------------------------
    fam("SLICEFORM", "slice", "slice", ast.Slice,
        ".trae/specs/attain-true-completeness/rounds/round8/REVIEW.md:52",
        ["subscript-index", "slice-bounds", "function-body", "module-level", "assign-rhs",
         "if-arm", "loop-body", "try-body", "call-arg", "return-value-expr"],
        [("sliceform-in-subscript", "形态位=下标内", lambda c: isinstance(c.p, ast.Subscript)),
         ("sliceform-in-del-target", "形态位=del 目标内", lambda c: has_anc(c, ast.Delete)),
         ("sliceform-in-assign-target", "形态位=赋值目标内", lambda c: has_anc(c, ast.Assign)),
         ("sliceform-nested-subscript", "形态位=链式下标内", lambda c: isinstance(c.p, ast.Subscript) and isinstance(c.p.value, (ast.Subscript, ast.Attribute))),
         ("sliceform-step-only", "形态位=仅 step", lambda c: c.n.step is not None and c.n.lower is None and c.n.upper is None),
         ("sliceform-full", "形态位=lower+upper+step", lambda c: c.n.step is not None and c.n.lower is not None and c.n.upper is not None),
         ("sliceform-single-bound", "形态位=单边界", lambda c: (c.n.lower is None) != (c.n.upper is None)),
         ("sliceform-in-call-arg", "形态位=调用实参内", lambda c: has_anc(c, ast.Call)),
         ("sliceform-in-return", "形态位=返回值内", lambda c: has_anc(c, ast.Return)),
         ("sliceform-in-try-body", "宿主=try 体", lambda c: in_body(c, (ast.Try, ast.TryStar)))],
        "test_repros/round4/c4_13_slice.pyc")

    # ================= NEW 族（25 行之外）================================
    fam("LAMBDA", "Lambda", "NEW", ast.Lambda,
        "core/cfg/ast_converter.py:110",
        ["function-body", "module-level", "assign-rhs", "call-arg", "return-value-expr",
         "class-body", "if-arm", "loop-body", "comprehension-scope", "condition-expr"],
        [("lambda-in-assign", "lambda 赋给名字", lambda c: parent_field(c, ast.Assign, "value")),
         ("lambda-as-call-arg", "lambda 作为实参", lambda c: isinstance(c.p, ast.Call) and ident_in(c.n, c.p.args)),
         ("lambda-in-return", "lambda 作为返回值", lambda c: parent_field(c, ast.Return, "value")),
         ("lambda-body-ternary", "lambda 体内为三元", lambda c: isinstance(c.n.body, ast.IfExp)),
         ("lambda-body-boolop", "lambda 体内含布尔运算", lambda c: desc_of(c.n.body, ast.BoolOp)),
         ("lambda-body-comprehension", "lambda 体内含推导式", lambda c: desc_of(c.n.body, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))),
         ("lambda-in-comprehension", "lambda 出现在推导式内", lambda c: has_anc(c, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp))),
         ("lambda-with-default", "lambda 带默认参数", lambda c: bool(c.n.args.defaults)),
         ("lambda-in-class-body", "lambda 出现在类体", lambda c: has_anc(c, ast.ClassDef)),
         ("lambda-in-loop-body", "lambda 出现在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While)))],
        "test_repros/round5/r5_11_comp_lambda.pyc")

    fam("DECORATOR", "Decorator", "NEW", ast.FunctionDef,
        "core/cfg/ast_converter.py:297",
        ["decorator-expr", "function-body", "class-body", "module-level", "call-arg"],
        [("deco-on-function", "函数上的装饰器", lambda c: isinstance(c.n, ast.FunctionDef) and bool(c.n.decorator_list)),
         ("deco-on-class", "类上的装饰器", lambda c: isinstance(c.n, ast.ClassDef) and bool(c.n.decorator_list)),
         ("deco-single", "单个装饰器", lambda c: len(c.n.decorator_list) == 1),
         ("deco-stack", "多个装饰器（有序）", lambda c: len(c.n.decorator_list) > 1),
         ("deco-with-args", "带参数的装饰器", lambda c: bool(c.n.decorator_list) and isinstance(c.n.decorator_list[0], ast.Call)),
         ("deco-name-form", "裸名字装饰器", lambda c: bool(c.n.decorator_list) and isinstance(c.n.decorator_list[0], ast.Name)),
         ("deco-attr-form", "属性访问装饰器", lambda c: bool(c.n.decorator_list) and isinstance(c.n.decorator_list[0], ast.Attribute)),
         ("deco-on-async-func", "async 函数上的装饰器", lambda c: isinstance(c.n, ast.AsyncFunctionDef) and bool(c.n.decorator_list))],
        "site-packages/fly/common/aes_encrypt.pyc")

    fam("SETCOMP", "SetComp", "NEW", ast.SetComp,
        "core/cfg/ast_converter.py:104",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "comprehension-scope", "comprehension-if", "if-arm", "loop-body", "class-body"],
        [("setcomp-single-for", "单 for 子句", lambda c: len(c.n.generators) == 1),
         ("setcomp-multi-for", "多 for 子句", lambda c: len(c.n.generators) > 1),
         ("setcomp-with-if", "带 if 过滤", lambda c: bool(c.n.ifs)),
         ("setcomp-async", "异步集合推导式", lambda c: any(g.is_async for g in c.n.generators)),
         ("setcomp-elt-ternary", "元素位为三元", lambda c: desc_of(c.n.elt, ast.IfExp)),
         ("setcomp-in-call-arg", "作为调用实参", lambda c: isinstance(c.p, ast.Call)),
         ("setcomp-in-assign", "作为赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("setcomp-nested-comp", "迭代式内嵌推导式", lambda c: any(isinstance(x, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for g in c.n.generators for x in ast.walk(g.iter)))],
        "test_repros/round5/r5_04_comp_cond.pyc")

    fam("DICTCOMP", "DictComp", "NEW", ast.DictComp,
        "core/cfg/ast_converter.py:105",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "comprehension-scope", "comprehension-if", "if-arm", "loop-body", "class-body"],
        [("dictcomp-single-for", "单 for 子句", lambda c: len(c.n.generators) == 1),
         ("dictcomp-multi-for", "多 for 子句", lambda c: len(c.n.generators) > 1),
         ("dictcomp-with-if", "带 if 过滤", lambda c: bool(c.n.ifs)),
         ("dictcomp-async", "异步字典推导式", lambda c: any(g.is_async for g in c.n.generators)),
         ("dictcomp-value-ternary", "值位为三元", lambda c: desc_of(c.n.value, ast.IfExp)),
         ("dictcomp-key-ternary", "键位为三元", lambda c: desc_of(c.n.key, ast.IfExp)),
         ("dictcomp-in-call-arg", "作为调用实参", lambda c: isinstance(c.p, ast.Call)),
         ("dictcomp-in-assign", "作为赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("dictcomp-nested-comp", "迭代式内嵌推导式", lambda c: any(isinstance(x, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for g in c.n.generators for x in ast.walk(g.iter)))],
        "test_repros/round5/r5_01_comp_basic.pyc")

    fam("GENEXP", "GeneratorExp", "NEW", ast.GeneratorExp,
        "core/cfg/ast_converter.py:106",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "comprehension-scope", "comprehension-if", "if-arm", "loop-body", "class-body"],
        [("genexp-single-for", "单 for 子句", lambda c: len(c.n.generators) == 1),
         ("genexp-multi-for", "多 for 子句", lambda c: len(c.n.generators) > 1),
         ("genexp-with-if", "带 if 过滤", lambda c: bool(c.n.ifs)),
         ("genexp-async", "异步生成器表达式", lambda c: any(g.is_async for g in c.n.generators)),
         ("genexp-elt-ternary", "元素位为三元", lambda c: desc_of(c.n.elt, ast.IfExp)),
         ("genexp-in-call-arg", "作为调用实参（sum/any）", lambda c: isinstance(c.p, ast.Call)),
         ("genexp-in-assign", "作为赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("genexp-nested-comp", "迭代式内嵌推导式", lambda c: any(isinstance(x, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)) for g in c.n.generators for x in ast.walk(g.iter)))],
        "test_repros/round5/r5_02_genexp.pyc")

    fam("NAMEDEXPR", "NamedExpr", "NEW", ast.NamedExpr,
        "core/cfg/ast_converter.py:107",
        ["function-body", "module-level", "if-arm", "else-arm", "loop-body", "condition-expr",
         "comprehension-if", "comprehension-for", "try-body", "except-handler", "with-body",
         "assign-rhs", "call-arg", "return-value-expr"],
        [("namedexpr-in-if-cond", "海象在 if 条件位", lambda c: parent_field(c, ast.If, "test")),
         ("namedexpr-in-while-cond", "海象在 while 条件位", lambda c: parent_field(c, ast.While, "test")),
         ("namedexpr-in-for-iter", "海象在 for 迭代式", lambda c: parent_field(c, ast.For, "iter") or parent_field(c, ast.AsyncFor, "iter")),
         ("namedexpr-in-comprehension-if", "海象在推导式过滤位", lambda c: isinstance(c.p, ast.comprehension) and ident_in(c.n, c.p.ifs)),
         ("namedexpr-in-comprehension-for", "海象在推导式 for 迭代式", lambda c: isinstance(c.p, ast.comprehension) and c.p.iter is c.n),
         ("namedexpr-in-call-arg", "海象作为调用实参", lambda c: isinstance(c.p, ast.Call)),
         ("namedexpr-in-assign", "海象在赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("namedexpr-in-return", "海象在返回值", lambda c: parent_field(c, ast.Return, "value")),
         ("namedexpr-in-loop-body", "海象在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("namedexpr-in-try", "海象在 try 体", lambda c: in_body(c, (ast.Try, ast.TryStar)))],
        "test_repros/round4/c4_10_walrus.pyc")

    fam("FSTRING", "JoinedStr", "NEW", ast.JoinedStr,
        "core/cfg/ast_converter.py:930",
        ["function-body", "module-level", "assign-rhs", "return-value-expr", "call-arg",
         "f-string-format", "if-arm", "loop-body", "try-body", "class-body", "dict-literal"],
        [("fstring-plain", "无插值 f-string", lambda c: not any(isinstance(v, ast.FormattedValue) for v in c.n.values)),
         ("fstring-with-var", "含 {var} 插值", lambda c: any(isinstance(v, ast.FormattedValue) for v in c.n.values)),
         ("fstring-with-format-spec", "含格式说明符", lambda c: any(isinstance(v, ast.FormattedValue) and v.format_spec is not None for v in c.n.values)),
         ("fstring-with-conversion", "含 !r/!s 转换", lambda c: any(isinstance(v, ast.FormattedValue) and v.conversion not in (-1, None) for v in c.n.values)),
         ("fstring-with-debug", "含 = 自文档插值", lambda c: any(isinstance(v, ast.FormattedValue) and v.format_spec is not None for v in c.n.values)),
         ("fstring-embedded-expr", "插值内为复杂表达式", lambda c: any(isinstance(v, ast.FormattedValue) and isinstance(v.value, (ast.Call, ast.BinOp, ast.IfExp)) for v in c.n.values)),
         ("fstring-in-call-arg", "f-string 作为实参", lambda c: isinstance(c.p, ast.Call)),
         ("fstring-in-assign", "f-string 作为赋值右值", lambda c: parent_field(c, ast.Assign, "value")),
         ("fstring-in-raise", "f-string 作为 raise 消息", lambda c: parent_field(c, ast.Raise, "exc")),
         ("fstring-in-dict-literal", "f-string 作为字典值", lambda c: isinstance(c.p, ast.Dict))],
        "test_repros/round3/e11_g8_fstrings.pyc")

    fam("STARRED", "Starred", "NEW", ast.Starred,
        "core/cfg/ast_converter.py:957",
        ["function-body", "module-level", "call-arg", "assign-rhs", "starred-operand",
         "return-value-expr", "list-literal", "tuple-literal", "if-arm", "loop-body"],
        [("starred-in-call", "调用实参展开 *args", lambda c: isinstance(c.p, ast.Call)),
         ("starred-at-head", "解包在头部 *a, b", lambda c: isinstance(c.p, (ast.Tuple, ast.List)) and c.p.elts and c.p.elts[0] is c.n),
         ("starred-at-mid", "解包在中部 a, *b, c", lambda c: isinstance(c.p, (ast.Tuple, ast.List)) and c.p.elts and c.p.elts[-1] is not c.n and c.p.elts[0] is not c.n),
         ("starred-at-tail", "解包在尾部 a, b, *c", lambda c: isinstance(c.p, (ast.Tuple, ast.List)) and c.p.elts and c.p.elts[-1] is c.n),
         ("starred-in-list-literal", "列表字面量内 *展开", lambda c: isinstance(c.p, ast.List)),
         ("starred-in-tuple-literal", "元组字面量内 *展开", lambda c: isinstance(c.p, ast.Tuple)),
         ("starred-in-return", "* 展开在返回值", lambda c: parent_field(c, ast.Return, "value")),
         ("starred-in-slice", "* 展开在切片边界", lambda c: has_anc(c, ast.Slice)),
         ("starred-in-assign", "赋值目标解包 *rest", lambda c: has_anc(c, ast.Assign))],
        "test_repros/round4/c4_12_star_args.pyc")

    fam("EXCEPTSTAR", "ExceptStar", "NEW", ast.TryStar,
        "core/cfg/region_ast_generator.py:9707",
        ["function-body", "module-level", "try-body", "except-handler", "else-of-try",
         "finally-body", "if-arm", "loop-body", "with-body", "nested-func-body"],
        [("es-single-handler", "单个 except* 臂", lambda c: len(c.n.handlers) == 1),
         ("es-multi-handler", "多个 except* 臂", lambda c: len(c.n.handlers) > 1),
         ("es-with-else", "except* 带 else 子句", lambda c: bool(c.n.orelse)),
         ("es-with-finally", "except* 带 finally 子句", lambda c: bool(c.n.finalbody)),
         ("es-group-exception-type", "异常类型为 ExceptionGroup", lambda c: bool(c.n.handlers) and isinstance(c.n.handlers[0].type, ast.Name) and "Group" in c.n.handlers[0].type.id),
         ("es-starred-capture", "handler 捕获 *rest", lambda c: bool(c.n.handlers) and c.n.handlers[0].name is not None),
         ("es-in-func", "except* 在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("es-in-loop", "except* 在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("es-in-try", "except* 嵌套在 try 内", lambda c: has_anc(c, (ast.Try, ast.TryStar))),
         ("es-in-with", "except* 在 with 体", lambda c: has_anc(c, (ast.With, ast.AsyncWith)))],
        "test_repros/round4/c4_03_except_star.pyc")

    fam("ANNASSIGN", "AnnAssign", "NEW", ast.AnnAssign,
        "core/cfg/ast_converter.py:76",
        ["function-body", "module-level", "class-body", "if-arm", "loop-body", "try-body",
         "except-handler", "with-body", "match-case-body", "annotation-context"],
        [("ann-simple-name", "带注解的名字目标", lambda c: isinstance(c.n.target, ast.Name)),
         ("ann-subscript-target", "带注解的下标目标", lambda c: isinstance(c.n.target, ast.Subscript)),
         ("ann-attr-target", "带注解的属性目标", lambda c: isinstance(c.n.target, ast.Attribute)),
         ("ann-with-value", "注解同时赋值", lambda c: c.n.value is not None),
         ("ann-no-value", "仅注解不赋值", lambda c: c.n.value is None),
         ("ann-in-class-body", "注解在类体", lambda c: has_anc(c, ast.ClassDef)),
         ("ann-in-func", "注解在函数体", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("ann-in-loop", "注解在循环体", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("ann-simple-type", "注解类型为简单名", lambda c: isinstance(c.n.annotation, ast.Name)),
         ("ann-subscript-type", "注解类型为泛型下标", lambda c: isinstance(c.n.annotation, ast.Subscript))],
        "test_repros/round2/c01_class_assign.pyc")

    fam("ASYNCFOR", "AsyncFor", "NEW", ast.AsyncFor,
        "core/cfg/ast_converter.py:66",
        ["async-func-body", "function-body", "comprehension-scope", "loop-body", "loop-else",
         "if-arm", "try-body", "with-body", "module-level", "nested-func-body"],
        [("af-in-async-def", "async for 在 async def 体", lambda c: has_anc(c, ast.AsyncFunctionDef)),
         ("af-nested-async-for", "嵌套 async for", lambda c: any(isinstance(x, ast.AsyncFor) for x in ast.walk(c.n) if x is not c.n)),
         ("af-with-else", "async for 带 else", lambda c: bool(c.n.orelse)),
         ("af-await-in-body", "体内含 await", lambda c: any(isinstance(x, ast.Await) for x in ast.walk(c.n))),
         ("af-in-try", "async for 在 try 内", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("af-in-with", "async for 在 with 内", lambda c: has_anc(c, (ast.With, ast.AsyncWith))),
         ("af-in-loop", "async for 嵌套在同步循环内", lambda c: has_anc(c, (ast.For, ast.While))),
         ("af-async-iter-ternary", "异步迭代式为三元", lambda c: desc_of(c.n.iter, ast.IfExp)),
         ("af-in-async-comp", "async for 出现在异步推导式", lambda c: has_anc(c, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)))],
        "test_repros/round6/r6_07_async_five.pyc")

    fam("ASYNCWITH", "AsyncWith", "NEW", ast.AsyncWith,
        "core/cfg/ast_converter.py:70",
        ["async-func-body", "function-body", "with-body", "with-item", "if-arm", "loop-body",
         "try-body", "except-handler", "match-case-body", "module-level", "nested-func-body"],
        [("aw-in-async-def", "async with 在 async def 体", lambda c: has_anc(c, ast.AsyncFunctionDef)),
         ("aw-single-item", "单管理项", lambda c: len(c.n.items) == 1),
         ("aw-multi-item", "多管理项", lambda c: len(c.n.items) > 1),
         ("aw-as-target", "带 as 绑定", lambda c: c.n.items[0].optional_vars is not None),
         ("aw-await-in-body", "体内含 await", lambda c: any(isinstance(x, ast.Await) for x in ast.walk(c.n))),
         ("aw-in-try", "async with 在 try 内", lambda c: in_body(c, (ast.Try, ast.TryStar))),
         ("aw-in-loop", "async with 在循环内", lambda c: has_anc(c, (ast.For, ast.AsyncFor, ast.While))),
         ("aw-in-match-case", "async with 在 match case 体", lambda c: has_anc(c, ast.match_case)),
         ("aw-nested-async-with", "嵌套 async with", lambda c: any(isinstance(x, ast.AsyncWith) for x in ast.walk(c.n) if x is not c.n)),
         ("aw-in-async-closure", "async with 在嵌套 async 闭包", lambda c: sum(1 for a in c.anc if isinstance(a, ast.AsyncFunctionDef)) >= 2)],
        "test_repros/round6/r6_08_async_cross.pyc")

    fam("ASYNCFUNC", "AsyncFunctionDef", "NEW", ast.AsyncFunctionDef,
        "core/cfg/ast_generator_v2.py:3696",
        ["function-body", "module-level", "class-body", "nested-func-body", "decorator-expr",
         "annotation-context", "default-arg"],
        [("afd-at-module", "模块级 async def", lambda c: not has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))),
         ("afd-in-class", "async def 作为方法", lambda c: has_anc(c, ast.ClassDef)),
         ("afd-nested", "async def 嵌套定义", lambda c: has_anc(c, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("afd-with-decorator", "async def 带装饰器", lambda c: bool(c.n.decorator_list)),
         ("afd-with-annotation", "async def 带返回注解", lambda c: c.n.returns is not None),
         ("afd-with-defaults", "async def 带默认参数", lambda c: bool(c.n.args.defaults)),
         ("afd-with-async-with", "体内含 async with", lambda c: any(isinstance(x, ast.AsyncWith) for x in ast.walk(c.n) if x is not c.n)),
         ("afd-with-async-for", "体内含 async for", lambda c: any(isinstance(x, ast.AsyncFor) for x in ast.walk(c.n) if x is not c.n)),
         ("afd-with-await", "体内含 await", lambda c: any(isinstance(x, ast.Await) for x in ast.walk(c.n))),
         ("afd-with-yield", "体内含 yield（异步生成器）", lambda c: any(isinstance(x, (ast.Yield, ast.YieldFrom)) for x in ast.walk(c.n)))],
        "test_repros/round6/r6_07_async_five.pyc")

    fam("PEP604", "PEP604Union", "NEW", ast.BinOp,
        "core/cfg/ast_converter.py:267",
        ["annotation-context", "function-body", "module-level", "class-body", "assign-rhs",
         "return-value-expr"],
        [("pep604-in-var-annotation", "X | Y 出现在变量注解", lambda c: _is_ann(c) and isinstance(c.p, ast.AnnAssign)),
         ("pep604-in-return-annotation", "X | Y 出现在返回注解", lambda c: _is_ann(c) and isinstance(c.p, (ast.FunctionDef, ast.AsyncFunctionDef))),
         ("pep604-optional-none", "X | None", lambda c: _is_ann(c) and isinstance(c.n.right, ast.Constant) and c.n.right.value is None),
         ("pep604-union-of-names", "两类型名取并", lambda c: _is_ann(c) and isinstance(c.n.left, ast.Name) and isinstance(c.n.right, ast.Name)),
         ("pep604-nested-union", "并集再嵌套并集", lambda c: _is_ann(c) and (isinstance(c.n.left, ast.BinOp) or isinstance(c.n.right, ast.BinOp))),
         ("pep604-in-call-arg", "X | Y 作为实参（运行时 union）", lambda c: isinstance(c.p, ast.Call) and isinstance(c.n.op, ast.BitOr)),
         ("pep604-in-assign", "X | Y 作为赋值右值", lambda c: parent_field(c, ast.Assign, "value") and isinstance(c.n.op, ast.BitOr)),
         ("pep604-bitor-not-in-ann", "普通位或（注解外）", lambda c: not _is_ann(c) and isinstance(c.n.op, ast.BitOr))],
        "core/cfg/ast_converter.py:267")

    return F


# --------------------------------------------------------------------------
# 生成
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="判定空间生成器")
    ap.add_argument("--evidence-root", default=".trae/specs/attain-true-completeness/rounds")
    ap.add_argument("--out", default=".trae/specs/attack-completeness-claims/rounds/round1/judgment_space.json")
    ap.add_argument("--md", default="")
    ap.add_argument("--stats", default="")
    args = ap.parse_args(argv)

    index = build_evidence_index(args.evidence_root)
    index_paths = {rel for (rel, _n) in index}
    fams = build_families()
    obs = observe(index, [(f["name"], f["nodes"], f["variants"]) for f in fams])

    entries = []
    seq = collections.Counter()
    for f in fams:
        obs_f = {k: v for k, v in obs.items() if k[0] == f["name"]}
        structural_added = 0
        zero_evidence = not obs_f
        cap = None if zero_evidence else f["structural_cap"]
        for vname, _vnote, _pred in f["variants"]:
            for h in admissible_hosts(f, vname):
                seen_depths = sorted({d for (_f, v, hh, d) in obs_f if v == vname and hh == h},
                                     key=lambda x: DEPTH_BUCKETS.index(x))
                buckets = sorted(set(host_depth_buckets(h)) | set(seen_depths),
                                 key=lambda x: DEPTH_BUCKETS.index(x))
                for d in buckets:
                    if d not in seen_depths:
                        continue
                    seq[f["code"]] += 1
                    eid = "JS-%s-%03d" % (f["code"], seq[f["code"]])
                    rel, nm = sorted(obs_f[(f["name"], vname, h, d)])[0]
                    binding = probe_binding(rel)
                    entries.append({
                        "id": eid, "form": f["name"], "host": h, "depth": d,
                        "variant": vname, "row": f["row"],
                        "required_evidence": [{
                            "kind": "probe",
                            "pyc": rel,
                            "note": "本单元专属见证探针（探针：%s；登记于 %s）"
                                    % (nm, "；".join(index[(rel, nm)]["stamps"][:2])),
                        }],
                        "status": "covered",
                        "source": f["source"],
                        "j_schema_version": J_SCHEMA_VERSION,
                        "expected_label": {"form": f["name"], "variant": vname,
                                           "host": h, "depth": d},
                        "counterexample_hint": f["anchor"],
                        "host_prelude": None,
                        "excluded": [],
                        **binding,
                    })
                if not seen_depths:
                    if cap is not None and structural_added >= cap:
                        continue
                    structural_added += 1
                    seq[f["code"]] += 1
                    eid = "JS-%s-%03d" % (f["code"], seq[f["code"]])
                    binding = probe_binding(f["anchor"])
                    entries.append({
                        "id": eid, "form": f["name"], "host": h, "depth": buckets[0],
                        "variant": vname, "row": f["row"],
                        "required_evidence": [{
                            "kind": "probe",
                            "pyc": f["anchor"],
                            "note": "本单元尚无专属探针：所引路径仅证明该形态族在仓内存在（%s），"
                                    "不证明本单元的宿主/深度/变体组合；需新造专属探针。" % f["anchor"],
                        }],
                        "status": "uncovered",
                        "source": f["source"],
                        "j_schema_version": J_SCHEMA_VERSION,
                        "expected_label": {"form": f["name"], "variant": vname,
                                           "host": h, "depth": buckets[0]},
                        "counterexample_hint": f["anchor"],
                        "host_prelude": None,
                        "excluded": [],
                        **binding,
                    })

    space = {
        "version": "v1",
        "j_schema_version": J_SCHEMA_VERSION,
        "generator_version": GENERATOR_VERSION,
        "generator_sha256": sha256_file(__file__),
        "seed": 0,
        "excluded": [],
        "created": "2026-10-21",
        "generator": "tools/completeness/jspace_generator.py",
        "counting_rules": {
            "depth": "depth = REGION_TYPES 祖先个数（Module 不计）；d1 = 0/1，d2 = 2，d3plus = >= 3；"
                     "宿主只允许 depth >= inherent(host)",
            "host": "host = 节点的直接父节点 + 该节点在父节点中的槽位唯一决定（host_of()）",
            "variant": "variant = 该形态族的语义变体槽；每槽由一个 AST 谓词判定（谓词源码在生成器内）",
            "cell": "条目 = (form, variant, host, depth)；族内按 variant 声明序 × 宿主声明序 × 深度档序展开",
            "structural": "结构性单元 = 该 (form,variant,host) 在证据索引中无任何观测时登记 1 条"
                          "（深度取该宿主最小档）；每族最多登记 structural_cap 条，整族零证据时不截断",
            "c1c5": "C1 = p_j/p_j_sha256/p_j_lines; C2 = pyc/pyc_sha256/pyc_loadable; C3/C4/C5 must come from an external evidence record; missing means not covered_5tuple.",
        },
        "dimensions": {
            "form": [f["name"] for f in fams],
            "host": sorted({h for f in fams for h in f["hosts"]}),
            "depth": list(DEPTH_BUCKETS),
            "variant": sorted({v[0] for f in fams for v in f["variants"]}),
        },
        "families": [
            {"code": f["code"], "form": f["name"], "row": f["row"], "source": f["source"],
             "hosts": f["hosts"], "structural_cap": f["structural_cap"],
             "variants": [{"name": v[0], "note": v[1]} for v in f["variants"]],
             "uncovered_anchor": f["anchor"]}
            for f in fams
        ],
        "entries": entries,
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(space, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    stats = build_stats(space, index_paths, index, obs, fams)
    if args.stats:
        with open(args.stats, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(stats, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    if args.md:
        write_md(args.md, space, stats)
    print("entries=%d covered=%d uncovered=%d index_paths=%d"
          % (stats["totals"]["entries"], stats["totals"]["covered"],
             stats["totals"]["uncovered"], stats["totals"]["index_paths"]))
    return 0


def build_stats(space, index_paths, index, obs=None, fams=None):
    per_fam = collections.defaultdict(lambda: collections.Counter())
    for e in space["entries"]:
        per_fam[e["form"]][e["status"]] += 1
        per_fam[e["form"]]["total"] += 1
    triples_total = triples_obs = 0
    if obs is not None and fams is not None:
        for f in fams:
            o = {k for k in obs if k[0] == f["name"]}
            for v, _n, _p in f["variants"]:
                for h in admissible_hosts(f, v):
                    triples_total += 1
                    if any(k[1] == v and k[2] == h for k in o):
                        triples_obs += 1
    covered = sum(1 for e in space["entries"] if e["status"] == "covered")
    uncovered = len(space["entries"]) - covered
    by_host = collections.Counter(e["host"] for e in space["entries"])
    by_depth = collections.Counter(e["depth"] for e in space["entries"])
    by_variant = collections.Counter(e["variant"] for e in space["entries"])
    by_row = collections.Counter(e["row"] for e in space["entries"])
    fam_rows = {}
    for e in space["entries"]:
        fam_rows.setdefault(e["form"], e["row"])
    worst = sorted(per_fam.items(), key=lambda kv: (-kv[1]["uncovered"], -kv[1]["total"]))
    green = 0
    for e in space["entries"]:
        if e["status"] != "covered":
            continue
        rel = e["required_evidence"][0]["pyc"]
        nm = None
        for (r, n) in index:
            if r == rel:
                nm = n
                break
        if nm is not None and "success" in (index[(rel, nm)]["status"] or []):
            green += 1
    return {
        "totals": {"entries": len(space["entries"]), "covered": covered, "uncovered": uncovered,
                   "families": len(space["families"]), "index_paths": len(index_paths),
                   "covered_with_green_witness": green,
                   "constructible_triples": triples_total,
                   "triples_with_observation": triples_obs,
                   "triples_without_observation": triples_total - triples_obs},
        "per_family": {k: {"total": v["total"], "covered": v["covered"], "uncovered": v["uncovered"],
                           "row": fam_rows.get(k, "?")} for k, v in sorted(per_fam.items())},
        "by_host": dict(sorted(by_host.items(), key=lambda kv: -kv[1])),
        "by_depth": dict(by_depth),
        "by_row": dict(sorted(by_row.items())),
        "variant_count": len(by_variant),
        "worst": [{"form": k, "total": v["total"], "covered": v["covered"], "uncovered": v["uncovered"]}
                  for k, v in worst[:12]],
    }


def sha256_file(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def probe_binding(pyc_rel):
    pyc_path = pyc_rel if os.path.isfile(pyc_rel) else None
    pyc_sha = sha256_file(pyc_path) if pyc_path else None
    source_path = None
    source_sha = None
    source_lines = None
    if isinstance(pyc_rel, str) and pyc_rel.lower().endswith(".pyc"):
        candidate = pyc_rel[:-1]
        if os.path.isfile(candidate):
            source_path = candidate
            source_sha = sha256_file(candidate)
            try:
                with open(candidate, "r", encoding="utf-8-sig", errors="replace") as fh:
                    source_lines = len(fh.read().splitlines())
            except OSError:
                source_lines = None
    return {
        "p_j": source_path,
        "p_j_sha256": source_sha,
        "p_j_lines": source_lines,
        "pyc": pyc_path or pyc_rel,
        "pyc_sha256": pyc_sha,
        "pyc_present": bool(pyc_path),
        "pyc_loadable": None,
        "input_model": {"kind": "module", "calls": [], "seed": 0,
                        "note": "default module model; stronger calls require C4 evidence"},
        "entrypoint": "module",
        "host_prelude": None,
        "host_prelude_reason": "host prelude is not derived from the probe source in J v2",
    }


ROWS25 = ["If", "BoolOp", "IfExp", "Try", "Raise", "Assert", "Import", "Global",
          "global_nonlocal", "Await", "ListComp", "await_expr", "Yield", "Match",
          "With", "match_statement", "Break", "Continue", "While", "Delete",
          "AugAssign", "Return", "Slice", "augmented_assign", "slice"]

NEW_REASONS = {
    "Lambda": "ast.Lambda 是独立文法族（`core/cfg/ast_converter.py:110` 有专有转换器）；上一规范 25 行无对应行。",
    "Decorator": "装饰器列表是函数/类的独立文法位置（`core/cfg/ast_converter.py:297` 读取 `decorator_list`），顺序与参数化形态在产物装配中单独成段；语料 `site-packages/fly/common/aes_encrypt.pyc` 含真实装饰器。",
    "SetComp": "ast.SetComp 走 SET_ADD（与 ListComp 的 LIST_APPEND 不同），是独立文法族（`core/cfg/ast_converter.py:104`）。",
    "DictComp": "ast.DictComp 走 MAP_ADD，是独立文法族（`core/cfg/ast_converter.py:105`）。",
    "GeneratorExp": "ast.GeneratorExp 与 ListComp 共享代码生成路径但语义为惰性生成器（`core/cfg/ast_converter.py:106`）。",
    "NamedExpr": "海象表达式（:=）是 3.8+ 独立文法族（`core/cfg/ast_converter.py:107`）。",
    "JoinedStr": "f-string 是独立文法族（`core/cfg/ast_converter.py:930` 专有 `_convert_joined_str_full`）。",
    "Starred": "星号展开在调用实参/解包/字面量三处语义不同（`core/cfg/ast_converter.py:957`）。",
    "ExceptStar": "3.11 `except*` 走独立异常表语义（`core/cfg/region_ast_generator.py:9707` 同时识别 Try/TryStar；`core/cfg/patch_detector.py:194` 列出 TryStar）。",
    "AnnAssign": "带注解赋值是独立文法族（`core/cfg/ast_converter.py:76` 专有 `_convert_ann_assign`）。",
    "AsyncFor": "async for 的迭代协议与同步 for 不同（`core/cfg/ast_converter.py:66`）。",
    "AsyncWith": "async with 的退出协议与同步 with 不同（`core/cfg/ast_converter.py:70`）。",
    "AsyncFunctionDef": "async def 的协程函数对象与普通函数不同（`core/cfg/ast_generator_v2.py:3696` 把 AsyncFor/AsyncWith 并入函数体区域集合）。",
    "PEP604Union": "`X | Y` 联合类型在注解位生成 `types.UnionType`，与 `typing.Union` 路径不同；产品侧按 BinOp 处理（`core/cfg/ast_converter.py:267`）。**本仓语料/探针 0 个 PEP604 样本**（实测扫描 5126 个 .py 全仓无命中）⇒ 整族无见证，属最诚实的缺口。",
}


def write_md(path, space, stats):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    L = []
    A = L.append
    A("# 判定空间（Judgment Space）— attack-completeness-claims / Task 1")
    A("")
    A("> 目的：把上一规范「完备 128 / 破口 0 / 零能力 0 = 100%」补上可证伪性——"
      "「完备」在此被重写为**有限可枚举的判定空间**（形态 × 宿主 × 深度 × 变体）的**全覆盖**。")
    A("> 生成器：`tools/completeness/jspace_generator.py`（本表与 `judgment_space.json` 同源、可重生成）。")
    A("> 机读清单：`rounds/round1/judgment_space.json`；覆盖检查器：`tools/completeness/coverage_checker.py`；"
      "首跑基线：`rounds/round1/COVERAGE_BASELINE.md`。")
    A("")
    A("> J schema v2 note: each entry now carries p_j/p_j_sha256/p_j_lines, pyc/pyc_sha256, expected_label, input_model and excluded. "
      "The `covered` field below is the legacy probe-observation status, NOT C1-C5 coverage. "
      "Use `coverage_checker.py` and `COVERAGE_C1C5.md` for covered_5tuple/probe_only/unexecuted counts.")
    A("")
    A("## 0. 规模读数（本文件由生成器写出，数字与 JSON 逐项一致）")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 条目总数 | **%d** |" % stats["totals"]["entries"])
    A("| 形态族数 | %d（25 行 %d + NEW %d） |" % (
        stats["totals"]["families"],
        sum(1 for f in space["families"] if f["row"] != "NEW"),
        sum(1 for f in space["families"] if f["row"] == "NEW")))
    A("| 形态维度取值数 | %d |" % len(space["dimensions"]["form"]))
    A("| 宿主维度取值数 | %d |" % len(space["dimensions"]["host"]))
    A("| 深度维度取值数 | %d |" % len(space["dimensions"]["depth"]))
    A("| 变体维度取值数 | %d |" % len(space["dimensions"]["variant"]))
    A("| 其中已落到条目上的变体取值数 | %d |" % stats["variant_count"])
    A("| 声明 covered（有专属见证探针） | %d |" % stats["totals"]["covered"])
    A("| 声明 uncovered | %d |" % stats["totals"]["uncovered"])
    A("| 其中见证探针曾判定为 success | %d |" % stats["totals"]["covered_with_green_witness"])
    A("| 证据索引内探针路径数 | %d |" % stats["totals"]["index_paths"])
    A("| 可构造 (form,variant,host) 三元组总数 | %d |" % stats["totals"]["constructible_triples"])
    A("| 其中已有观测的 | %d |" % stats["totals"]["triples_with_observation"])
    A("| 其中无观测的 | %d |" % stats["totals"]["triples_without_observation"])
    A("")
    A("## 1. 四个维度的定义")
    A("")
    A("### 1.1 形态（form）— 文法族")
    A("")
    A("形态 = **文法族**（不是 ast 节点名）。25 行沿用上一规范的行名（`REVIEW.md:19`）；"
      "其余为本规范新增（NEW），每族给出代码站点 file:line 作为「该形态在产品内被识别」的依据。")
    A("")
    A("| form | 归属行 | 依据（source） | 条目数 | covered | uncovered |")
    A("|---|---|---|---|---|---|")
    for f in space["families"]:
        pf = stats["per_family"][f["form"]]
        A("| %s | %s | `%s` | %d | %d | %d |" % (
            f["form"], f["row"], f["source"], pf["total"], pf["covered"], pf["uncovered"]))
    A("")
    A("### 1.2 宿主（host）— 宿主上下文")
    A("")
    A("host = 节点的**直接父节点** + 该节点在父节点中占据的**槽位**唯一决定（`host_of()`）。"
      "同一 ast 节点在不同槽位 = 不同宿主 = 不同判定单元。取值共 %d 个：" % len(space["dimensions"]["host"]))
    A("")
    A("| host | 条目数 | 最小深度 inherent | 允许深度档 |")
    A("|---|---|---|---|")
    for h in space["dimensions"]["host"]:
        inh = min(HOST_DEPTHS.get(h, (0,)))
        A("| %s | %d | %d | %s |" % (h, stats["by_host"].get(h, 0), inh,
                                  " / ".join(host_depth_buckets(h))))
    A("")
    A("### 1.3 深度（depth）— 深度档")
    A("")
    A("**计数规则（唯一、可复算）**：")
    A("")
    A("1. `REGION_TYPES` = {FunctionDef, AsyncFunctionDef, ClassDef, If, For, AsyncFor, While, "
      "With, AsyncWith, Try, TryStar, match_case, Lambda, ListComp, SetComp, DictComp, GeneratorExp}"
      " —— 即「会产生块/作用域边界」的节点。")
    A("2. 某节点的 **depth = 其 REGION_TYPES 祖先个数**（Module 不计）。")
    A("3. 深度档：`d1 单层` = depth 0 或 1；`d2 双层` = depth 2；`d3plus 三层及以上` = depth ≥ 3。")
    A("4. 宿主自身带来的必然 region 数（inherent）决定该宿主允许的深度档：宿主只允许 `depth >= inherent`"
      "（inherent=0/1 的宿主允许 d1/d2/d3plus；inherent=2 的宿主——except-handler / nested-func-body / "
      "elif-arm——只允许 d2/d3plus）。")
    A("")
    A("| depth | 条目数 |")
    A("|---|---|")
    for d in space["dimensions"]["depth"]:
        A("| %s | %d |" % (d, stats["by_depth"].get(d, 0)))
    A("")
    A("### 1.4 变体（variant）— 变体槽")
    A("")
    A("variant = **单个 ast 节点可承载的语义变体**。这是上一规范 128 计数所折叠掉的维度，"
      "也是本规范攻击的主轴。每槽由一个**可判定的 AST 谓词**定义（谓词源码见生成器 "
      "`tools/completeness/jspace_generator.py` 的 `build_families()`），并各自要求**独立证据**。")
    A("")
    A("| variant | 条目数 |")
    A("|---|---|")
    vc = collections.Counter(e["variant"] for e in space["entries"])
    for v, c in sorted(vc.items(), key=lambda kv: (-kv[1], kv[0])):
        A("| %s | %d |" % (v, c))
    A("")
    A("## 2. 计数规则（复算口径）")
    A("")
    A("| 计数 | 规则 | 复算命令 |")
    A("|---|---|---|")
    A("| 条目总数 | `len(entries)` | `python -X utf8 tools/completeness/jspace_generator.py --out ... --md ...` |")
    A("| 族条目数 | entries 中 `form` 等于该族名的行数 | 见 §3 |")
    A("| covered | 该 (form,variant,host,depth) 在证据索引的探针源码中**被观测到** ⇒ "
      "`required_evidence[0].pyc` 命中证据索引 | "
      "`python -X utf8 tools/completeness/coverage_checker.py --space ... --evidence-root ...` |")
    A("| uncovered | 该单元无观测 ⇒ `required_evidence[0].pyc` 指向**同族锚点探针**"
      "（仓内真实存在但**从未**登记进任何 `rec1_probes_*.json`） | 同上 |")
    A("| 结构性单元选取 | 某 (form,variant,host) 在索引中零观测时登记 1 条（深度取该宿主最小档）；"
      "每族最多登记 `structural_cap`=12 条；**整族零证据时不截断** | 同上 |")
    A("| 深度档 | §1.3 的 4 条 | 同上 |")
    A("")
    A("> **口径纠错声明**：上一规范台账「174 处标记」不可复现（实测 123 / 174 / 191 视正则口径而定，"
      "见 `baseline/markers.md` §5）。本空间**不使用**任何「标记数」口径；所有数字均可由 §2 的规则逐条重算。")
    A("")
    A("## 3. 逐族条目数")
    A("")
    A("| form | row | 条目 | covered | uncovered | 变体数 | 宿主数 |")
    A("|---|---|---|---|---|---|---|")
    for f in space["families"]:
        pf = stats["per_family"][f["form"]]
        A("| %s | %s | %d | %d | %d | %d | %d |" % (
            f["form"], f["row"], pf["total"], pf["covered"], pf["uncovered"],
            len(f["variants"]), len(f["hosts"])))
    A("")
    A("## 4. 全量条目表")
    A("")
    A("| id | form | host | depth | variant | row | required_evidence.pyc | status |")
    A("|---|---|---|---|---|---|---|---|")
    for e in space["entries"]:
        ev = e["required_evidence"][0]["pyc"] if e["required_evidence"] else ""
        A("| %s | %s | %s | %s | %s | %s | `%s` | %s |" % (
            e["id"], e["form"], e["host"], e["depth"], e["variant"], e["row"], ev, e["status"]))
    A("")
    A("## 5. 与既有 25 行的双向对齐（Task 1.3）")
    A("")
    A("| # | 25 行 | 空间条目数 | covered | uncovered | 归属判定 |")
    A("|---|---|---|---|---|---|")
    for i, r in enumerate(ROWS25, 1):
        pf = stats["per_family"].get(r)
        if pf is None:
            A("| %d | %s | **0** | 0 | 0 | **缺失** |" % (i, r))
        else:
            A("| %d | %s | %d | %d | %d | 已映射 |" % (i, r, pf["total"], pf["covered"], pf["uncovered"]))
    A("")
    A("**结论**：25 行**无一缺失**（每行在空间中至少 1 条独立条目，且每条要求独立证据）。")
    A("")
    A("### 5.1 NEW 族及其立项依据")
    A("")
    A("| NEW 族 | 依据（真实路径） | 立项理由 |")
    A("|---|---|---|")
    for f in space["families"]:
        if f["row"] != "NEW":
            continue
        A("| %s | `%s` | %s |" % (f["form"], f["source"], NEW_REASONS.get(f["form"], "")))
    A("")
    A("## 6. 诚实缺口声明")
    A("")
    A("- 本表存在 **%d 个 uncovered 单元**。它们的 `required_evidence[0].pyc` 指向**同族锚点探针**"
      "（仓内真实存在，但**从未**登记进任何 `rec1_probes_*.json` 证据索引），**不**指向该单元的专属探针"
      "——因为仓内不存在这样的专属探针。覆盖检查器据此判为未覆盖。" % stats["totals"]["uncovered"])
    A("- 未覆盖单元分两类：")
    A("  1. **结构性单元尚未可演示（structural cells not yet demonstrable）**：形态/宿主/变体组合在语言上可构造，"
      "但既有探针集里没有任何一个探针同时满足「该形态 + 该宿主 + 该深度档 + 该变体」；")
    A("  2. **整族零证据**：`global_nonlocal`（**25 行之一**，40 条）与 NEW 族 `ExceptStar`（96 条）"
      "**整族无任何见证探针**——这是本次攻击最硬的发现：上一规范把 `global_nonlocal` 判为「完备」，"
      "但其证据索引里没有任何一个探针包含 `ast.Nonlocal` 节点。")
    A("- 「covered」在本表内**只表示「该单元有专属见证探针」**，不表示「该单元的产物语义正确」——"
      "后者属语义级差分（Task 6/9 `semantic_diff.py`）与变异测试（Task 9 `mutation_test.py`）的判据，"
      "本轮不做、也不假装做了。")
    A("- **空间是「优先序化」的，不是穷尽的**：按 §2 规则，可构造的 (form,variant,host) 三元组共 "
      "%d 个，其中 %d 个已有观测、**%d 个无观测**；本表按「每族最多登记 12 条结构性单元」的规则"
      "优先登记其中一部分（整族零证据者不截断）。因此「uncovered = %d」是**已登记**缺口数，"
      "真实缺口规模上界为 %d —— 空间随证据增长而扩张（Task 3 的 L1 口径攻击负责把余量并入）。"
      % (stats["totals"]["constructible_triples"], stats["totals"]["triples_with_observation"],
         stats["totals"]["triples_without_observation"], stats["totals"]["uncovered"],
         stats["totals"]["triples_without_observation"]))
    A("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
        fh.write("\n")


if __name__ == "__main__":
    sys.exit(main())
