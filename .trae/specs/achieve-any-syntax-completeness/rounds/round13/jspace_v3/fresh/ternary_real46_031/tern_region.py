import sys, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

code = compile(open(r'D:\temp\opencode\tern_repro.py', encoding='utf-8').read(), 'tern_repro', 'exec')
cfg = build_cfg(code, name='tern_repro')
print('=== CFG blocks ===')
for b in cfg.blocks.values():
    last = b.get_last_instruction()
    succs = sorted(s.id for s in b.successors)
    preds = sorted(p.id for p in b.predecessors)
    print(f'B{b.id} off={b.start_offset:4} preds={preds} succs={succs} last={last.opname if last else None} argval={getattr(last,"argval",None)}')

an = RegionAnalyzer(cfg, parent_code=code)
regions = an.analyze()
print()
print('=== regions (flat) ===')
def bids(r):
    return sorted(getattr(b,'id',b) for b in (getattr(r,'blocks',None) or []))
for r in regions:
    entry = getattr(r.entry,'id',None)
    mb = getattr(r,'merge_block',None)
    bb = getattr(r,'body_blocks',None) or getattr(r,'body_block',None)
    if bb is None: bb=[]
    if not isinstance(bb,(list,set,tuple)): bb=[bb]
    eb = getattr(r,'else_blocks',None) or []
    print(f'{type(r).__name__}@{entry} blocks={bids(r)} merge={getattr(mb,"id",None)} body={sorted(getattr(b,"id",b) for b in bb)} else={sorted(getattr(b,"id",b) for b in eb)}')
