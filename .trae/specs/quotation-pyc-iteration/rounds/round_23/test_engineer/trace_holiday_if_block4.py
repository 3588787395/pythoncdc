"""R23-N20: 跟踪 block@342 (load_count > 5 if-condition) 的 IfRegion 创建过程"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import (
    RegionAnalyzer, IfRegion, TryExceptRegion, LoopRegion,
    BlockRole, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS,
    NOISE_OPS, CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS,
)


def main():
    from core.pyc_loader_v2 import load_pyc_file_v2
    PYC = '/workspace/quotation.pyc'
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target_co = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_holiday_online':
            target_co = const
            break

    cfg = build_cfg(target_co)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # 找到 block@342 (load_count > 5 if-condition)
    target_block = None
    for offset, blk in cfg.blocks.items():
        if blk.start_offset == 342:
            target_block = blk
            break

    if target_block is None:
        print("block@342 not found")
        sys.exit(1)

    print(f"=== block@342 信息 ===")
    print(f"  start_offset: {target_block.start_offset}")
    print(f"  conditional_successors: {[s.start_offset for s in target_block.conditional_successors]}")
    print(f"  successors: {[s.start_offset for s in target_block.successors]}")
    print(f"  predecessors: {[p.start_offset for p in target_block.predecessors]}")
    last = target_block.get_last_instruction()
    print(f"  last: {last.opname} -> {last.argval}")
    print(f"  block_to_region: {type(analyzer.block_to_region.get(target_block)).__name__}")
    print(f"  block_role: {analyzer.block_roles.get(target_block.start_offset)}")

    # 模拟 _identify_conditional_regions 的关键检查
    loop_regions = [r for r in analyzer.regions if isinstance(r, LoopRegion)]
    try_regions = [r for r in analyzer.regions if isinstance(r, TryExceptRegion)]

    print(f"\n=== 关键检查 ===")
    print(f"  loop_regions: {[r.entry.start_offset for r in loop_regions]}")
    print(f"  try_regions: {[r.entry.start_offset for r in try_regions]}")

    # 1. _should_skip_block_for_if_region
    block_region = analyzer.block_to_region.get(target_block)
    should_skip = analyzer._should_skip_block_for_if_region(target_block, block_region, loop_regions, last)
    print(f"  _should_skip_block_for_if_region: {should_skip}")

    # 2. try_cleanup_blocks 检查
    try_cleanup_blocks = set()
    for tr in try_regions:
        if hasattr(tr, 'cleanup_blocks') and tr.cleanup_blocks:
            try_cleanup_blocks.update(tr.cleanup_blocks)
    print(f"  in try_cleanup_blocks: {target_block in try_cleanup_blocks}")

    # 3. PUSH_EXC_INFO 检查
    has_exc = any(instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'PREP_RERAISE_STAR') for instr in target_block.instructions)
    print(f"  has exc instructions: {has_exc}")

    # 4. 检查条件后继
    cond_succs = list(target_block.conditional_successors)
    print(f"  cond_succs: {[s.start_offset for s in cond_succs]}")
    if len(cond_succs) == 2:
        then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)
        print(f"  then_succ: {then_succ.start_offset} (last={then_succ.get_last_instruction().opname if then_succ.get_last_instruction() else None})")
        print(f"  else_succ: {else_succ.start_offset} (last={else_succ.get_last_instruction().opname if else_succ.get_last_instruction() else None})")

        # 5. 检查 merge
        merge = analyzer._find_nearest_common_post_dominator(then_succ, else_succ)
        print(f"  merge (NCD): {merge.start_offset if merge else None}")

        # 6. 检查 sink 状态
        _then_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in then_succ.instructions) or then_succ.immediate_post_dominator is None
        _else_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in else_succ.instructions) or else_succ.immediate_post_dominator is None
        print(f"  then_sink: {_then_sink} (immediate_post_dom={then_succ.immediate_post_dominator.start_offset if then_succ.immediate_post_dominator else None})")
        print(f"  else_sink: {_else_sink} (immediate_post_dom={else_succ.immediate_post_dominator.start_offset if else_succ.immediate_post_dominator else None})")

        # 7. else_succ 的前驱
        print(f"  else_succ.predecessors: {[p.start_offset for p in else_succ.predecessors]}")
        print(f"  then_succ.predecessors: {[p.start_offset for p in then_succ.predecessors]}")

        # 8. 检查 TryExceptRegion handler_blocks
        for tr in try_regions:
            print(f"\n  TryExceptRegion entry={tr.entry.start_offset}:")
            if hasattr(tr, 'handler_entry_blocks'):
                print(f"    handler_entry_blocks: {[b.start_offset for b in tr.handler_entry_blocks]}")
            if hasattr(tr, 'except_handlers') and tr.except_handlers:
                for i, (exc_type, exc_cond, hblocks) in enumerate(tr.except_handlers):
                    print(f"    except_handler[{i}]: exc_cond={exc_cond.start_offset if hasattr(exc_cond, 'start_offset') else exc_cond}, hblocks={[b.start_offset for b in hblocks]}")
            if hasattr(tr, 'cleanup_blocks') and tr.cleanup_blocks:
                print(f"    cleanup_blocks: {[b.start_offset for b in tr.cleanup_blocks]}")
            if hasattr(tr, 'try_blocks') and tr.try_blocks:
                print(f"    try_blocks: {[b.start_offset for b in tr.try_blocks]}")
            print(f"    blocks: {[b.start_offset for b in tr.blocks]}")


if __name__ == '__main__':
    main()
