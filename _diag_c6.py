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

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("REGIONS:")
for r in regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")
    if isinstance(r, LoopRegion):
        print(f"    header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")

# Check block roles
for block in cfg.get_blocks_in_order():
    role = analyzer.get_block_role(block)
    if role != BlockRole.NORMAL:
        print(f"  Block @ {block.start_offset}: role={role.name}")
        for i in block.instructions:
            if i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                print(f"    JUMP_BACKWARD target={i.argval}")
