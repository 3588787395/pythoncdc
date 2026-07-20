"""Debug R6-17 annotation."""
import sys
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

src = "x: T = a if c else b"
code = compile(src, '<test>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
decomp = CodeGenerator().generate(result)
print('=== decompiled ===')
print(decomp)
print()

print('=== blocks ===')
for off, b in cfg.blocks.items():
    print(f"Block {off} (role={getattr(b, 'role', None)}):")
    for i in b.instructions:
        print(f'  {i.offset:4d} {i.opname:30s} {i.arg} {i.argval}')
    print(f'  successors: {[s.start_offset for s in b.successors]}')

print()
print('=== regions ===')
for r in analyzer.regions:
    print(type(r).__name__, r.region_type,
          'entry=', r.entry.start_offset if r.entry else None,
          'cond=', r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
          'merge=', getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None,
          'vt=', getattr(r, 'value_target', None))
