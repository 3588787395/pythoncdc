"""Trace R30-12 fix: check if IF_ELIF_CHAIN@584 is being generated."""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, RegionType
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

    # Find IF_THEN@214
    parent_214 = None
    for r in ra.regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 214:
            parent_214 = r
            break

    if parent_214 is None:
        print("IF_THEN@214 NOT FOUND")
        return

    # Simulate _process_if_blocks logic
    gen = RegionASTGenerator(cfg, ra)
    gen.generated_blocks = set()
    gen.generated_offsets = set()
    gen._generated_regions = set()
    gen._generating_regions = set()

    _block_set = set(parent_214.then_blocks)
    _nested_if_entry_generate = {}

    print(f"=== _block_set (IF_THEN@214 then_blocks) ===")
    for b in sorted(_block_set, key=lambda b: b.start_offset):
        print(f"  block {b.start_offset}")

    print(f"\n=== Checking nested IfRegion entries ===")
    for b in _block_set:
        _nr = ra.get_region_for_block(b)
        if _nr is None or _nr is parent_214 or not isinstance(_nr, IfRegion) or _nr.entry is not b:
            _er = ra.get_entry_region_for_block(b)
            if isinstance(_er, IfRegion) and _er is not parent_214 and _er.entry is b:
                _nr = _er
        if isinstance(_nr, IfRegion) and _nr is not parent_214 and _nr.entry is not None:
            if b == _nr.entry and _nr.entry in _block_set:
                _has_cc = bool(getattr(_nr, 'chained_compare_blocks', None))
                _has_elif = bool(getattr(_nr, 'elif_conditions', None))
                print(f"  block {b.start_offset}: nested IfRegion@{_nr.entry.start_offset} ENTRY, has_cc={_has_cc}, has_elif={_has_elif}")
                if _has_elif:
                    # My fix should handle this
                    _nr_id = id(_nr)
                    _nr_blocks_in_set = all(_nb in _block_set for _nb in _nr.blocks)
                    print(f"    blocks_in_set={_nr_blocks_in_set}, blocks={sorted([bb.start_offset for bb in _nr.blocks])}")
                    if _nr_blocks_in_set:
                        _nested_if_entry_generate[b] = _nr
                        print(f"    -> ADDED to _nested_if_entry_generate")

    print(f"\n=== _nested_if_entry_generate ===")
    for b, r in _nested_if_entry_generate.items():
        print(f"  block {b.start_offset} -> IfRegion@{r.entry.start_offset}")

    # Check child_expr_regions
    child_expr_regions = {}
    if hasattr(parent_214, 'children'):
        for child in getattr(parent_214, 'children', []):
            if isinstance(child, (BoolOpRegion,)):
                if child.entry:
                    child_expr_regions[child.entry] = child

    print(f"\n=== child_expr_regions ===")
    for b, r in child_expr_regions.items():
        merge_off = r.merge_block.start_offset if r.merge_block else None
        in_nested = b in _nested_if_entry_generate
        merge_in_nested = r.merge_block in _nested_if_entry_generate if r.merge_block else False
        print(f"  block {b.start_offset}: BoolOp@{b.start_offset} merge={merge_off} merge_in_nested_generate={merge_in_nested}")

    # Now generate the full AST
    print(f"\n=== Generating full AST ===")
    gen2 = RegionASTGenerator(cfg, ra)
    ast = gen2.generate()

    # Find load_bars_from_hundsun
    for node in ast:
        if isinstance(node, dict) and node.get('type') == 'FunctionDef' and node.get('name') == 'load_bars_from_hundsun':
            import json
            body_str = json.dumps(node.get('body', []), indent=2, default=str)
            # Check if IF_ELIF_CHAIN was generated
            if 'diffset' in body_str:
                print("  diffset FOUND in AST!")
            else:
                print("  diffset NOT found in AST!")
            if 'sectionstocks' in body_str:
                print("  sectionstocks FOUND in AST!")
            else:
                print("  sectionstocks NOT found in AST!")
            # Print the if structure
            for stmt in node.get('body', []):
                if stmt.get('type') == 'If':
                    _print_if(stmt, indent=1)
            break


def _print_if(if_node, indent=0):
    prefix = '  ' * indent
    test = if_node.get('test', {})
    test_str = json.dumps(test, default=str)[:80] if test else 'None'
    print(f"{prefix}If test={test_str}")
    for s in if_node.get('body', []):
        print(f"{prefix}  body: {s.get('type', '?')}")
    orelse = if_node.get('orelse', [])
    for s in orelse:
        if s.get('type') == 'If':
            _print_if(s, indent + 1)
        else:
            print(f"{prefix}  orelse: {s.get('type', '?')}")


import json
if __name__ == '__main__':
    main()
