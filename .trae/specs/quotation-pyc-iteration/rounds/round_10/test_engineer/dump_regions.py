"""R10 调试：dump get_growth_ability 的区域结构，定位 else 分支截断原因。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion, WithRegion


def load_func_code(pyc_path, func_name):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == func_name:
            return c
    return None


def main():
    func_name = 'get_growth_ability'
    code = load_func_code('/workspace/quotation.pyc', func_name)
    if code is None:
        print(f"Function {func_name} not found")
        return

    cfg = CFGBuilder().build(code)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()

    print(f"=== {func_name} ===")
    print(f"CFG blocks: {len(cfg.blocks)}")
    print(f"Regions: {len(regions)}")

    # Find the outer IfRegion (entry matches the first if)
    for r in regions:
        if isinstance(r, IfRegion):
            print(f"\n--- IfRegion entry={r.entry.start_offset} ---")
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
            print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
            print(f"  elif_conditions: {[b.start_offset for b in r.elif_conditions] if r.elif_conditions else []}")
            print(f"  elif_bodies: {[[b.start_offset for b in body] for body in r.elif_bodies] if r.elif_bodies else []}")
            print(f"  elif_final_else: {[b.start_offset for b in r.elif_final_else] if r.elif_final_else else []}")
            print(f"  children: {len(r.children or [])}")
            for ch in (r.children or []):
                ch_type = type(ch).__name__
                ch_entry = ch.entry.start_offset if hasattr(ch, 'entry') and ch.entry else None
                ch_blocks = [b.start_offset for b in ch.blocks] if hasattr(ch, 'blocks') else []
                print(f"    child: {ch_type} entry={ch_entry} blocks={ch_blocks[:10]}{'...' if len(ch_blocks)>10 else ''}")

    # Also dump all regions of interest (entry near 304)
    print(f"\n--- Regions with entry near 304 or 142 ---")
    for r in regions:
        entry_off = r.entry.start_offset if hasattr(r, 'entry') and r.entry else None
        if entry_off is not None and (140 <= entry_off <= 310):
            print(f"  {type(r).__name__} entry={entry_off} blocks={[b.start_offset for b in r.blocks][:15]}")


if __name__ == '__main__':
    main()
