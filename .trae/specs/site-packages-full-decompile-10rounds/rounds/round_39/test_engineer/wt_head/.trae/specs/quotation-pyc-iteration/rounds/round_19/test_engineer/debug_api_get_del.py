"""R19 测试工程师：分析 api_get 的 del x 问题"""
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

# 列出所有区域
print(f'=== All regions in api_get ===')
for r in ra.regions:
    print(f'  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}, '
          f'blocks={sorted([b.start_offset for b in r.blocks])}')

# 检查 block 578, 566, 588 的归属
for offset in [412, 578, 566, 588, 596]:
    blk = cfg.get_block_by_offset(offset)
    if not blk:
        print(f'Block {offset}: NOT FOUND')
        continue
    print(f'\n=== Block {offset} ===')
    for ins in blk.instructions:
        print(f'  {ins.offset:4d} {ins.opname:30s} {ins.argval}')
    print(f'  successors: {[s.start_offset for s in blk.successors]}')
    # 找出包含此 block 的 region
    for r in ra.regions:
        if blk in r.blocks:
            print(f'  in region: {type(r).__name__} entry={r.entry.start_offset if r.entry else None}')

# 找出 IfRegion
print(f'\n=== IfRegions ===')
for r in ra.regions:
    if isinstance(r, IfRegion):
        print(f'IfRegion: blocks={sorted([b.start_offset for b in r.blocks])}')
        print(f'  entry={r.entry.start_offset if r.entry else None}')
        print(f'  condition_block={r.condition_block.start_offset if r.condition_block else None}')
        print(f'  then_blocks={[b.start_offset for b in r.then_blocks]}')
        print(f'  else_blocks={[b.start_offset for b in (r.else_blocks or [])]}')
        print(f'  merge_block={r.merge_block.start_offset if r.merge_block else None}')

# 找出 TryExceptRegion
print(f'\n=== TryExceptRegions ===')
for r in ra.regions:
    if isinstance(r, TryExceptRegion):
        print(f'TryExceptRegion: blocks={sorted([b.start_offset for b in r.blocks])}')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
        print(f'  cleanup_blocks={[b.start_offset for b in (r.cleanup_blocks or [])]}')
