"""R21-55 merge-point probe: for a ternary diamond (true_block, false_block) measure
  - the block instruction tails, successors and predecessors
  - find_nearest_common_post_dominator({true, false})
  - whether the diamond sits inside an exception range (co_exceptiontable)
usage: python -X utf8 work/probe_merge_r2155.py <abs pyc> <co-name> <t_off> <f_off> [<m_off>]
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)

PYC, CONAME, TOFF, FOFF = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
MOFF = int(sys.argv[5]) if len(sys.argv) > 5 else None

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import dis

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()


def find(c, name):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r:
                return r
    return None


inner = find(code, CONAME) or code
cfg = build_cfg(inner)
an = RegionAnalyzer(cfg)
da = an.dom_analyzer


def show(off, label):
    b = cfg.get_block_by_offset(off)
    if b is None:
        print('%s @%s: NO BLOCK' % (label, off))
        return None
    eff = [i for i in b.instructions if i.opname not in ('CACHE', 'EXTENDED_ARG', 'NOP')]
    print('%s @%s instrs=%s' % (label, off, [(i.opname, (i.argrepr if getattr(i,'argrepr',None) else str(i.argval))[:28]) for i in eff]))
    print('    successors   =', sorted(getattr(s, 'start_offset', -1) for s in (b.successors or [])))
    print('    cond_succs   =', sorted(getattr(s, 'start_offset', -1) for s in (b.conditional_successors or [])))
    print('    predecessors =', sorted(getattr(p, 'start_offset', -1) for p in (b.predecessors or [])))
    return b


tb = show(TOFF, 'true_block')
fb = show(FOFF, 'false_block')
mb = show(MOFF, 'merge_block') if MOFF else None

if tb and fb:
    print('NCPD({t,f}) via analyzer.dom_analyzer =', da.find_nearest_common_post_dominator({tb, fb}))
    for name in ('post_dominates', 'immediate_post_dominator', 'post_dominators',
                 'compute_post_dominators', 'reverse_graph', 'exits'):
        if hasattr(da, name):
            print('  da has attr:', name)
    print('  cfg exits:', [getattr(x, 'start_offset', x) for x in (getattr(cfg, 'exit_blocks', None) or [])])

print('exception ranges of %s:' % CONAME)
for e in dis.exception_entries(inner.co_exceptiontable):
    print('  start=%d end=%d handler=%d' % (e.start, e.end, e.handler))
