import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
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

tests = [
    ('m013', 'match x:\n    case (1, 2):\n        y = 1\n    case _:\n        y = 0'),
    ('m027', 'match x:\n    case {"key": val}:\n        y = val\n    case _:\n        y = 0'),
    ('m039', 'match x:\n    case Point(x=x, y=y) if x == y:\n        y = 1\n    case _:\n        y = 0'),
    ('m028_none', 'match a:\n    case None:\n        pass'),
    ('m040', 'match x:\n    case [1, 2] | [3, 4]:\n        y = 1\n    case _:\n        y = 0'),
    ('m041', 'match x:\n    case (1, 2):\n        y = 1\n    case (3, 4):\n        y = 2\n    case _:\n        y = 0'),
    ('m045', 'match x:\n    case [_, second, _]:\n        y = second\n    case _:\n        y = 0'),
    ('m020_defaultfirst', 'match x:\n    case _:\n        y = 0'),
]

for name, src in tests:
    try:
        result = decompile(src)
        print(f'=== {name} ===')
        print(result)
        print()
    except Exception as e:
        import traceback
        print(f'=== {name} ERROR ===')
        traceback.print_exc()
        print()
