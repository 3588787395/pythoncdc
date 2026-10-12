"""Concise region tree + CFG dump for one code object of a pyc.

usage: python -X utf8 work/regdump.py <abs pyc> <co-name-substring> [--blocks]
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC, NEEDLE = sys.argv[1], sys.argv[2]

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


co = [c for c in walk(code) if NEEDLE in (getattr(c, 'co_qualname', None) or c.co_name)][0]
cfg = build_cfg(co)
off = lambda b: getattr(b, 'start_offset', b)
offs = lambda seq: sorted(off(x) for x in (seq or []))
blks = list(cfg.blocks.values())
if '--blocks' in sys.argv:
    print('--- blocks (id offset n first last succ pred)')
    for b in blks:
        ins = list(getattr(b, 'instructions', None) or [])
        print('blk %-3s @%-6s n=%-3d %-26s %-26s succ=%s pred=%s' % (
            getattr(b, 'block_id', '?'), off(b), len(ins),
            ins[0].opname if ins else '', ins[-1].opname if ins else '',
            offs(getattr(b, 'successors', None) or []),
            offs(getattr(b, 'predecessors', None) or [])))
    print('--- block_to_region')

regions = RegionAnalyzer(cfg).analyze()
print('--- regions=%d' % len(regions))
for r in regions:
    d = r.__dict__
    print('%-14s entry=%-6s cond=%-6s rt=%-4s hdr=%-6s merge=%-6s back=%s ccb=%s crb=%s' % (
        type(r).__name__, off(d.get('entry')), off(d.get('condition_block')),
        d.get('region_type'), off(d.get('header_block')), off(d.get('merge_block')),
        offs(d.get('back_edge_blocks')), offs(d.get('condition_chain_blocks')),
        offs(d.get('condition_recheck_blocks')))
    )
    print('      body=%s' % offs(d.get('body_blocks')))
    print('      else=%s' % offs(d.get('else_blocks')))
    for k in ('inline_boolop_chains', 'elif_conditions', 'elif_bodies', 'elif_final_else',
              'break_blocks', 'is_while_true', 'exit_blocks', 'and_blocks', 'or_blocks',
              'condition_chain_expr', 'metadata'):
        if k in d:
            v = d[k]
            if isinstance(v, (list, set, tuple)) and v and hasattr(list(v)[0], 'start_offset'):
                v = offs(v)
            if k == 'metadata' and isinstance(v, dict):
                v = {mk: (offs(mv) if isinstance(mv, (list, set, tuple)) and mv and
                           hasattr(list(mv)[0], 'start_offset') else str(mv)[:60])
                     for mk, mv in v.items()}
            print('      %-22s %s' % (k, str(v)[:300]))
print('--- block_to_region (owner per block)')
for b in blks:
    r = None
    for reg in regions:
        if reg.__dict__.get('entry') == b:
            r = 'ENTRY'
    print('  @%-6s -> %s' % (off(b), (type(r).__name__ if r is None else r)))
