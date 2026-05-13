import sys, types, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

source = '''def f(items):
    i = 0
    while i < len(items):
        if items[i] <= 0:
            i += 1
            continue
        a = items[i]
        i += 1'''
code = compile(source, '<test>', 'exec')
func = None
for c in code.co_consts:
    if isinstance(c, types.CodeType):
        func = c
        break

print('=== Original instructions ===')
orig_instrs = list(dis.get_instructions(func))
for ins in orig_instrs:
    print(f'  {ins.offset:3d}: {ins.opname:30s} {str(ins.argval)!r:20s}')

cfg = CFGBuilder().build(func)
analyzer = RegionAnalyzer(cfg)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
dec = code_gen.generate(result)

rec_code = compile(dec, '<rec>', 'exec')
rec_func = None
for c in rec_code.co_consts:
    if isinstance(c, types.CodeType):
        rec_func = c
        break

print(f'\n=== Decompiled ===\n{dec}')
print(f'\n=== Recompiled instructions ===')
rec_instrs = list(dis.get_instructions(rec_func))
for ins in rec_instrs:
    print(f'  {ins.offset:3d}: {ins.opname:30s} {str(ins.argval)!r:20s}')

print(f'\n=== Diff ===')
print(f'Original: {len(orig_instrs)} instrs, Recompiled: {len(rec_instrs)} instrs')
