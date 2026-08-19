#!/usr/bin/env python3
"""Round 5: Detailed analysis of remaining validate_data diff"""

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

def format_instr(instr):
    if instr is None:
        return "(missing)"
    argval = instr.argval if instr.argval is not None else ''
    if isinstance(argval, types.CodeType):
        argval = f"<code {argval.co_name}>"
    return f"{instr.opname:25s} {argval}"

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

for func_name in ['DataProcessor.validate_data', 'DataProcessor.exception_handling_complex']:
    orig = orig_codes.get(func_name)
    decomp = decomp_codes.get(func_name)

    if not orig or not decomp:
        continue

    orig_instrs = list(dis.get_instructions(orig))
    decomp_instrs = list(dis.get_instructions(decomp))

    output = io.StringIO()
    print(f"\n{'='*80}", file=output)
    print(f"Function: {func_name}", file=output)
    print(f"Original: {len(orig_instrs)} instructions", file=output)
    print(f"Decompiled: {len(decomp_instrs)} instructions", file=output)
    print(f"{'='*80}", file=output)

    # Find first divergence point
    first_diff = -1
    for i in range(min(len(orig_instrs), len(decomp_instrs))):
        o = orig_instrs[i]
        d = decomp_instrs[i]
        o_str = format_instr(o)
        d_str = format_instr(d)
        if o_str != d_str:
            first_diff = i
            break

    if first_diff >= 0:
        print(f"\nFirst divergence at instruction index {first_diff}:", file=output)
        print(f"  Original:  offset={orig_instrs[first_diff].offset}  {format_instr(orig_instrs[first_diff])}", file=output)
        print(f"  Decompiled: offset={decomp_instrs[first_diff].offset}  {format_instr(decomp_instrs[first_diff])}", file=output)

        # Show context around divergence
        start = max(0, first_diff - 3)
        end = min(max(len(orig_instrs), len(decomp_instrs)), first_diff + 20)
        print(f"\nContext (instructions {start} to {end}):", file=output)
        for i in range(start, end):
            o = orig_instrs[i] if i < len(orig_instrs) else None
            d = decomp_instrs[i] if i < len(decomp_instrs) else None
            o_str = format_instr(o)
            d_str = format_instr(d)
            match = "OK" if o_str == d_str else "DIFF"
            o_off = f"{o.offset:4d}" if o else "    "
            d_off = f"{d.offset:4d}" if d else "    "
            print(f"  [{i:3d}] O@{o_off} D@{d_off} | O: {o_str:55s} | D: {d_str:55s} {match}", file=output)

    # Also check if EXTENDED_ARG is present in original but not decompiled
    orig_has_ext = any(i.opname == 'EXTENDED_ARG' for i in orig_instrs)
    decomp_has_ext = any(i.opname == 'EXTENDED_ARG' for i in decomp_instrs)
    print(f"\nEXTENDED_ARG in original: {orig_has_ext}", file=output)
    print(f"EXTENDED_ARG in decompiled: {decomp_has_ext}", file=output)

    # Check exception table differences
    print(f"\nOriginal exception table: {orig.co_exceptiontable.hex()}", file=output)
    print(f"Decompiled exception table: {decomp.co_exceptiontable.hex()}", file=output)

    # Check co_consts differences
    print(f"\nOriginal co_consts: {orig.co_consts}", file=output)
    print(f"Decompiled co_consts: {decomp.co_consts}", file=output)

    filename = f"r05_{func_name.split('.')[-1]}_diff.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    print(f"Written to {filename}")