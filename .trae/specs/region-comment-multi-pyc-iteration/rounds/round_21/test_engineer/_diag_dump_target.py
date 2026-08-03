"""R21 diag: dump full instruction streams for _target (orig vs decomp) to files."""
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
OUTDIR = os.path.dirname(os.path.abspath(__file__))


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


def find_target(c):
    for k in walk(c, []):
        if k.co_name == '_target':
            return k
    return None


py_compile.compile(OK, doraise=True, cfile=DEC)
o = find_target(load_code(PYC))
d = find_target(load_code(DEC))

with open(os.path.join(OUTDIR, '_dis_target_orig.txt'), 'w', encoding='utf-8') as f:
    f.write(f'offset opname argval argrepr\n')
    for i in dis.get_instructions(o):
        f.write(f'{i.offset:5d} {i.opname:30s} {str(i.argval):30s} {i.argrepr}\n')

with open(os.path.join(OUTDIR, '_dis_target_dec.txt'), 'w', encoding='utf-8') as f:
    f.write(f'offset opname argval argrepr\n')
    for i in dis.get_instructions(d):
        f.write(f'{i.offset:5d} {i.opname:30s} {str(i.argval):30s} {i.argrepr}\n')

print(f'orig _target: {len(list(dis.get_instructions(o)))} instr, flags={o.co_flags}')
print(f'dec  _target: {len(list(dis.get_instructions(d)))} instr, flags={d.co_flags}')
print(f'orig varnames: {o.co_varnames}')
print(f'dec  varnames: {d.co_varnames}')
print(f'orig consts: {[repr(c)[:40] for c in o.co_consts]}')
print(f'dec  consts: {[repr(c)[:40] for c in d.co_consts]}')
