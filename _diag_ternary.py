import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

tests = [
    ("x if y else z", 'simple ternary'),
    ("'a' if x > 0 else 'b' if x == 0 else 'c'", 'nested ternary'),
    ("[x if y else z]", 'ternary in list'),
    ("(x if y else z,)", 'ternary in tuple'),
    ("{x if y else z}", 'ternary in set'),
    ("print(x if y else z)", 'ternary as arg'),
    ("1 if a else 2 if b else 3", 'nested ternary 2'),
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
