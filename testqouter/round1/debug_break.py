import sys
import os
import dis
import py_compile

sys.path.insert(0, 'd:/Desktop/ptrade相关/pythoncdc')

from pycdc import decompile_pyc

round1_dir = r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1'

for test_name in ['test_l01_for_break', 'test_l04_while_break']:
    print("=" * 70)
    print(f"TEST: {test_name}")
    print("=" * 70)

    py_path = os.path.join(round1_dir, f'{test_name}.py')
    pyc_path = py_path + 'c'

    with open(py_path, 'r', encoding='utf-8') as f:
        orig_source = f.read()
    print("\n[Original Source]")
    print(orig_source)

    if os.path.exists(pyc_path):
        os.remove(pyc_path)
    py_compile.compile(py_path, pyc_path, doraise=True)

    with open(py_path, 'r', encoding='utf-8') as f:
        orig = f.read()
    orig_co = compile(orig, py_path, 'exec')
    test_co = None
    for c in orig_co.co_consts:
        if hasattr(c, 'co_code'):
            test_co = c
            break

    print("\n[Bytecode of original test() function]")
    if test_co:
        dis.dis(test_co)
        print("\n[Instruction list]")
        for instr in dis.get_instructions(test_co):
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
    else:
        print("  Could not find test() code object")

    try:
        decompiled = decompile_pyc(pyc_path)
        lines = decompiled.split('\n')
        clean_lines = []
        for line in lines:
            if line.startswith('# Source') or line.startswith('# File:'):
                continue
            clean_lines.append(line)
        clean = '\n'.join(clean_lines).strip()
        print("\n[Decompiled Output]")
        print(clean)
    except Exception as e:
        print(f"\n[Decompile Error] {e}")
        import traceback
        traceback.print_exc()
    else:
        try:
            decomp_co = compile(clean, '<decompiled>', 'exec')
            test_decomp_co = None
            for c in decomp_co.co_consts:
                if hasattr(c, 'co_code'):
                    test_decomp_co = c
                    break
            print("\n[Bytecode of decompiled test() function]")
            if test_decomp_co:
                dis.dis(test_decomp_co)
                print("\n[Instruction list for decompiled]")
                for instr in dis.get_instructions(test_decomp_co):
                    print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
                print("\n[Bytecode comparison]")
                orig_instrs = [(i.opname, i.argrepr) for i in dis.get_instructions(test_co)]
                decomp_instrs = [(i.opname, i.argrepr) for i in dis.get_instructions(test_decomp_co)]
                print(f"  Original: {orig_instrs}")
                print(f"  Decompiled: {decomp_instrs}")
                print(f"  Match: {orig_instrs == decomp_instrs}")
            else:
                print("  Could not find test() in decompiled code")
        except SyntaxError as e:
            print(f"\n[Syntax Error in decompiled] {e}")

    if os.path.exists(pyc_path):
        os.remove(pyc_path)

    print()
