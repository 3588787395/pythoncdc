#!/usr/bin/env python3
"""Round 06: Detailed diff for complex_expressions and exception_handling_examples."""
import sys, os, dis, types, marshal, struct, io
from pathlib import Path
from collections import OrderedDict

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from testqouter.round1.base import compare_bytecode, decompile_pyc, _filter_noise_instrs, _normalize_argval

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        f.read(8)
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    result = OrderedDict()
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    orig_code = load_code_from_pyc(PYC_PATH)
    orig_all = collect_all_code_objects(orig_code)
    source = decompile_pyc(PYC_PATH)
    decomp_code = compile(source, '<decompiled>', 'exec')
    decomp_all = collect_all_code_objects(decomp_code)

    for target_name in ['<module>.complex_expressions', '<module>.exception_handling_examples']:
        print(f"\n{'='*70}")
        print(f"DIFF: {target_name}")
        print(f"{'='*70}")
        
        orig_c = orig_all[target_name]
        decomp_c = decomp_all[target_name]
        
        result = compare_bytecode(orig_c, decomp_c)
        print(f"Match: {result['match']}")
        print(f"True diffs: {len(result['true_diffs'])}")
        print(f"Jump diffs: {len(result['jump_diffs'])}")
        
        # Show original bytecode
        print(f"\n--- Original bytecode ({target_name}) ---")
        orig_instrs = list(dis.get_instructions(orig_c))
        for i, instr in enumerate(orig_instrs):
            print(f"  {i:3d} {instr.offset:4d} {instr.opname:25s} {instr.argrepr}")
        
        # Show decompiled bytecode
        print(f"\n--- Decompiled bytecode ({target_name}) ---")
        decomp_instrs = list(dis.get_instructions(decomp_c))
        for i, instr in enumerate(decomp_instrs):
            print(f"  {i:3d} {instr.offset:4d} {instr.opname:25s} {instr.argrepr}")
        
        # Show true diffs
        if result['true_diffs']:
            print(f"\n--- True diffs ---")
            for td in result['true_diffs']:
                print(f"  {td}")
        
        # Show jump diffs
        if result['jump_diffs']:
            print(f"\n--- Jump diffs ---")
            for jd in result['jump_diffs']:
                print(f"  {jd}")

        # Show decompiled source for this function
        print(f"\n--- Decompiled source ({target_name}) ---")
        import ast
        tree = ast.parse(source)
        for node in ast.walk(tree):
            short_name = target_name.split('.')[-1]
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == short_name:
                print(ast.unparse(node))
                break

if __name__ == '__main__':
    main()
