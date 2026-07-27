"""R23-N6: 直接反汇编 date_convert 的 PYC，查看原始字节"""
import sys
import dis
import types
import struct

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

module = load_pyc_file_v2('/workspace/quotation.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_func(co, name):
    if co.co_name == name:
        return co
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            r = find_func(const, name)
            if r:
                return r
    return None

func = find_func(code_obj, 'date_convert')
print(f"co_code: {func.co_code.hex()}")
print(f"co_consts: {func.co_consts}")
print(f"co_names: {func.co_names}")
print(f"co_varnames: {func.co_varnames}")
print()

# 打印偏移量240-260的字节
print("Bytes around offset 252-260:")
for i in range(250, 270, 2):
    if i < len(func.co_code):
        op = func.co_code[i]
        arg = func.co_code[i+1]
        print(f"  offset {i}: op={op} ({dis.opname[op]}) arg={arg}")

print()
print("=== Full disassembly ===")
dis.dis(func)
