# Dump region tree for t1_tryelse.f to find where the else block lands.
import sys, types, textwrap
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion, TryExceptRegion

src = open(r'D:\temp\opencode\cl_layout\repro\t1_tryelse.py', encoding='utf-8').read()
code = compile(src, '<f>', 'exec')
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]

cfg = build_cfg(fnc, name='f')
an = RegionAnalyzer(cfg, parent_code=fnc)
regions = an.analyze()

def label(r):
    e = getattr(r, 'entry', None)
    return f'{type(r).__name__}@B{e.id if e else "?"}'

def show(r, depth=0):
    ind = '  '*depth
    bids = sorted(b.id for b in getattr(r, 'blocks', set()) or set())
    extra = ''
    if isinstance(r, TryExceptRegion):
        tb = sorted(b.id for b in getattr(r, 'try_blocks', set()) or set())
        hb = [(h[0], h[1], sorted(b.id for b in h[2])) for h in getattr(r, 'except_handlers', []) or []]
        els = sorted(b.id for b in getattr(r, 'else_blocks', set()) or set())
        fb = sorted(b.id for b in getattr(r, 'finally_blocks', set()) or set()) if hasattr(r, 'finally_blocks') else None
        extra = f' try={tb} handlers={hb} else={els} finally={fb} has_else={r.has_else} try_end={getattr(r,"try_offset_end",None)}'
    print(f'{ind}{label(r)} blocks={bids}{extra}')
    for c in getattr(r, 'children', []) or []:
        show(c, depth+1)

for r in regions:
    show(r)

print('=== blocks ===')
for b in cfg.blocks.values():
    instrs = ' '.join(f'{i.offset}:{i.opname}' for i in b.instructions)
    print(f'B{b.id} [{b.start_offset}] preds={sorted(p.id for p in b.predecessors)} succs={sorted(s.id for s in b.successors)} | {instrs}')
