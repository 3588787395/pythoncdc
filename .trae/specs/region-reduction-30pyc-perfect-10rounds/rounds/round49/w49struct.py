# -*- coding: utf-8 -*-
"""Structural facts of the IfRegion whose arm absorbs the shared return tail.

usage: python -X utf8 w49struct.py <pyc> <func-name> <merge-offset>
"""
import importlib.util
import sys
import types as _t

REPO = r'F:\Downloads\pythoncdc-main'
PYC, NAME, MERGE = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('pc49s', REPO + '/pycdc.py')
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)
mod = pc.load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer


def off(b):
    return getattr(b, 'start_offset', None) if b is not None else None


def walk2(co, path=''):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            yield from walk2(c, path + '/' + c.co_name)


for p, co in walk2(code):
    if co.co_name != NAME:
        continue
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    hit = [r for r in ra.regions
           if off(getattr(r, 'merge_block', None)) == MERGE]
    print('regions=%d  with merge==%s: %d' % (len(ra.regions), MERGE, len(hit)))
    for r in hit:
        tb = sorted(r.then_blocks or [], key=lambda b: b.start_offset)
        eb = sorted(r.else_blocks or [], key=lambda b: b.start_offset)
        print('%-14s entry=%s cond=%s then=%s else=%s merge=%s' % (
            type(r).__name__, off(r.entry),
            off(getattr(r, 'condition_block', None)),
            [off(b) for b in tb], [off(b) for b in eb], off(r.merge_block)))
        tset = set(tb)
        reaches = [off(b) for b in tb if r.merge_block in (b.successors or [])]
        print('  then blocks reaching merge:', reaches)
        print('  then tail blocks (no succ inside then):')
        for b in tb:
            outs = [s for s in (b.successors or []) if s not in tset]
            if not (set(b.successors or []) & tset):
                last = b.get_last_instruction()
                tgt = None
                if last is not None and isinstance(last.argval, int) and last.opname.startswith('JUMP'):
                    tgt = last.argval
                print('    @%-6s ter=%-16s nsucc=%d outside=%s jump->%s' % (
                    off(b), last.opname if last else '?', len(b.successors or []),
                    sorted(off(x) for x in outs), tgt))
        mb = r.merge_block
        print('  merge @%s npred=%d preds=%s succs=%s ter=%s' % (
            off(mb), len(mb.predecessors), sorted(off(x) for x in mb.predecessors),
            sorted(off(x) for x in (mb.successors or [])),
            mb.get_last_instruction().opname))
        print('  region.blocks has merge? %s ; nblocks=%d' % (
            mb in (r.blocks or set()), len(r.blocks or set())))
    tail = [b for b in cfg.blocks if off(b) > MERGE][:0]
    for b in cfg.blocks:
        if off(b) in (1674, 1678, 1548, 1550):
            print('B@%-6s npred=%d preds=%s nsucc=%d succs=%s ter=%s' % (
                off(b), len(b.predecessors), sorted(off(x) for x in b.predecessors),
                len(b.successors or []), sorted(off(x) for x in (b.successors or [])),
                b.get_last_instruction().opname))
    break
