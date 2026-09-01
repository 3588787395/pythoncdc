#!/usr/bin/env python3
"""R13 诊断：定位 LoopRegion@1222 后向遍历吸收了哪些 predecessor (p)。

聚焦：while count > 0: 循环的 condition_block (_cb) 是谁？哪个 p 满足
p_target == _cb 而被误吸收（应该是外层 if 的条件块 692，跳到 _cb 是
"条件为假时 fall-through 到循环"）？
"""
import sys
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion, BoolOpRegion

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'get_date_and_count':
            target = const
            break

    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # Find LoopRegion@1222
    loop = None
    for r in analyzer.regions:
        if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 1222:
            loop = r
            break

    if loop is None:
        print("LoopRegion@1222 not found")
        return

    print(f"=== LoopRegion@{loop.entry.start_offset} ===")
    print(f"  header_block = {loop.header_block.start_offset if loop.header_block else None}")
    print(f"  condition_block = {loop.condition_block.start_offset if loop.condition_block else None}")
    print(f"  back_edge_block = {loop.back_edge_block.start_offset if loop.back_edge_block else None}")
    print(f"  body_blocks = {sorted([b.start_offset for b in loop.body_blocks])}")
    print(f"  region.blocks = {sorted([b.start_offset for b in loop.blocks])}")
    print(f"  else_blocks = {sorted([b.start_offset for b in (loop.else_blocks or [])])}")
    print(f"  break_blocks = {sorted([b.start_offset for b in (loop.break_blocks or [])])}")

    # Trace the backward walk: who are the predecessors of condition_block?
    cb = loop.condition_block
    if cb is None:
        print("  no condition_block — skip walk trace")
        return
    print(f"\n--- Backward walk from condition_block @{cb.start_offset} ---")
    body_set = set(loop.body_blocks)
    region_set = set(loop.blocks)
    visited = set()
    step = 0
    while cb is not None and step < 20:
        step += 1
        if cb.start_offset in visited:
            print(f"  step{step}: _cb@{cb.start_offset} (visited, stop)")
            break
        visited.add(cb.start_offset)
        preds = [p for p in cb.predecessors
                 if p not in body_set and p not in region_set
                 and p != loop.header_block]
        print(f"  step{step}: _cb@{cb.start_offset} preds={[p.start_offset for p in preds]}")
        from core.cfg.region_analyzer import FORWARD_CONDITIONAL_JUMP_OPS
        next_cb = None
        for p in preds:
            p_last = p.get_last_instruction()
            if p_last and p_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                if p_last.argval is not None:
                    p_target = cfg.get_block_by_offset(p_last.argval)
                    p_target_off = p_target.start_offset if p_target else None
                    cb_off = cb.start_offset
                    in_body = p_target in body_set if p_target else False
                    is_header = p_target == loop.header_block if p_target else False
                    is_cb = p_target_off == cb_off
                    print(f"    p@{p.start_offset}: last={p_last.opname} target={p_target_off} "
                          f"(==_cb?{is_cb} in_body?{in_body} ==header?{is_header})")
                    # show p's instructions
                    instrs = [(i.opname, getattr(i, 'argval', None)) for i in p.instructions]
                    print(f"      p@{p.start_offset} instrs={instrs}")
                    if is_cb or in_body or is_header:
                        print(f"      -> ABSORBED via p_target == _cb branch (or in_body/header)")
                        if p not in loop.header_block.predecessors if loop.header_block else True:
                            pass
                        # check back-edge to p
                        has_be = any(
                            be.get_last_instruction() is not None and
                            be.get_last_instruction().opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') and
                            be.get_last_instruction().argval == p.start_offset
                            for be in body_set
                        )
                        print(f"      has_back_edge_to_p?{has_be}")
                        if not has_be:
                            next_cb = p
        cb = next_cb

    # Also: what is the IfRegion@692 and what is its parent?
    print(f"\n--- IfRegion@692 / BoolOpRegion@1202 / IfRegion@678 ---")
    for r in analyzer.regions:
        if r.entry and r.entry.start_offset in (692, 1202, 678, 1314):
            rtype = type(r).__name__
            parent_off = (r.parent.entry.start_offset if (r.parent and r.parent.entry) else None)
            print(f"  {rtype}@{r.entry.start_offset} parent={parent_off} "
                  f"blocks={sorted([b.start_offset for b in r.blocks]) if hasattr(r, 'blocks') else []}")

    # What is at offset 692? Show its instructions + jump target
    print(f"\n--- Block@692 instructions (the if len(...)==0 condition) ---")
    b692 = cfg.get_block_by_offset(692)
    if b692:
        for i in b692.instructions:
            print(f"  {i.offset:>4} {i.opname:<28} argval={getattr(i, 'argval', None)}")
        print(f"  successors: {[s.start_offset for s in b692.successors]}")
        print(f"  last instr jumps to: {b692.get_last_instruction().argval if b692.get_last_instruction() else None}")

    # What is at offset 1202? (BoolOpRegion entry — the elif count == 1 and count > 0)
    print(f"\n--- Block@1202 instructions (elif count == 1 condition) ---")
    b1202 = cfg.get_block_by_offset(1202)
    if b1202:
        for i in b1202.instructions:
            print(f"  {i.offset:>4} {i.opname:<28} argval={getattr(i, 'argval', None)}")
        print(f"  successors: {[s.start_offset for s in b1202.successors]}")
        print(f"  last instr jumps to: {b1202.get_last_instruction().argval if b1202.get_last_instruction() else None}")

    # What is at offset 1222? (loop header / else block start)
    print(f"\n--- Block@1222 instructions (while loop region entry) ---")
    b1222 = cfg.get_block_by_offset(1222)
    if b1222:
        for i in b1222.instructions:
            print(f"  {i.offset:>4} {i.opname:<28} argval={getattr(i, 'argval', None)}")
        print(f"  successors: {[s.start_offset for s in b1222.successors]}")
        print(f"  predecessors: {[p.start_offset for p in b1222.predecessors]}")


if __name__ == '__main__':
    main()
