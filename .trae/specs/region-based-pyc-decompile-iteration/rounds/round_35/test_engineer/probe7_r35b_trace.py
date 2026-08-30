"""R35b 探针: 检查 generate() 顶层循环对 BoolOpRegion 的处理。
验证：datetime_func 中 BoolOpRegion(140)（parent=None）为何在 HEAD 不派发，
而 quotation 中 BoolOpRegion(424)（parent=IfRegion）能派发。
"""
import sys, os, marshal, types
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


def check(pyc, fn_name):
    print('\n' + '=' * 70)
    print('== %s / %s ==' % (pyc.split('\\')[-1], fn_name))
    co = find_code(load_code(ROOT + pyc), fn_name)
    if co is None:
        print('FN not found')
        return

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator

    cfg = CFGBuilder().build(co)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()

    gen = RegionASTGenerator(cfg, top_level_code=co if co.co_name == '<module>' else None)
    gen.regions = list(regions)
    gen.region_analyzer = an

    # 模拟 generate() 顶部孤儿释放后 top_level_regions 的构造
    # 直接调用 generate() 但 hook 顶层循环
    orig_gen_region = gen._generate_region

    def traced_generate_region(region, skip_store_targets=None):
        print('  [TRACE] _generate_region %-14s entry=%-5s blocks=%s parent=%s' % (
            type(region).__name__,
            region.entry.start_offset if getattr(region, 'entry', None) else None,
            [b.start_offset for b in (getattr(region, 'blocks', None) or [])],
            type(getattr(region, 'parent', None)).__name__ if getattr(region, 'parent', None) else None))
        return orig_gen_region(region, skip_store_targets=skip_store_targets)

    gen._generate_region = traced_generate_region

    try:
        ast_dict = gen.generate()
        print('  GENERATE OK')
    except Exception as e:
        print('  GENERATE ERR:', e)


check(r'\site-packages\IQCommon\util\datetime_func.pyc', 'change_2str_of_time_2_datetime')
check(r'\site-packages\fly\data\quotation.pyc', 'load_bars_from_hundsun')
