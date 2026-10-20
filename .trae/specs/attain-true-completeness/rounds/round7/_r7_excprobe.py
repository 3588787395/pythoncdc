# -*- coding: utf-8 -*-
"""R6 probe: inspect exception edges / try-region fields for a function."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402
from core.cfg.region_analyzer import TryExceptRegion, LoopRegion  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == fname:
        target = c
        break

builder = CFGBuilder()
cfg = builder.build(target)
print('=== exception table ===')
for e in cfg.exception_table:
    print(e)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('=== exception successors ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if getattr(b, 'exception_successors', None):
        print('blk@%s -> exc %s (is_handler=%s)' % (
            b.start_offset,
            sorted(s.start_offset for s in b.exception_successors),
            [getattr(s, 'is_exception_handler', None) for s in b.exception_successors]))

print('=== try regions ===')
for r in analyzer.regions:
    if not isinstance(r, TryExceptRegion):
        continue
    print('TRY entry=%s try_blocks=%s handler_entry_blocks=%s except_handlers=%s cleanup=%s finalbody=%s' % (
        r.entry.start_offset if r.entry else None,
        [b.start_offset for b in (getattr(r, 'try_blocks', None) or [])],
        [b.start_offset for b in (getattr(r, 'handler_entry_blocks', None) or [])],
        [(et, en, [b.start_offset for b in hbs]) for (et, en, hbs) in (getattr(r, 'except_handlers', None) or [])],
        [b.start_offset for b in (getattr(r, 'cleanup_blocks', None) or [])],
        [b.start_offset for b in (getattr(r, 'finalbody_blocks', None) or [])]))
    print('   finally_copy_blocks=%s has_finally=%s' % (
        [b.start_offset for b in (getattr(r, 'finally_copy_blocks', None) or [])],
        getattr(r, 'has_finally', None)))

print('=== loops ===')
for r in analyzer.regions:
    if not isinstance(r, LoopRegion):
        continue
    print('LOOP entry=%s header=%s cond=%s body=%s blocks=%s exit=%s loop_exit_blocks=%s else=%s' % (
        r.entry.start_offset if r.entry else None,
        r.header_block.start_offset if r.header_block else None,
        r.condition_block.start_offset if r.condition_block else None,
        [b.start_offset for b in (r.body_blocks or [])],
        [b.start_offset for b in (r.blocks or [])],
        r.exit_block.start_offset if getattr(r, 'exit_block', None) else None,
        [b.start_offset for b in (getattr(r, 'loop_exit_blocks', None) or [])],
        [b.start_offset for b in (r.else_blocks or [])]))
