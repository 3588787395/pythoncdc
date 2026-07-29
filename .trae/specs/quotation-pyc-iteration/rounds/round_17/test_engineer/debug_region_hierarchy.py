"""R17 调试 get_opt_objects 的区域层次结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_code(co, name):
    for const in co.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

fn_code = find_code(code_obj, 'get_opt_objects')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(fn_code)

ra = RegionAnalyzer(cfg)
ra.analyze()

print("=== 区域层次结构 ===")
for r in ra.regions:
    entry_off = r.entry.start_offset if r.entry else None
    blocks_off = [b.start_offset for b in r.blocks]
    children = getattr(r, 'children', []) or []
    children_types = [(type(c).__name__, c.entry.start_offset if c.entry else None) for c in children]
    parent = getattr(r, 'parent', None)
    parent_type = type(parent).__name__ if parent else None
    print(f"  {type(r).__name__}: entry={entry_off}, blocks={blocks_off}")
    print(f"    parent={parent_type}, children={children_types}")

print("\n=== get_entry_region_for_block(164) ===")
blk_164 = cfg.get_block_by_offset(164)
result = ra.get_entry_region_for_block(blk_164)
print(f"  result: {type(result).__name__} (entry={result.entry.start_offset if result and result.entry else None})")

# 显示所有以 164 为 entry 的区域
print("\n=== 所有以 164 为 entry 的区域 ===")
for r in ra.regions:
    if r.entry and r.entry.start_offset == 164:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, blocks={[b.start_offset for b in r.blocks]}")
