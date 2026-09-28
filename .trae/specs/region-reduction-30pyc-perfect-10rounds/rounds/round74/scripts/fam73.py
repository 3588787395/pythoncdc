# -*- coding: utf-8 -*-
"""R72 diag1 fam73: per-unit family classification using the ACTUAL ruler
verdicts (pylingual matching_iter + is_control_flow_equivalent + compare_bytecode).

usage: python -X utf8 fam73.py [--only=<substr>] [--out=<json>] [--quiet]

Writes fam72.json: one record per failing unit with the true verdict,
the first divergent instruction (on PATCHED bytecode, same as the ruler),
and a deterministic family label.
"""
import io
import json
import os
import py_compile
import sys
import tempfile
import shutil
import warnings
import re
from collections import Counter, defaultdict

warnings.filterwarnings('ignore')
PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'
sys.path.insert(0, PYLINGUAL)
import typing
if not hasattr(typing, 'override'):
    typing.override = lambda f: f
import types as _t
if 'pydot' not in sys.modules:
    _s = _t.ModuleType('pydot')
    _s.graph_from_dot_data = lambda *a, **k: []
    _s.Dot = _s.Node = _s.Edge = lambda *a, **k: None
    sys.modules['pydot'] = _s
if 'pylingual' not in sys.modules:
    _p = _t.ModuleType('pylingual')
    _p.__path__ = [os.path.join(PYLINGUAL, 'pylingual')]
    sys.modules['pylingual'] = _p

from pylingual.equivalence_check import (compare_bytecode, matching_iter,
                                         is_control_flow_equivalent,
                                         compare_instruction)
from pylingual.editable_bytecode import PYCFile
from pylingual.editable_bytecode.bytecode_patches import (
    fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop,
    replace_firstlno)
from pylingual.editable_bytecode.control_flow_graph import bytecode_to_control_flow_graph
from pylingual.control_flow_reconstruction.cfg import CFG

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
PATCHES = [remove_extended_arg, remove_nop, fix_indirect_jump,
           fix_unreachable, remove_extended_arg, replace_firstlno]

POLARITY = re.compile(r'^POP_JUMP\w*_(IF_TRUE|IF_FALSE|IF_NONE|IF_NOT_NONE|IF_NON_NULL|IF_NULL|IF_BAD|IF_NOT_BAD)')


def sig(it):
    av = it.argval
    if isinstance(av, _t.CodeType) or hasattr(av, 'co_name'):
        return ('code', getattr(av, 'co_name', '?'))
    return (it.opname, av)


def is_jump(op):
    return op.startswith('POP_JUMP') or op.startswith('JUMP_') or op in ('FOR_ITER', 'SEND')


def classify(ia, ib, ca, cb):
    sa = [sig(i) for i in ia]
    sb = [sig(i) for i in ib]
    la, lb = len(ia), len(ib)
    ea = ca.co_exceptiontable if ca else b''
    eb = cb.co_exceptiontable if cb else b''
    if sa == sb and ea == eb:
        na = [c for c in ca.co_consts if hasattr(c, 'co_name')]
        nb = [c for c in cb.co_consts if hasattr(c, 'co_name')]
        nested = [(c.co_name, c.co_firstlineno, c.co_linetable) for c in na] != \
                 [(c.co_name, c.co_firstlineno, c.co_linetable) for c in nb]
        selfmeta = (ca.co_firstlineno != cb.co_firstlineno) or (ca.co_linetable != cb.co_linetable)
        if nested:
            return 'F-META', 'instr+exc identical, NESTED code objects differ (name/lineno/linetable)'
        if selfmeta:
            return 'F-META', 'instr+exc identical, only this unit co_firstlineno/linetable differs %d/%d' % (
                ca.co_firstlineno, cb.co_firstlineno)
        return 'F-IDENT', 'instr+exc+lines identical -> ruler pairing artifact, check'
    if sa == sb and ea != eb:
        return 'F-EXCTABLE', 'instr identical, exception table differs (%d vs %d bytes)' % (len(ea), len(eb))
    n = min(la, lb)
    i = 0
    while i < n and sa[i] == sb[i]:
        i += 1
    if i >= n:
        return 'F-ABSORB', 'common prefix equal, len %d/%d' % (la, lb)
    oa, va = sa[i]
    ob, vb = sb[i]
    if oa != ob:
        pa, pb = POLARITY.match(oa), POLARITY.match(ob)
        if pa and pb and pa.group(1) != pb.group(1):
            return 'F-POLARITY', 'idx %d %s -> %s' % (i, oa, ob)
        if {oa, ob} == {'JUMP_FORWARD', 'RETURN_VALUE'}:
            return 'F-TERNARY', 'idx %d %s -> %s' % (i, oa, ob)
        ca_n = sum(1 for x in ia if x.opname == 'LOAD_ASSERTION_ERROR')
        cb_n = sum(1 for x in ib if x.opname == 'LOAD_ASSERTION_ERROR')
        if ca_n != cb_n:
            return 'F-ASSERT', 'LOAD_ASSERTION_ERROR %d/%d' % (ca_n, cb_n)
        if la != lb:
            return 'F-ABSORB', 'opname %s -> %s at idx %d, len %d/%d' % (oa, ob, i, la, lb)
        return 'F-OTHER', 'opname %s -> %s at idx %d, len equal %d' % (oa, ob, i, la)
    if is_jump(oa) and va != vb:
        ta = next((x for x in ia if x.offset == va), None)
        tb = next((x for x in ib if x.offset == vb), None)
        if ta is None or tb is None:
            return 'F-ABSORB', 'jump target off-stream %s -> %s' % (va, vb)
        if sig(ta) != sig(tb):
            return 'F-ABSORB', 'idx %d %s target %s -> %s lands on DIFFERENT instr (%s vs %s)' % (
                i, oa, va, vb, ta.opname, tb.opname)
        if la != lb:
            return 'F-ABSORB', 'target instr same but len %d/%d' % (la, lb)
        return 'F-PAD', 'idx %d %s target %s -> %s lands on SAME instr, len equal' % (i, oa, va, vb)
    if la != lb:
        return 'F-ABSORB', 'idx %d %s arg %r -> %r, len %d/%d' % (i, oa, va, vb, la, lb)
    return 'F-OTHER', 'idx %d %s arg %r -> %r, len equal' % (i, oa, va, vb)


