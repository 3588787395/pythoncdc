import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, WithRegion, LoopRegion, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = "for i in range(3):\n    with ctx:\n        if i > 1:\n            break"
code = compile(src, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)

# Check _is_with_exit_leading_to_break for block 48
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    role = analyzer.get_block_role(block)
    if role == BlockRole.RETURN:
        print(f"Block {block.start_offset} (RETURN):")
        for succ in block.successors:
            print(f"  Successor: {succ.start_offset}")

# Find the loop region
loop_region = None
for r in analyzer.regions:
    if isinstance(r, LoopRegion):
        loop_region = r
        break

# Find the with region
with_region = None
for r in analyzer.regions:
    if isinstance(r, WithRegion):
        with_region = r
        break

# Check block 46's successors
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    if block.start_offset == 46:
        print(f"\nBlock 46 successors:")
        for succ in block.successors:
            role = analyzer.get_block_role(succ)
            print(f"  Block {succ.start_offset}: role={role.name}")
            if loop_region:
                result = analyzer._is_with_exit_leading_to_break(succ, loop_region)
                print(f"    _is_with_exit_leading_to_break: {result}")
                result2 = analyzer._is_with_exit_leading_to_continue(succ, loop_region)
                print(f"    _is_with_exit_leading_to_continue: {result2}")

# Now test the actual generation
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print(f"\nDecompiled:\n{output}")
