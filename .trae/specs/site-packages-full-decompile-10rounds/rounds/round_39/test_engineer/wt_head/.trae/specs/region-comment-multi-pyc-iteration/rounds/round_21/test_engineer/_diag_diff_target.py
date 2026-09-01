"""R21 diag: dump instruction diff for _target functions (orig vs decompiled).
Decompiles handlers.pyc via pycdc, recompiles OK.py, compares instruction streams
per function, printing first diverging instructions with context."""
import os
import sys
import types
import marshal
import dis
import py_compile

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc'
OK = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.py'
DEC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.pyc.dec'


def load_code(pyc):
    with open(pyc, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def walk(c, out):
    out.append(c)
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            walk(k, out)
    return out


def norm_argval(a):
    if isinstance(a, types.CodeType):
        return f'<code {a.co_name}>'
    if isinstance(a, str):
        low = a.lower()
        if (low.endswith('.py') or low.endswith('.pyc')) and ('/' in a or '\\' in a):
            return os.path.basename(a)
    return a


def seq(code):
    return [(i.opname, norm_argval(i.argval)) for i in dis.get_instructions(code)]


py_compile.compile(OK, doraise=True, cfile=DEC)
orig_all = walk(load_code(PYC), [])
dec_all = walk(load_code(DEC), [])

orig_map = {}
for c in orig_all:
    orig_map.setdefault(c.co_name, []).append(c)
dec_map = {}
for c in dec_all:
    dec_map.setdefault(c.co_name, []).append(c)

for name in sorted(orig_map):
    if name not in dec_map:
        continue
    oi = seq(orig_map[name][0])
    di = seq(dec_map[name][0])
    if oi != di:
        print(f'=== MISMATCH: {name} (orig {len(oi)} instr, decomp {len(di)} instr) ===')
        n = max(len(oi), len(di))
        for idx in range(0, n, 1):
            o = oi[idx] if idx < len(oi) else ('<END>',)
            d = di[idx] if idx < len(di) else ('<END>',)
            if o[0] != d[0] or (len(o) > 1 and len(d) > 1 and o[1] != d[1]):
                # print window around first diff
                for j in range(max(0, idx - 4), min(n, idx + 6)):
                    oo = oi[j] if j < len(oi) else ('<END>',)
                    dd = di[j] if j < len(di) else ('<END>',)
                    mark = '  <--' if j == idx else ''
                    print(f'  [{j:3d}] orig={str(oo):55s} dec={str(dd):55s}{mark}')
                print()
                break
