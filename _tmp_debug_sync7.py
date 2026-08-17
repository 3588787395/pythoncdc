import marshal, types, sys
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.dominator_analyzer import LoopAnalyzer
from core.cfg.region_analyzer import RegionType, LoopRegion, NOISE_OPS, CONDITIONAL_JUMP_OPS, FORWARD_CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS

f = open('site-packages/IQEngine/plugins/plugin_system_simulation/live.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

def find_code(co, name):
    if hasattr(co, 'co_name') and co.co_name == name:
        return co
    for c in getattr(co, 'co_consts', []):
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r: return r
    return None

code = find_code(code, '_sync_worker')
cfg = build_cfg(code)

gen = RegionASTGenerator(cfg)
ra = gen.region_analyzer

ra.dom_analyzer.analyze()
ra.loop_analyzer = LoopAnalyzer(cfg, ra.dom_analyzer)
ra.loop_analyzer.analyze()
ra._coalesce_nop_prefix_loop_headers()
ra.dominance_frontiers = ra.dom_analyzer.compute_all_dominance_frontiers()

ra.regions = []
ra.block_to_region = {}

all_loops = ra.loop_analyzer.get_all_loops()
sorted_loops = sorted(all_loops.items(), key=lambda x: ra._get_dominance_depth(x[0]), reverse=True)

seen_bodies = set()
processed_bodies = []
regions = []

for header, _ in sorted_loops:
    has_for_iter = any(i.opname in ('FOR_ITER', 'GET_ANEXT') for i in header.instructions)
    back_edge_sources = [src for src, tgt in ra.loop_analyzer.back_edges
                        if tgt == header and ra.dom_analyzer.is_dominator(header, src)]
    if not back_edge_sources:
        if has_for_iter:
            back_edge_sources = []
        else:
            continue

    body = ra._collect_natural_loop_body(header, back_edge_sources, is_for_loop=has_for_iter)
    body_key = frozenset(body)
    if body_key in seen_bodies:
        continue
    seen_bodies.add(body_key)

    is_fake_loop = ra._is_fake_loop(header, body, back_edge_sources)
    if is_fake_loop:
        continue

    if ra._is_await_polling_loop(header, body):
        continue

    is_subset_of_existing = False
    for existing_body in processed_bodies:
        if body < existing_body:
            if not has_for_iter:
                is_subset_of_existing = True
                break
    if is_subset_of_existing:
        continue
    processed_bodies.append(body)

    loop_type, for_iter_setup, for_iter_exit, for_iter_fall_through, is_while_true, is_yield_from = \
        ra._classify_loop_type(header, body)

    if header.start_offset == 90:
        print(f"Outer loop: loop_type={loop_type}, is_while_true={is_while_true}")

    condition_block = None
    if loop_type == RegionType.WHILE_LOOP:
        for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
            if pred in body: continue
            last_instr = pred.get_last_instruction()
            if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                if last_instr.argval is not None:
                    target = ra.cfg.get_block_by_offset(last_instr.argval)
                    if target == header or target in body:
                        condition_block = pred
                        break
        if condition_block is None and not is_while_true:
            for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                if pred in body: continue
                last_instr = pred.get_last_instruction()
                if last_instr and last_instr.opname in CONDITIONAL_JUMP_OPS:
                    condition_block = pred
                    break
        if condition_block is None and not is_while_true:
            header_last = header.get_last_instruction()
            if header_last and header_last.opname in CONDITIONAL_JUMP_OPS:
                condition_block = header
        if condition_block is None and is_while_true:
            for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                if pred in body: continue
                last_instr = pred.get_last_instruction()
                if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    if last_instr.argval is not None:
                        target = ra.cfg.get_block_by_offset(last_instr.argval)
                        if target not in body and target != header:
                            condition_block = pred
                            is_while_true = False
                            break
        if condition_block is not None and is_while_true:
            cond_last = condition_block.get_last_instruction()
            if cond_last and cond_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                if cond_last.argval is not None:
                    target = ra.cfg.get_block_by_offset(cond_last.argval)
                    if target not in body and target != header:
                        is_while_true = False

    if header.start_offset == 90:
        print(f"  condition_block={'@'+str(condition_block.start_offset) if condition_block else 'None'}")
        print(f"  is_while_true={is_while_true}")

    try:
        else_blocks, natural_exit = ra._find_loop_else(header, body, loop_type, for_iter_exit, condition_block=condition_block)
        if header.start_offset == 90:
            print(f"  else_blocks={[b.start_offset for b in (else_blocks or [])]}")
            print(f"  natural_exit={'@'+str(natural_exit.start_offset) if natural_exit else 'None'}")
    except Exception as e:
        print(f"  EXCEPTION in _find_loop_else: {e}")
        continue

    else_blocks = else_blocks or []
    ra._current_loop_blocks = body
    back_edges_for_header = [src for src, tgt in ra.loop_analyzer.back_edges if tgt == header]
    if back_edges_for_header:
        _EXC_EPILOGUE_OPS = ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE', 'CHECK_EXC_MATCH', 'WITH_EXCEPT_START')
        back_edge_block = max(back_edges_for_header, key=lambda b: (
            0 if any(i.opname in _EXC_EPILOGUE_OPS for i in b.instructions) else 1,
            len([i for i in b.instructions
                 if i.opname not in NOISE_OPS
                 and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                 and i.opname not in CONDITIONAL_JUMP_OPS]),
            b.start_offset))
    else:
        back_edge_block = None

    if header.start_offset == 90:
        print(f"  back_edge_block={'@'+str(back_edge_block.start_offset) if back_edge_block else 'None'}")

    try:
        break_blocks, continue_map = ra._detect_break_continue(body, header, natural_exit, natural_back_edge=back_edge_block, condition_block=condition_block, for_iter_exit=for_iter_exit, else_blocks=else_blocks)
        if header.start_offset == 90:
            print(f"  break_blocks={[b.start_offset for b in break_blocks]}")
    except Exception as e:
        print(f"  EXCEPTION in _detect_break_continue: {e}")
        continue

    region_blocks = set(body)
    if condition_block and condition_block not in body:
        if header in condition_block.successors or any(pred in body for pred in condition_block.predecessors):
            region_blocks.add(condition_block)
    region_blocks.update(else_blocks)

    ordered_body = sorted(body, key=lambda b: b.start_offset)
    entry = condition_block or header
    region = LoopRegion(
        region_type=loop_type, entry=entry, blocks=region_blocks, header_block=header,
        is_async=any(i.opname in ('GET_ANEXT', 'GET_AITER') for i in header.instructions),
        back_edge_block=back_edge_block, is_while_true=is_while_true,
        has_break=bool(break_blocks), else_is_follow=False)
    region.body_blocks = ordered_body
    region.condition_block = condition_block
    region.else_blocks = else_blocks
    region.init_blocks = []
    region.back_edge_blocks = {back_edge_block} if back_edge_block else set()
    region.break_blocks = sorted(break_blocks, key=lambda b: b.start_offset)
    region.continue_map = continue_map

    ra.regions.append(region)
    for block in region.blocks:
        if block not in ra.block_to_region:
            ra.block_to_region[block] = region

    regions.append(region)
    if header.start_offset == 90:
        print(f"  CREATED LoopRegion: entry=@{entry.start_offset}, body={[b.start_offset for b in ordered_body]}")

print(f"\nTotal regions: {len(regions)}")
for r in regions:
    print(f"  {type(r).__name__} entry=@{r.entry.start_offset if r.entry else '?'}")
