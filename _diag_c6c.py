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

# Find the IfRegion
for r in gen.region_analyzer.regions:
    if isinstance(r, IfRegion):
        print(f"IfRegion: entry={r.entry.start_offset}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        for b in r.then_blocks:
            print(f"  then_block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
            role = gen.region_analyzer.get_block_role(b)
            print(f"    role: {role.name}")
        for b in (r.else_blocks or []):
            print(f"  else_block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}")
            role = gen.region_analyzer.get_block_role(b)
            print(f"    role: {role.name}")

# Monkey-patch _process_if_blocks to trace
orig = gen._process_if_blocks.__func__
import types as ty

def traced(self, blocks, region, branch='then'):
    print(f"\n_process_if_blocks(branch={branch}):")
    for b in blocks:
        print(f"  block @ {b.start_offset}")
    result = orig(self, blocks, region, branch)
    print(f"  result: {result}")
    return result

gen._process_if_blocks = ty.MethodType(traced, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
