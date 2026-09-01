"""R23-N20: 调试get_holiday_online中if-else-with-raise的IfRegion结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion


def main():
    from core.pyc_loader_v2 import load_pyc_file_v2
    PYC = '/workspace/quotation.pyc'
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # 找到get_holiday_online函数
    target_co = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_holiday_online':
            target_co = const
            break

    if target_co is None:
        print("get_holiday_online not found")
        sys.exit(1)

    print(f"=== get_holiday_online 字节码 ===")
    for ins in dis.get_instructions(target_co):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        _ar = getattr(ins, 'argrepr', '')
        print(f"  {ins.offset:4d} {ins.opname:30s} {_ar}")

    print(f"\n=== 构建 CFG ===")
    cfg = build_cfg(target_co)

    print(f"\n=== CFG 块信息 ===")
    for offset, blk in sorted(cfg.blocks.items()):
        last = blk.get_last_instruction() if hasattr(blk, 'get_last_instruction') else None
        last_str = f"{last.opname} -> {last.argval}" if last else "(none)"
        succs = [s.start_offset for s in blk.successors] if hasattr(blk, 'successors') else []
        preds = [p.start_offset for p in blk.predecessors] if hasattr(blk, 'predecessors') else []
        cond_succs = [s.start_offset for s in blk.conditional_successors] if hasattr(blk, 'conditional_successors') else []
        print(f"  block@{offset:4d} (start_off={blk.start_offset}) last={last_str}  succs={succs}  cond_succs={cond_succs}  preds={preds}")

    print(f"\n=== 区域分析 ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"\n=== block_roles ===")
    if hasattr(analyzer, 'block_roles'):
        for off, role in sorted(analyzer.block_roles.items()):
            print(f"  block@{off}: {role}")
    else:
        print("  (analyzer has no block_roles attribute)")

    print(f"\n=== block_to_region ===")
    if hasattr(analyzer, 'block_to_region'):
        for blk, reg in analyzer.block_to_region.items():
            bo = blk.start_offset if hasattr(blk, 'start_offset') else blk
            rt = type(reg).__name__ if reg is not None else None
            print(f"  block@{bo}: {rt}")

    print(f"\n=== 识别的区域 ===")
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry = r.entry.start_offset if hasattr(r, 'entry') else '?'
        blocks_list = [b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else []
        merge = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
        print(f"  {rtype} entry={entry} blocks={blocks_list} merge={merge}")
        if isinstance(r, IfRegion):
            then_blocks = [b.start_offset for b in r.then_blocks] if hasattr(r, 'then_blocks') and r.then_blocks else []
            else_blocks = [b.start_offset for b in r.else_blocks] if hasattr(r, 'else_blocks') and r.else_blocks else []
            elif_conds = [b.start_offset for b in r.elif_conditions] if hasattr(r, 'elif_conditions') and r.elif_conditions else []
            elif_bodies = [[b.start_offset for b in body] if body else [] for body in r.elif_bodies] if hasattr(r, 'elif_bodies') and r.elif_bodies else []
            elif_else = [b.start_offset for b in r.elif_final_else] if hasattr(r, 'elif_final_else') and r.elif_final_else else []
            print(f"    then_blocks={then_blocks}")
            print(f"    else_blocks={else_blocks}")
            print(f"    elif_conds={elif_conds}")
            print(f"    elif_bodies={elif_bodies}")
            print(f"    elif_final_else={elif_else}")
            # 所有属性
            for attr in dir(r):
                if not attr.startswith('_') and attr not in ('blocks', 'entry', 'parent', 'merge_block', 'instructions', 'then_blocks', 'else_blocks', 'elif_conditions', 'elif_bodies', 'elif_final_else', 'successors', 'predecessors'):
                    try:
                        val = getattr(r, attr)
                        if not callable(val):
                            if isinstance(val, list) and len(val) > 0 and hasattr(val[0], 'start_offset'):
                                print(f"    {attr}: {[b.start_offset for b in val]}")
                            elif isinstance(val, (str, int, float, bool, type(None))):
                                print(f"    {attr}: {val}")
                    except:
                        pass


if __name__ == '__main__':
    main()
