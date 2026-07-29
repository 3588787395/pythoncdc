"""R30: Debug block 2600 content and IfRegion 2660"""
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
    cfg = build_cfg(co)

    if isinstance(cfg.blocks, dict):
        all_blocks = list(cfg.blocks.values())
    else:
        all_blocks = list(cfg.blocks)

    def show_ins(label, block):
        print(f"=== {label} instructions ===")
        for ins in block.instructions:
            argval = ins.argval if ins.argval is not None else ''
            print(f"  {ins.offset:4d} {ins.opname:25s} {argval}")

    # Show block 2600 instructions
    show_ins("Block 2600", cfg.get_block_by_offset(2600))
    show_ins("Block 2746", cfg.get_block_by_offset(2746))
    show_ins("Block 2664", cfg.get_block_by_offset(2664))
    show_ins("Block 2660", cfg.get_block_by_offset(2660))

    # Show LoopRegion 2590 details
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    for r in analyzer.regions:
        if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 2590:
            print(f"\n=== LoopRegion entry=2590 ===")
            print(f"  blocks={sorted(b.start_offset for b in r.blocks)}")
            print(f"  body_blocks={sorted(b.start_offset for b in r.body_blocks)}")
            print(f"  else_blocks={sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"  header={r.header_block.start_offset}")
            print(f"  back_edge={r.back_edge_block.start_offset if r.back_edge_block else None}")
            print(f"  break_blocks={sorted(b.start_offset for b in r.break_blocks) if r.break_blocks else []}")
            print(f"  has_break={r.has_break}")
            print(f"  else_is_follow={r.else_is_follow}")
            # Check metadata
            if hasattr(r, 'metadata'):
                print(f"  metadata={r.metadata}")

        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 2660:
            print(f"\n=== IfRegion entry=2660 ===")
            print(f"  blocks={sorted(b.start_offset for b in r.blocks)}")
            print(f"  then={sorted(b.start_offset for b in r.then_blocks)}")
            print(f"  else={sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
            print(f"  merge={r.merge_block.start_offset if r.merge_block else None}")
            print(f"  region_type={r.region_type}")


if __name__ == '__main__':
    main()
