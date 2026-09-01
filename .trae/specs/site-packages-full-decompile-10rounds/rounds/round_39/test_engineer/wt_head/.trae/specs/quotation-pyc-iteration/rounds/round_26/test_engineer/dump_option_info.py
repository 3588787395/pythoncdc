"""R26: dump get_option_info bytecode around the spurious continue"""
import sys
import types
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_co(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_co(c, name)
            if r:
                return r
    return None

co = find_co(code_obj, 'get_option_info')
print("=== PYC get_option_info around 520-840 ===")
for ins in dis.get_instructions(co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    if 520 <= ins.offset <= 840:
        print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")

# Also dump SRC
with open('/tmp/r26_decompiled.py') as f:
    src = f.read()
sco = compile(src, '<x>', 'exec')
sco = find_co(sco, 'get_option_info')
print("\n=== SRC get_option_info around 520-840 ===")
for ins in dis.get_instructions(sco):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    if 520 <= ins.offset <= 840:
        print(f"  {ins.offset:>4} {ins.opname:<35} {ins.argrepr}")
