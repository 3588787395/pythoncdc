import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, MatchRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def debug_decompile(src, name):
    print(f'\n{"="*60}')
    print(f'=== {name} ===')
    code = compile(src, '<test>', 'exec')
    
    generator = RegionASTGenerator(CFGBuilder().build(code))
    result = generator.generate()
    analyzer = generator.region_analyzer
    
    code_gen = CodeGenerator()
    decompiled = code_gen.generate(result)
    
    print(f'Decompiled:')
    print(decompiled)
    
    match_regions = [r for r in analyzer.regions if isinstance(r, MatchRegion)]
    for mr in match_regions:
        print(f'  case_guards={mr.case_guards}')

tests = [
    ('m039', 'match x:\n    case Point(x=x, y=y) if x == y:\n        y = 1\n    case _:\n        y = 0'),
]

for name, src in tests:
    try:
        debug_decompile(src, name)
    except Exception as e:
        import traceback
        print(f'ERROR: {e}')
        traceback.print_exc()
