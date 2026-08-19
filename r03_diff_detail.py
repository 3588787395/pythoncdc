#!/usr/bin/env python3
"""Deep analysis of the two failing functions"""

import dis
import marshal
import types
import sys
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

def main():
    orig_code = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
    orig_codes = extract_all(orig_code)
    
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
    
    output = io.StringIO()
    
    for func_name in ['DataProcessor.validate_data', 'DataProcessor.exception_handling_complex']:
        print(f"\n{'#'*80}", file=output)
        print(f"# Analyzing: {func_name}", file=output)
        print(f"{'#'*80}", file=output)
        
        orig = orig_codes.get(func_name)
        decomp = decomp_codes.get(func_name)
        
        if not orig:
            print(f"  Original not found!", file=output)
            continue
        if not decomp:
            print(f"  Decompiled not found!", file=output)
            continue
            
        orig_instrs = list(dis.get_instructions(orig))
        decomp_instrs = list(dis.get_instructions(decomp))
        
        print(f"\nOriginal: {len(orig_instrs)} instructions", file=output)
        print(f"Decompiled: {len(decomp_instrs)} instructions", file=output)
        
        print(f"\n--- Side-by-side diff ---", file=output)
        max_len = max(len(orig_instrs), len(decomp_instrs))
        for i in range(max_len):
            o = orig_instrs[i] if i < len(orig_instrs) else None
            d = decomp_instrs[i] if i < len(decomp_instrs) else None
            
            o_str = format_instr(o)
            d_str = format_instr(d)
            
            match = "OK" if o_str == d_str else "DIFF"
            o_offset = f"{o.offset:4d}" if o else "    "
            d_offset = f"{d.offset:4d}" if d else "    "
            print(f"  [{i:3d}] O@{o_offset} D@{d_offset} | O: {o_str:55s} | D: {d_str:55s} {match}", file=output)
    
    with open("r03_diff_detail.txt", "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    
    print("Detail diff written to r03_diff_detail.txt")

if __name__ == '__main__':
    main()