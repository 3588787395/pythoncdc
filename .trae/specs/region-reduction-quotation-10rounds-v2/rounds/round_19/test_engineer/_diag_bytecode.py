"""R19 诊断：完整反汇编 get_str_data 的字节码，定位所有 POP_JUMP_FORWARD_IF_FALSE，
识别 7 个三元表达式的入口和出口。"""
import sys, dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# 找到 get_str_data code object
target_co = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'get_str_data':
        target_co = const
        break

print(f"Found get_str_data: co_name={target_co.co_name}")

# 完整反汇编
print("\n=== Full disassembly (filtered) ===")
SKIP = ('EXTENDED_ARG', 'CACHE', 'NOP')
instrs = [i for i in dis.get_instructions(target_co) if i.opname not in SKIP]
for idx, ins in enumerate(instrs):
    print(f"  idx={idx:>3} off={ins.offset:>4} {ins.opname:<32} {ins.argval!r}")

# 找所有 POP_JUMP_FORWARD_IF_FALSE
print("\n=== POP_JUMP_FORWARD_IF_FALSE / JUMP_FORWARD pattern ===")
for idx, ins in enumerate(instrs):
    if ins.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                      'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                      'JUMP_FORWARD', 'JUMP_BACKWARD'):
        print(f"  idx={idx:>3} off={ins.offset:>4} {ins.opname:<32} -> {ins.argval}")

# 找所有 STORE_SUBSCR
print("\n=== STORE_SUBSCR / BUILD_CONST_KEY_MAP ===")
for idx, ins in enumerate(instrs):
    if ins.opname in ('STORE_SUBSCR', 'BUILD_CONST_KEY_MAP', 'BUILD_MAP', 'BUILD_TUPLE', 'BUILD_LIST'):
        print(f"  idx={idx:>3} off={ins.offset:>4} {ins.opname:<32} arg={ins.arg} argval={ins.argval!r}")
