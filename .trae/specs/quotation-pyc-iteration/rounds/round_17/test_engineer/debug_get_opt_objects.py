"""R17 调试 get_opt_objects 函数的原始字节码"""
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

def find_code(co, name):
    for const in co.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == name:
            return const
    return None

fn_code = find_code(code_obj, 'get_opt_objects')
print("=== 原始字节码 (get_opt_objects) ===")
dis.dis(fn_code)
