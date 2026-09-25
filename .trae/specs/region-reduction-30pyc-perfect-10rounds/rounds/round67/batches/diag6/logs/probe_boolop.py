# -*- coding: utf-8 -*-
"""Trace why the live analyzer does (not) build a BoolOp chain for one code object.
usage: probe_boolop.py <pyc> <parent-fn> [nested-firstlineno]"""
import io, marshal, os, sys, types, traceback
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

def load_pyc(path):
    d = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try: return marshal.loads(d[off:])
        except Exception: pass
    raise SystemExit('bad pyc')

def walk(c, o):
    o.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType): walk(k, o)
    return o

pyc, parent = sys.argv[1], sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else None
codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == parent]
cands = []
for c in codes:
    for k in c.co_consts:
        if isinstance(k, types.CodeType) and k.co_name == '<genexpr>':
            cands.append(k)
if want: cands = [k for k in cands if k.co_firstlineno == want]
if not cands: cands = codes
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

O = lambda b: getattr(b, 'start_offset', None)
det = RegionAnalyzer._detect_boolop_conditional_chain
def wd(self, start_block, claimed, skip_claimed_check=False):
    r = det(self, start_block, claimed, skip_claimed_check)
    print('  cond_chain start=%s -> %s   (in-claimed=%s, claimed=%s)' % (
        O(start_block), [O(b) for b, _ in (r or [])], start_block in claimed, sorted(O(x) for x in claimed)))
    return r
RegionAnalyzer._detect_boolop_conditional_chain = wd
sc = RegionAnalyzer._detect_boolop_short_circuit_chain
def wsc(self, start_block, claimed, *a, **k):
    r = sc(self, start_block, claimed, *a, **k)
    print('  short_chain start=%s -> %s' % (O(start_block), [O(b) for b, _ in (r or [])]))
    return r
RegionAnalyzer._detect_boolop_short_circuit_chain = wsc
for code in cands:
    print('##### %s firstlineno=%d free=%s' % (code.co_name, code.co_firstlineno, code.co_freevars))
    cfg = build_cfg(code)
    bl = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    print('  blocks:', {O(b): [i.opname for i in b.instructions][-1] for b in bl})
    an = RegionAnalyzer(cfg)
    rs = an.analyze()
    print('  regions:', ['%s@%s' % (type(r).__name__, O(r.entry)) for r in sorted(rs, key=lambda x: O(x.entry) or 0)])
