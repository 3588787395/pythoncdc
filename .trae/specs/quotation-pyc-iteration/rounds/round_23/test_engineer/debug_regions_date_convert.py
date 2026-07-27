"""R23-N6: 分析 date_convert 的区域结构"""
import sys
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import (
    IfRegion, LoopRegion, TryExceptRegion, BoolOpRegion,
    TernaryRegion, WithRegion
)


def load_code():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            r = find_func(const, name)
            if r:
                return r
    return None


def dump_region_tree(region, depth=0, max_depth=10):
    if depth > max_depth:
        return
    indent = '  ' * depth
    rtype = type(region).__name__
    blocks = list(region.blocks) if hasattr(region, 'blocks') else []
    block_ids = [getattr(b, 'id', '?') for b in blocks[:5]]
    extra = ''
    if hasattr(region, 'merge_block') and region.merge_block:
        extra += f' merge={region.merge_block.id}'
    if hasattr(region, 'then_blocks') and region.then_blocks:
        extra += f' then={len(region.then_blocks)}'
    if hasattr(region, 'else_blocks') and region.else_blocks:
        extra += f' else={len(region.else_blocks)}'
    if hasattr(region, 'header_block') and region.header_block:
        extra += f' header={region.header_block.id}'
    if hasattr(region, 'metadata') and region.metadata:
        keys = list(region.metadata.keys())
        if keys:
            extra += f' meta={keys[:5]}'
    print(f"{indent}{rtype} blocks={block_ids}{extra}")
    if hasattr(region, 'children') and region.children:
        for c in region.children:
            dump_region_tree(c, depth + 1, max_depth)
    if hasattr(region, 'subregions') and region.subregions:
        for c in region.subregions:
            dump_region_tree(c, depth + 1, max_depth)
    if hasattr(region, 'then_regions') and region.then_regions:
        for c in region.then_regions:
            dump_region_tree(c, depth + 1, max_depth)
    if hasattr(region, 'else_regions') and region.else_regions:
        for c in region.else_regions:
            dump_region_tree(c, depth + 1, max_depth)


def main():
    code_obj = load_code()
    func = find_func(code_obj, 'date_convert')
    if not func:
        print("未找到 date_convert")
        return
    print(f"找到 date_convert, argcount={func.co_argcount}")

    cfg = build_cfg(func)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    _ = gen.generate()
    regions = gen.regions
    print(f"\n=== 顶层区域 ({len(regions)}) ===")
    for r in regions:
        dump_region_tree(r, 0, 5)

    # 打印CFG基本信息
    print(f"\n=== CFG blocks ({len(cfg.blocks)}) ===")
    for b in cfg.blocks:
        ins_str = ', '.join(f"{i.opname}" for i in b.instructions[:3])
        succs = [s.id for s in b.successors]
        print(f"  B{b.id} [{ins_str}...] succs={succs}")


if __name__ == '__main__':
    main()
