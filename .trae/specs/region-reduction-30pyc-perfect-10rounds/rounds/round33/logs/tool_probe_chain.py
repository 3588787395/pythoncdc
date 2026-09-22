# -*- coding: utf-8 -*-
"""Round 33 read-only diagnostic: instrument the return-through-cleanup chain walk for the
blocks that report `NO chain` (witness w1 block@68, load_yaml block@138).

Wraps RegionASTGenerator._find_return_chain_via_successors, prints for the requested start
offsets the roles / ownership / stack neutrality of every block the BFS visits, then calls the
original untouched.  Writes nothing but this script's own stdout.

usage: python -X utf8 probe_chain.py <pyc> <start-offset>[,<start-offset>...]
"""
import ast
import dis
import io
import os
import sys

REPO = r'F:/Downloads/pythoncdc-main'
# PROBE_CORE selects which core the probe measures with (default: the repo worktree = landed bytes)
CORE = os.environ.get('PROBE_CORE', REPO)
SRC = REPO + '/core/cfg/region_ast_generator.py'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, CORE)
sys.path.append(REPO)  # non-core packages (bytecode/, scripts/) still come from the repo

# the whitelist, read from the shipped source rather than re-typed, so the probe cannot drift
tree = ast.parse(io.open(SRC, encoding='utf-8-sig').read())
WL = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == '_find_return_chain_via_successors':
        for st in node.body:
            if isinstance(st, ast.Assign) and getattr(st.targets[0], 'id', None) == '_cleanup_only_ops':
                WL = {e.value for e in st.value.elts}
assert WL and 'POP_TOP' in WL and 'SWAP' in WL, WL
NOISE = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
JUMPS = ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')

import pycdc  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402
_got = os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/')
assert _got == CORE.replace('\\', '/').rstrip('/'), 'probe resolved to %s not %s' % (_got, CORE)
print('core arm: %s' % _got)

WANT = set(int(x) for x in sys.argv[2].split(','))
TARGET = sys.argv[1]
orig = RegionASTGenerator._find_return_chain_via_successors


def ops_of(b):
    return [i.opname for i in b.instructions if i.opname not in NOISE]


def net_effect(b):
    d, unknown = 0, False
    for i in b.instructions:
        if i.opname in NOISE:
            continue
        try:
            e = dis.stack_effect(i.opcode, i.arg)
        except (ValueError, TypeError):
            try:
                e = dis.stack_effect(i.opcode)
            except (ValueError, TypeError):
                e = None
        if e is None:
            unknown = True
        else:
            d += e
    return d, unknown


def terminal(b):
    o = ops_of(b)
    while o and o[-1] in JUMPS:
        o.pop()
    return o[-1] if o else None


def owned(b, gen, region):
    """structural ownership of b inside the enclosing try/finally region"""
    tags = []
    if region is None:
        return ['<no try_finally region>']
    if b in (region.finally_blocks or []):
        tags.append('finally_blocks')
    if b in (region.cleanup_blocks or []):
        tags.append('cleanup_blocks')
    if b in (region.try_blocks or []):
        tags.append('try_blocks')
    for k, v in (region.finally_copy_blocks or {}).items():
        if k == b.start_offset or v == b.start_offset:
            tags.append('finally_copy_blocks[%s->%s]' % (k, v))
    return tags


def wrapped(self, start_block, *a, **kw):
    res = orig(self, start_block, *a, **kw)
    if start_block.start_offset not in WANT:
        return res
    print('=== start block@%d  func=%s  role=%s  ops=%s'
          % (start_block.start_offset, getattr(self.cfg, 'name', '?'),
             self.block_role(start_block).name, ops_of(start_block)))
    reg = None
    try:
        reg = self.region_analyzer.find_enclosing_region(start_block, 'try_finally',
                                                         require_finally=True)
    except Exception as e:
        print('   find_enclosing_region raised %r' % e)
    if reg is None:
        print('   enclosing try_finally region: None')
    else:
        print('   enclosing try_finally: has_finally=%s try=%s finally=%s cleanup=%s copy=%s'
              % (reg.has_finally, [b.start_offset for b in reg.try_blocks],
                 [b.start_offset for b in reg.finally_blocks],
                 [b.start_offset for b in reg.cleanup_blocks],
                 dict(reg.finally_copy_blocks)))
    print('   try_depth=%s  result=%s' % (self._try_depth,
                                          None if res is None else [b.start_offset for b in res]))
    visited = set()
    queue = [(s, 1) for s in start_block.successors]
    maxd = int(os.environ.get('PROBE_DEPTH', '3'))
    while queue:
        b, depth = queue.pop(0)
        if id(b) in visited or depth > maxd:
            continue
        visited.add(id(b))
        o = ops_of(b)
        outside = sorted({x for x in o if x not in WL})
        has_ret = any(x in ('RETURN_VALUE', 'RETURN_CONST') for x in o)
        ne, unk = net_effect(b)
        print('   d%d block@%-5r role=%-18s preds=%s succs=%s ret=%-5s net=%s%s term=%-12s '
              'outside_wl=%s owned=%s ops=%s'
              % (depth, b.start_offset, self.block_role(b).name,
                 sorted(p.start_offset for p in b.predecessors),
                 sorted(s.start_offset for s in b.successors), has_ret, ne,
                 '(unknown)' if unk else '', terminal(b), outside, owned(b, self, reg), o))
        if depth < maxd:
            for s in b.successors:
                queue.append((s, depth + 1))
    return res


RegionASTGenerator._find_return_chain_via_successors = wrapped
text = pycdc.decompile_pyc(TARGET)
io.open(r'D:/Temp/r33gate/c33/probe_chain_product.py', 'w', encoding='utf-8').write(text)
print('product %d bytes (probe-local copy only)' % len(text))
