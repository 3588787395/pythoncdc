import sys, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

source = 'while True:\n    do_something()\n    if done:\n        break'
code = compile(source, '<test>', 'exec')
func = code

cfg = CFGBuilder().build(func)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if isinstance(r, LoopRegion):
        print(f'LOOP: cond={r.condition_block.start_offset if r.condition_block else None}, hdr={r.header_block.start_offset if r.header_block else None}')
        print(f'  body={sorted(b.start_offset for b in r.body_blocks)}, else={sorted(b.start_offset for b in r.else_blocks)}')
        ch = r.children or []
        print(f'  children: {[(c.region_type.name, c.entry.start_offset if c.entry else None) for c in ch]}')
    elif isinstance(r, IfRegion):
        print(f'IF: entry={r.entry.start_offset if r.entry else None}, blocks=sorted({sorted(b.start_offset for b in r.blocks)})')

generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
dec = code_gen.generate(result)
print(f'\nDecompiled:\n{dec}')
