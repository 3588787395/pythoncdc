#!/usr/bin/env python3
"""诊断 get_date_and_count 的区域结构：while 循环 + if/elif/else 链 + else 内嵌 while。"""
import sys
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, TernaryRegion, IfRegion, BoolOpRegion

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'get_date_and_count':
            target = const
            break
    if target is None:
        print("get_date_and_count not found")
        return

    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"=== get_date_and_count regions: {len(analyzer.regions)} ===")
    for r in sorted(analyzer.regions, key=lambda x: x.entry.start_offset if x.entry else 0):
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else -1
        blocks_offs = sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') else []
        parent_off = (r.parent.entry.start_offset if (r.parent and r.parent.entry) else None) if hasattr(r, 'parent') else None
        merge_off = getattr(r, 'merge_block', None)
        merge_off = merge_off.start_offset if merge_off else None
        merge_ctx = getattr(r, 'merge_context', None)
        print(f"  {rtype}@{entry_off} blocks={blocks_offs} parent={parent_off} merge={merge_off} merge_ctx={merge_ctx}")

    print("\n=== IfRegions (if/elif/else chain) ===")
    for r in analyzer.regions:
        if isinstance(r, IfRegion):
            entry_off = r.entry.start_offset if r.entry else -1
            then_offs = sorted([b.start_offset for b in r.then_blocks]) if hasattr(r, 'then_blocks') else []
            else_offs = sorted([b.start_offset for b in r.else_blocks]) if hasattr(r, 'else_blocks') else []
            merge_off = getattr(r, 'merge_block', None)
            merge_off = merge_off.start_offset if merge_off else None
            children = [type(c).__name__ + '@' + str(c.entry.start_offset) for c in (r.children or []) if c.entry]
            print(f"  If@entry={entry_off} then={then_offs} else={else_offs} merge={merge_off} children={children}")
            for c in (r.children or []):
                cb = sorted([b.start_offset for b in c.blocks]) if hasattr(c, 'blocks') else []
                print(f"    child {type(c).__name__}@{c.entry.start_offset if c.entry else -1} blocks={cb}")

    print("\n=== LoopRegions (while count > 0) ===")
    for r in analyzer.regions:
        if isinstance(r, LoopRegion):
            entry_off = r.entry.start_offset if r.entry else -1
            header_off = r.header_block.start_offset if r.header_block else -1
            body_offs = sorted([b.start_offset for b in r.body_blocks]) if hasattr(r, 'body_blocks') else []
            else_offs = sorted([b.start_offset for b in r.else_blocks]) if hasattr(r, 'else_blocks') else []
            children = [type(c).__name__ + '@' + str(c.entry.start_offset) for c in (r.children or []) if c.entry]
            print(f"  Loop@entry={entry_off} header={header_off} body={body_offs} else={else_offs} children={children}")
            for c in (r.children or []):
                cb = sorted([b.start_offset for b in c.blocks]) if hasattr(c, 'blocks') else []
                print(f"    child {type(c).__name__}@{c.entry.start_offset if c.entry else -1} blocks={cb}")


if __name__ == '__main__':
    main()
