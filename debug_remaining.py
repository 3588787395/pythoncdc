import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def decompile_src(src):
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    return code_gen.generate(result)

# W079: for+with+break
print('=== W079 ===')
src = "for i in range(3):\n    with ctx:\n        if i > 1:\n            break"
result = decompile_src(src)
print(result)
print()

# W080: for+with+continue
print('=== W080 ===')
src = "for i in range(3):\n    with ctx:\n        if i < 1:\n            continue"
result = decompile_src(src)
print(result)
print()

# W058: async with
print('=== W058 ===')
src = "async def f():\n    async with ctx as v:\n        x = v"
result = decompile_src(src)
print(result)
print()

# W102: with+try/except/finally
print('=== W102 ===')
src = "with ctx:\n    result = None\n    try:\n        result = compute()\n    except:\n        result = 0\n    finally:\n        cleanup()"
result = decompile_src(src)
print(result)
print()

# W30WithCustomCtx
print('=== W30WithCustomCtx ===')
src = "class Ctx:\n    def __enter__(self): return self\n    def __exit__(self, *a): pass\nwith Ctx() as c:\n    pass"
result = decompile_src(src)
print(result)
