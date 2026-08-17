"""分析 future_position.pyc 中 _close_holding 和 make_trade 的字节码差异。"""
import sys
import dis
import marshal
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load original pyc
pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc"
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    if flags & 0x1:
        f.read(8)  # source hash
    else:
        f.read(8)  # timestamp + size
    code = marshal.load(f)

# Load decompiled OK.py
ok_path = pyc_path.replace('.pyc', 'OK.py')
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def find_code_object(code_obj, name):
    """Recursively find a code object by name."""
    if code_obj.co_name == name:
        return code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result = find_code_object(const, name)
            if result:
                return result
    return None

def get_instructions(code_obj):
    """Get list of (offset, opname, arg, argstr) tuples."""
    instrs = []
    for instr in dis.get_instructions(code_obj):
        instrs.append((instr.offset, instr.opname, instr.arg, instr.argrepr))
    return instrs

targets = ['_close_holding', 'make_trade']

for target_name in targets:
    orig_co = find_code_object(code, target_name)
    decomp_co = find_code_object(decomp_code, target_name)
    
    if not orig_co:
        print(f"\n{'='*80}")
        print(f"FUNCTION: {target_name} - NOT FOUND in original")
        continue
    if not decomp_co:
        print(f"\n{'='*80}")
        print(f"FUNCTION: {target_name} - NOT FOUND in decompiled")
        continue
    
    orig_instrs = get_instructions(orig_co)
    decomp_instrs = get_instructions(decomp_co)
    
    print(f"\n{'='*80}")
    print(f"FUNCTION: {target_name}")
    print(f"  orig instructions: {len(orig_instrs)}")
    print(f"  decomp instructions: {len(decomp_instrs)}")
    
    # Find first difference
    min_len = min(len(orig_instrs), len(decomp_instrs))
    first_diff_idx = None
    for i in range(min_len):
        o = orig_instrs[i]
        d = decomp_instrs[i]
        if o[1] != d[1]:  # opname differs
            first_diff_idx = i
            break
    
    if first_diff_idx is None and len(orig_instrs) == len(decomp_instrs):
        print("  NO DIFFERENCES")
        continue
    
    if first_diff_idx is not None:
        start = max(0, first_diff_idx - 5)
        end = min(max(len(orig_instrs), len(decomp_instrs)), first_diff_idx + 20)
        print(f"\n  First diff at index {first_diff_idx}:")
        print(f"  Context [{start}..{end}]:")
        print(f"  {'idx':>4}  {'ORIG':<40} {'DECOMP':<40}")
        for i in range(start, end):
            o = orig_instrs[i] if i < len(orig_instrs) else ('', 'MISSING', '', '')
            d = decomp_instrs[i] if i < len(decomp_instrs) else ('', 'MISSING', '', '')
            marker = '>>' if i == first_diff_idx else '  '
            o_str = f"{o[1]} {o[3]}" if o[1] != 'MISSING' else '---'
            d_str = f"{d[1]} {d[3]}" if d[1] != 'MISSING' else '---'
            print(f"  {marker}{i:4d}  {o_str:<40} {d_str:<40}")
    
    # Also show source around the relevant function
    lines = source.split('\n')
    in_func = False
    func_lines = []
    for line in lines:
        if f'def {target_name}' in line:
            in_func = True
        if in_func:
            func_lines.append(line)
            if len(func_lines) > 1 and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                break
    if func_lines:
        print(f"\n  Decompiled source (first 30 lines):")
        for i, line in enumerate(func_lines[:30]):
            print(f"    {i+1:3d}  {line}")
