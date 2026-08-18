#!/usr/bin/env python3
"""Test Engineer: Decompile a pyc, compare bytecodes, generate report."""
import sys
import os
import dis
import types
import json
import marshal
import struct
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---- Bytecode comparison utilities (from testqouter/round1/base.py, simplified) ----

def load_pyc_code(pyc_path):
    """Load a .pyc file and return its top-level code object."""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        # Python 3.7+ has hash/algorithm fields
        if flags & 0x1:  # Hash-based
            f.read(8)  # hash + timestamp
        else:
            f.read(8)  # timestamp + size
        code = marshal.load(f)
    return code

def get_all_code_objects(code, prefix=''):
    """Recursively get all code objects from a code object."""
    result = {}
    result[prefix or '<module>'] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(get_all_code_objects(const, name))
    return result

def filter_noise_instrs(instrs):
    """Filter out noise instructions."""
    NOISE_OPS = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'}
    return [i for i in instrs if i.opname not in NOISE_OPS]

def normalize_argval(argval):
    """Normalize argval to remove recompilation identity noise."""
    if isinstance(argval, types.CodeType):
        return f"<code object {argval.co_name}>"
    if isinstance(argval, str):
        low = argval.lower()
        if (low.endswith('.py') or low.endswith('.pyc')) and ('/' in argval or '\\' in argval):
            return os.path.basename(argval)
    if isinstance(argval, frozenset):
        return frozenset(argval)
    return argval

def compare_instructions(orig_instrs, new_instrs):
    """Compare two instruction lists and return diffs."""
    orig_filtered = filter_noise_instrs(orig_instrs)
    new_filtered = filter_noise_instrs(new_instrs)
    
    diffs = []
    max_len = max(len(orig_filtered), len(new_filtered))
    
    for i in range(max_len):
        if i >= len(orig_filtered):
            diffs.append(('extra_in_new', i, new_filtered[i]))
        elif i >= len(new_filtered):
            diffs.append(('missing_in_new', i, orig_filtered[i]))
        else:
            o = orig_filtered[i]
            n = new_filtered[i]
            o_op = o.opname
            n_op = n.opname
            # Normalize jump target differences
            o_arg = normalize_argval(o.argval)
            n_arg = normalize_argval(n.argval)
            
            if o_op != n_op:
                diffs.append(('opcode_mismatch', i, o, n))
            elif o_arg != n_arg:
                # Check if it's just a jump offset difference
                if o_op in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                           'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                           'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                           'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                           'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                           'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
                           'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                           'FOR_ITER', 'SEND'):
                    diffs.append(('jump_offset_diff', i, o, n))
                else:
                    diffs.append(('argval_mismatch', i, o, n))
    
    return diffs

def decompile_pyc(pyc_path):
    """Decompile a pyc file using pycdc."""
    from pycdc import decompile_pyc as _decompile
    try:
        source = _decompile(pyc_path)
        # Clean up header lines
        lines = source.split('\n')
        clean_lines = []
        for line in lines:
            if line.startswith('# Source') or line.startswith('# File:'):
                continue
            clean_lines.append(line)
        return '\n'.join(clean_lines).strip()
    except Exception as e:
        traceback.print_exc()
        return None

def compile_source(source, filename='<decompiled>'):
    """Compile source code into a code object."""
    try:
        return compile(source, filename, 'exec')
    except SyntaxError as e:
        return f"SYNTAX_ERROR: {e}"

