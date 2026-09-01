"""R30: 编译get_option_info的源码并比较字节码"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find get_option_info
def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_code(c, name)
            if r:
                return r
    return None

pyc_co = find_code(code_obj, 'get_option_info')

# Read the generated source
with open('/tmp/r30_decompiled.py') as f:
    src = f.read()

mod = compile(src, '/tmp/r30_decompiled.py', 'exec')
src_co = find_code(mod, 'get_option_info')

# Compare the specific section around the extra JUMP_BACKWARD
print("=== PYC instructions (offset 580-680) ===")
for ins in dis.get_instructions(pyc_co):
    if 580 <= ins.offset <= 680:
        print(f"  {ins.offset:4d}: {ins.opname:30s} {ins.argval}")

print("\n=== SRC instructions (offset 580-700) ===")
for ins in dis.get_instructions(src_co):
    if 580 <= ins.offset <= 700:
        print(f"  {ins.offset:4d}: {ins.opname:30s} {ins.argval}")
