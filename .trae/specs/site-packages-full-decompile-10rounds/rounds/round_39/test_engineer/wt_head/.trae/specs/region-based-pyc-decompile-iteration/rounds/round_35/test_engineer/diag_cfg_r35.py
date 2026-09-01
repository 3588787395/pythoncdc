"""Round 35 诊断:datetime_func.change_2str_of_time_2_datetime 的 source_end 计算丢失。

原始逻辑:
  source_start = datetime.datetime.strptime(startttime[:8] + (len(startttime[8:]) == 4 and startttime[8:] or '0000'), '%Y%m%d%H%M')  # OK
  source_end   = datetime.datetime.strptime(endtime[:8]   + (len(endtime[8:])   == 4 and endtime[8:]   or '1530'), '%Y%m%d%H%M')  # 退化
  return source_start, source_end  # 退化

本脚本 dump CFG 块(含指令)与 region 树,对比两段的区域归属。
"""
import sys, marshal, types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
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


def dump_instrs(blk):
    out = []
    for ins in blk.instructions:
        out.append('@%d %s %s' % (ins.offset, ins.opname,
                                  ins.argval if ins.argval is not None else ''))
    return ' | '.join(out)


def main():
    pyc = load_code(PYC)
    fn = find_code(pyc, FN)

    from core.cfg.cfg_builder import CFGBuilder
    from core.cfg.region_analyzer import RegionAnalyzer

    _b = CFGBuilder()
    cfg = _b.build(fn)
    print('CFG blocks: %d' % len(cfg.blocks))
    for blk in cfg.get_blocks_in_order():
        last = blk.get_last_instruction()
        print('  blk@%-5d last=%-32s succ=%s pred=%s' % (
            blk.start_offset,
            last.opname if last else 'None',
            [s.start_offset for s in blk.successors],
            [p.start_offset for p in blk.predecessors]))
        print('      instr: %s' % dump_instrs(blk))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('\nregions: %d' % len(regions))
    for r in regions:
        print('  %-16s entry=%-5s blocks=%s then=%s else=%s merge=%s' % (
            type(r).__name__,
            r.entry.start_offset if r.entry else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            [b.start_offset for b in getattr(r, 'then_blocks', None) or []],
            [b.start_offset for b in getattr(r, 'else_blocks', None) or []],
            r.merge_block.start_offset if getattr(r, 'merge_block', None) else None))


if __name__ == '__main__':
    main()
