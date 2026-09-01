#!/usr/bin/env python3
"""诊断 IfRegion@614 / TernaryRegion@844 / @1226 的字段与块归属。"""
import sys
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, TernaryRegion, IfRegion

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'get_str_data':
            target = const
            break
    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    for r in analyzer.regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 614:
            print("=== IfRegion@614 ===")
            print(f"  entry={r.entry.start_offset}")
            print(f"  blocks={[b.start_offset for b in r.blocks]}")
            print(f"  then_blocks={[b.start_offset for b in r.then_blocks] if hasattr(r,'then_blocks') else 'N/A'}")
            print(f"  else_blocks={[b.start_offset for b in r.else_blocks] if hasattr(r,'else_blocks') else 'N/A'}")
            print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
            print(f"  condition_block={r.condition_block.start_offset if r.condition_block else None}")
            print(f"  children={[type(c).__name__+'@'+str(c.entry.start_offset) for c in (r.children or []) if c.entry]}")
        if isinstance(r, TernaryRegion) and r.entry and r.entry.start_offset in (844, 1226):
            print(f"=== TernaryRegion@{r.entry.start_offset} ===")
            print(f"  blocks={[b.start_offset for b in r.blocks]}")
            print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
            print(f"  merge_context={getattr(r,'merge_context',None)}")
            print(f"  parent={type(r.parent).__name__+'@'+str(r.parent.entry.start_offset) if (r.parent and r.parent.entry) else None}")

    # block_to_region ownership
    print("\n=== block_to_region ownership (844, 1096, 1120, 1226, 1286, 1310, 1416) ===")
    b2r = getattr(analyzer, 'block_to_region', None)
    if b2r is None:
        b2r = {}
        for rr in analyzer.regions:
            for b in rr.blocks:
                b2r[b] = rr
    for off in [844, 1096, 1120, 1226, 1286, 1310, 1416]:
        blk = cfg.get_block_by_offset(off)
        owner = b2r.get(blk)
        print(f"  block@{off}: owner={type(owner).__name__+'@'+str(owner.entry.start_offset) if (owner and owner.entry) else owner}")

    # Print instructions of block 844 and 1226 to see pre-ternary pushes
    print("\n=== block@844 instructions (first 12) ===")
    blk844 = cfg.get_block_by_offset(844)
    for i in blk844.instructions[:12]:
        print(f"  {i.offset:>4} {i.opname:<28} {i.argval!r}")
    print(f"  ... total {len(blk844.instructions)} instrs, last={[blk844.instructions[-1].opname]}")
    print("\n=== block@1226 instructions (first 8) ===")
    blk1226 = cfg.get_block_by_offset(1226)
    for i in blk1226.instructions[:8]:
        print(f"  {i.offset:>4} {i.opname:<28} {i.argval!r}")
    print(f"  ... total {len(blk1226.instructions)} instrs, last={[blk1226.instructions[-1].opname]}")
    print("\n=== block@1416 instructions (first 10) ===")
    blk1416 = cfg.get_block_by_offset(1416)
    for i in blk1416.instructions[:10]:
        print(f"  {i.offset:>4} {i.opname:<28} {i.argval!r}")


if __name__ == '__main__':
    main()
