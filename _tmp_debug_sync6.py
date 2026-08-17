import marshal, types, sys
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.dominator_analyzer import LoopAnalyzer

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

# Initialize like analyze() does
ra.dom_analyzer.analyze()
ra.loop_analyzer = LoopAnalyzer(cfg, ra.dom_analyzer)
ra.loop_analyzer.analyze()
ra._coalesce_nop_prefix_loop_headers()
ra.dominance_frontiers = ra.dom_analyzer.compute_all_dominance_frontiers()

# Check the loops
all_loops = ra.loop_analyzer.get_all_loops()
print(f"all_loops has {len(all_loops)} entries")
for header in all_loops:
    body = all_loops[header]
    print(f"  header=@{header.start_offset} body={[b.start_offset for b in body]}")

sorted_loops = sorted(all_loops.items(), key=lambda x: ra._get_dominance_depth(x[0]), reverse=True)
print(f"\nsorted_loops has {len(sorted_loops)} entries")
for header, body in sorted_loops:
    depth = ra._get_dominance_depth(header)
    print(f"  header=@{header.start_offset} depth={depth}")

# Now manually trace the loop identification
ra.regions = []
ra.block_to_region = {}
seen_bodies = set()
processed_bodies = []
regions = []

for header, _ in sorted_loops:
    has_for_iter = any(i.opname in ('FOR_ITER', 'GET_ANEXT') for i in header.instructions)
    back_edge_sources = [src for src, tgt in ra.loop_analyzer.back_edges
                        if tgt == header and ra.dom_analyzer.is_dominator(header, src)]
    print(f"\nProcessing header=@{header.start_offset}")
    print(f"  back_edge_sources={[s.start_offset for s in back_edge_sources]}")
    if not back_edge_sources:
        if has_for_iter:
            back_edge_sources = []
        else:
            print("  SKIP: no back edge sources")
            continue

    body = ra._collect_natural_loop_body(header, back_edge_sources, is_for_loop=has_for_iter)
    body_key = frozenset(body)
    print(f"  body={[b.start_offset for b in body]}")

    if body_key in seen_bodies:
        print("  SKIP: body already seen")
        continue
    seen_bodies.add(body_key)

    is_fake = ra._is_fake_loop(header, body, back_edge_sources)
    if is_fake:
        print("  SKIP: fake loop")
        continue

    is_await = ra._is_await_polling_loop(header, body)
    if is_await:
        print("  SKIP: await polling")
        continue

    is_subset = False
    for eb in processed_bodies:
        if body < eb:
            if not has_for_iter:
                is_subset = True
                break
    if is_subset:
        print("  SKIP: subset")
        continue
    processed_bodies.append(body)
    print("  ACCEPTED - proceeding to classify")

    loop_type, for_iter_setup, for_iter_exit, for_iter_fall_through, is_while_true, is_yield_from = \
        ra._classify_loop_type(header, body)
    print(f"  loop_type={loop_type}, is_while_true={is_while_true}")

    # Check condition_block search
    condition_block = None
    if loop_type is not None and hasattr(ra, '_BODY_CODE_OPS'):
        # Check what _BODY_CODE_OPS contains
        pass

    # Simplified: just check if we get to the end
    print(f"  -> Would create LoopRegion")
