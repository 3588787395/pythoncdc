import sys, types
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

src_path = sys.argv[1] if len(sys.argv) > 1 else r'D:\temp\opencode\r31_repro.py'
src = open(src_path, encoding='utf-8').read()
code = compile(src, 'probe', 'exec')
fcode = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'f':
        fcode = c
        break
if fcode is None:
    print('no f() found'); sys.exit(1)
cfg = build_cfg(fcode, name='f')
print('=== CFG blocks ===')
for b in cfg.blocks.values():
    last = b.get_last_instruction()
    succs = sorted(s.id for s in b.successors)
    preds = sorted(p.id for p in b.predecessors)
    print(f'B{b.id} off={b.start_offset:3} preds={preds} succs={succs} last={last.opname if last else None}')

an = RegionAnalyzer(cfg, parent_code=fcode)
regions = an.analyze()
print()
print('=== regions ===')
def bids(r):
    return sorted(getattr(b, 'id', b) for b in (getattr(r, 'blocks', None) or []))
for r in regions:
    entry = getattr(r.entry, 'id', None)
    mb = getattr(r, 'merge_block', None)
    bb = getattr(r, 'body_blocks', None) or getattr(r, 'body_block', None) or []
    if not isinstance(bb, (list, set, tuple)):
        bb = [bb]
    eb = getattr(r, 'else_blocks', None) or []
    print(f'{type(r).__name__}@{entry} blocks={bids(r)} merge={getattr(mb, "id", None)} '
          f'body={sorted(getattr(b, "id", b) for b in bb)} else={sorted(getattr(b, "id", b) for b in eb)}')
