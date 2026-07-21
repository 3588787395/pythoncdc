import sys
import os
sys.path.insert(0, '/workspace')
import dis
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator


def debug_decompile(src, name):
    print(f'\n{"=" * 60}\n{name}: {src!r}\n{"=" * 60}')
    code = compile(src, '<test>', 'exec')
    print('--- Original bytecode ---')
    dis.dis(code)
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze() if isinstance(analyzer.analyze(), list) else analyzer.regions
    print('\n--- Regions ---')
    if isinstance(regions, dict):
        for off, region in sorted(regions.items()):
            print(f'  offset={off}: {type(region).__name__}')
    else:
        for region in regions:
            print(f'  {type(region).__name__}: blocks={getattr(region, "blocks", None)}')
    generator = RegionASTGenerator(cfg, analyzer)
    ast_result = generator.generate()
    code_gen = CodeGenerator()
    src_out = code_gen.generate(ast_result)
    print(f'\n--- Decompiled source ---')
    print(src_out)
    print(f'\n--- Re-encoded bytecode ---')
    try:
        recompiled = compile(src_out, '<recompiled>', 'exec')
        dis.dis(recompiled)
    except SyntaxError as e:
        print(f'SyntaxError: {e}')


# adv02: if (a if c else d) or b: pass
debug_decompile('if (a if c else d) or b:\n    pass', 'adv02')

# bool11: while not done and has_data(): process()
debug_decompile('while not done and has_data():\n    process()', 'bool11')
