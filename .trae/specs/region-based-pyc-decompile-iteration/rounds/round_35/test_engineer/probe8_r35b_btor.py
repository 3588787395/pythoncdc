"""R35b 探针: 检查 generate() 内部 top_level_regions 的构造与派发。
直接 hook generate() 中 top_level_regions 循环。
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

    # 打印 analyzer 所有区域
    print('analyzer regions (%d):' % len(regions))
    for r in regions:
        print('  %-16s type=%-16s entry=%-5s blocks=%s parent=%s' % (
            type(r).__name__,
            r.region_type.name,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            (type(r.parent).__name__ + '@' + str(r.parent.entry.start_offset))
            if getattr(r, 'parent', None) and getattr(r.parent, 'entry', None) else
            (type(r.parent).__name__ if getattr(r, 'parent', None) else 'None')))

    # 手动构造 generator 并模拟 generate() 顶层
    gen = RegionASTGenerator(cfg, top_level_code=co if co.co_name == '<module>' else None)
    gen.regions = list(regions)
    gen.region_analyzer = an

    # 打印 block_to_region
    print('block_to_region:')
    for blk in cfg.get_blocks_in_order():
        owner = an.block_to_region.get(blk)
        if owner is not None:
            print('  blk@%-5d -> %-14s(entry=%s, type=%s)' % (
                blk.start_offset,
                type(owner).__name__,
                owner.entry.start_offset if getattr(owner, 'entry', None) else None,
                owner.region_type.name))


check(r'\site-packages\IQCommon\util\datetime_func.pyc', 'change_2str_of_time_2_datetime')
