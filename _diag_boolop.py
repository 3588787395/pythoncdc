import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

tests = [
    ('if a or (b and c) or d:\n    x = 1', 'mixed and/or'),
    ('if a and b or c:\n    x = 1', 'and then or'),
    ('x = a and b', 'and assign'),
    ('x = a or b', 'or assign'),
    ('if a and b:\n    x = 1', 'simple and'),
    ('if a or b:\n    x = 1', 'simple or'),
]

cfg_builder = CFGBuilder()
code_gen = CodeGenerator()

for src, name in tests:
    try:
        code = compile(src, '<test>', 'exec')
        cfg = cfg_builder.build(code)
        analyzer = RegionAnalyzer(cfg)
        generator = RegionASTGenerator(cfg, analyzer)
        result = generator.generate()
        output = code_gen.generate(result)
        print(f'=== {name} ===')
        print(output)
        print()
    except Exception as e:
        print(f'=== {name} === ERROR: {e}')
        import traceback
        traceback.print_exc()
        print()
