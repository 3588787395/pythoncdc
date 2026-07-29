"""R23-N4: 调试 get_str_data 的区域层级和 for_iter_setup 元数据"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion, RegionType

PYC = '/workspace/quotation.pyc'


def load_code():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    return code_obj


def find_func(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_func(c, name)
            if r:
                return r
    return None


def dump_region_tree(region, depth=0, max_depth=10):
    """递归打印区域树"""
    if depth > max_depth:
        return
    indent = '  ' * depth
    rtype = type(region).__name__
    rt = region.region_type.name if hasattr(region, 'region_type') and region.region_type else 'None'
    entry = region.entry.start_offset if hasattr(region, 'entry') and region.entry else '?'
    header = region.header_block.start_offset if hasattr(region, 'header_block') and region.header_block else None
    fis = region.metadata.get('for_iter_setup') if hasattr(region, 'metadata') else None
    fis_off = fis.start_offset if fis else None
    blocks = [b.start_offset for b in region.blocks] if hasattr(region, 'blocks') else []
    print(f"{indent}{rtype}({rt}) entry={entry} header={header} fis={fis_off} blocks={blocks[:8]}{'...' if len(blocks)>8 else ''} (total={len(blocks)})")
    fis_marker = ''
    if hasattr(region, 'metadata'):
        for k, v in region.metadata.items():
            if k != 'for_iter_setup' and v is not None:
                if isinstance(v, list):
                    v_short = [getattr(x, 'start_offset', x) for x in v[:3]]
                    print(f"{indent}  meta.{k}={v_short}{'...' if len(v)>3 else ''}")
                elif not isinstance(v, (str, int, bool, type(None))):
                    v_short = getattr(v, 'start_offset', repr(v)[:50])
                    print(f"{indent}  meta.{k}={v_short}")
    for child in (region.children or []):
        dump_region_tree(child, depth + 1, max_depth)


def main():
    code_obj = load_code()
    func = find_func(code_obj, 'get_str_data')
    if not func:
        print("未找到 get_str_data")
        return
    print(f"找到 get_str_data, argcount={func.co_argcount}")

    cfg = build_cfg(func)
    print(f"CFG: {len(cfg.blocks)} blocks")

    # 打印所有块
    print("\n=== 所有基本块 ===")
    for offset, block in sorted(cfg.blocks.items()):
        instrs = [(i.opname, i.argval) for i in block.instructions]
        print(f"  block@{offset}: {instrs[:5]}{'...' if len(instrs)>5 else ''} (total={len(instrs)})")

    # 获取区域分析器
    gen = RegionASTGenerator(cfg, top_level_code=None)
    # 必须先调用 generate() 才能初始化 regions
    _ = gen.generate()
    analyzer = gen.region_analyzer
    regions = gen.regions
    print(f"\n=== 顶层区域 ({len(regions)}) ===")
    for r in regions:
        dump_region_tree(r, 0, 5)

    # 重点查找包含 offset 588 (for_iter_setup of inner for) 的区域
    print("\n=== 查找 offset 588 的归属 ===")
    target_block = cfg.blocks.get(588)
    if target_block:
        print(f"block@588 存在, instrs={[(i.opname, i.argval) for i in target_block.instructions]}")
    else:
        # 找到包含 offset 588 的块
        for off, blk in sorted(cfg.blocks.items()):
            last_off = blk.instructions[-1].offset if blk.instructions else off
            if off <= 588 <= last_off:
                target_block = blk
                print(f"block@{off} (last={last_off}) 包含 offset 588, instrs={[(i.opname, i.argval) for i in blk.instructions]}")
                break

    if target_block:
        # 找到所有包含该块的区域
        def find_regions_containing(regions_list, block):
            result = []
            for r in regions_list:
                if block in r.blocks:
                    result.append(r)
                if hasattr(r, 'children') and r.children:
                    result.extend(find_regions_containing(r.children, block))
            return result

        containing = find_regions_containing(regions, target_block)
        print(f"\n  包含 block@{target_block.start_offset} 的区域 ({len(containing)}):")
        for r in containing:
            rtype = type(r).__name__
            rt = r.region_type.name if r.region_type else 'None'
            entry = r.entry.start_offset if hasattr(r, 'entry') and r.entry else '?'
            header = r.header_block.start_offset if hasattr(r, 'header_block') and r.header_block else None
            fis = r.metadata.get('for_iter_setup') if hasattr(r, 'metadata') else None
            fis_off = fis.start_offset if fis else None
            print(f"    {rtype}({rt}) entry={entry} header={header} fis={fis_off}")
            if isinstance(r, LoopRegion):
                fis = r.metadata.get('for_iter_setup')
                if fis is target_block:
                    print(f"      ** block@{target_block.start_offset} 是 LoopRegion 的 for_iter_setup **")
            else:
                print(f"      (不是 LoopRegion, 不会跳过 for_iter_setup)")


if __name__ == '__main__':
    main()
