"""R19 测试工程师：查看 check_frequency 的原始字节码"""
import sys
import dis

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
target_name = 'check_frequency'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == target_name:
        target = const
        break

print(f'=== {target_name} original bytecode ===')
dis.dis(target)
