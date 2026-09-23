# -*- coding: utf-8 -*-
"""Round 53 boolop dump: what op_chain / segment structure does the analyzer produce for
`A or B and C` (defect) vs `(A or B) and C` (renders fine)?

usage: python -X utf8 boolop53.py <pyc-path> [fn-name]
"""
import inspect
import io
import marshal
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
from core.cfg import build_cfg, CFGRegionAnalyzer  # noqa: E402
from core.cfg.region_analyzer import BoolOpRegion, IfRegion  # noqa: E402

PYC = os.path.abspath(sys.argv[1])
FN = sys.argv[2] if len(sys.argv) > 2 else 'w'
with io.open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
for c in code.co_consts:
    if inspect.iscode(c) and c.co_name == FN:
        code = c
cfg = build_cfg(code)
an = CFGRegionAnalyzer(cfg)
an.analyze()
RG = list(an.regions.values()) if isinstance(an.regions, dict) else list(an.regions)
BL = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
print('== blocks of %s ==' % FN)
for b in sorted(BL, key=lambda x: x.start_offset):
    last = b.get_last_instruction()
    print('  %-5s %-58s succ=%s last=%s->%s' % (
        b.start_offset,
        ','.join('%d:%s' % (i.offset, i.opname) for i in b.instructions)[:58],
        sorted(s.start_offset for s in (b.successors or set())),
        last.opname if last else None,
        getattr(last, 'argval', None) if last else None))
print('== BoolOpRegions ==')


def bo(b):
    r = an.block_to_region.get(b)
    return '%s@%s' % (type(r).__name__, r.entry.start_offset if r and r.entry else '?')


for r in RG:
    if not isinstance(r, BoolOpRegion):
        continue
    ch = getattr(r, 'op_chain', None) or []
    print(' entry=%s blocks=%s merge=%s' % (
        r.entry.start_offset if r.entry else None,
        sorted(x.start_offset for x in r.blocks),
        r.merge_block.start_offset if r.merge_block else None))
    for i, e in enumerate(ch):
        b = e[0] if isinstance(e, (tuple, list)) else e
        op = e[1] if isinstance(e, (tuple, list)) and len(e) > 1 else '?'
        last = b.get_last_instruction()
        print('   [%d] blk=%-5s op=%-4s last=%-26s tgt=%-5s owner=%s succ=%s' % (
            i, b.start_offset, op, last.opname if last else '-',
            getattr(last, 'argval', None) if last else None, bo(b),
            sorted(s.start_offset for s in (b.successors or set()))))
    for k, v in sorted(vars(r).items()):
        if 'seg' in k or 'nest' in k or 'group' in k or 'value' in k:
            print('   attr %s = %r' % (k, v)[:200])
print('== IfRegions with condition inside a BoolOpRegion ==')
for r in RG:
    if isinstance(r, IfRegion) and r.condition_block is not None:
        cb = r.condition_block
        own = an.block_to_region.get(cb)
        if isinstance(own, BoolOpRegion):
            print('  If@%s type=%s cond=%s merge=%s then=%s else=%s boolop@%s chain=%s' % (
                r.entry.start_offset if r.entry else '?', getattr(r.region_type, 'name', '?'),
                cb.start_offset, r.merge_block.start_offset if r.merge_block else None,
                sorted(b.start_offset for b in (r.then_blocks or [])),
                sorted(b.start_offset for b in (r.else_blocks or [])),
                own.entry.start_offset,
                [(e[0].start_offset, e[1]) for e in (getattr(own, 'op_chain', None) or [])
                 if isinstance(e, (tuple, list))]))
