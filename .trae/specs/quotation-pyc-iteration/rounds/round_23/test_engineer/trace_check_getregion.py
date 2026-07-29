"""R23-N4: 跟踪 check_index_code 的 get_region_for_block"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, RegionType, IfRegion, BoolOpRegion, TernaryRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion
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

    # 找最外层 IfRegion
    outer = None
    for r in analyzer.regions:
        if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
            outer = r
            break

    print(f"=== 外层 IfRegion@0 ===")
    print(f"  elif_final_else: {[b.start_offset for b in (outer.elif_final_else or [])]}")
    print(f"  children: {[c.region_type.name + '@' + str(c.entry.start_offset if c.entry else None) for c in (outer.children or [])]}")

    # 对每个 elif_final_else 块，看 get_region_for_block 返回什么
    print(f"\n=== get_region_for_block for elif_final_else blocks ===")
    for b in outer.elif_final_else:
        r = analyzer.get_region_for_block(b)
        print(f"  block@{b.start_offset}: region = {type(r).__name__}@{r.entry.start_offset if r and r.entry else None} (type={r.region_type.name if r else None})")

    # 对所有 blocks
    print(f"\n=== get_region_for_block for all blocks ===")
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        r = analyzer.get_region_for_block(b)
        print(f"  block@{b.start_offset}: region = {type(r).__name__}@{r.entry.start_offset if r and r.entry else None} (type={r.region_type.name if r else None})")


if __name__ == '__main__':
    main()
