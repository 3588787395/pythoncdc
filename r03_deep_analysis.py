#!/usr/bin/env python3
"""Deep analysis of validate_data and exception_handling_complex bytecode differences"""

import dis
import marshal
import types
import sys
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

def print_instructions(code, label):
    print(f"\n{'='*80}")
    print(f"{label}: {code.co_name}")
    print(f"{'='*80}")
    for instr in dis.get_instructions(code):
        argval = instr.argval if instr.argval is not None else ''
        if isinstance(argval, types.CodeType):
            argval = f"<code {argval.co_name}>"
        print(f"  {instr.offset:4d}  {instr.opname:30s} {instr.arg if instr.arg is not None else '':>5}  {argval}")

def main():
    pyc_path = "decompiler_test_comprehensive.cpython-311.pyc"
    orig_code = load_code_from_pyc(pyc_path)
    
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
    
    # Compare validate_data
    for func_name in ['validate_data', 'exception_handling_complex']:
        print(f"\n{'#'*80}")
        print(f"# Analyzing: {func_name}")
        print(f"{'#'*80}")
        
        orig = find_code_by_name(orig_code, func_name)
        decomp = find_code_by_name(decomp_code, func_name)
        
        if orig:
            print_instructions(orig, "ORIGINAL")
        if decomp:
            print_instructions(decomp, "DECOMPILED")
        
        # Show side-by-side diff for first 30 instructions
        if orig and decomp:
            orig_instrs = list(dis.get_instructions(orig))
            decomp_instrs = list(dis.get_instructions(decomp))
            
            print(f"\n--- Side-by-side diff (first 40 instructions) ---")
            max_len = min(40, max(len(orig_instrs), len(decomp_instrs)))
            for i in range(max_len):
                o = orig_instrs[i] if i < len(orig_instrs) else None
                d = decomp_instrs[i] if i < len(decomp_instrs) else None
                
                o_str = f"{o.opname:25s} {o.argval}" if o else "(missing)"
                d_str = f"{d.opname:25s} {d.argval}" if d else "(missing)"
                
                # Normalize code object references
                if o and isinstance(o.argval, types.CodeType):
                    o_str = f"{o.opname:25s} <code {o.argval.co_name}>"
                if d and isinstance(d.argval, types.CodeType):
                    d_str = f"{d.opname:25s} <code {d.argval.co_name}>"
                
                match = "OK" if o_str == d_str else "DIFF"
                print(f"  [{i:3d}] O: {o_str:60s} | D: {d_str:60s} {match}")

if __name__ == '__main__':
    main()