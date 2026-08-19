#!/usr/bin/env python3
"""Dump decompiled bytecode for validate_data"""

import dis
import marshal
import types
import io

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

# Load decompiled
with open("decompiler_test_comprehensive_decompiled_r03_clean.py", 'rb') as f:
    raw = f.read()
for enc in ['utf-16', 'utf-8', 'latin-1']:
    try:
        source = raw.decode(enc)
        break
    except:
        continue
decomp_code = compile(source, "decompiled", 'exec')
decomp_codes = extract_all(decomp_code)

vd = decomp_codes.get("DataProcessor.validate_data")

output = io.StringIO()
print(f"co_consts: {vd.co_consts}", file=output)
print(f"co_names: {vd.co_names}", file=output)
print(f"co_varnames: {vd.co_varnames}", file=output)
print(f"co_exceptiontable: {vd.co_exceptiontable}", file=output)
print(f"\n--- Disassembly ---", file=output)
for instr in dis.get_instructions(vd):
    argval = instr.argval if instr.argval is not None else ''
    if isinstance(argval, types.CodeType):
        argval = f"<code {argval.co_name}>"
    print(f"  {instr.offset:4d}  {instr.opname:30s} {instr.arg if instr.arg is not None else '':>5}  {argval}", file=output)

with open("r03_decomp_vd_disasm.txt", "w", encoding="utf-8") as f:
    f.write(output.getvalue())

print("Written to r03_decomp_vd_disasm.txt")