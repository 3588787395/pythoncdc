"""R23-N21: 调试get_price函数的区域分析"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import (
    RegionAnalyzer, IfRegion, BoolOpRegion, LoopRegion, TryExceptRegion,
)


def main():
    pyc_path = '/workspace/quotation.pyc'
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # 找到 get_price 函数
    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_price':
            target = const
            break
    if target is None:
        print("get_price not found")
        return

    print(f"=== get_price 字节码 ===")
    for ins in dis.get_instructions(target):
        if ins.opname not in ('EXTENDED_ARG', 'CACHE'):
            print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argrepr}")

    print(f"\n=== 构建 CFG ===")
    builder = CFGBuilder()
    cfg = builder.build(target)

    print(f"\n=== CFG 块 ===")
    for off in sorted(cfg.blocks.keys()):
        b = cfg.blocks[off]
        last = b.get_last_instruction()
        last_str = f"{last.opname}->{last.argval}" if last else "None"
        succs = [s.start_offset for s in b.successors]
        print(f"  block@{off}: last={last_str}, succs={succs}")

    print(f"\n=== 区域分析 ===")
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    print(f"\n=== 区域列表 ===")
    for r in analyzer.regions:
        rtype = type(r).__name__
        entry = r.entry.start_offset if r.entry else None
        if isinstance(r, IfRegion):
            merge = r.merge_block.start_offset if r.merge_block else None
            print(f"  {rtype} entry={entry} merge={merge}")
            print(f"    then_blocks: {[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
            if r.elif_conditions:
                print(f"    elif_conditions: {len(r.elif_conditions)}")
            if r.elif_bodies:
                print(f"    elif_bodies: {[[bb.start_offset for bb in eb] for eb in r.elif_bodies]}")
            if r.elif_final_else:
                print(f"    elif_final_else: {[b.start_offset for b in r.elif_final_else]}")
        elif isinstance(r, BoolOpRegion):
            print(f"  {rtype} entry={entry}")
            print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
            print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")
            print(f"    body_block: {r.body_block.start_offset if r.body_block else None}")
        else:
            print(f"  {rtype} entry={entry}")


if __name__ == '__main__':
    main()
