"""Diagnostic: dump TryExceptRegions identified for a minimal Pattern T repro.

Pattern T = `try: <body> except <Exc> as e: <handler>` whose except handler is
dropped by the decompiler (try emitted with no except).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg, CFGRegionAnalyzer
from core.cfg.region_analyzer import TryExceptRegion

SRC = '''
import shutil
def f(strategy_path, backtest_path):
    try:
        shutil.copy(strategy_path, backtest_path)
    except FileExistsError as e:
        return 'missing'
    return 'after'
'''

code_obj = compile(SRC, '<pat_t>', 'exec')
# find function code
fn_code = None
for c in code_obj.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'f':
        fn_code = c
        break

print('exception table for f:')
for entry in fn_code.co_exceptiontable:
    print('  ', entry)

cfg = build_cfg(fn_code, 'f')
analyzer = CFGRegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f'\n# regions = {len(regions)}')
for r in regions:
    cls = type(r).__name__
    entry_off = r.entry.start_offset if r.entry is not None else None
    if isinstance(r, TryExceptRegion):
        print(f'\n[{cls}] entry={entry_off} try_range=({r.try_offset_start},{r.try_offset_end})')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
        print(f'  except_handlers ({len(r.except_handlers)}):')
        for i, (exc_type, exc_name, hblocks) in enumerate(r.except_handlers):
            print(f'    [{i}] exc_type={exc_type!r} exc_name={exc_name!r} blocks={[b.start_offset for b in hblocks]}')
        print(f'  else_blocks={[b.start_offset for b in r.else_blocks]}')
        print(f'  finally_blocks={[b.start_offset for b in r.finally_blocks]}')
        print(f'  cleanup_blocks={[b.start_offset for b in r.cleanup_blocks]}')
        print(f'  has_else={r.has_else} has_finally={r.has_finally}')
    else:
        print(f'\n[{cls}] entry={entry_off} blocks={sorted(b.start_offset for b in r.blocks)}')

# Now also decompile to confirm the bug reproduces on the minimal case
from core.cfg import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
generator = CodeGenerator()
src_out = generator.generate(py_ast)
print('\n===== DECOMPILED =====')
print(src_out)
print('===== END =====')
