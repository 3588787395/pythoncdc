"""Verify Round 01: decompile IQCommon/__init__.pyc and check bytecode match."""
import sys, os, dis, marshal, types

sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
os.chdir('f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

pyc_path = 'site-packages/IQCommon/__init__.pyc'

# Load original code
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

# Decompile
decomp_source = decompile_pyc(pyc_path)
print("=== Decompiled source ===")
print(decomp_source)
print("=== End ===")

# Strip header lines
lines = decomp_source.split('\n')
while lines and (lines[0].startswith('#') or lines[0].strip() == ''):
    lines.pop(0)
decomp_source = '\n'.join(lines)

# Compile decompiled
decomp_code = compile(decomp_source, '<decompiled>', 'exec')

# Compare
def compare_code_objects(orig_code, decomp_code, prefix=""):
    if orig_code.co_code != decomp_code.co_code:
        print(f"  {prefix}code mismatch")
        orig_instrs = list(dis.get_instructions(orig_code))
        decomp_instrs = list(dis.get_instructions(decomp_code))
        for i in range(max(len(orig_instrs), len(decomp_instrs))):
            o = orig_instrs[i] if i < len(orig_instrs) else None
            d = decomp_instrs[i] if i < len(decomp_instrs) else None
            if o is None:
                print(f"  Extra: {d.opname} {d.argrepr}")
                break
            if d is None:
                print(f"  Missing: {o.opname} {o.argrepr}")
                break
            if o.opname != d.opname or o.arg != d.arg:
                print(f"  [{i}] ORIG: {o.opname} {o.argrepr}")
                print(f"  [{i}] DECP: {d.opname} {d.argrepr}")
                break
        return False
    if orig_code.co_exceptiontable != decomp_code.co_exceptiontable:
        print(f"  {prefix}exception table mismatch")
        return False
    orig_funcs = [c for c in orig_code.co_consts if hasattr(c, 'co_code')]
    decomp_funcs = [c for c in decomp_code.co_consts if hasattr(c, 'co_code')]
    if len(orig_funcs) != len(decomp_funcs):
        print(f"  {prefix}func count {len(orig_funcs)} vs {len(decomp_funcs)}")
        return False
    for of, df in zip(orig_funcs, decomp_funcs):
        if not compare_code_objects(of, df, f"{of.co_name}: "):
            return False
    return True

ok = compare_code_objects(orig_code, decomp_code)
print(f"\nBytecode match: {ok}")

# Check if OK file exists
ok_path = pyc_path.replace('.pyc', 'OK.py')
if os.path.exists(ok_path):
    print(f"OK file exists: {ok_path}")
else:
    print(f"OK file NOT found: {ok_path}")
