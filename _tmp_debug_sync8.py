import marshal, types
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
gen.regions = gen.region_analyzer.analyze()
ra = gen.region_analyzer

print(f'Regions: {len(ra.regions)}')
for r in ra.regions:
    rt = type(r).__name__
    e = r.entry.start_offset if r.entry else None
    parts = [f'{rt}', f'entry={e}']
    if hasattr(r,'body_blocks'):
        parts.append(f'body={[b.start_offset for b in r.body_blocks]}')
    if hasattr(r,'blocks'):
        parts.append(f'blocks={sorted(b.start_offset for b in r.blocks)}')
    if hasattr(r,'is_while_true'):
        parts.append(f'while_true={r.is_while_true}')
    if hasattr(r,'condition_block') and r.condition_block:
        parts.append(f'cond={r.condition_block.start_offset}')
    print(' '.join(parts))
