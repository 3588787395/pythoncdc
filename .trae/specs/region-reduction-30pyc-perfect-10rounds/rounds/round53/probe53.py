# -*- coding: utf-8 -*-
"""Round 53 line A probe: what does the region graph look like for `if a<b<c or d:` ?

Dumps, for a witness, the region list (type/entry/blocks/then/else/merge), the block
successors, and which region owns each block -- so the R52-B predicate can be
extended on structure rather than guesswork.

usage: python -X utf8 probe53.py <core-dir> <pyc-path>
"""
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BASE = os.path.abspath(sys.argv[1])
PYC = os.path.abspath(sys.argv[2])
FN = sys.argv[3] if len(sys.argv) > 3 else 'w'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, BASE)
sys.path.insert(0, REPO)
for k in [k for k in list(sys.modules) if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
from core.cfg import build_cfg, CFGRegionAnalyzer  # noqa: E402
from core.cfg.region_analyzer import (IfRegion, LoopRegion,  # noqa: E402
                                      RegionType, BlockRole)
import dis  # noqa: E402
import marshal  # noqa: E402

import inspect  # noqa: E402

with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
for c in code.co_consts:
    if inspect.iscode(c) and c.co_name == FN:
        code = c
print('==== DIS of %s (%s) ====' % (FN, PYC))
dis.dis(code)
cfg = build_cfg(code)
an = CFGRegionAnalyzer(cfg)
an.analyze()
REGIONS = list(an.regions.values()) if isinstance(an.regions, dict) else list(an.regions)
BLOCKS = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
print('==== BLOCKS ====')
for b in sorted(BLOCKS, key=lambda x: x.start_offset):
    insns = ','.join('%d:%s' % (i.offset, i.opname) for i in b.instructions)
    print('blk %-5s %-70s succ=%s' % (b.start_offset, insns[:70],
                                      sorted(s.start_offset for s in (b.successors or set()))))
print('==== REGIONS ====')


def rid(r):
    return '%s@%s' % (type(r).__name__, r.entry.start_offset if r.entry else '?')


for r in REGIONS:
    t = getattr(r, 'region_type', None)
    line = '%-12s entry=%-5s type=%-22s blocks=%s' % (
        type(r).__name__, r.entry.start_offset if r.entry else '?',
        getattr(t, 'name', t), sorted(b.start_offset for b in r.blocks))
    if isinstance(r, IfRegion):
        line += ' then=%s else=%s merge=%s cond=%s cc_blocks=%s cc_ops=%s' % (
            sorted(b.start_offset for b in (r.then_blocks or [])),
            sorted(b.start_offset for b in (r.else_blocks or [])),
            r.merge_block.start_offset if r.merge_block else None,
            r.condition_block.start_offset if r.condition_block else None,
            sorted(b.start_offset for b in (getattr(r, 'chained_compare_blocks', None) or [])),
            getattr(r, 'chained_compare_ops', None))
    if isinstance(r, LoopRegion):
        line += ' header=%s' % (r.header_block.start_offset if r.header_block else None)
    print(line)
print('==== OWNERSHIP ====')
for b in sorted(BLOCKS, key=lambda x: x.start_offset):
    print('blk %-5s owner=%s role=%s' % (b.start_offset, rid(an.block_to_region.get(b)),
                                         getattr(an.get_block_role(b), 'name', None)))
