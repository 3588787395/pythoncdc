import marshal, types, sys
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import LoopRegion

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

# Initialize analyzers
ra.dom_analyzer.analyze()
from core.cfg.dominator_analyzer import LoopAnalyzer
ra.loop_analyzer = LoopAnalyzer(cfg, ra.dom_analyzer)
ra.loop_analyzer.analyze()
ra._coalesce_nop_prefix_loop_headers()
ra.dominance_frontiers = ra.dom_analyzer.compute_all_dominance_frontiers()

# Call _identify_loop_regions directly
ra.regions = []
ra.block_to_region = {}
loop_regions = ra._identify_loop_regions()

print(f"loop_regions returned {len(loop_regions)} regions:")
for r in loop_regions:
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
    if hasattr(r,'condition_block') and r.condition_block:
        parts.append(f'cond={r.condition_block.start_offset}')
    if hasattr(r,'header_block') and r.header_block:
        parts.append(f'header={r.header_block.start_offset}')
    print(' '.join(parts))

print(f"\nself.regions has {len(ra.regions)} regions")
