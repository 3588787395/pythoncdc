import sys, marshal, types, io, dis
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

with open(r'D:\temp\opencode\cl_layout\variants\shapes.pyc','rb') as f:
    mc = marshal.loads(f.read()[16:])
for name in ('s1','s3','s4','s5'):
    c = [k for k in mc.co_consts if isinstance(k,types.CodeType) and k.co_name==name][0]
    cfg = build_cfg(c, name=name)
    an = RegionAnalyzer(cfg, parent_code=c)
    regions = an.analyze()
    print('='*20, name)
    def label(r):
        e = getattr(r, 'entry', None)
        return f'{type(r).__name__}@B{e.id if e else "?"}'
    def show(r, depth=0):
        ind = '  '*depth
        bids = sorted(b.id for b in getattr(r, 'blocks', set()) or set())
        extra = ''
        if isinstance(r, TryExceptRegion):
            tb = sorted(b.id for b in getattr(r, 'try_blocks', set()) or set())
            els = sorted(b.id for b in getattr(r, 'else_blocks', set()) or set())
            extra = f' try={tb} else={els} has_else={r.has_else} try_end={getattr(r,"try_offset_end",None)}'
        print(f'{ind}{label(r)} blocks={bids}{extra}')
        for cc in getattr(r, 'children', []) or []:
            show(cc, depth+1)
    for r in regions:
        show(r)
    for b in cfg.blocks.values():
        instrs = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions)
        print(f'  B{b.id} [{b.start_offset}] preds={sorted(p.id for p in b.predecessors)} succs={sorted(s.id for s in b.successors)} | {instrs[:150]}')
