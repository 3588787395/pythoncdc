#!/usr/bin/env python3
"""Round 3 real test: compare bytecode with clean code state"""

import sys
import os
import json
import types
import dis
import marshal
from pathlib import Path

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_all_code_objects(const))
    return result

def normalize_instr(instr):
    """Normalize instruction for comparison - ignore code object addresses and file paths"""
    if instr is None:
        return None
    # For LOAD_CONST with code objects, only compare co_name
    if instr.opname == 'LOAD_CONST' and isinstance(instr.argval, types.CodeType):
        return f"{instr.opname} <code object {instr.argval.co_name}>"
    # For jump instructions, compare offset + opname
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
            diffs.append({
                'offset': i * 2,
                'original': orig_str,
                'decompiled': decomp_str
            })
    
    return {
        'match': len(diffs) == 0,
        'diff': diffs,
        'orig_count': len(orig_instrs),
        'decomp_count': len(decomp_instrs)
    }

def compare_pyc_files(orig_pyc, decomp_py):
    orig_code = load_code_from_pyc(orig_pyc)
    orig_codes = extract_all_code_objects(orig_code)
    
    with open(decomp_py, 'rb') as f:
        raw = f.read()
    
    source = None
    for enc in ['utf-16', 'utf-8', 'latin-1']:
        try:
            source = raw.decode(enc)
            break
        except:
            continue
    
    if source is None:
        return {'error': 'Cannot decode file'}
    
    try:
        decomp_code = compile(source, decomp_py, 'exec')
    except SyntaxError as e:
        return {
            'total_functions': len(orig_codes),
            'matched': 0,
            'mismatches': [{'function': '<module>', 'error': str(e)}],
            'success_rate': 0.0,
            'syntax_error': str(e)
        }
    
    decomp_codes = extract_all_code_objects(decomp_code)
    
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
    return {
        'total_functions': total,
        'matched': matched,
        'mismatches': mismatches,
        'success_rate': rate
    }

if __name__ == '__main__':
    orig = "decompiler_test_comprehensive.cpython-311.pyc"
    decomp = "decompiler_test_comprehensive_decompiled_r03_clean.py"
    result = compare_pyc_files(orig, decomp)
    print(f"Total: {result['total_functions']}")
    print(f"Matched: {result['matched']}")
    print(f"Success rate: {result['success_rate']:.2f}%")
    print(f"Mismatches: {len(result['mismatches'])}")
    for m in result['mismatches'][:10]:
        fn = m['function']
        if 'error' in m:
            print(f"  {fn}: {m['error']}")
        else:
            print(f"  {fn}: {m['total_diffs']} diffs (orig={m['orig_count']}, decomp={m['decomp_count']})")