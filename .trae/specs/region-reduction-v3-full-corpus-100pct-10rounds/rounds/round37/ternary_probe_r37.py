"""Probe R21-37: find the AST nodes whose conditional-expression arms are empty, and which lines
built them, for trade_live_broker._process_order.

Read-only: generates the single function's AST in its own process, with a line trace restricted to
region_ast_generator.py. Nothing in the pipeline is edited.

usage: python -X utf8 ternary_probe_r37.py
"""
import marshal
import os
import re
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
PYC = os.path.join(REPO, "site-packages", "IQEngine", "plugins", "plugin_system_trade",
                   "trade_live_broker.pyc")
GEN = os.path.join(REPO, "core", "cfg", "region_ast_generator.py")
UNIT = "_process_order"

from core.cfg import build_cfg                                     # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator       # noqa: E402

CO = type(compile("", "", "exec"))


def gather(c, acc):
    acc.append(c)
    for cst in c.co_consts:
        if isinstance(cst, CO):
            gather(cst, acc)


code = marshal.loads(open(PYC, 'rb').read()[16:])
acc = []
gather(code, acc)
fn = [c for c in acc if c.co_name == UNIT][0]

src_lines = open(GEN, encoding='utf-8-sig').read().split('\n')
BUILD_SITES = set()
for n, l in enumerate(src_lines, 1):
    if re.search(r"'type':\s*'(IfExp|Call|Ternary|If)\b", l) or 'IfExp' in l:
        BUILD_SITES.add(n)

executed = set()


def tracer(frame, event, arg):
    if event == 'line':
        f = frame.f_code
        if os.path.normcase(f.co_filename) == os.path.normcase(GEN):
            executed.add(frame.f_lineno)
    return tracer


gen = RegionASTGenerator(build_cfg(fn), top_level_code=fn)
sys.settrace(tracer)
ast = gen.generate()
sys.settrace(None)

print("IfExp/Call/If construction lines executed: %s"
      % sorted(n for n in executed if n in BUILD_SITES)[:24])


def describe(v):
    if isinstance(v, dict):
        t = v.get('type')
        if t == 'Constant':
            return 'Constant(%r)' % (v.get('value'),)
        return t or '?'
    if isinstance(v, list):
        return 'list[%d]' % len(v)
    if v is None:
        return 'None'
    return type(v).__name__


findings = []


def walk(node, path='root'):
    if isinstance(node, dict):
        t = node.get('type')
        if t == 'IfExp':
            findings.append((path, 'IfExp', describe(node.get('body')), describe(node.get('orelse')),
                             describe(node.get('test'))))
        if t == 'If':
            b, o = node.get('body'), node.get('orelse')
            if not b or (isinstance(b, list) and len(b) == 0) or o == []:
                findings.append((path, 'If', describe(b), describe(o), describe(node.get('test'))))
        if t == 'Call':
            args = node.get('args') or []
            empty = [i for i, a in enumerate(args) if a in (None, {}, [], '')]
            if empty:
                findings.append((path, 'Call.empty-args@%s' % empty, len(args), '', ''))
        for k, v in node.items():
            walk(v, path + '.' + str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + '[%d]' % i)


walk(ast)
print("nodes with missing arms/args: %d" % len(findings))
for f in findings[:25]:
    print("   %-58s %-14s body=%-12s orelse=%-12s test=%s" % f)
