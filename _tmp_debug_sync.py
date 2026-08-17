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
print(f"Found: {code.co_name}")
cfg = build_cfg(code)
blocks = sorted(cfg.blocks.values(), key=lambda b: b.start_offset)

print(f"\n--- Blocks ({len(blocks)}) ---")
for b in blocks:
    last = b.get_last_instruction()
    last_s = f'{last.opname}({last.argval})' if last else 'none'
    print(f'@{b.start_offset}: last={last_s}')
    for ins in b.instructions:
        if ins.opname not in ('RESUME','NOP','CACHE'):
            print(f'  {ins.offset:4d} {ins.opname:28s} {ins.argval}')

gen = RegionASTGenerator(cfg)
ra = gen.region_analyzer
print(f"\n--- Regions ({len(ra.regions)}) ---")
for r in ra.regions:
    rt = type(r).__name__
    e = r.entry.start_offset if r.entry else None
    parts = [f'{rt}', f'entry={e}']
    if hasattr(r,'condition_block') and r.condition_block:
        parts.append(f'cond={r.condition_block.start_offset}')
    if hasattr(r,'then_blocks'):
        parts.append(f'then={[b.start_offset for b in r.then_blocks]}')
    if hasattr(r,'else_blocks'):
        parts.append(f'else={[b.start_offset for b in r.else_blocks]}')
    if hasattr(r,'merge_block') and r.merge_block:
        parts.append(f'merge={r.merge_block.start_offset}')
    if hasattr(r,'body_blocks'):
        parts.append(f'body={[b.start_offset for b in r.body_blocks]}')
    if hasattr(r,'header_block') and r.header_block:
        parts.append(f'header={r.header_block.start_offset}')
    if hasattr(r,'back_edge_block') and r.back_edge_block:
        parts.append(f'back_edge={r.back_edge_block.start_offset}')
    print(' '.join(parts))
