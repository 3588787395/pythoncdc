"""Region ownership tree (parent/children) for one code object.

usage: python -X utf8 work/regtree.py <abs pyc> <co-name-substring>
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
ana = RegionAnalyzer(cfg)
regions = ana.analyze()
off = lambda b: getattr(b, 'start_offset', b)
for i, r in enumerate(regions):
    p = getattr(r, 'parent', None)
    ch = getattr(r, 'children', None) or []
    print('%-14s idx=%-3d entry=%-6s cond=%-6s parent=%s children=%s blocks=%s' % (
        type(r).__name__, i, off(r.entry), off(getattr(r, 'condition_block', None)),
        ('%s@%s' % (type(p).__name__, off(p.entry))) if p is not None else 'None',
        ['%s@%s' % (type(c).__name__, off(c.entry)) for c in ch],
        sorted(off(b) for b in (r.blocks or []))[:14]))
print('--- block_to_region')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    r = ana.block_to_region.get(b)
    print('  @%-6s -> %s' % (b.start_offset,
                             ('%s@%s' % (type(r).__name__, off(r.entry))) if r is not None else '-'))
