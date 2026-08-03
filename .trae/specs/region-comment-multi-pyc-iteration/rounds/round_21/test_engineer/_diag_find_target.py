"""R21 diag: find which _target mismatches and dump bytecode diff."""
import sys
import marshal
import dis
import types

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc'
DEC_PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlersOK.pyc.dec'

with open(PYC, 'rb') as f:
    f.read(16)
    code_orig = marshal.load(f)
with open(DEC_PYC, 'rb') as f:
    f.read(16)
    code_dec = marshal.load(f)


def walk(c, out):
    out.append(c)
    for k in c.co_consts:
        if hasattr(k, 'co_code'):
            walk(k, out)


origs = {}
for c in walk(code_orig, []):
    origs.setdefault(c.co_name, []).append(c)
decs = {}
for c in walk(code_dec, []):
    decs.setdefault(c.co_name, []).append(c)

for name in sorted(set(origs) & set(decs)):
    if len(origs[name]) != len(decs[name]):
        print(f'{name}: count orig={len(origs[name])} dec={len(decs[name])}')
        for o, d in zip(origs[name], decs[name]):
            oi = [(i.opname, i.argval) for i in dis.get_instructions(o)]
            di = [(i.opname, i.argval) for i in dis.get_instructions(d)]
            if oi != di:
                print(f'  MISMATCH co_consts depth: orig nconsts={len(o.co_consts)} dec={len(d.co_consts)}')
