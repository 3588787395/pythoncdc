"""Diagnose Pattern T3 in create_full_graph of graph.pyc.

Dump regions, block_to_region, try_blocks, handler_entry_blocks, and trace
which blocks get marked as post-try / generated when _generate_try runs for
the OUTER and INNER TryExceptRegion.
"""
import os, sys, marshal, dis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion, IfRegion, BlockRole

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/graph.pyc'
with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find create_full_graph
target = None
for c in code.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'ModelGraph':
        for cc in c.co_consts:
            if hasattr(cc, 'co_code') and cc.co_name == 'create_full_graph':
                target = cc
                break
    if target: break

print(f'Target: {target.co_name} firstlineno={target.co_firstlineno}')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f'\nTotal regions: {len(analyzer.regions)}')
for r in analyzer.regions:
    parent = r.parent
    parent_name = parent.entry.co_name if hasattr(parent, 'entry') and parent is not None and hasattr(parent.entry, 'co_name') else type(parent).__name__ if parent else 'None'
    print(f'  [{type(r).__name__}] entry_off={r.entry.start_offset if r.entry else None}')
    if isinstance(r, TryExceptRegion):
        print(f'      try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'      handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
        print(f'      else_blocks={[b.start_offset for b in r.else_blocks]}')
        print(f'      except_handlers={[(t, n, [b.start_offset for b in hbs]) for t,n,hbs in r.except_handlers]}')
        print(f'      try_offset_start={r.try_offset_start} try_offset_end={r.try_offset_end}')
        # Check if any handler_entry is in try_blocks
        for heb in r.handler_entry_blocks:
            owner = analyzer.block_to_region.get(id(heb)) if hasattr(analyzer, 'block_to_region') else None
            print(f'      handler_entry {heb.start_offset} owner via id: {owner}')
        # Check block_to_region for handler_entry
        for heb in r.handler_entry_blocks:
            owner = analyzer.block_to_region.get(heb)
            print(f'      handler_entry {heb.start_offset} block_to_region: {owner} (is_self={owner is r})')
    if isinstance(r, LoopRegion):
        blks_sorted = sorted(r.blocks, key=lambda b: b.start_offset) if hasattr(r.blocks, '__iter__') and not isinstance(r.blocks, list) else r.blocks
        print(f'      blocks (first 5)={[b.start_offset for b in blks_sorted[:5]]}...')
        print(f'      total blocks={len(r.blocks)}')

# Now check for the OUTER region (the one whose handler_entry is at offset 640)
print('\n=== Looking for OUTER region (handler_entry @640) ===')
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        for heb in r.handler_entry_blocks:
            if heb.start_offset == 640:
                print(f'OUTER region: entry={r.entry.start_offset}, try_blocks={[b.start_offset for b in r.try_blocks]}')
                print(f'  try_blocks count={len(r.try_blocks)}')
                print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
                print(f'  blocks count={len(r.blocks)}')
                print(f'  try_offset_start={r.try_offset_start} try_offset_end={r.try_offset_end}')
                # Check successors of each try_block
                print(f'  --- try_blocks successors (looking for who points to 640) ---')
                for tb in r.try_blocks:
                    role = analyzer.get_block_role(tb)
                    succs = [s.start_offset for s in tb.successors]
                    has_640 = 640 in succs
                    in_region = tb in set(r.blocks)
                    in_handler = tb in set(r.handler_entry_blocks)
                    print(f'    tb@{tb.start_offset} role={role} succs={succs} points_to_640={has_640} in_region={in_region} in_handler_entries={in_handler}')
                # Check if 640 is in handler_entry_blocks
                print(f'  Is 640 in handler_entry_blocks set? {640 in [b.start_offset for b in r.handler_entry_blocks]}')

# INNER region (handler_entry @408)
print('\n=== Looking for INNER region (handler_entry @408) ===')
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        for heb in r.handler_entry_blocks:
            if heb.start_offset == 408:
                print(f'INNER region: entry={r.entry.start_offset}, try_blocks={[b.start_offset for b in r.try_blocks]}')
                print(f'  try_blocks count={len(r.try_blocks)}')
                print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
                print(f'  blocks count={len(r.blocks)}')
                # Check successors of each try_block
                print(f'  --- try_blocks successors ---')
                for tb in r.try_blocks:
                    role = analyzer.get_block_role(tb)
                    succs = [s.start_offset for s in tb.successors]
                    in_region = tb in set(r.blocks)
                    print(f'    tb@{tb.start_offset} role={role} succs={succs} in_region={in_region}')

# Check block_to_region for block 640
print('\n=== block_to_region for key blocks ===')
for off in [12, 42, 316, 406, 408, 524, 532, 636, 640, 642, 762]:
    blk = None
    for b in cfg.blocks:
        if b.start_offset == off:
            blk = b
            break
    if blk is None:
        print(f'  block@{off}: NOT FOUND')
        continue
    owner = analyzer.block_to_region.get(blk)
    owner_type = type(owner).__name__ if owner else 'None'
    owner_entry = owner.entry.start_offset if owner and owner.entry else None
    print(f'  block@{off}: owner={owner_type} entry={owner_entry}')
