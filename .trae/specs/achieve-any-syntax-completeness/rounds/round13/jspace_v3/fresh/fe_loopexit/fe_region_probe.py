import sys, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

src = open(r'D:\temp\opencode\cl_layout\fe\fe_variants.py', encoding='utf-8').read()
code = compile(src, '<f>', 'exec')
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name=='m3'][0]
cfg = build_cfg(fnc, name='m')
an = RegionAnalyzer(cfg, parent_code=fnc)
regions = an.analyze()

def label(r):
    e = getattr(r, 'entry', None)
    return f'{type(r).__name__}@B{e.id if e else "?"}'
def show(r, depth=0):
    ind = '  '*depth
    bids = sorted(b.id for b in getattr(r, 'blocks', set()) or set())
    extra = ''
    if isinstance(r, LoopRegion):
        els = sorted(b.id for b in getattr(r, 'else_blocks', set()) or set())
        extra = f' else={els}'
    print(f'{ind}{label(r)} blocks={bids}{extra}')
    for c in getattr(r, 'children', []) or []:
        show(c, depth+1)
for r in regions:
    show(r)
print('=== blocks ===')
for b in cfg.blocks.values():
    instrs = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions)
    print(f'B{b.id} [{b.start_offset}] preds={sorted(p.id for p in b.predecessors)} succs={sorted(s.id for s in b.successors)} | {instrs[:120]}')
