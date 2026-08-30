"""R35 探针2:走真实管线 generate_ast_from_regions,追踪 merge=300 处理路径。"""
import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

ROOT = r"F:\Downloads\pythoncdc-main"
PYC = ROOT + r'\site-packages\IQCommon\util\datetime_func.pyc'
FN = 'change_2str_of_time_2_datetime'


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
    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer
    from core.cfg.region_ast_generator import RegionASTGenerator, generate_ast_from_regions

    pyc = load_code(PYC)
    fn = find_code(pyc, FN)

    _b = CFGBuilder()
    cfg = _b.build(fn)

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('analyzer regions: %d' % len(regions))
    for r in regions:
        print('  %-16s entry=%-5s blocks=%s merge=%s type=%s' % (
            type(r).__name__,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None,
            r.region_type.name if getattr(r, 'region_type', None) else '?'))

    print('\nanalyzer.regions attr: %d' % len(an.regions))
    for r in an.regions:
        print('  %-16s entry=%-5s blocks=%s type=%s' % (
            type(r).__name__,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            r.region_type.name if getattr(r, 'region_type', None) else '?'))

    gen = RegionASTGenerator(cfg)
    print('\ngenerator self.regions: %d' % len(gen.regions))
    for r in gen.regions:
        print('  %-16s entry=%-5s blocks=%s merge=%s' % (
            type(r).__name__,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            getattr(r, 'merge_block', None).start_offset if getattr(r, 'merge_block', None) else None))

    # 追踪 merge=300
    for r in gen.regions:
        if getattr(r, 'merge_block', None) is not None and r.merge_block.start_offset == 300:
            _other = [rr for rr in gen.regions
                      if rr is not r and getattr(rr, 'entry', None) is r.merge_block]
            print('\nBoolOpRegion merge=300: other_entry=%d' % len(_other))
            for rr in _other:
                print('  other: %s entry=%s blocks=%s' % (type(rr).__name__, rr.entry.start_offset,
                                                          [b.start_offset for b in rr.blocks]))
            _ds = gen._downstream_region_entry(r.merge_block, r)
            print('  _downstream_region_entry ->', _ds)


if __name__ == '__main__':
    main()
