#!/usr/bin/env python3
"""Compare validate_data excluding EXTENDED_ARG and jump target offsets"""

import dis, marshal, types

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    result = {name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_prefix = name + "." if name != "<module>" else ""
            result.update(extract_all(const, new_prefix))
    return result

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

with open("decompiler_test_comprehensive_decompiled_r06.py", 'rb') as f:
    raw = f.read()
for enc in ['utf-16', 'utf-8', 'latin-1']:
    try: source = raw.decode(enc); break
    except: continue
decomp_code = compile(source, "decompiled", 'exec')
decomp_codes = extract_all(decomp_code)

target = "DataProcessor.validate_data"
orig_co = orig_codes[target]
decomp_co = decomp_codes[target]

# Remove EXTENDED_ARG and compare opname+argval (not offsets)
orig_instrs = [i for i in dis.get_instructions(orig_co) if i.opname != 'EXTENDED_ARG']
decomp_instrs = [i for i in dis.get_instructions(decomp_co) if i.opname != 'EXTENDED_ARG']

print(f"Original (no EXTENDED_ARG): {len(orig_instrs)} instructions")
print(f"Decompiled: {len(decomp_instrs)} instructions")

# Compare opname only (not jump targets which differ due to offset)
JUMP_OPS = {'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
            'JUMP_FORWARD', 'JUMP_BACKWARD', 'FOR_ITER',
            'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'}

real_diffs = 0
for i in range(max(len(orig_instrs), len(decomp_instrs))):
    orig = orig_instrs[i] if i < len(orig_instrs) else None
    decomp = decomp_instrs[i] if i < len(decomp_instrs) else None
    if orig is None:
        real_diffs += 1
        print(f"  EXTRA in decomp @{i}: {decomp.opname} {decomp.argval}")
        continue
    if decomp is None:
        real_diffs += 1
        print(f"  MISSING in decomp @{i}: {orig.opname} {orig.argval}")
        continue
    if orig.opname != decomp.opname:
        real_diffs += 1
        print(f"  OPNAME DIFF @{i}: orig={orig.opname} {orig.argval} | decomp={decomp.opname} {decomp.argval}")
        continue
    # Same opname, check argval (but skip jump targets)
    if orig.opname in JUMP_OPS:
        continue  # Jump targets will differ due to offset
    if orig.argval != decomp.argval:
        # Skip CodeType constants (they have different ids)
        if isinstance(orig.argval, types.CodeType) and isinstance(decomp.argval, types.CodeType):
            if orig.argval.co_name == decomp.argval.co_name:
                continue
        real_diffs += 1
        print(f"  ARGVAL DIFF @{i}: {orig.opname} orig={orig.argval} | decomp={decomp.argval}")

print(f"\nReal diffs (excluding jump targets): {real_diffs}")
print(f"Missing instructions: {len(orig_instrs) - len(decomp_instrs)}")