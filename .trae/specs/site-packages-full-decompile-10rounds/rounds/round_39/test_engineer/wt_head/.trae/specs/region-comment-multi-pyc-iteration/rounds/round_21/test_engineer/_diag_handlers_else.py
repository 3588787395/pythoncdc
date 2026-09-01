"""R21 diag: handlers.pyc _target (stream) else blocks"""
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

# Focus on TryExceptRegion@254
for r in ra.regions:
    if type(r).__name__ == 'TryExceptRegion' and r.entry.start_offset == 254:
        print(f'TryExceptRegion entry@{r.entry.start_offset}')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
        print(f'  has_else={getattr(r, "has_else", None)}')
        for b in getattr(r, "else_blocks", []):
            role = ra.get_block_role(b)
            ops = [(i.offset, i.opname, getattr(i, 'argval', '')) for i in b.instructions
                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')]
            print(f'  else block@{b.start_offset} role={role}: {ops[:8]}')
            print(f'    succs={[s.start_offset for s in b.successors]}')

        print(f'\n  all blocks={[b.start_offset for b in r.blocks]}')
        print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')
        for exc, name, hb in r.except_handlers:
            print(f'  handler exc={exc} blocks={[b.start_offset for b in hb]}')
            for b in hb:
                role = ra.get_block_role(b)
                print(f'    handler block@{b.start_offset} role={role}')

# Also check the LoopRegion
for r in ra.regions:
    if type(r).__name__ == 'LoopRegion':
        print(f'\nLoopRegion entry@{r.entry.start_offset}')
        print(f'  body_blocks={[b.start_offset for b in getattr(r, "body_blocks", [])]}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')

# Check what region owns block@682
b682 = cfg.get_block_by_offset(682)
if b682:
    owner = ra.block_to_region.get(b682)
    print(f'\nblock@682 owner={type(owner).__name__ if owner else None} entry@{owner.entry.start_offset if owner else None}')
    entry_region = ra.get_entry_region_for_block(b682)
    print(f'block@682 entry_region={type(entry_region).__name__ if entry_region else None}')
