#!/usr/bin/env python3
"""Deep analysis - write to UTF-8 file"""

import dis
import marshal
import types
import sys
import io
from pathlib import Path

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def find_code_by_name(code, name_path):
    parts = name_path.split('.')
    current = code
    for part in parts:
        if part == '<module>':
            continue
        found = None
        for const in current.co_consts:
            if isinstance(const, types.CodeType) and const.co_name == part:
                found = const
                break
        if found is None:
            return None
        current = found
    return current

def format_instr(instr):
    if instr is None:
        return "(missing)"
    argval = instr.argval if instr.argval is not None else ''
    if isinstance(argval, types.CodeType):
        argval = f"<code {argval.co_name}>"
    return f"{instr.opname:25s} {argval}"

def main():
    pyc_path = "decompiler_test_comprehensive.cpython-311.pyc"
    orig_code = load_code_from_pyc(pyc_path)
    
    with open("decompiler_test_comprehensive_decompiled_r03_clean.py", 'rb') as f:
        raw = f.read()
    for enc in ['utf-16', 'utf-8', 'latin-1']:
        try:
            source = raw.decode(enc)
            break
        except:
            continue
    decomp_code = compile(source, "decompiled", 'exec')
    
    output = io.StringIO()
    
    for func_name in ['validate_data', 'exception_handling_complex']:
        print(f"\n{'#'*80}", file=output)
        print(f"# Analyzing: {func_name}", file=output)
        print(f"{'#'*80}", file=output)
        
        orig = find_code_by_name(orig_code, func_name)
        decomp = find_code_by_name(decomp_code, func_name)
        
        if orig and decomp:
            orig_instrs = list(dis.get_instructions(orig))
            decomp_instrs = list(dis.get_instructions(decomp))
            
            print(f"\nOriginal: {len(orig_instrs)} instructions", file=output)
            print(f"Decompiled: {len(decomp_instrs)} instructions", file=output)
            
            print(f"\n--- Side-by-side diff (all instructions) ---", file=output)
            max_len = max(len(orig_instrs), len(decomp_instrs))
            for i in range(max_len):
                o = orig_instrs[i] if i < len(orig_instrs) else None
                d = decomp_instrs[i] if i < len(decomp_instrs) else None
                
                o_str = format_instr(o)
                d_str = format_instr(d)
                
                match = "OK" if o_str == d_str else "DIFF"
                print(f"  [{i:3d}] O: {o_str:55s} | D: {d_str:55s} {match}", file=output)
    
    with open("r03_diff_output.txt", "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    
    print("Analysis written to r03_diff_output.txt")

if __name__ == '__main__':
    main()