"""R23-N6: 转储 date_convert 的行号表"""
import sys
import dis
import types

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
print(f"co_firstlineno: {func.co_firstlineno}")
print()

# 使用 co_positions 获取每个指令的源码位置
print("=== Per-instruction positions ===")
for ins in dis.get_instructions(func):
    if ins.opname in ('EXTENDED_ARG', 'CACHE'):
        continue
    pos = ins.positions
    line = pos[0] if pos else None
    print(f"  {ins.offset:4d}  {ins.opname:30s} {ins.argrepr:30s}  line={line}")
