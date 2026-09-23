# -*- coding: utf-8 -*-
"""Offline evaluation of the R49-A candidate predicate on real CFGs.

usage: python -X utf8 w49eval.py <pyc> <func-name> [more func names...]
"""
import importlib.util
import sys
import types as _t

REPO = r'D:/Temp/r43gate/mirr_head49'
PYC = sys.argv[1]
NAMES = sys.argv[2:]
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
sys.path.insert(1, r'F:/Downloads/pythoncdc-main')
_s = importlib.util.spec_from_file_location('pc49e', REPO + '/pycdc.py')
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)
mod = pc.load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

SINK_OPS = ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE')


def off(b):
    return getattr(b, 'start_offset', None) if b is not None else None


def norm_succ(b):
    exc = getattr(b, 'exception_successors', set()) or set()
    return [s for s in (b.successors or []) if s not in exc]


def evaluate(ra, header, then_succ, else_succ, struct_blocks):
    struct = set(struct_blocks or ())
    struct.add(header)
    struct.add(then_succ)
    struct.add(else_succ)
    closure = set()
    work = [then_succ]
    while work:
        b = work.pop()
        if b in closure:
            continue
        closure.add(b)
        for s in (b.successors or []):
            if s in struct or s in closure:
                continue
            work.append(s)
    out = {'closure': len(closure), 'else_in_closure': else_succ in closure}
    if else_succ in closure:
        return out, None
    outside = set()
    work = [else_succ]
    while work:
        b = work.pop()
        if b in outside or b in closure:
            continue
        outside.add(b)
        for s in (b.successors or []):
            if s in closure or s in outside:
                continue
            work.append(s)
    cands = []
    for b in sorted(closure, key=lambda x: (off(x) is None, off(x))):
        last = b.get_last_instruction()
        if last is None or last.opname not in SINK_OPS:
            continue
        if norm_succ(b):
            continue
        eps = sorted(off(p) for p in (b.predecessors or [])
                     if p in outside and p not in struct)
        if eps:
            cands.append((b, eps))
    out['cands'] = [(off(b), e, b.get_last_instruction().opname) for b, e in cands]
    if len(cands) != 1:
        return out, None
    return out, cands[0][0]


def walk2(co, path=''):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            yield from walk2(c, path + '/' + c.co_name)


for p, co in walk2(code):
    if NAMES and co.co_name not in NAMES:
        continue
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    # every IfRegion-like region: re-derive its (header, then_succ, else_succ) entry blocks
    seen = set()
    for r in ra.regions:
        cb = getattr(r, 'condition_block', None) or getattr(r, 'header_block', None)
        tb = getattr(r, 'then_blocks', None)
        eb = getattr(r, 'else_blocks', None)
        if not tb:
            continue
        then_succ = tb[0]
        else_succ = eb[0] if eb else getattr(r, 'merge_block', None)
        if then_succ is None or else_succ is None:
            continue
        key = (off(cb), off(then_succ), off(else_succ))
        if key in seen:
            continue
        seen.add(key)
        info, res = evaluate(ra, cb, then_succ, else_succ, {cb})
        tag = 'FIRE->%s' % off(res)
        if info.get('cands') is None and info.get('else_in_closure'):
            tag = 'skip(else in closure)'
        print('%-22s H=%-6s T=%-6s E=%-6s merge=%-6s  %-12s %s' % (
            co.co_name[:22], off(cb), off(then_succ), off(else_succ),
            off(getattr(r, 'merge_block', None)), tag, info))
