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
ra.analyze()  # Force analysis

all_loops = ra.loop_analyzer.get_all_loops()
print(f"LoopAnalyzer found {len(all_loops)} loops:")
for header, body in all_loops.items():
    body_offsets = sorted(b.start_offset for b in body)
    print(f"  header=@{header.start_offset} body={body_offsets}")

print(f"\nBack edges:")
for src, tgt in ra.loop_analyzer.back_edges:
    print(f"  @{src.start_offset} -> @{tgt.start_offset}")

blocks = {b.start_offset: b for b in cfg.blocks.values()}
b90 = blocks.get(90)
b324 = blocks.get(324)
if b90 and b324:
    is_dom = ra.dom_analyzer.is_dominator(b90, b324)
    print(f"\nDoes @90 dominate @324? {is_dom}")

for header in all_loops:
    depth = ra._get_dominance_depth(header)
    print(f"  Dominance depth of @{header.start_offset}: {depth}")

print(f"\nRegions after analyze: {len(ra.regions)}")
for r in ra.regions:
    rt = type(r).__name__
    e = r.entry.start_offset if r.entry else None
    parts = [f'{rt}', f'entry={e}']
    if hasattr(r,'body_blocks'):
        parts.append(f'body={[b.start_offset for b in r.body_blocks]}')
    if hasattr(r,'else_blocks'):
        parts.append(f'else={[b.start_offset for b in r.else_blocks]}')
    if hasattr(r,'is_while_true'):
        parts.append(f'while_true={r.is_while_true}')
    if hasattr(r,'back_edge_block') and r.back_edge_block:
        parts.append(f'back_edge={r.back_edge_block.start_offset}')
    print(' '.join(parts))
