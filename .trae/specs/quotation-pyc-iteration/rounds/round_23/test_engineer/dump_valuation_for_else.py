"""R24-N1 调试：dump valuation 函数的 pyc 字节码，分析 for-else + try-except 结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find valuation function
def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            result = find_func(const, name)
            if result:
                return result
    return None

val_co = find_func(code_obj, 'valuation')
print(f"=== valuation bytecode (full) ===")
for ins in dis.get_instructions(val_co):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argrepr}")
