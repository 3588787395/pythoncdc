"""R21 diag: why _find_try_else_blocks returns empty for handlers.pyc _target"""
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

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
t = targets[-1]

cfg = build_cfg(t)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find TryExceptRegion@254
for r in ra.regions:
    if type(r).__name__ == 'TryExceptRegion' and r.entry.start_offset == 254:
        try_region = r
        break

# Trace _find_try_else_blocks step by step
print(f'try_offset_end={try_region.try_offset_end}')
try_end_block = cfg.get_block_by_offset(try_region.try_offset_end)
print(f'try_end_block@{try_region.try_offset_end} succs={[s.start_offset for s in try_end_block.successors]}')

# Check try_end_block instructions
for i in try_end_block.instructions:
    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
        print(f'  {i.offset}: {i.opname} {i.argval}')

# Check merge_point
handler_end_offsets = []
for _, _, hblocks in try_region.except_handlers:
    if hblocks:
        last_hb = max(hblocks, key=lambda b: b.start_offset)
        if last_hb.instructions:
            eo = last_hb.instructions[-1].offset + 2
            handler_end_offsets.append(eo)

handler_end_blocks = [cfg.get_block_by_offset(o) for o in handler_end_offsets]
handler_end_blocks = [b for b in handler_end_blocks if b]
all_exit_points = {try_end_block} | set(handler_end_blocks)
merge_point = ra.dom_analyzer.find_nearest_common_post_dominator(all_exit_points)
print(f'\nmerge_point={merge_point.start_offset if merge_point else None}')
print(f'handler_end_offsets={handler_end_offsets}')
precise_handler_end = max(handler_end_offsets) if handler_end_offsets else 0
print(f'precise_handler_end={precise_handler_end}')

# Call _find_try_else_blocks directly
eb = ra._find_try_else_blocks(try_region)
print(f'\n_find_try_else_blocks -> {[b.start_offset for b in eb]}')

# Manual trace of the R21 fix logic
try_end_is_back_edge = (
    try_end_block and try_end_block.instructions and
    any(i.opname == 'JUMP_BACKWARD' for i in try_end_block.instructions)
)
print(f'\ntry_end_is_back_edge={try_end_is_back_edge}')

_te_jf_target = None
for _te_i in try_end_block.instructions:
    if _te_i.opname == 'JUMP_FORWARD':
        _te_jf_target = _te_i.argval
        break
print(f'_te_jf_target={_te_jf_target}')

all_handler_blocks = set(try_region.handler_entry_blocks)
for _, _, hb in try_region.except_handlers:
    all_handler_blocks.update(hb)

if _te_jf_target is not None and _te_jf_target > precise_handler_end:
    _te_target_block = cfg.get_block_by_offset(_te_jf_target)
    print(f'_te_target_block@{_te_target_block.start_offset if _te_target_block else None}')
    print(f'  in all_handler_blocks: {_te_target_block in all_handler_blocks}')
    print(f'  in try_region.blocks: {_te_target_block in set(try_region.blocks)}')
