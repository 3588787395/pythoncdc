# -*- coding: utf-8 -*-
"""R5 B70 probe: compare WithRegion fields, green for-unit vs red while-unit."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion  # noqa: E402

with open(r'test_repros\round9\rv9_02_b66_with_nest.pyc', 'rb') as f:
    code = marshal.loads(f.read()[16:])


def dump_unit(name):
    target = next(c for c in code.co_consts
                  if hasattr(c, 'co_name') and c.co_name == name)
    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    print('=== unit %s ===' % name)
    for r in analyzer.regions:
        if isinstance(r, WithRegion):
            print('WithRegion entry@%s' % r.entry.start_offset)
            print('  blocks=%s' % [b.start_offset for b in r.blocks])
            print('  with_blocks=%s' % [b.start_offset for b in r.with_blocks])
            print('  cleanup_blocks=%s' % [b.start_offset for b in getattr(r, 'cleanup_blocks', [])])
            print('  exception_blocks=%s' % [b.start_offset for b in getattr(r, 'exception_blocks', [])])
            print('  exit_block=%s' % (r.exit_block and r.exit_block.start_offset))
            print('  body_offset_start=%s body_offset_end=%s' % (
                getattr(r, 'body_offset_start', None), getattr(r, 'body_offset_end', None)))
            print('  target=%r is_async=%s' % (r.target, r.is_async))
        print('  REGION %s entry@%s blocks=%s' % (
            type(r).__name__, r.entry.start_offset, [b.start_offset for b in r.blocks]))
    # block roles for exit-call-ish blocks
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        last = b.instructions[-1] if b.instructions else None
        print('  blk@%s role=%s last=%s' % (
            b.start_offset, analyzer.get_block_role(b),
            last and last.opname))
    print()


dump_unit('with_whole_body_pass')
dump_unit('while_with_whole_body')
