import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, MatchRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def debug_decompile(src, name):
    print(f'\n{"="*60}')
    print(f'=== {name} ===')
    print(f'Source: {repr(src)}')
    code = compile(src, '<test>', 'exec')
    
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    
    print(f'\nCFG Blocks:')
    for block in cfg.get_blocks_in_order():
        instrs = ', '.join(f'{i.opname}({i.argval})' for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE'))
        succs = [s.start_offset for s in block.successors]
        print(f'  offset={block.start_offset}: [{instrs}] -> {succs}')
    
    generator = RegionASTGenerator(cfg)
    result = generator.generate()
    
    analyzer = generator.region_analyzer
    
    code_gen = CodeGenerator()
    decompiled = code_gen.generate(result)
    
    print(f'\nDecompiled:')
    print(decompiled)
    
    match_regions = [r for r in analyzer.regions if isinstance(r, MatchRegion)]
    all_region_types = [(type(r).__name__, r.region_type) for r in analyzer.regions]
    print(f'\nAll regions: {all_region_types}')
    print(f'Match regions found: {len(match_regions)}')
    for mr in match_regions:
        print(f'  subject_block={mr.subject_block.start_offset if mr.subject_block else None}')
        print(f'  case_blocks={[cb.start_offset for cb in mr.case_blocks]}')
        print(f'  case_patterns={mr.case_patterns}')
        print(f'  case_bodies={[[b.start_offset for b in body] for body in mr.case_bodies]}')
        print(f'  case_body_start_indices={mr.case_body_start_indices}')

tests = [
    ('m013', 'match x:\n    case (1, 2):\n        y = 1\n    case _:\n        y = 0'),
    ('m027', 'match x:\n    case {"key": val}:\n        y = val\n    case _:\n        y = 0'),
    ('m028_none', 'match a:\n    case None:\n        pass'),
    ('m040', 'match x:\n    case [1, 2] | [3, 4]:\n        y = 1\n    case _:\n        y = 0'),
    ('m020_defaultfirst', 'match x:\n    case _:\n        y = 0'),
    ('m039', 'match x:\n    case Point(x=x, y=y) if x == y:\n        y = 1\n    case _:\n        y = 0'),
    ('m045', 'match x:\n    case [_, second, _]:\n        y = second\n    case _:\n        y = 0'),
]

for name, src in tests:
    try:
        debug_decompile(src, name)
    except Exception as e:
        import traceback
        print(f'ERROR: {e}')
        traceback.print_exc()
