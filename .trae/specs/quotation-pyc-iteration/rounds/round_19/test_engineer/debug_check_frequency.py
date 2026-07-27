"""R19 测试工程师：调试 check_frequency 的回归问题"""
import sys
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'
target_name = 'check_frequency'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == target_name:
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)
ra = RegionAnalyzer(cfg)
ra.analyze()

try_region = None
for r in ra.regions:
    if isinstance(r, TryExceptRegion):
        try_region = r
        break

if try_region:
    print(f'=== TryExceptRegion ===')
    print(f'  blocks: {sorted([b.start_offset for b in try_region.blocks])}')
    print(f'  try_blocks: {[b.start_offset for b in try_region.try_blocks]}')
    print(f'  else_blocks: {[b.start_offset for b in (try_region.else_blocks or [])]}')
    print(f'  finally_blocks: {[b.start_offset for b in (try_region.finally_blocks or [])]}')
    print(f'  cleanup_blocks: {[b.start_offset for b in (try_region.cleanup_blocks or [])]}')
    print(f'  handler_entry_blocks: {[b.start_offset for b in try_region.handler_entry_blocks]}')
    print(f'  has_else: {try_region.has_else}')
    print(f'  has_finally: {try_region.has_finally}')
    print(f'  try_offset_end: {try_region.try_offset_end}')

    # Print else_block successors
    print(f'\n=== else_block successors ===')
    for eb in (try_region.else_blocks or []):
        print(f'Block {eb.start_offset}:')
        for ins in eb.instructions:
            print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
        print(f'  successors: {[s.start_offset for s in eb.successors]}')

    # Find post-try blocks
    print(f'\n=== Post-try blocks (not in region.blocks) ===')
    region_block_set = set(try_region.blocks)
    for b in try_region.blocks:
        for succ in b.successors:
            if succ not in region_block_set:
                print(f'Block {succ.start_offset} (from block {b.start_offset}):')
                for ins in succ.instructions:
                    print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
                print(f'  successors: {[s.start_offset for s in succ.successors]}')

# Print all regions
print(f'\n=== All Regions ===')
for r in ra.regions:
    blocks = sorted([b.start_offset for b in r.blocks])
    print(f'  {type(r).__name__}: blocks={blocks}, entry={r.entry.start_offset if r.entry else None}')
