#!/usr/bin/env python3
"""Round 5 verification"""

import dis
import marshal
import types

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
    if instr is None:
        return None
    if instr.opname == 'LOAD_CONST' and isinstance(instr.argval, types.CodeType):
        return f"{instr.opname} <code {instr.argval.co_name}>"
    return f"{instr.opname} {instr.argval if instr.argval is not None else ''}".strip()

def compare_bytecode(orig_co, decomp_co):
    orig_instrs = list(dis.get_instructions(orig_co))
    decomp_instrs = list(dis.get_instructions(decomp_co))
    diffs = []
    max_len = max(len(orig_instrs), len(decomp_instrs))
    for i in range(max_len):
        orig = orig_instrs[i] if i < len(orig_instrs) else None
        decomp = decomp_instrs[i] if i < len(decomp_instrs) else None
        if normalize_instr(orig) != normalize_instr(decomp):
            diffs.append(i)
    return len(diffs) == 0, len(diffs), len(orig_instrs), len(decomp_instrs)

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

with open("decompiler_test_comprehensive_decompiled_r05.py", 'rb') as f:
    raw = f.read()
for enc in ['utf-16', 'utf-8', 'latin-1']:
    try:
        source = raw.decode(enc)
        break
    except:
        continue
decomp_code = compile(source, "decompiled", 'exec')
decomp_codes = extract_all(decomp_code)

matched = 0
mismatches = []
for name, orig_co in orig_codes.items():
    if name.startswith('<') and name.endswith('>'):
        continue
    decomp_co = decomp_codes.get(name)
    if decomp_co is None:
        mismatches.append((name, 'Not found', 0, 0, 0))
        continue
    match, ndiffs, orig_n, decomp_n = compare_bytecode(orig_co, decomp_co)
    if match:
        matched += 1
    else:
        mismatches.append((name, ndiffs, orig_n, decomp_n))

total = len(orig_codes)
rate = (matched / total * 100) if total > 0 else 0
print(f"Total: {total}")
print(f"Matched: {matched}")
print(f"Success rate: {rate:.2f}%")
print(f"Mismatches: {len(mismatches)}")
for m in mismatches:
    print(f"  {m[0]}: {m[1]} diffs (orig={m[2]}, decomp={m[3]})")