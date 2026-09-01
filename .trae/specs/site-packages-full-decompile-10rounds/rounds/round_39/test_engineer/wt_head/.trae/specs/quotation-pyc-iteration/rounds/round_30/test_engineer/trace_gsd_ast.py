"""Trace IfRegion AST generation for get_str_data."""
import sys
import ast
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def load_code(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    for c in code_obj.co_consts:
        if isinstance(c, type(code_obj)) and c.co_name == 'get_str_data':
            return c
    return None


def main():
    co = load_code(PYC)
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()

    # Print region hierarchy
    print("=== Region hierarchy ===")
    for r in ra.regions:
        entry = getattr(r, 'entry_block', None) or getattr(r, 'condition_block', None) or getattr(r, 'header_block', None)
        eo = entry.start_offset if entry is not None else None
        if eo in (760, 762, 788, 832, 836, 838, 844):
            rtype = getattr(r, 'region_type', type(r).__name__)
            parent = getattr(r, 'parent', None)
            po = parent.entry_block.start_offset if parent and hasattr(parent, 'entry_block') and parent.entry_block else None
            children = [getattr(c, 'entry_block', None) for c in getattr(r, 'children', [])]
            co_list = [c.start_offset if c else None for c in children]
            print(f"  {rtype} entry={eo} parent={po} children={co_list}")
            # Print all attributes
            for attr in ('then_blocks', 'else_blocks', 'merge_block', 'condition_block', 'all_condition_blocks'):
                if hasattr(r, attr):
                    val = getattr(r, attr)
                    if val is not None:
                        if isinstance(val, (list, set, tuple)):
                            print(f"    {attr}={[b.start_offset for b in val]}")
                        else:
                            print(f"    {attr}={val.start_offset}")

    # Generate AST
    print()
    print("=== AST generation ===")
    gen = RegionASTGenerator(ra)
    try:
        tree = gen.generate()
        if tree:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'get_str_data':
                    print(ast.dump(node, indent=2, include_attributes=False)[:5000])
                    break
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
