import sys, marshal, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion, BoolOpRegion

mc = marshal.loads(open(r'D:\temp\opencode\cl_layout\fi\fi1.pyc','rb').read()[16:])
cfg = build_cfg(mc, name='find')
an = RegionAnalyzer(cfg, parent_code=mc)
regions = an.analyze()
for b in cfg.blocks.values():
    instrs = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions)
    print(f'B{b.id} [{b.start_offset}] preds={sorted(p.start_offset for p in b.predecessors)} succs={sorted(s.start_offset for s in b.successors)} | {instrs[:120]}')
print('---- regions:')
def label(r):
    e = getattr(r, 'entry', None)
    return f'{type(r).__name__}@{e.start_offset if e else "?"}'
def show(r, depth=0):
    ind = '  '*depth
    offs = sorted(getattr(b,'start_offset',None) for b in getattr(r,'blocks',set()) or set())
    extra = ''
    if isinstance(r, LoopRegion):
        els = sorted(getattr(b,'start_offset',None) for b in getattr(r,'else_blocks',set()) or set())
        bbs = sorted(getattr(b,'start_offset',None) for b in getattr(r,'break_blocks',set()) or set())
        extra = f' else={els} break_blocks={bbs}'
    if isinstance(r, IfRegion):
        tb = sorted(getattr(b,'start_offset',None) for b in getattr(r,'then_blocks',set()) or set())
        mb = getattr(r,'merge_block',None)
        extra = f' then={tb} merge={mb.start_offset if mb else None}'
    if isinstance(r, BoolOpRegion):
        extra = f' op={getattr(r,"op",None)}'
    print(f'{ind}{label(r)} blocks={offs}{extra}')
    for c in getattr(r,'children',[]) or []:
        show(c, depth+1)
for r in regions:
    show(r)
print('---- block_to_region:')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    r = an.block_to_region.get(b)
    print(f'  off={b.start_offset} -> {label(r) if r else None}')
