#!/usr/bin/env python3
"""Show detailed diff for validate_data after R6 fix"""

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

def normalize_instr(instr):
    if instr is None: return None
    if instr.opname == 'LOAD_CONST' and isinstance(instr.argval, types.CodeType):
        return f"{instr.opname} <code {instr.argval.co_name}>"
    return f"{instr.opname} {instr.argval if instr.argval is not None else ''}".strip()

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

orig_instrs = list(dis.get_instructions(orig_co))
decomp_instrs = list(dis.get_instructions(decomp_co))

print(f"Original: {len(orig_instrs)} instructions")
print(f"Decompiled: {len(decomp_instrs)} instructions")

# Show diffs
max_len = max(len(orig_instrs), len(decomp_instrs))
for i in range(max_len):
    orig = orig_instrs[i] if i < len(orig_instrs) else None
    decomp = decomp_instrs[i] if i < len(decomp_instrs) else None
    orig_s = normalize_instr(orig)
    decomp_s = normalize_instr(decomp)
    if orig_s != decomp_s:
        print(f"  DIFF @{i}: orig={orig_s} | decomp={decomp_s}")