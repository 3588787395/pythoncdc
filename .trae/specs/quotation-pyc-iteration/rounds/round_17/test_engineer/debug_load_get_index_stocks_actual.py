"""R17 调试：检查 quotation.pyc 中 load_get_index_stocks 的字节码"""
import sys
import dis
import importlib.util

sys.path.insert(0, '/workspace')

# 加载 pyc
from core.pyc_loader_v2 import load_pyc_file_v2
PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到 load_get_index_stocks 函数
import types

def find_code(co, name):
    for const in co.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

fn_code = find_code(code_obj, 'load_get_index_stocks')
print("=== 原始字节码 (load_get_index_stocks) ===")
dis.dis(fn_code)
print()

# 显示反编译结果
with open('/tmp/r17_decompiled.py', 'r') as f:
    src = f.read()
new_co = compile(src, '<decompiled>', 'exec')
new_fn_code = find_code(new_co, 'load_get_index_stocks')
print("=== 反编译后字节码 (load_get_index_stocks) ===")
dis.dis(new_fn_code)
print()

# 对比
orig_instrs = [(i.opname, i.argval) for i in dis.get_instructions(fn_code) if i.opname not in ('CACHE', 'EXTENDED_ARG')]
new_instrs = [(i.opname, i.argval) for i in dis.get_instructions(new_fn_code) if i.opname not in ('CACHE', 'EXTENDED_ARG')]

print(f"=== 对比结果 ===")
print(f"原始: {len(orig_instrs)} 指令")
print(f"反编译: {len(new_instrs)} 指令")
for i, (a, b) in enumerate(zip(orig_instrs, new_instrs)):
    if a != b:
        print(f"  差异位置 {i}: 原始={a}, 反编译={b}")
        print(f"  原始上下文: {orig_instrs[max(0,i-3):i+5]}")
        print(f"  反编译上下文: {new_instrs[max(0,i-3):i+5]}")
        break
if len(orig_instrs) != len(new_instrs):
    print(f"  长度差异: 原始={len(orig_instrs)}, 反编译={len(new_instrs)}")
