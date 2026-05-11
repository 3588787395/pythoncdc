import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def decompile(src):
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    return code_gen.generate(result)

tests = {
    'w035': "with open('f') as f:\n    lines = []\n    for line in f:\n        lines.append(line.strip())",
    'w043': "with open('f') as f:\n    x = f.read()\n    for c in x:\n        print(c)",
    'w058': 'async def f():\n    async with ctx as v:\n        x = v',
    'w075': "with open('f') as f:\n    x = f.read()\nfinally_run()",
    'w079': 'for i in range(3):\n    with ctx:\n        if i > 1:\n            break',
    'w080': 'for i in range(3):\n    with ctx:\n        if i < 1:\n            continue',
    'w091': 'with ctx1:\n    pass\nwith ctx2:\n    pass',
    'w092': "with open('a') as fa:\n    pass\nwith open('b') as fb:\n    pass",
    'w093': 'with lock:\n    x = 1\nwith lock:\n    y = 2',
    'w097': 'with ctx:\n    try:\n        pass\n    except:\n        pass',
    'w099': 'with lock:\n    x = 0\n    for i in range(5):\n        x += i',
    'w100': 'with ctx:\n    x = []\n    for i in range(3):\n        x.append(i)',
    'w102': 'with ctx:\n    result = None\n    try:\n        result = compute()\n    except:\n        result = 0\n    finally:\n        cleanup()',
    'w21withelse_a': "with open('f') as a:\n    pass\nx = 1",
    'w26withinwhile_a': "while True:\n    with open('f') as a:\n        break",
    'w30withcustomctx': "class Ctx:\n    def __enter__(self): return self\n    def __exit__(self, *a): pass\nwith Ctx() as c:\n    pass",
}

for name, src in tests.items():
    print(f'=== {name} ===')
    print(f'Source: {repr(src)}')
    try:
        result = decompile(src)
        print(f'Decompiled:\n{result}')
    except Exception as e:
        import traceback
        print(f'Error: {e}')
        traceback.print_exc()
    print()
