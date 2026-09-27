# -*- coding: utf-8 -*-
"""ADR-1 displacement metrics: for every failing unit, measure orig-vs-product
defect shape for the landed product and for one candidate arm, then compare.

per unit:
  hunks_raw  = non-equal opcodes of SequenceMatcher(opname+' '+argrepr)   [align.py view]
  hunks_norm = same but every jump arg -> 'J', codeobj -> 'CODEOBJ'        [nhunks.py view]
  first_diff = index of first differing instruction (None => clean unit)
  sdelta     = sum |prod_target - orig_target| over jumps whose argval differs

ADR-1 (pure displacement, counts equal): hunks strictly down, first_diff moves back
(later index / disappears), sum|delta| not up.  Anything worse on any unit = flagged.

usage: python -X utf8 adr73.py <arm> [<list.json>]   (default dump/fam73_pad_r73.json)
"""
import io
import json
import os
import re
import sys
import tempfile
import shutil
import warnings
import py_compile
from difflib import SequenceMatcher

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

from pylingual.equivalence_check import matching_iter, compare_instruction
from pylingual.editable_bytecode import PYCFile
from pylingual.editable_bytecode.bytecode_patches import (
    fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop,
    replace_firstlno)

REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r73gate/center'
ROOT = os.path.dirname(os.path.abspath(__file__))
PATCHES = [remove_extended_arg, remove_nop, fix_indirect_jump,
           fix_unreachable, remove_extended_arg, replace_firstlno]
JUMPISH = re.compile(r'^(JUMP|POP_JUMP|FOR_ITER|SEND)')
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            import marshal
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal ' + path)


def walk(code, prefix, out):
    out[prefix] = code
    for c in code.co_consts:
        if isinstance(c, _t.CodeType):
            walk(c, prefix + '.' + c.co_name, out)
    return out


def instrs(ba):
    r = []
    for i in ba:
        r.append((i.opname, i.argrepr if i.arg is not None else '', i.argval))
    return r


def key_raw(t):
    return t[0] + ((' ' + t[1]) if t[1] else '')


def key_norm(t):
    op, arg, av = t
    if op.startswith(('JUMP', 'POP_JUMP', 'FOR_ITER', 'SEND')) or arg.startswith('to '):
        return op + ' J'
    if '<code object' in arg:
        return op + ' CODEOBJ'
    return op + ((' ' + arg) if arg else '')


def metrics(ia, ib):
    ka, kb = [key_raw(x) for x in ia], [key_raw(x) for x in ib]
    sm = SequenceMatcher(None, ka, kb, autojunk=False)
    hunks = [o for o in sm.get_opcodes() if o[0] != 'equal']
    na, nb = [key_norm(x) for x in ia], [key_norm(x) for x in ib]
    sm2 = SequenceMatcher(None, na, nb, autojunk=False)
    hunks_n = [o for o in sm2.get_opcodes() if o[0] != 'equal']
    first = None
    n = min(len(ia), len(ib))
    for k in range(n):
        if ia[k][0] != ib[k][0] or ia[k][1] != ib[k][1]:
            first = k
            break
    if first is None and len(ia) != len(ib):
        first = n
    sd = 0
    deltas = []
    for k in range(n):
        a, b = ia[k], ib[k]
        if a[0] == b[0] and JUMPISH.match(a[0]) and isinstance(a[2], int) and isinstance(b[2], int) \
                and a[2] != b[2]:
            sd += abs(b[2] - a[2])
            deltas.append([k, a[0], a[1], b[1], b[2] - a[2]])
    return {'hunks': len(hunks), 'hunks_norm': len(hunks_n), 'first_diff': first,
            'sdelta': sd, 'deltas': deltas, 'len': [len(ia), len(ib)]}


