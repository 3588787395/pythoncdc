import marshal, types, sys
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

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
ra.analyze()

blocks = {b.start_offset: b for b in cfg.blocks.values()}

all_loops = ra.loop_analyzer.get_all_loops()
sorted_loops = sorted(all_loops.items(), key=lambda x: ra._get_dominance_depth(x[0]), reverse=True)

seen_bodies = set()
processed_bodies = []

for header, _ in sorted_loops:
    has_for_iter = any(i.opname in ('FOR_ITER', 'GET_ANEXT') for i in header.instructions)
    back_edge_sources = [src for src, tgt in ra.loop_analyzer.back_edges
                        if tgt == header and ra.dom_analyzer.is_dominator(header, src)]
    if not back_edge_sources:
        if has_for_iter:
            back_edge_sources = []
        else:
            print(f"@{header.start_offset}: no back edge sources, skipping")
            continue

    body = ra._collect_natural_loop_body(header, back_edge_sources, is_for_loop=has_for_iter)
    body_key = frozenset(body)
    
    print(f"\nProcessing header=@{header.start_offset}")
    print(f"  body={[b.start_offset for b in body]}")
    print(f"  body_key in seen_bodies: {body_key in seen_bodies}")
    
    if body_key in seen_bodies:
        print("  SKIPPED: body already seen")
        continue
    seen_bodies.add(body_key)

    is_fake_loop = ra._is_fake_loop(header, body, back_edge_sources)
    print(f"  is_fake_loop: {is_fake_loop}")
    if is_fake_loop:
        print("  SKIPPED: fake loop")
        continue

    is_await = ra._is_await_polling_loop(header, body)
    print(f"  is_await_polling: {is_await}")
    if is_await:
        print("  SKIPPED: await polling")
        continue

    is_subset = False
    for existing_body in processed_bodies:
        if body < existing_body:
            if not has_for_iter:
                is_subset = True
                break
    print(f"  is_subset_of_existing: {is_subset}")
    if is_subset:
        print("  SKIPPED: subset of existing")
        continue
    processed_bodies.append(body)
    print("  ACCEPTED")
