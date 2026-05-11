import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

source = """try:
    if bad:
        raise ValueError('bad')
    else:
        process()
except ValueError:
    handle()"""

code = compile(source, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

for r in analyzer.regions:
    rtype = type(r).__name__
    if hasattr(r, 'try_offset_start'):
        print(rtype + ' try=' + str(r.try_offset_start) + '-' + str(r.try_offset_end))
        print('  try_blocks=' + str([b.start_offset for b in r.try_blocks]))
        if hasattr(r, 'except_handlers') and r.except_handlers:
            for exc_type, exc_name, hblocks in r.except_handlers:
                print('  handler: type=' + str(exc_type) + ' blocks=' + str([b.start_offset for b in hblocks]))
        if hasattr(r, 'handler_entry_blocks') and r.handler_entry_blocks:
            print('  handler_entries=' + str([b.start_offset for b in r.handler_entry_blocks]))
    else:
        print(rtype)

gen = RegionASTGenerator(cfg, analyzer)
result = CodeGenerator().generate(gen.generate())
print()
print('Result:')
print(result)
