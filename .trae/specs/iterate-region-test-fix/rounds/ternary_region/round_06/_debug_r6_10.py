"""Debug R6-10 listcomp with filter."""
import sys
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

src = "z = [a if c else b for x in ys if x > 0]"
code = compile(src, '<test>', 'exec')

# Decompile at outer level
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
decomp = CodeGenerator().generate(result)
print('=== decompiled (outer) ===')
print(decomp)

# Find the listcomp code object
for const in code.co_consts:
    if hasattr(const, 'co_code'):
        listcomp_code = const
        break

print('\n=== listcomp code object ===')
print('co_consts:', listcomp_code.co_consts)
print()

# Build CFG for listcomp
cfg2 = CFGBuilder().build(listcomp_code)
analyzer2 = RegionAnalyzer(cfg2)
analyzer2.analyze()
print('=== listcomp regions ===')
for r in analyzer2.regions:
    print(type(r).__name__, r.region_type, 'entry=', r.entry.start_offset if r.entry else None,
          'cond=', r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
          'merge=', getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None,
          'vt=', getattr(r, 'value_target', None),
          'ct=', getattr(r, 'container_type', None),
          'mc=', getattr(r, 'merge_context', None))

print('\n=== listcomp blocks ===')
for off, b in cfg2.blocks.items():
    print(f"Block {off}:")
    for i in b.instructions:
        print(f'  {i.offset:4d} {i.opname:30s} {i.arg} {i.argval}')
