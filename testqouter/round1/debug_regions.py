import py_compile, sys, os, types
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg import build_cfg, CFGRegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

tests = [
    'test_r1_chained_compare.py',
    'test_e09_nested_try.py',
    'test_n11_try_while_continue.py',
    'test_n16_for_if_try_except.py',
    'test_r1_if_try_except.py',
    'test_e05_try_except_finally.py',
]

for tf in tests:
    pyc = tf + 'c'
    if not os.path.exists(tf):
        print(f'SKIP {tf} - not found')
        continue
    py_compile.compile(tf, cfile=pyc, doraise=True)
    code_obj = compile(open(tf).read(), tf, 'exec')
    func_code = code_obj.co_consts[0]
    cfg = build_cfg(func_code)
    ra = CFGRegionAnalyzer(cfg)
    regions = ra.analyze()

    print(f'=== {tf} ===')
    for r in regions:
        extra = ''
        if isinstance(r, IfRegion):
            extra = f' cond={r.condition_block.start_offset if r.condition_block else None} then={[b.start_offset for b in r.then_blocks]} else={[b.start_offset for b in r.else_blocks]} merge={r.merge_block.start_offset if r.merge_block else None} chained_cmp={[b.start_offset for b in r.chained_compare_blocks] if r.chained_compare_blocks else []} cmp_ops={r.chained_compare_ops}'
        print(f'  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}{extra}')
    print()

    print('  Blocks:')
    for block in cfg.blocks:
        try:
            instrs = [(i.opname, i.argval) for i in block.instructions]
            succs = [s.start_offset for s in block.successors]
            print(f'    {block.start_offset}: {instrs} -> {succs}')
        except:
            print(f'    {block}: (error)')
    print()

    os.remove(pyc)
