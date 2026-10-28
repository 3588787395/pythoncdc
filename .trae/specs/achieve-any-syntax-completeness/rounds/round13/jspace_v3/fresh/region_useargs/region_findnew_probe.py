# Dump region ownership for enum._find_new_ to find where the use_args join block lands.
import sys, types, textwrap
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

lines = open(r'D:\Python\Lib\enum.py', encoding='utf-8').read().split('\n')
start = next(i for i,l in enumerate(lines) if 'def _find_new_' in l)
end = start+1
while end < len(lines):
    l = lines[end]
    if l.startswith('    def ') or l.startswith('class ') or l.startswith('EnumMeta'):
        break
    end += 1
src = textwrap.dedent('\n'.join(lines[start:end]))
code = compile(src + '\n', '<fnc>', 'exec')
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]

cfg = build_cfg(fnc, name='_find_new_')
an = RegionAnalyzer(cfg, parent_code=fnc)
regions = an.analyze()

# map block id -> region
def label(r):
    return f'{type(r).__name__}@{getattr(r,"entry",None) and r.entry.id}'

def show(r, depth=0):
    ind = '  '*depth
    bids = sorted(b.id for b in getattr(r, 'blocks', set()) or set())
    body = sorted(b.id for b in getattr(r, 'body_blocks', set()) or set()) if hasattr(r,'body_blocks') else None
    els = sorted(b.id for b in getattr(r, 'else_blocks', set()) or set()) if hasattr(r,'else_blocks') else None
    print(f'{ind}{label(r)} blocks={bids} body={body} else={els}')
    for c in getattr(r, 'children', []) or []:
        show(c, depth+1)

for r in regions:
    show(r)

print('=== block_to_region for key blocks ===')
for bid in (3,12,14,15,16,17,18,19):
    b = cfg.blocks.get(bid)
    if b is None: continue
    reg = an.block_to_region.get(b)
    print(f'B{bid} -> {label(reg) if reg else None}')
