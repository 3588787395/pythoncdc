"""R30: Debug block structure and loop body for build_future_fill_time"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

PYC = '/workspace/quotation.pyc'


def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_name'):
            r = find_code(c, name)
            if r:
                return r
    return None


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    co = find_code(code_obj, 'build_future_fill_time')
    if not co:
        print("Function not found")
        return

    cfg = build_cfg(co)

    # Get blocks - handle both list and dict
    if hasattr(cfg, 'blocks') and isinstance(cfg.blocks, dict):
        all_blocks = list(cfg.blocks.values())
    elif hasattr(cfg, 'all_blocks'):
        all_blocks = list(cfg.all_blocks)
    else:
        all_blocks = list(cfg.blocks)

    # Show all blocks in the range 2580-2790
    print("=== Blocks (offset 2580-2790) ===")
    for b in sorted(all_blocks, key=lambda x: x.start_offset):
        if b.start_offset < 2580 or b.start_offset > 2790:
            continue
        succs = [s.start_offset for s in b.successors]
        preds = [p.start_offset for p in b.predecessors]
        last = b.get_last_instruction()
        last_op = last.opname if last else 'None'
        print(f"  block {b.start_offset}: last={last_op}, succ={succs}, pred={preds}")

    print("\n=== Regions (offset > 2400) ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if hasattr(r, 'entry') and r.entry else None
        if entry_off is None or entry_off < 2400:
            continue
        print(f"\n  {rtype} entry={entry_off}")
        if hasattr(r, 'blocks'):
            print(f"    blocks={sorted(b.start_offset for b in r.blocks)}")
        if isinstance(r, LoopRegion):
            print(f"    body_blocks={sorted(b.start_offset for b in r.body_blocks)}")
            print(f"    else_blocks={sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"    header={r.header_block.start_offset if r.header_block else None}")
            print(f"    back_edge={r.back_edge_block.start_offset if r.back_edge_block else None}")
            print(f"    break_blocks={sorted(b.start_offset for b in r.break_blocks) if r.break_blocks else []}")
        if isinstance(r, IfRegion):
            if r.then_blocks:
                print(f"    then={sorted(b.start_offset for b in r.then_blocks)}")
            if r.else_blocks:
                print(f"    else={sorted(b.start_offset for b in r.else_blocks)}")
            if r.merge_block:
                print(f"    merge={r.merge_block.start_offset}")


if __name__ == '__main__':
    main()
