#!/usr/bin/env python3
"""Round 8 verification"""

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

# Use the fresh output from pycdc
with open("_r108_out5.py", 'r', encoding='utf-8', errors='replace') as f:
    source = f.read()
decomp_code = compile(source, "decompiled", 'exec')
decomp_codes = extract_all(decomp_code)

matched = 0
mismatches = []
for name, orig_co in orig_codes.items():
    if name.startswith('<') and name.endswith('>'): continue
    decomp_co = decomp_codes.get(name)
    if decomp_co is None:
        mismatches.append((name, 'Not found', 0, 0)); continue
    orig_instrs = list(dis.get_instructions(orig_co))
    decomp_instrs = list(dis.get_instructions(decomp_co))
    diffs = sum(1 for i in range(max(len(orig_instrs), len(decomp_instrs)))
                if normalize_instr(orig_instrs[i] if i < len(orig_instrs) else None) !=
                   normalize_instr(decomp_instrs[i] if i < len(decomp_instrs) else None))
    if diffs == 0: matched += 1
    else: mismatches.append((name, diffs, len(orig_instrs), len(decomp_instrs)))

total = len(orig_codes)
print(f"Total: {total}")
print(f"Matched: {matched}")
print(f"Success rate: {matched/total*100:.2f}%")
for m in mismatches:
    print(f"  {m[0]}: {m[1]} diffs (orig={m[2]}, decomp={m[3]})")