def main():
    only = None
    out = os.path.join(ROOT, 'fam73_pad.json')
    quiet = False
    for a in sys.argv[1:]:
        if a.startswith('--only='):
            only = a[7:]
        elif a.startswith('--out='):
            out = a[6:]
        elif a == '--quiet':
            quiet = True
    filecat = json.load(io.open(os.path.join(ROOT, 'filecat.json'), encoding='utf-8'))
    tmp = tempfile.mkdtemp(prefix='fam72_')
    recs = []
    try:
        for e in filecat:
            if e['units_failed'] == 0:
                continue
            if only and only not in e['file']:
                continue
            rec = os.path.join(tmp, 'r.pyc')
            try:
                py_compile.compile(e['pyc'][:-4] + 'OK.py', cfile=rec, doraise=True, optimize=0)
            except Exception as exc:
                print('COMPILE-FAIL %s %s' % (e['file'], exc))
                continue
            A = PYCFile(e['pyc'])
            B = PYCFile(rec)
            A.apply_patches(PATCHES)
            B.apply_patches(PATCHES)
            npass = nfail = 0
            for ba, bb in matching_iter(A, B):
                if ba is None:
                    recs.append({'file': e['file'], 'name': bb.name, 'verdict': 'Extra',
                                 'family': 'F-EXTRA', 'reason': 'product-only code object'})
                    nfail += 1
                    continue
                if bb is None:
                    recs.append({'file': e['file'], 'name': ba.name, 'verdict': 'Missing',
                                 'family': 'F-MISSING', 'reason': 'orig-only code object'})
                    nfail += 1
                    continue
                name = ba.name
                try:
                    cfg_a = bytecode_to_control_flow_graph(ba)
                    cfg_b = bytecode_to_control_flow_graph(bb)
                    bga = CFG.from_graph(cfg_a, ba, iterate=False)
                    bgb = CFG.from_graph(cfg_b, bb, iterate=False)
                    cf = not is_control_flow_equivalent(bga, bgb)
                except Exception as exc:
                    recs.append({'file': e['file'], 'name': name, 'verdict': 'CFGERROR',
                                 'family': 'F-CFGERR', 'reason': repr(exc)[:160]})
                    nfail += 1
                    continue
                if cf:
                    verdict, cat = 'Different control flow', 'cf'
                else:
                    bres = compare_bytecode(ba, bb)
                    if not bres.result:
                        verdict, cat = 'Different bytecode', 'bc'
                    else:
                        npass += 1
                        continue
                nfail += 1
                ia, ib = list(ba), list(bb)
                ca, cb = ba.codeobj, bb.codeobj
                fam, why = classify(ia, ib, ca, cb)
                j = next((k for k in range(min(len(ia), len(ib)))
                          if not compare_instruction(ia[k], ib[k])), min(len(ia), len(ib)))
                r = {'file': e['file'], 'name': name, 'verdict': verdict, 'cat': cat,
                     'family': fam, 'reason': why, 'lenA': len(ia), 'lenB': len(ib),
                     'firstidx': j if j < min(len(ia), len(ib)) else None}
                if r['firstidx'] is not None:
                    r['firstA'] = '%d %s %s' % (ia[j].offset, ia[j].opname, ia[j].argrepr)
                    r['firstB'] = '%d %s %s' % (ib[j].offset, ib[j].opname, ib[j].argrepr)
                    try:
                        r['lineA'] = ca.co_lines and next((l for s, e2, l in ca.co_lines()
                                                           if s <= ia[j].offset < e2 and l), None)
                    except Exception:
                        r['lineA'] = None
                    try:
                        r['lineB'] = next((l for s, e2, l in cb.co_lines()
                                           if s <= ib[j].offset < e2 and l), None)
                    except Exception:
                        r['lineB'] = None
                recs.append(r)
            if not quiet:
                print('%-70s fail=%d (ruler filecat=%d) pass=%d' % (
                    e['file'], nfail, e['units_failed'], npass))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    json.dump(recs, io.open(out, 'w', encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)
    print()
    print('TOTAL failing units: %d' % len(recs))
    for k, v in Counter(r['family'] for r in recs).most_common():
        print('  %-12s %d' % (k, v))
    print('verdicts:', dict(Counter(r['verdict'] for r in recs)))
    print()
    for f, n in Counter(r['file'] for r in recs).most_common():
        fams = Counter(r['family'] for r in recs if r['file'] == f)
        print('%-70s %2d  %s' % (f, n, dict(fams)))
    print('-> %s' % out)


if __name__ == '__main__':
    main()
