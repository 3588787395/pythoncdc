# -*- coding: utf-8 -*-
"""diag1b read-only probe: print the immediate-post-dominator chain of blocks.

usage: python -X utf8 pdom.py <pyc> <func> <off> [<off> ...]
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('no')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


pyc, name = sys.argv[1], sys.argv[2]
offs = [int(x) for x in sys.argv[3:]]
c = [x for x in walk(load_pyc(pyc), []) if x.co_name == name][0]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=None)
da = gen.region_analyzer.dom_analyzer
gen.region_analyzer.analyze()
if -1 in offs:
    _bl = getattr(cfg, 'blocks', [])
    _bl = list(_bl.values()) if isinstance(_bl, dict) else list(_bl)
    _bl = [b for b in _bl if hasattr(b, 'start_offset')]
    n = len(_bl)
    for b in sorted(_bl, key=lambda x: x.start_offset):
        sz = len(getattr(b, 'post_dominators', set()))
        ns = sorted(s.start_offset for s in b.successors)
        print('%6d pdom=%3d/%d succ=%s %s' % (
            b.start_offset, sz, n, ns,
            'STUCK-ALL' if sz >= n else ''))
    raise SystemExit(0)
for off in offs:
    b = cfg.get_block_by_offset(off)
    if b is None:
        print('%s: no block' % off)
        continue
    ch, cur, seen = [], b, set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        ch.append(cur.start_offset)
        cur = getattr(cur, 'immediate_post_dominator', None)
    first = b.instructions[0].opname if b.instructions else '?'
    last = b.instructions[-1].opname if b.instructions else '?'
    print('%5d %-12s..%-12s succ=%s exc=%s  IPD-chain=%s  pdom=%s' % (
        off, first, last,
        sorted(s.start_offset for s in b.successors),
        sorted(getattr(s, 'start_offset', -1) for s in getattr(b, 'exception_successors', []) or []),
        ch, sorted(x.start_offset for x in getattr(b, 'post_dominators', set()))))
