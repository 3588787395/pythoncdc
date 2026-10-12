import os, sys, types
MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR); sys.path.insert(0, os.path.join(MIRROR, 'core'))
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as ra

PYC = sys.argv[1]
mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code,'get') else mod.code
if hasattr(code,'to_python_code'): code = code.to_python_code()
def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType): yield from walk(k)
co = [c for c in walk(code) if 'sync_worker' in (getattr(c,'co_qualname',None) or c.co_name)][0]
cfg = build_cfg(co)
ana = ra.RegionAnalyzer(cfg)
regions = ana.analyze()
loops = [r for r in regions if isinstance(r, ra.LoopRegion)]
inner = [r for r in loops if r.condition_block is not None and r.condition_block.start_offset==232][0]
cb = inner.condition_block
print('inner loop entry', inner.entry.start_offset, 'cond', cb.start_offset,
      'header', inner.header_block.start_offset, 'back', [b.start_offset for b in inner.back_edge_blocks],
      'body', [b.start_offset for b in inner.body_blocks],
      'else', [b.start_offset for b in (inner.else_blocks or [])])
f = ana._detect_while_boolop_forward_chain(cb, inner, ra.FORWARD_CONDITIONAL_JUMP_OPS | ra.SHORT_CIRCUIT_JUMP_OPS)
print('forward_chain ->', None if f is None else [(b.start_offset, o) for b,o in f])
n = ana._detect_while_condition_nested_and_or_chain(cb, inner)
print('nested_and_or ->', None if n is None else [(b.start_offset,o) for b,o in n])
full = ana._detect_while_condition_boolop_chain(cb, inner)
print('full ->', None if full is None else [(b.start_offset,o) for b,o in full])
last = cb.get_last_instruction()
print('cond last', last.opname, last.argval)
for b in (cb,)+tuple(cb.successors):
    l=b.get_last_instruction()
    print('  blk', b.start_offset, l.opname, l.argval, 'succ', [s.start_offset for s in b.successors])
