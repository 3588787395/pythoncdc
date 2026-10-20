# -*- coding: utf-8 -*-
"""R5 B70 probe: which misfire fires in _check_jump_backward_for_break."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import (  # noqa: E402
    RegionAnalyzer, LoopRegion, WithRegion, RegionType)

with open(r'test_repros\round9\rv9_02_b66_with_nest.pyc', 'rb') as f:
    code = marshal.loads(f.read()[16:])
target = next(c for c in code.co_consts
              if hasattr(c, 'co_name') and c.co_name == 'while_with_whole_body')

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

b4 = cfg.get_block_by_offset(4)
b84 = cfg.get_block_by_offset(84)
b36 = cfg.get_block_by_offset(36)

print('regions with entry@4:')
for r in analyzer.regions:
    if getattr(r, 'entry', None) is b4:
        print('  %s region_type=%s condition_block=%s header_block=%s' % (
            type(r).__name__, getattr(r, 'region_type', None),
            getattr(r, 'condition_block', None) and r.condition_block.start_offset,
            getattr(r, 'header_block', None) and r.header_block.start_offset))

r4 = analyzer.get_entry_region_for_block(b4)
print('get_entry_region_for_block(4) =', type(r4).__name__)

# trace _check_jump_backward_for_break on b84 with current code
res = analyzer._check_jump_backward_for_break(b84, None)
print('_check_jump_backward_for_break(84, no-loop) =', res)

loop = next(r for r in analyzer.regions if isinstance(r, LoopRegion))
res2 = analyzer._check_jump_backward_for_break(b84, loop)
print('_check_jump_backward_for_break(84, LoopRegion@4) =', res2)
print('loop.condition_block =', loop.condition_block)
print('loop.region_type =', loop.region_type)
print('loop.entry offset =', loop.entry.start_offset)
print('_is_with_exit_leading_to_break(36, loop) =',
      analyzer._is_with_exit_leading_to_break(b36, loop))
print('_is_with_exit_leading_to_continue(36, loop) =',
      analyzer._is_with_exit_leading_to_continue(b36, loop))
