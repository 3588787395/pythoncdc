import sys, types, marshal
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')
builder = CFGBuilder()
cfg = builder.build(tick)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the OUTER loop (header=48), which contains the inner loop (header=50)
outer_loop = None
inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block:
        if region.header_block.start_offset == 48:
            outer_loop = region
        elif region.header_block.start_offset == 50:
            inner_loop = region

print("Outer loop header:", outer_loop.header_block.start_offset if outer_loop else None)
print("Inner loop header:", inner_loop.header_block.start_offset if inner_loop else None)
print("Outer loop body_blocks:", [b.start_offset for b in outer_loop.body_blocks] if outer_loop else [])
print("Inner loop body_blocks:", [b.start_offset for b in inner_loop.body_blocks] if inner_loop else [])
print()

# Block 50 is the inner loop's header, but is it also in the outer loop's body_blocks?
block_50 = cfg.get_block_by_offset(50)
print("block_50 in outer_loop.body_blocks:", block_50 in outer_loop.body_blocks if outer_loop else False)
print("block_50 in inner_loop.body_blocks:", block_50 in inner_loop.body_blocks if inner_loop else False)

# Check if the inner loop is a child of the outer loop
print()
print("Outer loop children:", [type(c).__name__ + '@' + str(c.entry.start_offset if c.entry else '?') for c in (outer_loop.children or [])] if outer_loop else [])

# Is block 50 the inner loop's header or is it processed by the outer loop?
print()
print("Inner loop entry:", inner_loop.entry.start_offset if inner_loop and inner_loop.entry else None)
print("Inner loop header_block:", inner_loop.header_block.start_offset if inner_loop and inner_loop.header_block else None)
