"""Trace IF_ELIF_CHAIN@584 processing in load_bars_from_hundsun."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, RegionType

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

    # Find IF_ELIF_CHAIN@584
    elif_chain = None
    for r in ra.regions:
        if (isinstance(r, IfRegion)
                and r.region_type == RegionType.IF_ELIF_CHAIN
                and r.entry is not None
                and r.entry.start_offset == 584):
            elif_chain = r
            break

    if elif_chain is None:
        print("IF_ELIF_CHAIN@584 NOT FOUND")
        return

    print(f"=== IF_ELIF_CHAIN@584 ===")
    print(f"  entry: {elif_chain.entry.start_offset}")
    print(f"  blocks: {sorted([b.start_offset for b in elif_chain.blocks])}")
    print(f"  then_blocks: {[b.start_offset for b in elif_chain.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in elif_chain.else_blocks]}")
    print(f"  elif_conditions: {[b.start_offset for b in elif_chain.elif_conditions] if elif_chain.elif_conditions else None}")
    print(f"  elif_bodies: {[[b.start_offset for b in body] for body in elif_chain.elif_bodies] if elif_chain.elif_bodies else None}")
    print(f"  merge_block: {elif_chain.merge_block.start_offset if elif_chain.merge_block else None}")

    # Find parent IF_THEN@214
    parent_214 = None
    for r in ra.regions:
        if (isinstance(r, IfRegion)
                and r.entry is not None
                and r.entry.start_offset == 214):
            parent_214 = r
            break

    if parent_214:
        print(f"\n=== Parent IF_THEN@214 ===")
        print(f"  entry: {parent_214.entry.start_offset}")
        print(f"  then_blocks: {[b.start_offset for b in parent_214.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in parent_214.else_blocks]}")
        print(f"  merge_block: {parent_214.merge_block.start_offset if parent_214.merge_block else None}")
        print(f"  children: {[type(c).__name__ for c in getattr(parent_214, 'children', [])]}")

    # Check BoolOp regions with merge=584
    print(f"\n=== BoolOp regions with merge=584 ===")
    for r in ra.regions:
        if isinstance(r, BoolOpRegion):
            if r.merge_block and r.merge_block.start_offset == 584:
                print(f"  BoolOp merge=584 entry={r.entry.start_offset if r.entry else None}")
                print(f"    blocks: {sorted([b.start_offset for b in r.blocks])}")
                print(f"    is child of IF_THEN@214: {r in getattr(parent_214, 'children', []) if parent_214 else 'N/A'}")

    # Check get_region_for_block for key blocks
    print(f"\n=== Region ownership ===")
    for off in [286, 562, 584, 748, 824, 888]:
        b = cfg.get_block_by_offset(off)
        if b is None:
            continue
        r1 = ra.get_region_for_block(b)
        r2 = ra.get_entry_region_for_block(b)
        r1_name = f"{type(r1).__name__}@{r1.entry.start_offset}" if r1 and r1.entry else (type(r1).__name__ if r1 else "None")
        r2_name = f"{type(r2).__name__}@{r2.entry.start_offset}" if r2 and r2.entry else (type(r2).__name__ if r2 else "None")
        print(f"  block {off}: get_region_for_block={r1_name}, get_entry_region_for_block={r2_name}")

    # Check what _process_if_blocks would do with block 584
    print(f"\n=== Simulating _process_if_blocks for IF_THEN@214 ===")
    if parent_214:
        _block_set = set(parent_214.then_blocks)
        for b in sorted(_block_set, key=lambda b: b.start_offset):
            _nr = ra.get_region_for_block(b)
            if _nr is None or _nr is parent_214 or not isinstance(_nr, IfRegion) or _nr.entry is not b:
                _er = ra.get_entry_region_for_block(b)
                if isinstance(_er, IfRegion) and _er is not parent_214 and _er.entry is b:
                    _nr = _er
            if isinstance(_nr, IfRegion) and _nr is not parent_214 and _nr.entry is not None:
                if _nr.entry in _block_set and b != _nr.entry:
                    _has_cc = bool(getattr(_nr, 'chained_compare_blocks', None))
                    _has_elif = bool(getattr(_nr, 'elif_conditions', None))
                    action = "skip" if not _has_cc and not _has_elif else "NO ACTION (has_elif or has_cc)"
                    print(f"  block {b.start_offset}: nested IfRegion@{_nr.entry.start_offset} non-entry, action={action}")
                elif b == _nr.entry and _nr.entry in _block_set:
                    _has_cc = bool(getattr(_nr, 'chained_compare_blocks', None))
                    _has_elif = bool(getattr(_nr, 'elif_conditions', None))
                    if not _has_cc and not _has_elif:
                        action = "entry_skip or entry_generate"
                    else:
                        action = f"NO ACTION (has_cc={_has_cc}, has_elif={_has_elif}) <- BUG?"
                    print(f"  block {b.start_offset}: nested IfRegion@{_nr.entry.start_offset} ENTRY, action={action}")
            else:
                # Check if in child_region_blocks
                in_child = False
                for child in getattr(parent_214, 'children', []):
                    if b in child.blocks:
                        in_child = True
                        break
                print(f"  block {b.start_offset}: normal block (in_child_region={in_child})")


if __name__ == '__main__':
    main()
