"""R30 测试工程师：调试get_cb_calender_info - 深入分析entry=1138"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, LoopRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find get_cb_calender_info
def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r:
                return r
    return None

target = find_code(code_obj, 'get_cb_calender_info')

# Build CFG and regions
builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the block 1138 and its predecessor
for offset_to_check in [1120, 1138, 1004, 496]:
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        if b.start_offset == offset_to_check:
            print(f"=== Block {offset_to_check} ===")
            for i in b.instructions:
                print(f"  {i.opname} {i.argval}")
            print(f"  predecessors: {[p.start_offset for p in b.predecessors]}")
            print(f"  successors: {[s.start_offset for s in b.successors]}")
            print()
            break

# What region contains block 1120?
print("=== Regions containing block 1120 ===")
for r in analyzer.regions:
    if any(b.start_offset == 1120 for b in r.blocks):
        print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}, id={id(r)}")
        if hasattr(r, 'blocks'):
            print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")

# Find the LoopRegion with entry=492 and show its body_blocks
print("\n=== LoopRegion entry=492 ===")
for r in analyzer.regions:
    if type(r).__name__ == 'LoopRegion' and r.entry and r.entry.start_offset == 492:
        print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
        if hasattr(r, 'body_blocks'):
            print(f"  body_blocks: {sorted(b.start_offset for b in r.body_blocks)}")
        if hasattr(r, 'header_block'):
            print(f"  header_block: {r.header_block.start_offset if r.header_block else None}")
        if hasattr(r, 'condition_block'):
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        # Check children
        if hasattr(r, 'children'):
            for c in r.children:
                print(f"  child: {type(c).__name__} entry={c.entry.start_offset if c.entry else None}")



# Find TryExceptRegion with entry 1138
print()
for r in analyzer.regions:
    if r.entry and r.entry.start_offset == 1138:
        print(f"\n=== Region with entry=1138: {type(r).__name__} (id={id(r)}) ===")
        print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
        if isinstance(r, TryExceptRegion):
            print(f"  try_blocks: {sorted(b.start_offset for b in r.try_blocks)}")
            print(f"  else_blocks: {sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"  finally_blocks: {sorted(b.start_offset for b in r.finally_blocks) if r.finally_blocks else []}")
            print(f"  handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")
            print(f"  try_offset_start: {r.try_offset_start}")
            print(f"  try_offset_end: {r.try_offset_end}")
            print(f"  entry in try_blocks: {r.entry in r.try_blocks}")
            print(f"  entry.start_offset < try_offset_start: {r.entry.start_offset < r.try_offset_start}")
        elif isinstance(r, IfRegion):
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks: {sorted(b.start_offset for b in r.then_blocks) if r.then_blocks else []}")
            print(f"  else_blocks: {sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  parent: {type(r.parent).__name__ if r.parent else None}")
        if r.parent:
            print(f"  parent.entry: {r.parent.entry.start_offset if r.parent.entry else None}")

# Find regions with entry 1200
print()
for r in analyzer.regions:
    if r.entry and r.entry.start_offset == 1200:
        print(f"\n=== Region with entry=1200: {type(r).__name__} (id={id(r)}) ===")
        print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
        if isinstance(r, IfRegion):
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks: {sorted(b.start_offset for b in r.then_blocks) if r.then_blocks else []}")
            print(f"  else_blocks: {sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  parent: {type(r.parent).__name__ if r.parent else None}")
