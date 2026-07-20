"""Debug R6-20."""
import sys
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

src = "x[a if c else b][d if e else f] = 1"
code = compile(src, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
print("=== regions ===")
for r in analyzer.regions:
    print(type(r).__name__, r.region_type, 'entry=', r.entry.start_offset if r.entry else None,
          'cond=', r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
          'merge=', getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None,
          'vt=', getattr(r, 'value_target', None),
          'ct=', getattr(r, 'container_type', None),
          'mc=', getattr(r, 'merge_context', None),
          'fci=', bool(getattr(r, 'func_call_info', None)))

# Now decompile
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
decomp = CodeGenerator().generate(result)
print('=== decompiled ===')
print(decomp)

# Inspect blocks
print('=== blocks ===')
for off, b in cfg.blocks.items():
    print(f"Block {off}:")
    for i in b.instructions:
        print(f'  {i.offset:4d} {i.opname:30s} {i.arg} {i.argval}')
