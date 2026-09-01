"""Categorize all 21 failures by difference type."""
import sys, dis, types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def collect_codes(co, prefix=''):
    name = prefix + co.co_name if prefix else co.co_name
    if co.co_name == '<module>' and not prefix:
        name = '<module>'
    result = {name: co}
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            result.update(collect_codes(const, sub_prefix))
    return result

pyc_codes = collect_codes(code_obj)

with open(SRC) as f:
    src = f.read()
compiled = compile(src, '<decompiled>', 'exec')
src_codes = collect_codes(compiled)

def get_instrs(co):
    return [(ins.offset, ins.opname, ins.argval) for ins in dis.get_instructions(co) if ins.opname not in ('EXTENDED_ARG', 'CACHE')]

# Read failure list
with open('/tmp/r23_failures.txt') as f:
    failures = [l.strip() for l in f if l.strip()]

for name in failures:
    pc = pyc_codes[name]
    sc = src_codes[name]
    pi = get_instrs(pc)
    si = get_instrs(sc)
    
    # Find first diff
    first_diff = None
    for i in range(max(len(pi), len(si))):
        a = pi[i] if i < len(pi) else None
        b = si[i] if i < len(si) else None
        if not (a and b and a[1] == b[1] and a[2] == b[2]):
            first_diff = i
            break
    
    if first_diff is None:
        print(f"{name}: IDENTICAL (shouldn't be in failures)")
        continue
    
    a = pi[first_diff] if first_diff < len(pi) else None
    b = si[first_diff] if first_diff < len(si) else None
    
    # Categorize
    diff_type = "unknown"
    if a and b:
        if a[1] == b[1] and a[0] == b[0]:
            # Same op, same offset, different argval (jump target)
            if 'JUMP' in a[1] or 'FOR_ITER' in a[1]:
                target_diff = (b[2] or 0) - (a[2] or 0) if isinstance(a[2], int) and isinstance(b[2], int) else '?'
                diff_type = f"jump_target_diff({target_diff})"
            else:
                diff_type = f"argval_diff({a[2]} vs {b[2]})"
        elif a[1] != b[1]:
            diff_type = f"opname_diff({a[1]} vs {b[1]})"
        elif a[0] != b[0]:
            diff_type = f"offset_diff({a[0]} vs {b[0]})"
    elif a and not b:
        diff_type = "src_missing"
    elif b and not a:
        diff_type = "src_extra"
    
    count_diff = len(si) - len(pi)
    
    # Show first diff context
    a_str = f"{a[0]:4d} {a[1]} {a[2]}" if a else "(none)"
    b_str = f"{b[0]:4d} {b[1]} {b[2]}" if b else "(none)"
    
    print(f"{name}: p={len(pi)} s={len(si)} diff={count_diff:+d} type={diff_type}")
    print(f"  first_diff[{first_diff}]: p={a_str}  s={b_str}")
