"""Round 33: 探针——dump stock_order_response_transform 的 region 识别结果。

用反编译器同路径（to_python_code -> build_cfg -> RegionAnalyzer）dump IfRegion 结构。
"""
import sys, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion, BoolOpRegion, TernaryRegion

PYC = r'F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc'


def find_func_code(co, name):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            r = find_func_code(c, name)
            if r:
                return r
    return None


def main():
    module = load_pyc_file_v2(PYC)
    if hasattr(module.code, 'get'):
        code_obj = module.code.get()
    else:
        code_obj = module.code
    actual = code_obj.to_python_code()
    fn = find_func_code(actual, 'stock_order_response_transform')
    print('目标函数:', fn.co_name)

    cfg = build_cfg(fn)
    blocks = cfg.get_blocks_in_order()
    print('blocks:', len(blocks))
    for b in blocks:
        last = b.get_last_instruction()
        print('  blk@%-5d succ=%s  last=%s' % (
            b.start_offset,
            sorted(s.start_offset for s in b.successors),
            (last.opname + ' ' + str(last.argval)) if last else '-'))

    ra = RegionAnalyzer(cfg, fn)
    regions = ra.analyze()
    print('\nregions:', len(regions))
    for r in regions:
        rtype = type(r).__name__
        entry = getattr(r, 'entry', None)
        off = entry.start_offset if entry else None
        extra = ''
        if isinstance(r, IfRegion):
            extra = 'elif_conds=%d' % len(r.elif_conditions or [])
            if r.elif_conditions:
                extra += ' elif@' + str([c.start_offset for c in r.elif_conditions][:5])
            extra += ' then@' + str(sorted(b.start_offset for b in (r.then_blocks or []))[:6])
            if r.else_blocks:
                extra += ' else@' + str(sorted(b.start_offset for b in r.else_blocks)[:6])
        elif isinstance(r, BoolOpRegion):
            extra = 'op_chain=%d' % len(r.op_chain)
        print('  %-18s entry=%-6s blocks=%-3d %s' % (rtype, off, len(r.blocks), extra))


if __name__ == '__main__':
    main()
