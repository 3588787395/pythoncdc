"""R23-N8 调试 get_fundflow_day 循环体 block 204 的语句生成"""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion, LoopRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_fundflow_day':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find block 204
block_204 = None
for b in cfg.get_blocks_in_order():
    if b.start_offset == 204:
        block_204 = b
        break

print(f"Block@204 instructions:")
for i in block_204.instructions:
    print(f"  {i.offset:>4} {i.opname:<25} {repr(i.argval)[:50]}")
print(f"  successors: {[s.start_offset for s in block_204.successors]}")
print(f"  predecessors: {[p.start_offset for p in block_204.predecessors]}")

# Find the LoopRegion
loop_region = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.entry and region.entry.start_offset == 198:
        loop_region = region
        break

print(f"\nLoopRegion: entry={loop_region.entry.start_offset}, body_blocks={[b.start_offset for b in loop_region.body_blocks]}")

# Generate AST
generator = RegionASTGenerator(cfg, analyzer)
generator.regions = analyzer.regions

# Generate the loop body block statements
print("\n=== Generating block 204 statements ===")
try:
    stmts = generator._generate_block_statements(block_204)
    import json
    print(json.dumps(stmts, indent=2, default=str))
except Exception as e:
    import traceback
    traceback.print_exc()
