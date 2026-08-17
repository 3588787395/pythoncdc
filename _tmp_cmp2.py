"""Compile future_positionOK.py and compare make_trade bytecode with original pyc."""
import dis
import marshal
import types
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load original pyc
pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc"
with open(pyc_path, 'rb') as f:
    f.read(4)  # magic
    f.read(4)  # flags
    f.read(8)  # timestamp + size
    orig_code = marshal.load(f)

# Load decompiled OK.py
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def find_code_object(code_obj, name):
    if code_obj.co_name == name:
        return code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result = find_code_object(const, name)
            if result:
                return result
    return None

# Noise instructions to filter
NOISE = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'PUSH_EXC_INFO',
         'COPY_FREE_VARS', 'MAKE_CELL', 'EXTENDED_ARG', 'PRECALL'}

def get_filtered_instructions(code_obj):
    return [(i.offset, i.opname, i.arg, i.argrepr) 
            for i in dis.get_instructions(code_obj)
            if i.opname not in NOISE]

target = 'make_trade'
orig_co = find_code_object(orig_code, target)
decomp_co = find_code_object(decomp_code, target)

if not orig_co or not decomp_co:
    print(f"Could not find {target}")
    sys.exit(1)

orig_instrs = get_filtered_instructions(orig_co)
decomp_instrs = get_filtered_instructions(decomp_co)

print(f"Function: {target}")
print(f"  Original instructions (filtered): {len(orig_instrs)}")
print(f"  Decompiled instructions (filtered): {len(decomp_instrs)}")

# Find first diff
min_len = min(len(orig_instrs), len(decomp_instrs))
first_diff = None
for i in range(min_len):
    if orig_instrs[i][1] != decomp_instrs[i][1]:  # opname differs
        first_diff = i
        break

if first_diff is None and len(orig_instrs) == len(decomp_instrs):
    print("  NO DIFFERENCES!")
else:
    if first_diff is not None:
        start = max(0, first_diff - 5)
        end = min(max(len(orig_instrs), len(decomp_instrs)), first_diff + 30)
        print(f"\n  First diff at filtered index {first_diff}:")
        print(f"  {'idx':>4}  {'ORIG':<45} {'DECOMP':<45}")
        for i in range(start, end):
            o = orig_instrs[i] if i < len(orig_instrs) else (0, 'MISSING', 0, '')
            d = decomp_instrs[i] if i < len(decomp_instrs) else (0, 'MISSING', 0, '')
            marker = '>>' if i == first_diff else '  '
            o_str = f"{o[1]} {o[3]}" if o[1] != 'MISSING' else '---'
            d_str = f"{d[1]} {d[3]}" if d[1] != 'MISSING' else '---'
            print(f"  {marker}{i:4d}  {o_str:<45} {d_str:<45}")

# Also show source around the relevant lines
lines = source.split('\n')
in_func = False
func_start = 0
for i, line in enumerate(lines):
    if f'def {target}' in line:
        in_func = True
        func_start = i
    if in_func and i > func_start and line.strip().startswith('def '):
        break
    if in_func:
        print(f"  {i+1:4d}  {line}")
