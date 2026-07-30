"""Diagnostic: test multiple Pattern T variants to find the exact trigger for
the full except-handler drop (as seen in backtest.pyc) vs the handler-body-drop
(as seen in the minimal repro).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _ in range(8):
    if os.path.exists(os.path.join(sys.path[0], 'pycdc.py')):
        break
    sys.path[0] = os.path.dirname(sys.path[0])

from core.cfg import build_cfg, RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator
from core.cfg.region_analyzer import TryExceptRegion, RegionAnalyzer as CFGRegionAnalyzer


def decompile_fn(src, fn_name='f'):
    code_obj = compile(src, '<v>', 'exec')
    fn_code = None
    for c in code_obj.co_consts:
        if hasattr(c, 'co_name') and c.co_name == fn_name:
            fn_code = c
            break
    if fn_code is None:
        return '(no fn)', None, None
    cfg = build_cfg(fn_code, fn_name)
    analyzer = CFGRegionAnalyzer(cfg)
    regions = analyzer.analyze()
    gen = RegionASTGenerator(cfg)
    ast_dict = gen.generate()
    converter = CFGASTConverter()
    py_ast = converter.convert(ast_dict)
    generator = CodeGenerator()
    src_out = generator.generate(py_ast)
    try_regs = [r for r in regions if isinstance(r, TryExceptRegion)]
    return src_out, try_regs, cfg


VARIANTS = {
    'v1_minimal_return_str': '''
import shutil
def f(a, b):
    try:
        shutil.copy(a, b)
    except FileExistsError as e:
        return 'missing'
    return 'after'
''',
    'v2_return_tuple': '''
import shutil
def f(a, b):
    try:
        shutil.copy(a, b)
    except FileExistsError as e:
        return ({'code': '2', 'message': 'missing'}, None, None)
    return 'after'
''',
    'v3_post_try_code': '''
import shutil, datetime
def f(a, b):
    try:
        shutil.copy(a, b)
    except FileExistsError as e:
        return 'missing'
    t = datetime.datetime.now()
    x = len(t)
    return x
''',
    'v4_in_else_branch': '''
import shutil, datetime
def f(a, b, cond):
    if cond is None:
        return 'err'
    else:
        try:
            shutil.copy(a, b)
        except FileExistsError as e:
            return 'missing'
        t = datetime.datetime.now()
        return t
''',
    'v5_return_tuple_in_else_posttry': '''
import shutil, datetime
def f(a, b, cond):
    if cond is None:
        return 'err'
    else:
        try:
            shutil.copy(a, b)
        except FileExistsError as e:
            return ({'code': '2', 'message': 'missing'}, None, None)
        t = datetime.datetime.now()
        x = len(t)
        return x
''',
    'v6_no_as_binding': '''
import shutil
def f(a, b):
    try:
        shutil.copy(a, b)
    except FileExistsError:
        return 'missing'
    return 'after'
''',
    'v7_bare_except': '''
import shutil
def f(a, b):
    try:
        shutil.copy(a, b)
    except:
        return 'missing'
    return 'after'
''',
}

for name, src in VARIANTS.items():
    out, try_regs, cfg = decompile_fn(src)
    print('=' * 70)
    print(f'[{name}]  #try_regions={len(try_regs) if try_regs else 0}')
    if try_regs:
        for r in try_regs:
            print(f'  try_range=({r.try_offset_start},{r.try_offset_end}) '
                  f'handlers={len(r.except_handlers)} '
                  f'handler_entry={[b.start_offset for b in r.handler_entry_blocks]} '
                  f'has_else={r.has_else} has_finally={r.has_finally}')
            for i, (et, en, hb) in enumerate(r.except_handlers):
                print(f'    handler[{i}] exc={et!r} as={en!r} blocks={[b.start_offset for b in hb]}')
    print('  --- decompiled ---')
    for line in out.splitlines():
        print('    ' + line)
