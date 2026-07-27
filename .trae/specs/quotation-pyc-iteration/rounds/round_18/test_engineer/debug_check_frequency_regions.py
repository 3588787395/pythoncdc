"""R18: 调试 check_frequency 的区域识别"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, AssertRegion, IfRegion, TryExceptRegion, LoopRegion
from core.cfg.cfg_builder import CFGBuilder


def main():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    # find check_frequency
    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'check_frequency':
            target = const
            break

    if not target:
        print("check_frequency not found")
        return

    print(f"=== check_frequency 字节码 ===")
    for ins in dis.get_instructions(target):
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

    print(f"\n=== 构建 CFG ===")
    cfg = CFGBuilder().build(target)
    ra = RegionAnalyzer(cfg, parent_code=target)
    ra.analyze()

    print(f"\n=== 区域列表 ({len(ra.regions)} 个) ===")
    for r in sorted(ra.regions, key=lambda x: x.entry.start_offset if x.entry else 0):
        entry_off = r.entry.start_offset if r.entry else None
        blocks_off = sorted(b.start_offset for b in r.blocks)
        rtype = type(r).__name__
        if isinstance(r, AssertRegion):
            cb = r.condition_block.start_offset if r.condition_block else None
            mb = r.message_block.start_offset if r.message_block else None
            print(f"  {rtype}: entry={entry_off}, blocks={blocks_off}")
            print(f"    condition_block={cb}, message_block={mb}")
        elif isinstance(r, IfRegion):
            print(f"  {rtype}: entry={entry_off}, blocks={blocks_off}")
        elif isinstance(r, TryExceptRegion):
            print(f"  {rtype}: entry={entry_off}, blocks={blocks_off}")
        else:
            print(f"  {rtype}: entry={entry_off}, blocks={blocks_off}")

    # 重点：检查 offset 252 (LOAD_FAST tmp) 的块属于哪个 region
    print(f"\n=== 检查 offset 252 块 (LOAD_FAST tmp) ===")
    blk_252 = cfg.get_block_by_offset(252)
    if blk_252:
        print(f"  block 252 instructions:")
        for ins in blk_252.instructions:
            if ins.opname not in ('CACHE',):
                print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
        print(f"  block 252 successors: {[s.start_offset for s in blk_252.successors]}")
        print(f"  block 252 conditional_successors: {[s.start_offset for s in blk_252.conditional_successors]}")
        region_252 = ra.block_to_region.get(blk_252)
        print(f"  block 252 region: {type(region_252).__name__ if region_252 else None}")
        if isinstance(region_252, AssertRegion):
            print(f"    condition_block={region_252.condition_block.start_offset}, message_block={region_252.message_block.start_offset if region_252.message_block else None}")
    else:
        print("  block 252 not found")

    # 检查 offset 262 (LOAD_ASSERTION_ERROR)
    print(f"\n=== 检查 offset 262 块 (LOAD_ASSERTION_ERROR) ===")
    blk_262 = cfg.get_block_by_offset(262)
    if blk_262:
        print(f"  block 262 instructions:")
        for ins in blk_262.instructions:
            if ins.opname not in ('CACHE',):
                print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
        region_262 = ra.block_to_region.get(blk_262)
        print(f"  block 262 region: {type(region_262).__name__ if region_262 else None}")


if __name__ == '__main__':
    main()
