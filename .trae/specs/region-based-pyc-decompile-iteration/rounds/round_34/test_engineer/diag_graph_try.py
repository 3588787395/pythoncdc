"""Round 34 诊断：IQCommon/graph._process_task_queue 的 try 块内语句丢失。

原始 try 块（level==0 分支）:
  value_list = tmp_node_dict[node]
  nodes = [...listcomp...]
  value_list.append(nodes)          # <- 丢失
  tmp_node_dict[node] = value_list  # <- 丢失
  queue[task_id] = tmp_node_dict    # <- 丢失(只剩裸 task_id)
  return None

本脚本 dump CFG 块、region 树、异常处理器映射,定位语句被吞的环节。
"""
import sys, marshal, types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYC = ROOT + r'\site-packages\IQCommon\graph.pyc'


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
        out.append('%s %s' % (ins.opname, ins.argval if ins.argval is not None else ''))
    return ' | '.join(out)


def main():
    pyc = load_code(PYC)
    fn = find_code(pyc, '_process_task_queue')

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
        if blk.start_offset in (0, 240, 320, 362, 372, 382, 386, 410, 570):
            print('      instr: %s' % dump_instrs(blk))

    print('\nexception table (blocks with exception info):')
    for blk in cfg.get_blocks_in_order():
        if getattr(blk, 'exception_successors', None):
            print('  blk@%-5d exc_succ=%s' % (
                blk.start_offset,
                [s.start_offset for s in blk.exception_successors]))
        if getattr(blk, 'has_exception_handler', False) or getattr(blk, 'is_handler', False):
            print('  blk@%-5d HANDLER(has_exc_handler=%s)' % (
                blk.start_offset, getattr(blk, 'has_exception_handler', False)))

    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print('\nregions: %d' % len(regions))
    for r in regions:
        ibc = getattr(r, 'inline_boolop_chains', None)
        info = ''
        if ibc:
            for k, v in ibc.items():
                info += ' ibc{%s: op=%s blocks=%s}' % (
                    k, v.get('op'), [b.start_offset for b in v.get('blocks', [])])
        print('  %-14s entry=%-5s blocks=%s then=%s else=%s merge=%s%s' % (
            type(r).__name__,
            r.entry.start_offset if r.entry else None,
            [b.start_offset for b in (getattr(r, 'blocks', None) or [])],
            [b.start_offset for b in getattr(r, 'then_blocks', None) or []],
            [b.start_offset for b in getattr(r, 'else_blocks', None) or []],
            r.merge_block.start_offset if getattr(r, 'merge_block', None) else None,
            info))


if __name__ == '__main__':
    main()
