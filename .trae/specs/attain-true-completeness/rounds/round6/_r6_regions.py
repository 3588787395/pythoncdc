# -*- coding: utf-8 -*-
"""R6 evidence: CFG + regions for a function in a staged pyc."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]
outname = sys.argv[3]

out = open(os.path.join(HERE, outname), 'w', encoding='utf-8')


def w(s):
    out.write(s + '\n')


with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == fname:
        target = c
        break
w('co_name=%s varnames=%s' % (target.co_name, target.co_varnames))

builder = CFGBuilder()
cfg = builder.build(target)
w('=== CFG blocks ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    w('BLK@%s..%s succ=%s pred=%s' % (
        b.start_offset,
        b.instructions[-1].offset if b.instructions else None,
        [s.start_offset for s in b.successors],
        [p.start_offset for p in b.predecessors]))
    for i in b.instructions:
        w('   %s %s %s' % (i.offset, i.opname, i.argval))

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
w('=== regions ===')
for r in analyzer.regions:
    w('REGION %s entry=%s blocks=%s parent=%s' % (
        type(r).__name__,
        getattr(r, 'entry', None) and r.entry.start_offset,
        [b.start_offset for b in getattr(r, 'blocks', [])],
        type(r.parent).__name__ if getattr(r, 'parent', None) else None))
    for attr in ('header_block', 'body_blocks', 'break_blocks', 'continue_blocks',
                 'exit_block', 'merge_block', 'with_blocks', 'condition_block',
                 'else_blocks', 'then_blocks', 'loop_exit_blocks',
                 'finally_blocks', 'handler_blocks'):
        v = getattr(r, attr, None)
        if v is None:
            continue
        if isinstance(v, (list, set)):
            w('   %s=%s' % (attr, [getattr(x, 'start_offset', x) for x in v]))
        else:
            w('   %s=%s' % (attr, getattr(v, 'start_offset', v)))
w('=== block_to_region ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    r = analyzer.block_to_region.get(b)
    w('blk@%s -> %s' % (b.start_offset, type(r).__name__ if r else None))
w('=== block roles ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    try:
        w('blk@%s role=%s' % (b.start_offset, analyzer.get_block_role(b)))
    except Exception as e:
        w('blk@%s role ERR %s' % (b.start_offset, e))
out.close()
print('done ' + outname)
