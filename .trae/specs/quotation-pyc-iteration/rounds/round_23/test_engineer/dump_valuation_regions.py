"""R24-N1 调试：dump valuation 函数的区域结构，分析 for-else + try-except 归属问题"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find valuation function
import types
def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_func(const, name)
            if result:
                return result
    return None

val_co = find_func(code_obj, 'valuation')

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(val_co)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

def walk(region, depth=0):
    prefix = '  ' * depth
    rtype = region.__class__.__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks_offs = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') and region.blocks else []
    print(f"{prefix}{rtype}@{entry_off} blocks={blocks_offs}")
    if hasattr(region, 'body_blocks') and region.body_blocks:
        body_offs = sorted(b.start_offset for b in region.body_blocks)
        print(f"{prefix}  body_blocks={body_offs}")
    if hasattr(region, 'else_blocks') and region.else_blocks:
        else_offs = sorted(b.start_offset for b in region.else_blocks)
        print(f"{prefix}  else_blocks={else_offs}")
    if hasattr(region, 'header_block') and region.header_block:
        print(f"{prefix}  header_block={region.header_block.start_offset}")
    if hasattr(region, 'back_edge_block') and region.back_edge_block:
        print(f"{prefix}  back_edge_block={region.back_edge_block.start_offset}")
    if hasattr(region, 'try_blocks') and region.try_blocks:
        try_offs = sorted(b.start_offset for b in region.try_blocks)
        print(f"{prefix}  try_blocks={try_offs}")
    if hasattr(region, 'handler_blocks') and region.handler_blocks:
        h_offs = sorted(b.start_offset for b in region.handler_blocks)
        print(f"{prefix}  handler_blocks={h_offs}")
    if hasattr(region, 'then_blocks') and region.then_blocks:
        t_offs = sorted(b.start_offset for b in region.then_blocks)
        print(f"{prefix}  then_blocks={t_offs}")
    if hasattr(region, 'else_block') and region.else_block:
        print(f"{prefix}  else_block={region.else_block.start_offset}")
    for child in getattr(region, 'children', []):
        walk(child, depth + 1)

print("=== Region tree for valuation ===")
for r in analyzer.regions:
    walk(r)
