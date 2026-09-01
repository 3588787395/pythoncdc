"""Dump full bytecode of change_future_real_date to understand structure."""
import sys
import dis
sys.path.insert(0, '/workspace')

import marshal, importlib.util

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)  # header
    code = marshal.load(f)

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r:
                return r
    return None

target = find(code, 'change_future_real_date')
print(f"=== {target.co_name} ===")
print(f"argcount={target.co_argcount}, varnames={target.co_varnames}")
print()
for ins in dis.get_instructions(target):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"{ins.offset:4d} {ins.opname:30s} {ins.argrepr}")
