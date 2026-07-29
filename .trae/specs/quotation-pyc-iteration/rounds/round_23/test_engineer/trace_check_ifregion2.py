"""R23-N4: 跟踪 check_index_code 的所有 Region（包括 IF_ELIF_CHAIN）"""
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

    print("=== 所有 Region（按 entry 排序）===")
    sorted_regions = sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0)
    for r in sorted_regions:
        rt = r.region_type.name
        cls = type(r).__name__
        print(f"\n{cls}@{r.entry.start_offset if r.entry else None} (type={rt})")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        if isinstance(r, IfRegion):
            print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks: {[b.start_offset for b in (r.then_blocks or [])]}")
            print(f"  else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}")
            print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
            print(f"  elif_conditions: {[b.start_offset for b in (r.elif_conditions or [])]}")
            print(f"  elif_bodies: {[[b.start_offset for b in body] for body in (r.elif_bodies or [])]}")
            print(f"  elif_final_else: {[b.start_offset for b in (r.elif_final_else or [])]}")

    # 找最外层 region
    print("\n=== 找最外层 Region（entry=0）===")
    for r in sorted_regions:
        if r.entry and r.entry.start_offset == 0:
            print(f"\n{type(r).__name__}@0")
            print(f"  blocks: {[b.start_offset for b in r.blocks]}")
            if isinstance(r, IfRegion):
                print(f"  elif_conditions: {[b.start_offset for b in (r.elif_conditions or [])]}")
                print(f"  elif_bodies: {[[b.start_offset for b in body] for body in (r.elif_bodies or [])]}")
                print(f"  elif_final_else: {[b.start_offset for b in (r.elif_final_else or [])]}")


if __name__ == '__main__':
    main()
