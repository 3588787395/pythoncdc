"""R35 诊断: load_bars_from_hundsun 的 elif 条件丢失（回归）。

分析 merge_block post-store 的 if 条件处理路径。
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


def dump_instrs(blk):
    out = []
    for ins in blk.instructions:
        out.append('@%d %s %s' % (ins.offset, ins.opname,
                                  ins.argval if ins.argval is not None else ''))
    return ' | '.join(out)


def main():
    pyc = load_code(PYC)
    fn = find_code(pyc, FN)
    if fn is None:
        print('FN not found')
        return
    print('== %s: %d instrs ==' % (FN, len(fn.co_code)))

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer

    cfg = CFGBuilder().build(fn)
    print('CFG blocks: %d' % len(cfg.blocks))
    for blk in cfg.get_blocks_in_order():
        last = blk.get_last_instruction()
        print('  blk@%-5d last=%-32s succ=%s' % (
            blk.start_offset,
            last.opname if last else 'None',
            [s.start_offset for s in blk.successors]))
        print('      %s' % dump_instrs(blk))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('\nregions: %d' % len(regions))
    for r in regions:
        print('  %-16s entry=%-5s blocks=%s merge=%s' % (
            type(r).__name__,
            r.entry.start_offset if getattr(r, 'entry', None) else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            r.merge_block.start_offset if getattr(r, 'merge_block', None) else None))


if __name__ == '__main__':
    main()
