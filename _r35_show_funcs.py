"""R35 测试工程师：查看具体函数的反编译输出"""
import sys, os, dis, types, marshal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from testqouter.round1.base import decompile_pyc, get_bytecode_instructions

pyc_path = "site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc"

# Load original code
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Decompile
source = decompile_pyc(pyc_path)

# Find and show specific functions
# Show the source of get_orders and submit_order
lines = source.split('\n')

# Find get_orders function
in_func = False
func_lines = []
func_name = None
for line in lines:
    if line.startswith('def get_orders') or line.startswith('def submit_order') or line.startswith('def cancel_order') or line.startswith('def get_open_orders'):
        if func_lines and func_name:
            print(f"\n=== {func_name} (decompiled source) ===")
            print('\n'.join(func_lines[:30]))
            print("..." if len(func_lines) > 30 else "")
        func_name = line.split('(')[0].replace('def ', '')
        in_func = True
        func_lines = [line]
    elif in_func:
        if line and not line[0].isspace() and not line.startswith('#') and not line.startswith('def '):
            if func_lines:
                print(f"\n=== {func_name} (decompiled source) ===")
                print('\n'.join(func_lines[:30]))
                print("..." if len(func_lines) > 30 else "")
            in_func = False
            func_lines = []
        else:
            func_lines.append(line)

if func_lines and func_name:
    print(f"\n=== {func_name} (decompiled source) ===")
    print('\n'.join(func_lines[:30]))
    print("..." if len(func_lines) > 30 else "")

# Also show original bytecode for get_orders
def find_code(code, name):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                return c
            result = find_code(c, name)
            if result:
                return result
    return None

for fname in ['get_orders', 'get_open_orders']:
    fc = find_code(orig_code, fname)
    if fc:
        print(f"\n=== {fname} (original bytecode, first 20 instrs) ===")
        instrs = get_bytecode_instructions(fc)
        for i, inst in enumerate(instrs[:20]):
            print(f"  {i:3d} {inst.opname:30s} {inst.argval}")

# Now check disassembly of decompiled get_orders
decomp_code = compile(source, '<decompiled>', 'exec')
for fname in ['get_orders', 'get_open_orders']:
    fc = find_code(decomp_code, fname)
    if fc:
        print(f"\n=== {fname} (decompiled bytecode, first 20 instrs) ===")
        instrs = get_bytecode_instructions(fc)
        for i, inst in enumerate(instrs[:20]):
            print(f"  {i:3d} {inst.opname:30s} {inst.argval}")
