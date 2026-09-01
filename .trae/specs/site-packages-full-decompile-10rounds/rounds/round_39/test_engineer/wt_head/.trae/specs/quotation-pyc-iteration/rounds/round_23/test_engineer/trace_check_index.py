"""R23-N4: 跟踪 check_index_code 的区域分析"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, RegionType
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

    print("\n=== CFG ===")
    cfg = build_cfg(co)
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        print(f"  Block@{b.start_offset}-{b.end_offset}")
        for ins in b.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE'):
                continue
            print(f"    {ins.offset:4d}  {ins.opname:30s} argval={ins.argval!r}")
        print(f"    succ: {[s.start_offset for s in b.successors]}")
        print(f"    pred: {[p.start_offset for p in b.predecessors]}")

    print("\n=== 区域分析 ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    print(f"区域数: {len(analyzer.regions)}")
    for r in analyzer.regions:
        print(f"\n  Region: type={r.region_type.name}, entry={r.entry.start_offset if r.entry else None}")
        print(f"    blocks: {[b.start_offset for b in r.blocks]}")
        print(f"    metadata: {r.metadata}")
        if hasattr(r, 'then_blocks') and r.then_blocks:
            print(f"    then: {[b.start_offset for b in r.then_blocks]}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            print(f"    else: {[b.start_offset for b in r.else_blocks]}")
        if hasattr(r, 'header_block') and r.header_block:
            print(f"    header: {r.header_block.start_offset}")
        if hasattr(r, 'body_blocks') and r.body_blocks:
            print(f"    body: {[b.start_offset for b in r.body_blocks]}")
        if hasattr(r, 'exit_block') and r.exit_block:
            print(f"    exit: {r.exit_block.start_offset}")
        # 父区域
        if hasattr(r, 'parent_region') and r.parent_region:
            print(f"    parent: {r.parent_region.region_type.name}@{r.parent_region.entry.start_offset if r.parent_region.entry else None}")


if __name__ == '__main__':
    main()
