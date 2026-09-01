#!/usr/bin/env python3
"""诊断 get_str_data 的区域结构：for datas 循环体 + 子 TernaryRegion 归属。"""
import sys
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # find get_str_data code object
    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'get_str_data':
            target = const
            break
    if target is None:
        print("get_str_data not found")
        return

    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"=== get_str_data regions: {len(analyzer.regions)} ===")
    for r in sorted(analyzer.regions, key=lambda x: x.entry.start_offset if x.entry else 0):
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else -1
        blocks_offs = sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') else []
        parent_off = (r.parent.entry.start_offset if (r.parent and r.parent.entry) else None) if hasattr(r, 'parent') else None
        merge_off = getattr(r, 'merge_block', None)
        merge_off = merge_off.start_offset if merge_off else None
        merge_ctx = getattr(r, 'merge_context', None)
        print(f"  {rtype}@{entry_off} blocks={blocks_offs} parent={parent_off} merge={merge_off} merge_ctx={merge_ctx}")

    # Find the for-datas loop: the one whose header FOR_ITER jumps to the end
    print("\n=== LoopRegions (for-datas is the inner for over datass_list) ===")
    from core.cfg.region_analyzer import LoopRegion, TernaryRegion, IfRegion
    for r in analyzer.regions:
        if isinstance(r, LoopRegion):
            entry_off = r.entry.start_offset if r.entry else -1
            header_off = r.header_block.start_offset if r.header_block else -1
            body_offs = sorted([b.start_offset for b in r.body_blocks]) if hasattr(r, 'body_blocks') else []
            else_offs = sorted([b.start_offset for b in r.else_blocks]) if hasattr(r, 'else_blocks') else []
            children = [type(c).__name__ + '@' + str(c.entry.start_offset) for c in (r.children or []) if c.entry]
            print(f"  Loop@entry={entry_off} header={header_off} body={body_offs} else={else_offs} children={children}")
            # print child region details
            for c in (r.children or []):
                cb = sorted([b.start_offset for b in c.blocks]) if hasattr(c, 'blocks') else []
                print(f"    child {type(c).__name__}@{c.entry.start_offset if c.entry else -1} blocks={cb}")


if __name__ == '__main__':
    main()
