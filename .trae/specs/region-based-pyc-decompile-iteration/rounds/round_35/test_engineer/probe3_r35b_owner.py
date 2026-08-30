"""R35b 探针: 检查 blk@584 的 block_to_region 归属、IfRegion(584) region_type、
以及 _downstream_region_entry 在该场景下的返回值。
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
    from core.cfg.region_analyzer import RegionAnalyzer, RegionType
    from core.cfg.region_ast_generator import RegionASTGenerator

    cfg = CFGBuilder().build(fn)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()

    blk584 = cfg.get_block_by_offset(584)
    print('block 584:', blk584)
    print('block_to_region[584] =', an.block_to_region.get(blk584))
    owner = an.block_to_region.get(blk584)
    if owner is not None:
        print('  owner type=%s region_type=%s entry=%s' % (
            type(owner).__name__, owner.region_type,
            owner.entry.start_offset if getattr(owner, 'entry', None) else None))

    # 找 BoolOpRegion(424)
    boolop424 = None
    for r in regions:
        if type(r).__name__ == 'BoolOpRegion' and getattr(r, 'entry', None) \
                and r.entry.start_offset == 424:
            boolop424 = r
            break
    print('BoolOpRegion(424):', boolop424)
    if boolop424:
        print('  merge_block =', boolop424.merge_block.start_offset if boolop424.merge_block else None)

    # 找所有 entry=584 的区域
    print('\nregions with entry=584:')
    for r in regions:
        if getattr(r, 'entry', None) and r.entry.start_offset == 584:
            print('  type=%s region_type=%s blocks=%s' % (
                type(r).__name__, r.region_type,
                [b.start_offset for b in r.blocks]))

    # 直接调用 _downstream_region_entry
    gen = RegionASTGenerator(cfg)
    gen.regions = list(regions)  # 模拟 generator 视角
    gen.region_analyzer = an
    gen._generated_regions = set()
    gen._generating_regions = set()
    ds = gen._downstream_region_entry(blk584, boolop424)
    print('\n_downstream_region_entry(584, BoolOp424) =', ds)
    if ds is not None:
        print('  type=%s region_type=%s blocks=%s' % (
            type(ds).__name__, ds.region_type,
            [b.start_offset for b in ds.blocks]))

    # 再模拟: 若 IfRegion(584) 已被 generated
    ifregion584 = None
    for r in regions:
        if type(r).__name__ == 'IfRegion' and getattr(r, 'entry', None) \
                and r.entry.start_offset == 584:
            ifregion584 = r
            break
    print('\nIfRegion(584):', ifregion584)
    if ifregion584:
        print('  region_type=%s blocks=%s' % (
            ifregion584.region_type, [b.start_offset for b in ifregion584.blocks]))
        gen._generated_regions.add(id(ifregion584))
        ds2 = gen._downstream_region_entry(blk584, boolop424)
        print('  after marking generated: _downstream_region_entry =', ds2)


if __name__ == '__main__':
    main()
