# -*- coding: utf-8 -*-
"""branch_conditions.py — 程序自身**每一分支判断条件**的跟踪与相似度比较

对白名单 61 模块（core/ parsers/ bytecode/ utils/ + pycdc + pycdas，与
program_cfg.py 同口径）做 **AST 级**判定点提取：每个分支判定点记录其
条件表达式原文 + 结构归一化形态 + 结构/文本哈希 + 判定嵌套深度。

判定点分类（与完备性标准的分支形态对齐；for 的 FOR_ITER 与异常表边
不是源级"判断条件"，不进条件库——由 program-cfg.json 覆盖）：
  IF_TEST          ast.If.test（if/elif 链逐条件）
  WHILE_TEST       ast.While.test
  IFEXP_TEST       ast.IfExp.test
  BOOLOP_OPERAND   ast.BoolOp.values[i]（and/or 短路链逐操作数）
  COMP_IF          ast.comprehension.ifs[j]（推导式 if 子句）
  MATCH_GUARD      ast.match_case.guard（非 None 才记录）
  ASSERT_TEST      ast.Assert.test

归一化（用于相似度，消除变量名/常量字面差异，保留结构）：
  Name→N, Attribute→A, Constant→C, arg→N
  结构哈希 h = sha1(ast.dump(归一化AST))[:12]   —— 同形同哈希（精确结构重复）
  文本哈希 t = sha1(去空白 unparse)[:12]          —— 逐字重复
相似度（查询模式）：
  score = SequenceMatcher(None, q_norm, r_norm).ratio()（长度差>50% 预过滤）
  结构哈希全等 → score 直接记 1.0

用法：
  python -X utf8 tools/kb/branch_conditions.py                     # 提取 → docs/refactor/branch-conditions.json
  python -X utf8 tools/kb/branch_conditions.py similar "inner_merge != merge_" [--top-k 20] [--kind IF_TEST] [--module core/cfg/region_analyzer.py]
  python -X utf8 tools/kb/branch_conditions.py dupes [--min-size 3] [--show 15]
"""
import ast
import difflib
import hashlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = r'F:\Downloads\pythoncdc-main'
OUT = os.path.join(ROOT, 'docs', 'refactor', 'branch-conditions.json')
WL_DIRS = ['core', 'parsers', 'bytecode', 'utils']
ENTRIES = ['pycdc', 'pycdas']

FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
SCOPE_PUSH_KIND = {'if', 'while', 'ifexp', 'boolop', 'match', 'comp'}


# ---------------- 归一化 ----------------
class _Norm(ast.NodeTransformer):
    def visit_Name(self, node):
        return ast.copy_location(ast.Name(id='N', ctx=node.ctx), node)

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = 'A'
        return node

    def visit_Constant(self, node):
        return ast.copy_location(ast.Constant(value='C'), node)

    def visit_arg(self, node):
        node.arg = 'N'
        self.generic_visit(node)
        return node


def _sha12(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:12]


def norm_pair(node):
    """返回 (归一化文本, 结构哈希, 文本哈希, 原文)"""
    orig = ast.unparse(node)
    norm_tree = _Norm().visit(ast.parse(orig, mode='eval'))
    norm = ast.unparse(norm_tree.body)
    dump = ast.dump(norm_tree.body, annotate_fields=False, include_attributes=False)
    return norm, _sha12(dump), _sha12(re.sub(r'\s+', '', orig)), orig


