"""R25: dump full bytecode of share_change from pyc to understand the real structure"""
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

target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'share_change':
        target = const
        break

print(f"=== share_change bytecode (pyc) ===")
print(f"co_varnames: {target.co_varnames}")
print(f"co_consts (non-code): {[c for c in target.co_consts if not isinstance(c, types.CodeType)]}")
print()
for ins in dis.get_instructions(target):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argrepr}")
