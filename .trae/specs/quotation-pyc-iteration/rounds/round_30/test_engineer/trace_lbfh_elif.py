"""Trace IF_ELIF_CHAIN generation for load_bars_from_hundsun."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'load_bars_from_hundsun':
            return c
    return None


def main():
    co = load_code(PYC)
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()

    # Find IF_ELIF_CHAIN at 584
    target_region = None
    for r in ra.regions:
        if (isinstance(r, IfRegion)
                and r.region_type == RegionType.IF_ELIF_CHAIN
                and r.entry is not None
                and r.entry.start_offset == 584):
            target_region = r
            break

    if target_region is None:
        print("IF_ELIF_CHAIN at 584 NOT FOUND")
        # Show all IF_ELIF_CHAIN regions
        for r in ra.regions:
            if isinstance(r, IfRegion) and r.region_type == RegionType.IF_ELIF_CHAIN:
                eo = r.entry.start_offset if r.entry else None
                print(f"  IF_ELIF_CHAIN entry={eo}")
        return

    print(f"=== IF_ELIF_CHAIN at 584 ===")
    print(f"  entry: {target_region.entry.start_offset}")
    print(f"  condition_block: {target_region.condition_block.start_offset if target_region.condition_block else None}")
    print(f"  then_blocks: {[b.start_offset for b in target_region.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in target_region.else_blocks]}")
    print(f"  merge_block: {target_region.merge_block.start_offset if target_region.merge_block else None}")
    print(f"  elif_conditions: {[b.start_offset for b in target_region.elif_conditions] if target_region.elif_conditions else None}")
    print(f"  elif_bodies: {[[b.start_offset for b in body] for body in target_region.elif_bodies] if target_region.elif_bodies else None}")
    print(f"  elif_final_else: {[b.start_offset for b in target_region.elif_final_else] if target_region.elif_final_else else None}")
    print(f"  blocks: {sorted([b.start_offset for b in target_region.blocks])}")

    # Find parent IF_THEN at 214
    parent_region = None
    for r in ra.regions:
        if (isinstance(r, IfRegion)
                and r.entry is not None
                and r.entry.start_offset == 214):
            parent_region = r
            break

    if parent_region:
        print(f"\n=== Parent IF_THEN at 214 ===")
        print(f"  entry: {parent_region.entry.start_offset}")
        print(f"  condition_block: {parent_region.condition_block.start_offset if parent_region.condition_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in parent_region.then_blocks]}")
        print(f"  merge_block: {parent_region.merge_block.start_offset if parent_region.merge_block else None}")

    # Generate AST
    print(f"\n=== Generating AST ===")
    gen = RegionASTGenerator(cfg, ra)
    try:
        result = gen.generate()
        print(f"Generated {len(result)} top-level statements")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
