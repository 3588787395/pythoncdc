"""R30 调试 get_cb_time_info 的 for 循环体 - 检查 IfRegion 与块1016的关系"""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, type(code_obj)) and const.co_name == 'get_cb_time_info':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the for-loop over stock_list2 (the one with block 1016)
target_loop = None
for r in regions:
    if isinstance(r, LoopRegion) and any(b.start_offset == 1016 for b in r.blocks):
        target_loop = r
        break

print(f"=== Target LoopRegion ===")
print(f"  blocks: {sorted(b.start_offset for b in target_loop.blocks)}")
print(f"  header: {target_loop.header_block.start_offset}")
print(f"  body_blocks: {sorted(b.start_offset for b in target_loop.body_blocks)}")
print(f"  children: {[type(c).__name__ for c in target_loop.children] if target_loop.children else None}")

# Find IfRegions inside this loop
print(f"\n=== IfRegions inside the loop ===")
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset in [b.start_offset for b in target_loop.blocks]:
        print(f"\n  IfRegion: entry={r.entry.start_offset}")
        print(f"    blocks: {sorted(b.start_offset for b in r.blocks)}")
        print(f"    condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"    then_blocks: {[b.start_offset for b in r.then_blocks] if r.then_blocks else None}")
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else None}")
        print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")

# Check block roles
print(f"\n=== Block roles for loop blocks ===")
for b in sorted(target_loop.blocks, key=lambda b: b.start_offset):
    role = analyzer.get_block_role(b)
    entry_region = analyzer.get_entry_region_for_block(b)
    print(f"  block {b.start_offset}: role={role}, entry_region={type(entry_region).__name__ if entry_region else None}")

# Check what region block 1016 belongs to
print(f"\n=== Block 1016 details ===")
b1016 = cfg.get_block_by_offset(1016)
print(f"  get_region_for_block: {type(analyzer.get_region_for_block(b1016)).__name__}")
print(f"  get_entry_region_for_block: {type(analyzer.get_entry_region_for_block(b1016)).__name__ if analyzer.get_entry_region_for_block(b1016) else None}")
