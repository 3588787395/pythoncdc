"""R35b 探针: 检查 quotation 中 424/560/584/1862 各 merge_block 的 block_to_region owner，
以及 _downstream_region_entry 在真实 generate 语境下是否返回非 None。
"""
import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\fly\data\quotation.pyc'
FN = 'load_bars_from_hundsun'


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


def main():
    pyc = load_code(PYC)
    fn = find_code(pyc, FN)
    if fn is None:
        print('FN not found')
        return

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator

    cfg = CFGBuilder().build(fn)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()

    print('== block_to_region owners for merge blocks ==')
    for off in (400, 424, 560, 584, 1862, 2022):
        blk = cfg.get_block_by_offset(off)
        if blk is None:
            print('  blk@%d: NOT FOUND' % off)
            continue
        owner = an.block_to_region.get(blk)
        print('  blk@%-5d owner=%-18s owner_type=%s' % (
            off, owner.entry.start_offset if owner and getattr(owner, 'entry', None) else None,
            type(owner).__name__ if owner else None))

    # 找 BoolOpRegion(424) 与 BoolOpRegion(400)
    boolop424 = None
    boolop400 = None
    for r in regions:
        if type(r).__name__ == 'BoolOpRegion' and getattr(r, 'entry', None):
            if r.entry.start_offset == 424:
                boolop424 = r
            if r.entry.start_offset == 400:
                boolop400 = r
    print('\nboolop424:', boolop424 is not None, 'boolop400:', boolop400 is not None)

    gen = RegionASTGenerator(cfg)
    gen.regions = list(regions)
    gen.region_analyzer = an
    gen._generated_regions = set()
    gen._generating_regions = set()

    for off, exclude in ((424, boolop424), (560, boolop424), (584, boolop424)):
        blk = cfg.get_block_by_offset(off)
        if blk is None or exclude is None:
            continue
        ds = gen._downstream_region_entry(blk, exclude)
        print('  _downstream_region_entry(blk@%d, BoolOp424) = %s' % (
            off,
            '%s(entry=%s)' % (type(ds).__name__, ds.entry.start_offset) if ds is not None else 'None'))


if __name__ == '__main__':
    main()