def main():
    arm = sys.argv[1]
    fam = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'dump', 'fam73_pad_r73.json')
    units = json.load(io.open(fam, encoding='utf-8'))
    filecat = json.load(io.open(os.path.join(ROOT, 'filecat.json'), encoding='utf-8'))
    byfile = {}
    for e in filecat:
        byfile[e['file']] = e
    tmp = tempfile.mkdtemp(prefix='adr73_')
    out = []
    try:
        for fname in sorted({u['file'] for u in units}):
            e = byfile[fname]
            landed_src = e['pyc'][:-4] + 'OK.py'
            rel = fname
            pre = REPO.replace('\\', '/') + '/site-packages/'
            if rel.startswith(pre):
                rel = rel[len(pre):]
            cand_src = os.path.join(GATE, 'build_' + arm,
                                    rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')
            if not os.path.isfile(cand_src):
                print('NO CANDIDATE PRODUCT for %s (%s)' % (fname, cand_src))
                continue
            maps = {}
            for tag, src in (('landed', landed_src), (arm, cand_src)):
                rec = os.path.join(tmp, tag + '.pyc')
                py_compile.compile(src, cfile=rec, doraise=True, optimize=0)
                maps[tag] = walk(load_pyc(rec), '<module>', {})
            O = walk(load_pyc(e['pyc']), '<module>', {})
            for u in units:
                if u['file'] != fname:
                    continue
                name = u['name']
                co = O.get(name)
                if co is None:
                    continue
                A = PYCFile(e['pyc'])
                A.apply_patches(PATCHES)
                rec = {'file': fname, 'unit': name, 'family': u['family']}
                # pair by qualname through the ruler objects
                for tag in ('landed', arm):
                    try:
                        P = PYCFile(os.path.join(tmp, tag + '.pyc'))
                        P.apply_patches(PATCHES)
                        ia = ib = None
                        for ba, bb in matching_iter(A, P):
                            if ba is not None and ba.name == name:
                                ia = list(ba)
                            if bb is not None and bb.name == name:
                                ib = list(bb)
                        if ia is None or ib is None:
                            rec[tag] = 'UNPAIRED %s/%s' % (ia is not None, ib is not None)
                            continue
                        rec[tag] = metrics([(x.opname, x.argrepr if x.arg is not None else '', x.argval)
                                            for x in ia],
                                           [(x.opname, x.argrepr if x.arg is not None else '', x.argval)
                                            for x in ib])
                    except Exception as ex:
                        rec[tag] = 'ERR %r' % (ex,)
                out.append(rec)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    worse = []
    better = []
    for r in out:
        a, b = r.get('landed'), r.get(arm)
        if not isinstance(a, dict) or not isinstance(b, dict):
            continue
        flags = []
        if b['hunks'] > a['hunks']:
            flags.append('hunks %d->%d' % (a['hunks'], b['hunks']))
        if b['hunks_norm'] > a['hunks_norm']:
            flags.append('hunks_norm %d->%d' % (a['hunks_norm'], b['hunks_norm']))
        if b['sdelta'] > a['sdelta']:
            flags.append('sdelta %d->%d' % (a['sdelta'], b['sdelta']))
        fa, fb = a['first_diff'], b['first_diff']
        if fb is None and fa is not None:
            pass  # candidate is clean for this unit: improvement, not a regression
        elif fa is None and fb is not None:
            flags.append('first_diff None->%s (NEW DIFF)' % fb)
        elif fa is not None and fb is not None and fb < fa:
            flags.append('first_diff %s->%s (EARLIER)' % (fa, fb))
        if flags:
            worse.append((r, flags))
        if (a['hunks'], a['hunks_norm'], a['sdelta'], a['first_diff']) != \
           (b['hunks'], b['hunks_norm'], b['sdelta'], b['first_diff']):
            better.append((r, flags))
    print('units compared: %d   changed: %d   WORSE: %d' % (len(out), len(better), len(worse)))
    for r, f in worse:
        print('  WORSE %-44s %-46s %s' % (r['file'].split('/')[-1], r['unit'].split('.')[-1], '; '.join(f)))
    print('--- improved (candidate strictly better on ≥1 metric, none worse) ---')
    for r, f in better:
        a, b = r['landed'], r[arm]
        if f:
            continue
        print('  IMPROVED %-40s %-44s hunks %d->%d norm %d->%d first %s->%s sd %d->%d'
              % (r['file'].split('/')[-1], r['unit'].split('.')[-1],
                 a['hunks'], b['hunks'], a['hunks_norm'], b['hunks_norm'],
                 a['first_diff'], b['first_diff'], a['sdelta'], b['sdelta']))
    io.open(os.path.join(ROOT, 'dump', 'adr73_%s.json' % arm), 'w', encoding='utf-8',
            newline='\n').write(json.dumps(out, ensure_ascii=False, indent=1))
    print('-> dump/adr73_%s.json' % arm)


main()
