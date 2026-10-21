# -*- coding: utf-8 -*-
"""R8 probe: dump ALL regions after analyze()."""
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2] if len(sys.argv) > 2 else None

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = code
if fname:
    found = None
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == fname:
            found = c
            break
    if found is None:
        print('NOT FOUND')
        sys.exit(1)
    target = found

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('=== all regions ===')
for r in analyzer.regions:
    blocks = sorted(b.start_offset for b in (getattr(r, 'blocks', None) or []))
    extra = ''
    for attr in ('entry', 'merge_block', 'condition_block', 'exit_block', 'header_block'):
        v = getattr(r, attr, None)
        if v is not None and hasattr(v, 'start_offset'):
            extra += ' %s=%s' % (attr, v.start_offset)
    for attr in ('then_blocks', 'else_blocks', 'body_blocks', 'break_blocks', 'continue_blocks'):
        v = getattr(r, attr, None)
        if v:
            extra += ' %s=%s' % (attr, sorted(b.start_offset for b in v if hasattr(b, 'start_offset')))
    for attr in ('merge_context', 'value_target', 'container_type', 'true_value_block', 'false_value_block'):
        v = getattr(r, attr, None)
        if v is not None:
            extra += ' %s=%s' % (attr, getattr(v, 'start_offset', v))
    print('%-22s blocks=%s%s' % (type(r).__name__, blocks, extra))
print('=== block_to_region ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    r = analyzer.block_to_region.get(b)
    print('blk@%s -> %s' % (b.start_offset, type(r).__name__ if r else None))
