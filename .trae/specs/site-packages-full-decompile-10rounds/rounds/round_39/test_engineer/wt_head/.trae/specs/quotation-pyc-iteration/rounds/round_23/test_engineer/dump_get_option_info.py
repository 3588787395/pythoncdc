"""Dump get_option_info bytecode from both pyc and decompiled source."""
import sys, dis, types
sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'

from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None

pyc_fn = find(code_obj, 'get_option_info')

with open(SRC) as f:
    src = f.read()
compiled = compile(src, '<decompiled>', 'exec')
src_fn = find(compiled, 'get_option_info')

def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

pa = get_instrs(pyc_fn)
sa = get_instrs(src_fn)

print(f"pyc: {len(pa)} instrs, src: {len(sa)} instrs")

for i in range(max(len(pa), len(sa))):
    a = pa[i] if i < len(pa) else None
    b = sa[i] if i < len(sa) else None
    a_str = f"{a[0]:4d} {a[1]:30s} {a[3]}" if a else "(none)"
    b_str = f"{b[0]:4d} {b[1]:30s} {b[3]}" if b else "(none)"
    match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
    if match == "!!":
        print(f"[{i:3d}] {match} p: {a_str}")
        print(f"      {match} s: {b_str}")
    else:
        print(f"[{i:3d}] {match} p: {a_str}")
