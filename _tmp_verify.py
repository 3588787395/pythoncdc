import marshal, types, dis, sys, io, struct
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions

pyc_file = 'site-packages/IQEngine/core/asset.pyc'

# Get original bytecode
with open(pyc_file, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Decompile
src = decompile_pyc(pyc_file)

# Compile decompiled source
try:
    compiled = compile(src, '<decompiled>', 'exec')
except SyntaxError as e:
    print(f"SyntaxError: {e}")
    sys.exit(1)

# Compare all nested code objects
def get_all_codes(code_obj, prefix=''):
    result = {prefix + code_obj.co_name: code_obj}
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(get_all_codes(const, prefix + code_obj.co_name + '.'))
    return result

orig_codes = get_all_codes(code, '')
new_codes = get_all_codes(compiled, '')

mismatches = 0
total = 0
for name, orig_co in sorted(orig_codes.items()):
    if name not in new_codes:
        print(f"MISSING: {name}")
        mismatches += 1
        continue
    new_co = new_codes[name]
    total += 1
    orig_instrs = get_bytecode_instructions(orig_co)
    new_instrs = get_bytecode_instructions(new_co)
    if orig_instrs != new_instrs:
        mismatches += 1
        print(f"MISMATCH: {name}")
        # Show first difference
        for i, (o, n) in enumerate(zip(orig_instrs, new_instrs)):
            if o != n:
                print(f"  Instr {i}: orig={o} vs new={n}")
                break
        if len(orig_instrs) != len(new_instrs):
            print(f"  Length: orig={len(orig_instrs)} vs new={len(new_instrs)}")
    else:
        print(f"OK: {name}")

print(f"\n=== Summary: {total - mismatches}/{total} matched, {mismatches} mismatches ===")
