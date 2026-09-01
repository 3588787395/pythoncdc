"""R22: detailed get_str_data block layout and region ownership"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

PYC = r'f:/Downloads/pythoncdc-main/site-packages/fly/data/quotation.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

for c in collect(root, []):
    if c.co_name == 'get_str_data':
        code = c
        break

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Show all blocks with roles
blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)
print(f'=== Blocks ({len(blocks)}) ===')
for b in blocks:
    role = ra.get_block_role(b)
    owner = ra.block_to_region.get(b)
    owner_type = type(owner).__name__ if owner else 'UNOWNED'
    owner_entry = owner.entry.start_offset if owner and hasattr(owner, 'entry') else '?'
    last_i = b.get_last_instruction()
    last_op = last_i.opname if last_i else 'NONE'
    succs = sorted(s.start_offset for s in b.successors)
    print(f'  @{b.start_offset:4d} role={str(role):20s} owner={owner_type}@{owner_entry} last={last_op:30s} succs={succs}')

# Show region hierarchy
print(f'\n=== Region Hierarchy ===')
for r in ra.regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if hasattr(r, 'entry') else '?'
    rblocks = [b.start_offset for b in getattr(r, 'blocks', [])]
    print(f'{rtype}@{entry} blocks={rblocks}')
    if rtype == 'LoopRegion':
        body = [b.start_offset for b in getattr(r, 'body_blocks', [])]
        else_b = [b.start_offset for b in getattr(r, 'else_blocks', [])]
        print(f'  body={body}')
        print(f'  else={else_b}')

# Check unowned blocks
unowned = [b for b in blocks if b not in ra.block_to_region]
if unowned:
    print(f'\n=== UNOWNED BLOCKS: {[b.start_offset for b in unowned]} ===')
