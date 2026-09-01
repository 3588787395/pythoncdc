"""R35b 探针: 对比 datetime_func 与 quotation(load_bars_from_hundsun) 的区域父子结构，
理解 BoolOpRegion 链的派发差异。
"""
import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

ROOT = r"F:\Downloads\pythoncdc-main"


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r:
                return r
    return None


def analyze(pyc, fn_name):
    print('\n' + '=' * 70)
    print('== %s / %s ==' % (pyc.split('\\')[-1], fn_name))
    pyc_abs = ROOT + pyc
    co = find_code(load_code(pyc_abs), fn_name)
    if co is None:
        print('FN not found')
        return

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer

    cfg = CFGBuilder().build(co)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()

    # 打印所有 BoolOpRegion 及其 parent
    print('BoolOpRegions:')
    for r in regions:
        if type(r).__name__ == 'BoolOpRegion':
            par = getattr(r, 'parent', None)
            print('  %-14s entry=%-5s merge=%-5s value_target=%-12s parent=%s(entry=%s)' % (
                type(r).__name__,
                r.entry.start_offset if getattr(r, 'entry', None) else None,
                r.merge_block.start_offset if getattr(r, 'merge_block', None) else None,
                getattr(r, 'value_target', None),
                type(par).__name__ if par else None,
                par.entry.start_offset if par and getattr(par, 'entry', None) else None))
    # 打印 IfRegion 及 children
    print('IfRegions (with BoolOp children):')
    for r in regions:
        if type(r).__name__ == 'IfRegion':
            kids = getattr(r, 'children', None) or []
            boolop_kids = [k for k in kids if type(k).__name__ == 'BoolOpRegion']
            if boolop_kids:
                print('  IfRegion entry=%-5s boolop_children=%s' % (
                    r.entry.start_offset,
                    [k.entry.start_offset for k in boolop_kids]))


analyze(r'\site-packages\IQCommon\util\datetime_func.pyc', 'change_2str_of_time_2_datetime')
analyze(r'\site-packages\fly\data\quotation.pyc', 'load_bars_from_hundsun')
analyze(r'\site-packages\fly\data\quotation.pyc', 'fill_minute_or_day_blank')
