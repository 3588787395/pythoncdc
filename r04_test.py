#!/usr/bin/env python3
"""Round 4 test: verify fix effectiveness"""

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
        orig_str = normalize_instr(orig)
        decomp_str = normalize_instr(decomp)
        if orig_str != decomp_str:
            diffs.append({'offset': i, 'original': orig_str, 'decompiled': decomp_str})
    return {'match': len(diffs) == 0, 'diff': diffs, 'orig_count': len(orig_instrs), 'decomp_count': len(decomp_instrs)}

orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
orig_codes = extract_all(orig_code)

with open("decompiler_test_comprehensive_decompiled_r04.py", 'rb') as f:
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
        mismatches.append({'function': name, 'error': 'Not found'})
        continue
    result = compare_bytecode(orig_co, decomp_co)
    if result['match']:
        matched += 1
    else:
        mismatches.append({
            'function': name,
            'total_diffs': len(result['diff']),
            'orig_count': result['orig_count'],
            'decomp_count': result['decomp_count'],
            'first_diffs': result['diff'][:5]
        })

total = len(orig_codes)
rate = (matched / total * 100) if total > 0 else 0
print(f"Total: {total}")
print(f"Matched: {matched}")
print(f"Success rate: {rate:.2f}%")
print(f"Mismatches: {len(mismatches)}")
for m in mismatches[:10]:
    fn = m['function']
    if 'error' in m:
        print(f"  {fn}: {m['error']}")
    else:
        print(f"  {fn}: {m['total_diffs']} diffs (orig={m['orig_count']}, decomp={m['decomp_count']})")
        for d in m.get('first_diffs', [])[:3]:
            print(f"    [{d['offset']}] orig={d['original']} decomp={d['decompiled']}")