"""Compile generated change_future_real_date and compare bytecode."""
import sys
import dis
import marshal
sys.path.insert(0, '/workspace')

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)
    pyc_code = marshal.load(f)

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r:
                return r
    return None

pyc_fn = find(pyc_code, 'change_future_real_date')

# Read generated source
with open('/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_23/test_engineer/r23_decompiled.py') as f:
    src = f.read()

# Compile the whole module
src_code = compile(src, '<decompiled>', 'exec')
src_fn = find(src_code, 'change_future_real_date')

def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval, ins.argrepr) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

pa = get_instrs(pyc_fn)
sa = get_instrs(src_fn)
print(f"pyc instructions: {len(pa)}")
print(f"src instructions: {len(sa)}")
print()

# Show all instructions side by side
max_len = max(len(pa), len(sa))
for i in range(max_len):
    a = pa[i] if i < len(pa) else None
    b = sa[i] if i < len(sa) else None
    a_str = f"{a[0]:4d} {a[1]:30s} {a[3]}" if a else "(none)"
    b_str = f"{b[0]:4d} {b[1]:30s} {b[3]}" if b else "(none)"
    match = "OK" if a and b and a[1] == b[1] and a[2] == b[2] else "!!"
    print(f"  {match} p: {a_str}")
    print(f"  {match} s: {b_str}")
