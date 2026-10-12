"""Probe R21-37 step 2: dump the AST subtree that carries the 'SPECULATION' / 'OPEN' ternaries in
_process_order, so it is decided from the tree whether the arms exist there (and are dropped
downstream) or were never built.

usage: python -X utf8 ternary_probe_r37b.py
"""
import json
import marshal
import os
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
PYC = os.path.join(REPO, "site-packages", "IQEngine", "plugins", "plugin_system_trade",
                   "trade_live_broker.pyc")
UNIT = "_process_order"

from core.cfg import build_cfg                                    # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator      # noqa: E402

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
ast = RegionASTGenerator(build_cfg(fn), top_level_code=fn).generate()

TYPES = {}


def count_types(node):
    if isinstance(node, dict):
        TYPES[node.get('type')] = TYPES.get(node.get('type'), 0) + 1
        for v in node.values():
            count_types(v)
    elif isinstance(node, list):
        for v in node:
            count_types(v)


count_types(ast)
print("node type census: %s" % json.dumps(TYPES, sort_keys=True))

WANT = ('SPECULATION', 'OPEN', '非备兑类型委托', '开仓')
hits = []


def find(node, path='root', ancestors=()):
    if isinstance(node, dict):
        if node.get('type') == 'Constant' and node.get('value') in WANT:
            hits.append((path, node.get('value'), ancestors))
        for k, v in node.items():
            find(v, path + '.' + str(k), ancestors[-2:] + (node.get('type'),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            find(v, path + '[%d]' % i, ancestors[-2:] + ('list',))


find(ast)
print("constant hits: %d" % len(hits))
for path, val, anc in hits[:6]:
    print("   %r  at %s   ancestors=%s" % (val, path[-90:], anc))


def sub(node, dotted):
    cur = node
    for tok in dotted.replace('root', '').strip('.').replace('[', '.[').split('.'):
        if not tok:
            continue
        if tok.startswith('['):
            cur = cur[int(tok[1:-1])]
        else:
            cur = cur[tok]
    return cur


for path, val, anc in hits[:2]:
    for depth in (3, 2, 1):
        parts = path.split('.')
        cut = '.'.join(parts[:len(parts) - depth]) if len(parts) > depth else path
        try:
            node = sub(ast, cut)
        except Exception:
            continue
        s = json.dumps(node, ensure_ascii=False, default=str)
        print("---- %s (up %d) len=%d" % (cut[-70:], depth, len(s)))
        print("     " + s[:700])
        break
