import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

tests = [
    ('match x:\n    case [a]:\n        y = a', 'sequence 1'),
    ('match x:\n    case [a, b]:\n        y = a + b', 'sequence 2'),
    ('match x:\n    case [a, *rest]:\n        y = rest', 'sequence star'),
    ('match x:\n    case {"key": v}:\n        y = v', 'mapping'),
    ('match x:\n    case 1 | 2:\n        y = 1\n    case _:\n        y = 0', 'or pattern'),
    ('match x:\n    case 1:\n        pass\n    case 2:\n        pass', 'literal pass'),
    ('match x:\n    case True:\n        y = 1\n    case False:\n        y = 0', 'bool literal'),
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
