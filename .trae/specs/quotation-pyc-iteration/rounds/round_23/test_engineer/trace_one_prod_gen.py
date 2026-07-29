"""R23-N9 跟踪 one_prod_to_dataframe 的生成过程"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'one_prod_to_dataframe':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the LoopRegion with entry=348
target_region = None
for r in analyzer.regions:
    if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 348:
        target_region = r
        break

print(f"Target LoopRegion: entry={target_region.entry.start_offset}")
print(f"  blocks: {[b.start_offset for b in target_region.blocks]}")
print(f"  header_block: {target_region.header_block.start_offset}")
print(f"  body_blocks: {[b.start_offset for b in target_region.body_blocks]}")
print(f"  metadata: {target_region.metadata}")

# Now create generator and trace
generator = RegionASTGenerator(cfg, analyzer, target)

# Check what blocks are processed in order
print(f"\n=== Block order in cfg ===")
for b in cfg.get_blocks_in_order():
    print(f"  Block@{b.start_offset}")

# Manually call _loop_generate_for and check the result
print(f"\n=== Calling _loop_generate_for ===")
result = generator._loop_generate_for(target_region)
import json
print(json.dumps(result, indent=2, default=str))
