"""R21 diag: cleanup why 642/682 removed in handlers.pyc _target"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, BlockRole

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

# Check try_end_block successors
try_end_offset = 336
try_end_block = cfg.get_block_by_offset(try_end_offset)
print(f'try_end_block@{try_end_offset} succs={[s.start_offset for s in try_end_block.successors]}')
last_instr = try_end_block.get_last_instruction()
print(f'  last_instr: {last_instr.opname if last_instr else None}')

# Check each else block
for offset in [514, 642, 682]:
    b = cfg.get_block_by_offset(offset)
    role = ra.get_block_role(b)
    is_in_try_end_succs = b in try_end_block.successors
    print(f'block@{offset} role={role} in_try_end_succs={is_in_try_end_succs}')
    last = b.get_last_instruction()
    print(f'  last_instr: {last.opname if last else None}')
    print(f'  succs={[s.start_offset for s in b.successors]}')

# Now trace _cleanup
for r in ra.regions:
    if isinstance(r, TryExceptRegion) and r.entry.start_offset == 254:
        print(f'\nTryExceptRegion entry@254')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
        print(f'  try_offset_end={r.try_offset_end}')