def run_test_engineer(pyc_path, round_dir):
    """Main test engineer workflow."""
    print(f"=== Test Engineer: {pyc_path} ===")
    
    # 1. Load original pyc
    orig_code = load_pyc_code(pyc_path)
    orig_funcs = get_all_code_objects(orig_code)
    print(f"Original code objects: {len(orig_funcs)}")
    
    # 2. Decompile
    source = decompile_pyc(pyc_path)
    if source is None:
        print("ERROR: Decompilation failed!")
        return None
    
    # Save decompiled source
    decompiled_path = os.path.join(round_dir, 'test_engineer', 'decompiled.py')
    with open(decompiled_path, 'w', encoding='utf-8') as f:
        f.write(source)
    print(f"Decompiled source saved to: {decompiled_path}")
    
    # 3. Compile decompiled source
    new_code = compile_source(source, os.path.basename(pyc_path).replace('.pyc', 'OK.py'))
    if isinstance(new_code, str):
        print(f"ERROR: Compilation failed: {new_code}")
        # Save report
        report_path = os.path.join(round_dir, 'test_engineer', 'decompile_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Decompile Report\n\n## Pyc: {pyc_path}\n\n## Status: COMPILATION FAILED\n\n{new_code}\n")
        return None
    
    new_funcs = get_all_code_objects(new_code)
    print(f"Decompiled code objects: {len(new_funcs)}")
    
    # 4. Compare bytecodes
    matched = 0
    total = 0
    mismatches = []
    
    for name, orig_func_code in orig_funcs.items():
        total += 1
        if name not in new_funcs:
            mismatches.append((name, 'missing_in_decompiled', None))
            continue
        
        new_func_code = new_funcs[name]
        orig_instrs = list(dis.get_instructions(orig_func_code))
        new_instrs = list(dis.get_instructions(new_func_code))
        
        diffs = compare_instructions(orig_instrs, new_instrs)
        if not diffs:
            matched += 1
        else:
            # Classify diffs
            true_diffs = [d for d in diffs if d[0] not in ('jump_offset_diff',)]
            jump_diffs = [d for d in diffs if d[0] == 'jump_offset_diff']
            if not true_diffs:
                matched += 1  # Only jump offset diffs, considered matched
            else:
                mismatches.append((name, 'bytecode_mismatch', diffs))
    
    success_rate = matched / total if total > 0 else 0
    print(f"\nResults: {matched}/{total} matched ({success_rate*100:.1f}%)")
    
    # 5. Generate report
    report_path = os.path.join(round_dir, 'test_engineer', 'decompile_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Decompile Report\n\n")
        f.write(f"## Pyc: {pyc_path}\n\n")
        f.write(f"## Success Rate: {matched}/{total} ({success_rate*100:.1f}%)\n\n")
        f.write(f"## Matched Functions:\n")
        for name in orig_funcs:
            if name not in [m[0] for m in mismatches]:
                f.write(f"  - {name} ✓\n")
        f.write(f"\n## Mismatched Functions:\n")
        for name, mtype, diffs in mismatches:
            f.write(f"  - {name}: {mtype}\n")
            if diffs:
                for d in diffs[:20]:
                    f.write(f"    - {d}\n")
                if len(diffs) > 20:
                    f.write(f"    ... and {len(diffs)-20} more\n")
        
        # Print bytecode for mismatched functions
        f.write(f"\n## Bytecode Diffs Detail:\n")
        for name, mtype, diffs in mismatches:
            if mtype == 'bytecode_mismatch' and name in orig_funcs and name in new_funcs:
                f.write(f"\n### {name}\n")
                orig_instrs = filter_noise_instrs(list(dis.get_instructions(orig_funcs[name])))
                new_instrs = filter_noise_instrs(list(dis.get_instructions(new_funcs[name])))
                f.write(f"Original ({len(orig_instrs)} instrs):\n```\n")
                for i in orig_instrs:
                    f.write(f"  {i.offset:4d} {i.opname:30s} {i.argrepr}\n")
                f.write(f"```\nDecompiled ({len(new_instrs)} instrs):\n```\n")
                for i in new_instrs:
                    f.write(f"  {i.offset:4d} {i.opname:30s} {i.argrepr}\n")
                f.write("```\n")
    
    print(f"Report saved to: {report_path}")
    return {
        'matched': matched,
        'total': total,
        'success_rate': success_rate,
        'mismatches': mismatches,
        'source': source,
        'orig_funcs': orig_funcs,
        'new_funcs': new_funcs,
    }

if __name__ == '__main__':
    pyc_path = sys.argv[1] if len(sys.argv) > 1 else 'site-packages/IQCommon/__init__.pyc'
    round_dir = sys.argv[2] if len(sys.argv) > 2 else '.trae/specs/site-packages-full-decompile-10rounds/rounds/round_01'
    run_test_engineer(pyc_path, round_dir)
