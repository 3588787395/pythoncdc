"""R17 追踪 get_opt_objects 的 TryExceptRegion 生成"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

# Patch _generate_region to trace
orig_generate_region = RegionASTGenerator._generate_region
def traced_generate_region(self, region):
    if hasattr(region, 'entry') and region.entry and region.entry.start_offset in (164, 0, 232, 270):
        print(f"\n!!! _generate_region called for {type(region).__name__} (entry={region.entry.start_offset}) !!!")
        print(f"  blocks={[b.start_offset for b in region.blocks]}")
        print(f"  children={[type(c).__name__ for c in (getattr(region, 'children', []) or [])]}")
    result = orig_generate_region(self, region)
    if hasattr(region, 'entry') and region.entry and region.entry.start_offset in (164, 0, 232, 270):
        print(f"!!! _generate_region for {type(region).__name__} (entry={region.entry.start_offset}) returned: {result} !!!")
    return result
RegionASTGenerator._generate_region = traced_generate_region

# Patch _process_if_blocks to trace
orig_pib = RegionASTGenerator._process_if_blocks
def traced_pib(self, blocks, region, branch='then'):
    block_offsets = [b.start_offset for b in blocks]
    if 164 in block_offsets or 270 in block_offsets:
        print(f"\n!!! _process_if_blocks called: branch={branch}, blocks={block_offsets} !!!")
        print(f"  region: {type(region).__name__} (entry={region.entry.start_offset if region.entry else None})")
        children = getattr(region, 'children', []) or []
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in children]}")
    result = orig_pib(self, blocks, region, branch)
    if 164 in block_offsets or 270 in block_offsets:
        print(f"!!! _process_if_blocks returned: {result} !!!")
    return result
RegionASTGenerator._process_if_blocks = traced_pib

# Patch _generate_try_except
orig_gte = None
if hasattr(RegionASTGenerator, '_generate_try_except'):
    orig_gte = RegionASTGenerator._generate_try_except
    def traced_gte(self, region):
        print(f"\n!!! _generate_try_except called (entry={region.entry.start_offset if region.entry else None}) !!!")
        print(f"  blocks={[b.start_offset for b in region.blocks]}")
        result = orig_gte(self, region)
        print(f"!!! _generate_try_except returned: {result} !!!")
        return result
    RegionASTGenerator._generate_try_except = traced_gte

from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'
print("=== 反编译 get_opt_objects ===")
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)

# 找到 get_opt_objects 函数
import re
m = re.search(r'def get_opt_objects\(.*?\n(?=def |\Z)', src, re.DOTALL)
if m:
    print("\n=== get_opt_objects 反编译结果 ===")
    print(m.group(0))
