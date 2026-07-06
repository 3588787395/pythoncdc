import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, LoopRegion
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# List all regions
for r in gen.region_analyzer.regions:
    print(f"Region: {type(r).__name__}")
    if isinstance(r, LoopRegion):
        print(f"  header={r.header_block.start_offset if r.header_block else None}")
        print(f"  back_edge={r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"  body_blocks={[b.start_offset for b in (r.body_blocks or [])]}")

# Check block 28's successors
block28 = cfg.get_block_by_offset(28)
print(f"\nBlock 28: {[(i.opname, i.argval) for i in block28.instructions]}")
print(f"  succs: {[b.start_offset for b in block28.successors]}")

for succ in block28.successors:
    role = gen.region_analyzer.get_block_role(succ)
    print(f"  succ {succ.start_offset}: role={role.name}")
    print(f"    instructions: {[(i.opname, i.argval) for i in succ.instructions]}")