# ---------------- 提取 ----------------
class Extractor:
    def __init__(self):
        self.records = []
        self.stack = []          # 判定嵌套栈：('if'|'while'|'ifexp'|'boolop'|'match'|'comp')
        self.scopes = []         # (name, is_class)

    def qualname(self):
        parts = []
        for i, (name, is_class) in enumerate(self.scopes):
            if i == 0:
                parts.append(name)
            else:
                parent_is_func = not self.scopes[i - 1][1]
                sep = '.<locals>.' if (parent_is_func and not is_class) else '.'
                parts.append(sep + name)
        return ''.join(parts) or '<module>'

    def rec(self, kind, node, depth, **extra):
        norm, h, t, orig = norm_pair(node)
        r = {'m': self.module, 'q': self.qualname(), 'k': kind,
             'L': node.lineno, 'E': node.end_lineno or node.lineno,
             'c': orig, 'n': norm, 'h': h, 't': t, 'd': depth}
        r.update(extra)
        self.records.append(r)

    def visit_Module(self, node):
        for child in node.body:
            self._c(child)

    # —— 作用域入栈 ——
    def _push_scope(self, node, is_class=False):
        self.scopes.append((node.name, is_class))

    def _pop_scope(self):
        self.scopes.pop()

    def _c(self, node):
        """通用递归：处理判定点 + 作用域 + 深度栈"""
        if node is None:
            return
        if isinstance(node, ast.If):
            self.rec('IF_TEST', node.test, len(self.stack))
            self._c(node.test)                 # 条件内嵌 BoolOp/IfExp 逐操作数记录
            self.stack.append('if')
            for s in node.body:
                self._c(s)
            self.stack.pop()
            self.stack.append('if')       # elif/else 分支同属该判定深度
            for s in node.orelse:
                self._c(s)
            self.stack.pop()
        elif isinstance(node, ast.While):
            self.rec('WHILE_TEST', node.test, len(self.stack))
            self._c(node.test)
            self.stack.append('while')
            for s in node.body:
                self._c(s)
            self.stack.pop()
            for s in node.orelse:
                self._c(s)
        elif isinstance(node, ast.IfExp):
            self.rec('IFEXP_TEST', node.test, len(self.stack))
            self._c(node.test)
            self.stack.append('ifexp')
            self._c(node.body)
            self.stack.pop()
            self._c(node.orelse)
        elif isinstance(node, ast.BoolOp):
            self.stack.append('boolop')
            op = 'and' if isinstance(node.op, ast.And) else 'or'
            for v in node.values:
                self.rec('BOOLOP_OPERAND', v, len(self.stack), op=op)
            for v in node.values:
                self._c(v)
            self.stack.pop()
        elif isinstance(node, ast.Match):
            self._c(node.subject)
            self.stack.append('match')
            for case in node.cases:
                if case.guard is not None:
                    self.rec('MATCH_GUARD', case.guard, len(self.stack))
                    self._c(case.guard)
                for child in ast.iter_child_nodes(case.pattern):
                    self._c(child)
                for s in case.body:
                    self._c(s)
            self.stack.pop()
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in node.generators:
                self.stack.append('comp')
                for cond in gen.ifs:
                    self.rec('COMP_IF', cond, len(self.stack))
                    self._c(cond)
                self._c(gen.iter)
                self.stack.pop()
            if isinstance(node, ast.DictComp):
                self._c(node.key)
                self._c(node.value)
            else:
                self._c(node.elt)
        elif isinstance(node, ast.Assert):
            self.rec('ASSERT_TEST', node.test, len(self.stack))
            self._c(node.test)
            if node.msg is not None:
                self._c(node.msg)
        elif isinstance(node, FUNC_NODES):
            self._push_scope(node)
            for d in node.decorator_list:
                self._c(d)
            for a in node.args.defaults + [x for x in node.args.kw_defaults if x is not None]:
                self._c(a)
            for s in node.body:
                self._c(s)
            self._pop_scope()
        elif isinstance(node, ast.ClassDef):
            self._push_scope(node, is_class=True)
            for d in node.decorator_list:
                self._c(d)
            for b in node.bases:
                self._c(b)
            for s in node.body:
                self._c(s)
            self._pop_scope()
        elif isinstance(node, ast.Lambda):
            self.scopes.append(('<lambda>', False))
            for a in node.args.defaults:
                self._c(a)
            self._c(node.body)
            self._pop_scope()
        else:
            for child in ast.iter_child_nodes(node):
                self._c(child)


