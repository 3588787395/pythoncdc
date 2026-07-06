import sys, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

source = 'while (line := f.readline()):\n    lines.append(line.strip())'
code = compile(source, '<test>', 'exec')
func = code

cfg = CFGBuilder().build(func)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
dec = code_gen.generate(result)
print(f'Source:\n{source}')
print(f'\nDecompiled:\n{dec}')

# Show instructions
for instr in __import__('dis').get_instructions(func):
    print(f'  {instr.offset}: {instr.opname} {instr.argval!r}')
print()
rec = compile(dec, '<rec>', 'exec')
rf = None
for c in rec.co_consts:
    if isinstance(c, type(code)):
        rf = c
        break
if rf:
    for instr in __import__('dis').get_instructions(rf):
        print(f'  {instr.offset}: {instr.opname} {instr.argval!r}')
