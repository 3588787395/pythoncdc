import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, TryExceptRegion, IfRegion, LoopRegion
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)
# Check effective_instructions
print("EFFECTIVE INSTRUCTIONS:")
for offset, eff in gen.region_analyzer.effective_instructions.items():
    print(f"  offset {offset}: {eff}")

# Also check what _generate_block_statements produces for block 42
block42 = cfg.get_block_by_offset(42)
print(f"\nBlock 42: {[(i.opname, i.argval) for i in block42.instructions]}")
result = gen._generate_block_statements(block42)
print(f"_generate_block_statements result: {result}")
