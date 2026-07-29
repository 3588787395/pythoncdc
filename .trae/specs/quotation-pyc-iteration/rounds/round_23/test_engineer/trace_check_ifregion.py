"""R23-N4: 跟踪 check_index_code 的 IfRegion 结构"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, RegionType, IfRegion
from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['check_index_code']

    cfg = build_cfg(co)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # 找所有 IfRegion
    print("=== 所有 IfRegion ===")
    for r in analyzer.regions:
        if isinstance(r, IfRegion):
            print(f"\nIfRegion@{r.entry.start_offset if r.entry else None}")
            print(f"  region_type: {r.region_type.name}")
            print(f"  blocks: {[b.start_offset for b in r.blocks]}")
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks: {[b.start_offset for b in (r.then_blocks or [])]}")
            print(f"  else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}")
            print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
            print(f"  elif_conditions: {[b.start_offset for b in (r.elif_conditions or [])]}")
            print(f"  elif_bodies: {[[b.start_offset for b in body] for body in (r.elif_bodies or [])]}")
            print(f"  elif_final_else: {[b.start_offset for b in (r.elif_final_else or [])]}")
            print(f"  is_empty_then_chained_compare: {getattr(r, 'is_empty_then_chained_compare', None)}")
            print(f"  children: {[c.region_type.name + '@' + str(c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")
            print(f"  parent: {r.parent_region.region_type.name if r.parent_region else None}")


if __name__ == '__main__':
    main()
