import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# while-else WITH break
src = '''
def while_else_break(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        print('no break')
    print('after while')
'''
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        print('=== CFG Blocks ===')
        for offset, block in sorted(cfg.blocks.items()):
            print(f'  Block@{offset}:')
            for instr in block.instructions:
                print(f'    {instr.offset}: {instr.opname} {instr.arg} {instr.argval}')
            print(f'    succs: {[s.start_offset for s in block.successors]}')
        
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        print()
        print('=== Loop Regions ===')
        for r in regions:
            if isinstance(r, LoopRegion):
                print(f'  LoopRegion: header={r.header_block.start_offset if r.header_block else None}')
                print(f'    condition_block={r.condition_block.start_offset if r.condition_block else None}')
                print(f'    body_blocks={[b.start_offset for b in r.body_blocks]}')
                print(f'    else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}')
                print(f'    break_blocks={[b.start_offset for b in r.break_blocks] if r.break_blocks else []}')
                print(f'    has_break={r.has_break}')
                print(f'    else_is_follow={r.else_is_follow}')
        
        print()
        gen = RegionASTGenerator(cfg)
        ast_dict = gen.generate()
        from core.cfg.ast_converter import CFGASTConverter
        from core.cfg.code_generator import CodeGenerator
        converter = CFGASTConverter()
        py_ast = converter.convert(ast_dict)
        generator = CodeGenerator()
        result = generator.generate(py_ast)
        print('=== Decompiled ===')
        print(result)
