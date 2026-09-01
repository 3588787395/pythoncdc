"""R21 diag: trace _find_try_else_blocks step by step for 2nd _target."""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

def main():
    root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
    targets = [c for c in collect(root, []) if c.co_name == '_target']
    t = targets[-1]
    cfg = build_cfg(t)
    blocks_by_off = {b.start_offset: b for b in
                     (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks))}

    ra = RegionAnalyzer(cfg)
    regions = ra.analyze()
    try_region = None
    for r in regions:
        if type(r).__name__ == 'TryExceptRegion' and r.entry.start_offset == 254:
            try_region = r
            break
    if not try_region:
        print('No TryExceptRegion@254 found!')
        return

    print(f'try_region: entry={try_region.entry.start_offset}')
    print(f'  try_offset_end={try_region.try_offset_end}')
    print(f'  handler_entry_blocks={[b.start_offset for b in try_region.handler_entry_blocks]}')
    print(f'  try_blocks={[b.start_offset for b in try_region.try_blocks]}')
    print(f'  all blocks={[b.start_offset for b in try_region.blocks]}')

    # Step 1: try_end_block
    try_end_offset = try_region.try_offset_end
    try_end_block = cfg.get_block_by_offset(try_end_offset)
    print(f'\ntry_end_block@{try_end_offset}: succs={[s.start_offset for s in try_end_block.successors]}')
    print(f'  instructions: {[(i.offset,i.opname,i.argval) for i in try_end_block.instructions if i.opname not in ("RESUME","NOP","CACHE","PUSH_NULL")]}')

    # Step 2: handler_end_offsets
    handler_blocks_set = set().union(*(set(h[2]) for h in try_region.except_handlers))
    all_handler_blocks = set(try_region.handler_entry_blocks)
    for _, _, hb in try_region.except_handlers:
        all_handler_blocks.update(hb)

    handler_end_offsets = []
    for _, _, hblocks in try_region.except_handlers:
        if hblocks:
            last_hb = max(hblocks, key=lambda b: b.start_offset)
            if last_hb.instructions:
                eo = last_hb.instructions[-1].offset + 2
                if eo not in handler_end_offsets:
                    handler_end_offsets.append(eo)

    print(f'\nhandler_end_offsets={handler_end_offsets}')
    precise_handler_end = max(handler_end_offsets)
    print(f'precise_handler_end={precise_handler_end}')

    # Step 3: merge_point
    handler_end_blocks = [cfg.get_block_by_offset(o) for o in handler_end_offsets]
    handler_end_blocks = [b for b in handler_end_blocks if b]
    all_exit_points = {try_end_block} | set(handler_end_blocks)
    print(f'\nall_exit_points blocks={[b.start_offset for b in all_exit_points]}')

    merge_point = ra.dom_analyzer.find_nearest_common_post_dominator(all_exit_points)
    print(f'merge_point={merge_point.start_offset if merge_point else None}')

    # Step 4: check condition
    cond = not merge_point or merge_point.start_offset <= precise_handler_end
    print(f'\ncondition (no merge or merge <= handler_end): {cond}')

    # Step 5: alternative_merges
    try_end_is_back_edge = (
        try_end_block and try_end_block.instructions and
        any(i.opname == 'JUMP_BACKWARD' for i in try_end_block.instructions)
    )
    print(f'try_end_is_back_edge={try_end_is_back_edge}')

    alternative_merges = []
    for block in cfg.get_blocks_in_order():
        if (block.start_offset > precise_handler_end and
            block not in handler_blocks_set and
            block not in try_region.blocks):
            from_try = any(
                ra._is_reachable_from(s, block, set())
                for s in try_end_block.successors
                if s not in handler_blocks_set
            )
            from_handler = any(
                ra._is_reachable_from(hb, block, set())
                for hb in handler_end_blocks
            )
            if from_try and from_handler:
                alternative_merges.append(block)

    print(f'\nalternative_merges={[b.start_offset for b in alternative_merges]}')

    # Step 6: try_end_block successors and handler_end_block successors
    print(f'\ntry_end_block@{try_end_offset} successors:')
    for s in try_end_block.successors:
        print(f'  -> block@{s.start_offset} (in_handler={s in handler_blocks_set}, in_try={s in set(try_region.blocks)})')

    print(f'\nhandler_end_blocks successors:')
    for heb in handler_end_blocks:
        for s in heb.successors:
            print(f'  block@{heb.start_offset} -> block@{s.start_offset}')

    # Step 7: what try_end_block JUMP_FORWARD targets
    for i in try_end_block.instructions:
        if i.opname == 'JUMP_FORWARD':
            print(f'\ntry_end_block JUMP_FORWARD target={i.argval}')

    # Key insight: block@514 is the else clause, reachable from try but NOT from handler
    # handler exits via JUMP_BACKWARD to loop header (continue)
    block_514 = blocks_by_off.get(514)
    if block_514:
        print(f'\nblock@514: succs={[s.start_offset for s in block_514.successors]}')
        print(f'  in handler_blocks_set: {block_514 in handler_blocks_set}')
        print(f'  in try_region.blocks: {block_514 in set(try_region.blocks)}')
        print(f'  in all_handler_blocks: {block_514 in all_handler_blocks}')

    # Step 8: what _find_inner_else_blocks does
    try_body_blocks = getattr(try_region, 'try_blocks', [])
    handler_set = set(getattr(try_region, 'handler_entry_blocks', []))
    try_body_max_end = 0
    for tb in try_body_blocks:
        has_exc_edge = any(s in handler_set for s in tb.successors)
        is_try_entry = tb is try_region.entry or tb.start_offset == try_region.entry.start_offset
        if has_exc_edge or is_try_entry:
            for instr in tb.instructions:
                if instr.offset > try_body_max_end and instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    try_body_max_end = instr.offset
    print(f'\ntry_body_max_end={try_body_max_end}')
    print(f'first_handler_entry={min(b.start_offset for b in try_region.handler_entry_blocks)}')
    print(f'condition try_body_max_end < first_handler_entry: {try_body_max_end < min(b.start_offset for b in try_region.handler_entry_blocks)}')


if __name__ == '__main__':
    main()
