"""Dump region structure for get_option_info to find extra JUMP_BACKWARD."""
import sys, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None

fn = find(code_obj, 'get_option_info')

# Build CFG
cfg = CFGBuilder().build(fn)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the inner for loop around offset 600
def walk(region, depth=0):
    prefix = '  ' * depth
    rtype = region.__class__.__name__
    entry_off = region.entry.start_offset if region.entry else None
    print(f"{prefix}{rtype}@{entry_off}")
    
    if hasattr(region, 'blocks'):
        block_offs = sorted(b.start_offset for b in region.blocks)
        print(f"{prefix}  blocks={block_offs}")
    if hasattr(region, 'body_blocks') and region.body_blocks:
        body_offs = sorted(b.start_offset for b in region.body_blocks)
        print(f"{prefix}  body_blocks={body_offs}")
    if hasattr(region, 'back_edge_block') and region.back_edge_block:
        print(f"{prefix}  back_edge_block={region.back_edge_block.start_offset}")
    if hasattr(region, 'header_block') and region.header_block:
        print(f"{prefix}  header_block={region.header_block.start_offset}")
    if hasattr(region, 'else_blocks') and region.else_blocks:
        else_offs = sorted(b.start_offset for b in region.else_blocks)
        print(f"{prefix}  else_blocks={else_offs}")
    
    for child in getattr(region, 'children', []):
        walk(child, depth + 1)

# Find the LoopRegion containing offset 600
for r in analyzer.regions:
    if hasattr(r, 'header_block') and r.header_block and r.header_block.start_offset == 600:
        print("=== Inner for loop at 600 ===")
        walk(r)
        break

# Also dump blocks around 730-740
print("\n=== All blocks in inner for loop (558-735) ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if 555 <= b.start_offset <= 735:
        print(f"Block@{b.start_offset}:")
        for ins in b.instructions:
            argrepr = getattr(ins, 'argrepr', str(ins.argval) if ins.argval is not None else '')
            print(f"  {ins.offset:4d} {ins.opname:30s} {argrepr}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
        print(f"  predecessors: {[s.start_offset for s in b.predecessors]}")
        print()
