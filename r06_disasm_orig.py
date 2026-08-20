#!/usr/bin/env python3
"""Show original bytecode for validate_data around offset 400-540"""

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

target = "DataProcessor.validate_data"
orig_co = orig_codes[target]

print("=== Original bytecode ===")
for instr in dis.get_instructions(orig_co):
    if instr.offset >= 400 and instr.offset <= 540:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")

print()
print("=== Decompiled bytecode ===")
with open("decompiler_test_comprehensive_decompiled_r05b.py", 'rb') as f:
    raw = f.read()
for enc in ['utf-16', 'utf-8', 'latin-1']:
    try: source = raw.decode(enc); break
    except: continue
decomp_code = compile(source, "decompiled", 'exec')
decomp_codes = extract_all(decomp_code)
decomp_co = decomp_codes[target]

for instr in dis.get_instructions(decomp_co):
    if instr.offset >= 350 and instr.offset <= 450:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")