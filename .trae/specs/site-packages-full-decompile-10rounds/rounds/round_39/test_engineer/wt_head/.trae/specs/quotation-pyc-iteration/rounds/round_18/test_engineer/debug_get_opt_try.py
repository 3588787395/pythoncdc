"""R18: 调试 get_opt_objects 的 TryExceptRegion 详细结构"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.region_analyzer import RegionAnalyzer, AssertRegion, IfRegion, TryExceptRegion, LoopRegion, BoolOpRegion
from core.cfg.cfg_builder import CFGBuilder


def main():
    module = load_pyc_file_v2('/workspace/quotation.pyc')
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_opt_objects':
            target = const
            break

    if not target:
        print("get_opt_objects not found")
        return

    cfg = CFGBuilder().build(target)
    ra = RegionAnalyzer(cfg, parent_code=target)
    ra.analyze()

    print(f"=== TryExceptRegion 详细结构 ===")
    for r in ra.regions:
        if isinstance(r, TryExceptRegion):
            print(f"  entry={r.entry.start_offset}")
            print(f"  blocks={[b.start_offset for b in r.blocks]}")
            print(f"  try_blocks={[b.start_offset for b in r.try_blocks] if r.try_blocks else []}")
            print(f"  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks] if r.handler_entry_blocks else []}")
            print(f"  except_handlers={r.except_handlers}")
            print(f"  has_else={r.has_else}")
            print(f"  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
            print(f"  has_finally={r.has_finally}")
            print(f"  finally_blocks={[b.start_offset for b in r.finally_blocks] if r.finally_blocks else []}")
            print(f"  try_offset_end={r.try_offset_end}")
            print(f"  cleanup_blocks={[b.start_offset for b in r.cleanup_blocks] if r.cleanup_blocks else []}")
            print(f"  children={[type(c).__name__ + f'({c.entry.start_offset})' for c in (r.children or [])]}")

    print(f"\n=== IfRegion 详细结构 ===")
    for r in ra.regions:
        if isinstance(r, IfRegion):
            print(f"  entry={r.entry.start_offset}")
            print(f"  blocks={[b.start_offset for b in r.blocks]}")
            print(f"  condition_block={r.condition_block.start_offset if r.condition_block else None}")
            print(f"  then_blocks={[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
            print(f"  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
            print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
            print(f"  children={[type(c).__name__ + f'({c.entry.start_offset})' for c in (r.children or [])]}")

    print(f"\n=== BoolOpRegion 详细结构 ===")
    for r in ra.regions:
        if isinstance(r, BoolOpRegion):
            print(f"  entry={r.entry.start_offset}")
            print(f"  blocks={[b.start_offset for b in r.blocks]}")
            print(f"  op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
            print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")

    # 重点：检查 block 270 (if body: strategy_log.error + return [])
    print(f"\n=== 检查 block 270 (if body) ===")
    blk_270 = cfg.get_block_by_offset(270)
    if blk_270:
        print(f"  instructions:")
        for ins in blk_270.instructions:
            if ins.opname != 'CACHE':
                print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
        print(f"  successors: {[s.start_offset for s in blk_270.successors]}")
        region_270 = ra.block_to_region.get(blk_270)
        print(f"  block_to_region: {type(region_270).__name__ if region_270 else None}")
        entry_region_270 = ra.get_entry_region_for_block(blk_270)
        print(f"  get_entry_region_for_block: {type(entry_region_270).__name__ if entry_region_270 else None}")

    # 检查 block 314 (after if: get_trade_days + return)
    print(f"\n=== 检查 block 314 (after if) ===")
    blk_314 = cfg.get_block_by_offset(314)
    if blk_314:
        print(f"  instructions:")
        for ins in blk_314.instructions:
            if ins.opname != 'CACHE':
                print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
        print(f"  successors: {[s.start_offset for s in blk_314.successors]}")
        region_314 = ra.block_to_region.get(blk_314)
        print(f"  block_to_region: {type(region_314).__name__ if region_314 else None}")


if __name__ == '__main__':
    main()
