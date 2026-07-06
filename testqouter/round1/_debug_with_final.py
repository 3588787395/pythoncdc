import sys
import os
import dis
import py_compile

os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

targets = ['test_w01_with.py', 'test_w02_with_no_as.py']

for tf in targets:
    print(f"\n{'='*80}")
    print(f"  FILE: {tf}")
    print(f"{'='*80}")

    with open(tf, 'r', encoding='utf-8') as f:
        orig_source = f.read()

    print(f"\n[1] ORIGINAL SOURCE:")
    print(f"---")
    print(orig_source)
    print(f"---")

    pyc_path = tf + 'c'
    py_compile.compile(tf, cfile=pyc_path, doraise=True)

    decompiled_source = decompile_pyc(pyc_path)

    lines = decompiled_source.split('\n')
    clean_lines = []
    for line in lines:
        if line.startswith('# Source') or line.startswith('# File:'):
            continue
        clean_lines.append(line)
    clean_decompiled = '\n'.join(clean_lines).strip()

    print(f"\n[2] DECOMPILED SOURCE:")
    print(f"---")
    print(clean_decompiled)
    print(f"---")

    orig_code = compile(orig_source, '<original>', 'exec')
    decomp_code = compile(clean_decompiled, '<decompiled>', 'exec')

    orig_func_code = orig_code.co_consts[0]
    decomp_func_code = decomp_code.co_consts[0]

    print(f"\n[3] MODULE-LEVEL BYTECODE COMPARISON:")
    orig_mod_ops = [i.opname for i in dis.get_instructions(orig_code)]
    decomp_mod_ops = [i.opname for i in dis.get_instructions(decomp_code)]
    match_mod = orig_mod_ops == decomp_mod_ops
    print(f"  Module bytecode match: {match_mod}")
    print(f"  Original ops:  {orig_mod_ops}")
    print(f"  Decompiled ops: {decomp_mod_ops}")

    print(f"\n[4] FUNCTION-LEVEL BYTECODE (test() in original):")
    print(f"  {'Offset':>6}  {'Opcode':<24} {'Arg':<20} {'Argval'}")
    print(f"  {'-'*6}  {'-'*24} {'-'*20} {'-'*30}")
    for instr in dis.get_instructions(orig_func_code):
        argval = instr.argval
        if hasattr(argval, 'co_name'):
            argval = f"<code:{argval.co_name}>"
        print(f"  {instr.offset:>6}  {instr.opname:<24} {str(instr.arg):<20} {str(argval)}")

    print(f"\n[5] FUNCTION-LEVEL BYTECODE (test() in decompiled):")
    print(f"  {'Offset':>6}  {'Opcode':<24} {'Arg':<20} {'Argval'}")
    print(f"  {'-'*6}  {'-'*24} {'-'*20} {'-'*30}")
    for instr in dis.get_instructions(decomp_func_code):
        argval = instr.argval
        if hasattr(argval, 'co_name'):
            argval = f"<code:{argval.co_name}>"
        print(f"  {instr.offset:>6}  {instr.opname:<24} {str(instr.arg):<20} {str(argval)}")

    print(f"\n[6] DETAILED DIFFERENCES:")
    orig_instrs = []
    for instr in dis.get_instructions(orig_func_code):
        if not instr.opname.startswith('CACHE'):
            argval = instr.argval
            if hasattr(argval, 'co_name'):
                argval = f"<code:{argval.co_name}>"
            orig_instrs.append((instr.opname, argval))

    decomp_instrs = []
    for instr in dis.get_instructions(decomp_func_code):
        if not instr.opname.startswith('CACHE'):
            argval = instr.argval
            if hasattr(argval, 'co_name'):
                argval = f"<code:{argval.co_name}>"
            decomp_instrs.append((instr.opname, argval))

    max_len = max(len(orig_instrs), len(decomp_instrs))
    diff_count = 0
    for i in range(max_len):
        o = orig_instrs[i] if i < len(orig_instrs) else None
        d = decomp_instrs[i] if i < len(decomp_instrs) else None
        if o != d:
            diff_count += 1
            print(f"  [{i:>3}] ORIG: {o}  |  DECOMP: {d}")

    if diff_count == 0:
        print(f"  (no differences - bytecode matches exactly)")
    else:
        print(f"  Total differences: {diff_count}")

    print(f"\n[7] CONSTANTS COMPARISON (test code object constants):")
    print(f"  Original consts ({len(orig_func_code.co_consts)}): {list(orig_func_code.co_consts)}")
    print(f"  Decompiled consts ({len(decomp_func_code.co_consts)}): {list(decomp_func_code.co_consts)}")

    print(f"\n[8] NAMES COMPARISON:")
    print(f"  Original names: {list(orig_func_code.co_names)}")
    print(f"  Decompiled names: {list(decomp_func_code.co_names)}")

    print(f"\n[9] VARNAMES COMPARISON:")
    print(f"  Original varnames: {list(orig_func_code.co_varnames)}")
    print(f"  Decompiled varnames: {list(decomp_func_code.co_varnames)}")

    if os.path.exists(pyc_path):
        os.remove(pyc_path)
