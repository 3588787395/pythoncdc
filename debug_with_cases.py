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

# W033: with+for
print('=== W033 ===')
print(decompile_src('with lock:\n    for i in range(10):\n        shared += 1'))
print()

# W05WithTry: with inside try
print('=== W05WithTry ===')
src = "try:\n    with open('f') as a:\n        pass\nexcept IndexError:\n    pass"
print(decompile_src(src))
print()

# W26WithInWhile: with inside while
print('=== W26WithInWhile ===')
src = "while True:\n    with open('f') as a:\n        break"
print(decompile_src(src))
print()

# W13WithFor: with+for
print('=== W13WithFor ===')
src = "with open('f') as a:\n    for i in range(3):\n        pass"
print(decompile_src(src))
print()

# W058: async with
print('=== W058 ===')
src = "async def f():\n    async with ctx as v:\n        x = v"
print(decompile_src(src))
print()

# W079: for+with+break
print('=== W079 ===')
src = "for i in range(3):\n    with ctx:\n        if i > 1:\n            break"
print(decompile_src(src))
print()

# W080: for+with+continue
print('=== W080 ===')
src = "for i in range(3):\n    with ctx:\n        if i < 1:\n            continue"
print(decompile_src(src))
print()

# W102: with+try/except/finally
print('=== W102 ===')
src = "with ctx:\n    result = None\n    try:\n        result = compute()\n    except:\n        result = 0\n    finally:\n        cleanup()"
print(decompile_src(src))
print()

# W30WithCustomCtx
print('=== W30WithCustomCtx ===')
src = "class Ctx:\n    def __enter__(self): return self\n    def __exit__(self, *a): pass\nwith Ctx() as c:\n    pass"
print(decompile_src(src))
print()

# W095: with+for
print('=== W095 ===')
src = "with lock:\n    for i in range(10):\n        shared += 1"
print(decompile_src(src))
print()

# W099: with+for
print('=== W099 ===')
src = "with open('f') as a:\n    x = 1\n    for i in range(3):\n        y = i"
print(decompile_src(src))
print()

# W100: with+for
print('=== W100 ===')
src = "with open('f') as a:\n    b = []\n    for i in range(3):\n        b.append(i)"
print(decompile_src(src))
print()