def extract():
    srcs = []
    for d in WL_DIRS:
        base = os.path.join(ROOT, d)
        for dp, dn, fn in os.walk(base):
            for f in sorted(fn):
                if f.endswith('.py'):
                    srcs.append(os.path.join(dp, f))
    for e in ENTRIES:
        srcs.append(os.path.join(ROOT, e + '.py'))
    srcs.sort()

    ex = Extractor()
    n_ok = n_fail = 0
    fail = Counter()
    for path in srcs:
        rel = os.path.relpath(path, ROOT).replace('\\', '/')
        try:
            src = io.open(path, encoding='utf-8-sig', errors='replace').read()  # utf-8-sig：region_ast_generator.py 带 BOM（G0 保护）
            tree = ast.parse(src, filename=rel)
        except Exception as e:
            n_fail += 1
            fail[rel + ':' + type(e).__name__] += 1
            continue
        n_ok += 1
        ex.module = rel
        try:
            ex.visit_Module(tree)
        except RecursionError:
            n_fail += 1
            fail[rel + ':RecursionError'] += 1

    by_kind = Counter(r['k'] for r in ex.records)
    by_mod = Counter(r['m'] for r in ex.records)
    by_h = defaultdict(list)
    for r in ex.records:
        by_h[r['h']].append(r)
    dup_groups = {h: v for h, v in by_h.items() if len(v) > 1}
    dup_records = sum(len(v) for v in dup_groups.values())
    max_d = max((r['d'] for r in ex.records), default=0)
    depth_hist = Counter(min(r['d'], 60) for r in ex.records)

    out = {
        'program': {
            'modules': len(srcs), 'parsed': n_ok, 'fail': n_fail,
            'decision_points': len(ex.records),
            'unique_struct_hashes': len(by_h),
            'structural_dup_records': dup_records,
            'structural_dup_groups': len(dup_groups),
            'max_decision_depth': max_d,
        },
        'by_kind': dict(by_kind.most_common()),
        'by_module_top30': dict(by_mod.most_common(30)),
        'depth_hist': {str(k): v for k, v in sorted(depth_hist.items(), key=lambda kv: int(kv[0]))},
        'fail_kinds': dict(fail.most_common()),
        'records': ex.records,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(out, ensure_ascii=False, separators=(',', ':')))

    print('=== 分支判定条件库 ===')
    print('modules=%d parsed=%d fail=%d' % (len(srcs), n_ok, n_fail))
    print('判定点=%d 唯一结构哈希=%d 结构重复记录=%d(组=%d) 最深判定嵌套=%d'
          % (len(ex.records), len(by_h), dup_records, len(dup_groups), max_d))
    print('\n--- by kind ---')
    for k, v in by_kind.most_common():
        print('%8d  %s' % (v, k))
    print('\n--- 判定点最多的模块 top 20 ---')
    for k, v in by_mod.most_common(20):
        print('%8d  %s' % (v, k))
    print('\n--- 结构重复组 top 15（同形条件簇） ---')
    for h, v in sorted(dup_groups.items(), key=lambda kv: -len(kv[1]))[:15]:
        print('%6d x  %s   (示例 %s:%d  %s)' % (len(v), v[0]['k'], v[0]['m'], v[0]['L'], v[0]['c'][:70]))
    print('\nJSON -> %s' % OUT)


# ---------------- 相似度查询 ----------------
def load_records():
    if not os.path.exists(OUT):
        print('先运行提取：python -X utf8 tools/kb/branch_conditions.py')
        sys.exit(2)
    return json.load(io.open(OUT, encoding='utf-8'))['records']


def similar(query, top_k=20, kind=None, module=None):
    records = load_records()
    q_norm, q_h, q_t, q_orig = norm_pair(ast.parse(query, mode='eval').body)
    qlen = len(q_norm)
    scored = []
    n_skip = 0
    for r in records:
        if kind and r['k'] != kind:
            continue
        if module and module not in r['m']:
            continue
        rl = len(r['n'])
        if qlen and rl and abs(rl - qlen) > max(qlen, rl) * 0.5:
            n_skip += 1
            continue
        if r['h'] == q_h:
            score = 1.0
        else:
            score = difflib.SequenceMatcher(None, q_norm, r['n']).ratio()
        if score > 0.30:
            scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], x[1]['m'], x[1]['L']))
    print('query: %s' % q_orig)
    print('归一化: %s   结构哈希: %s' % (q_norm, q_h))
    print('candidates=%d (长度预过滤跳过 %d)  top %d:' % (len(scored), n_skip, min(top_k, len(scored))))
    for s, r in scored[:top_k]:
        exact = ' [结构全等]' if r['h'] == q_h else ''
        print('%5.3f  %-16s %s :: %s:%d%s' % (s, r['k'], r['m'], r['q'], r['L'], exact))
        print('        %s' % r['c'][:110])


def dupes(min_size=3, show=15):
    data = json.load(io.open(OUT, encoding='utf-8'))
    groups = defaultdict(list)
    for r in data['records']:
        groups[r['h']].append(r)
    big = [(h, v) for h, v in groups.items() if len(v) >= min_size]
    big.sort(key=lambda kv: -len(kv[1]))
    print('结构哈希组总数=%d  ≥%d 的组=%d' % (len(groups), min_size, len(big)))
    for h, v in big[:show]:
        mods = Counter(r['m'] for r in v)
        print('\n%6d x  [%s]  归一化: %s' % (len(v), v[0]['k'], v[0]['n'][:90]))
        print('        模块分布: %s' % ', '.join('%s(%d)' % kv for kv in mods.most_common(5)))
        for r in v[:4]:
            print('        - %s :: %s:%d  %s' % (r['m'], r['q'], r['L'], r['c'][:80]))


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        extract()
    elif args[0] == 'similar':
        q = args[1] if len(args) > 1 else ''
        top_k = int(args[args.index('--top-k') + 1]) if '--top-k' in args else 20
        kind = args[args.index('--kind') + 1] if '--kind' in args else None
        module = args[args.index('--module') + 1] if '--module' in args else None
        similar(q, top_k, kind, module)
    elif args[0] == 'dupes':
        min_size = int(args[args.index('--min-size') + 1]) if '--min-size' in args else 3
        show = int(args[args.index('--show') + 1]) if '--show' in args else 15
        dupes(min_size, show)
    else:
        print(__doc__)
        sys.exit(2)
