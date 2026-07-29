"""R19 测试工程师：深入分析 api_get 的 post-try 代码丢失问题"""
import sys
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'
target_name = 'api_get'

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

# 找到 TryExceptRegion
try_region = None
for r in ra.regions:
    if isinstance(r, TryExceptRegion):
        try_region = r
        break

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

# 打印 else_block 的指令和后继
print(f'\n=== else_block 270 instructions ===')
for b in try_region.else_blocks:
    print(f'Block {b.start_offset}:')
    for ins in b.instructions:
        print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
    print(f'  successors: {[s.start_offset for s in b.successors]}')

# 打印 cleanup_blocks 的指令和后继
print(f'\n=== cleanup_blocks instructions ===')
for b in try_region.cleanup_blocks:
    print(f'Block {b.start_offset}:')
    for ins in b.instructions:
        print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
    print(f'  successors: {[s.start_offset for s in b.successors]}')

# 找到 post-try block (不在 region.blocks 中的后继)
print(f'\n=== Post-try blocks (not in region.blocks) ===')
region_block_set = set(try_region.blocks)
visited = set()
for b in try_region.blocks:
    for succ in b.successors:
        if succ not in region_block_set and succ not in visited:
            visited.add(succ)
            print(f'Block {succ.start_offset} (from block {b.start_offset}):')
            for ins in succ.instructions:
                print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
            print(f'  successors: {[s.start_offset for s in succ.successors]}')

# 检查 IfRegion 包含哪些块
print(f'\n=== IfRegion containing block 604 ===')
for r in ra.regions:
    if isinstance(r, IfRegion) and any(b.start_offset == 604 for b in r.blocks):
        print(f'IfRegion: blocks={sorted([b.start_offset for b in r.blocks])}, entry={r.entry.start_offset}')
        print(f'  condition_block: {r.condition_block.start_offset if r.condition_block else None}')
        print(f'  then_blocks: {[b.start_offset for b in r.then_blocks]}')
        print(f'  else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}')
        print(f'  merge_block: {r.merge_block.start_offset if r.merge_block else None}')

# 检查 block 604 的归属
print(f'\n=== Block 604 region ownership ===')
b604 = cfg.get_block_by_offset(604)
for r in ra.regions:
    if b604 in r.blocks:
        print(f'  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}')
