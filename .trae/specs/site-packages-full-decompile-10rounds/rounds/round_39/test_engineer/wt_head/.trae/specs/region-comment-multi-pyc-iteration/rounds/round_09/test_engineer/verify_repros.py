"""Verify all R09 minimal repros: compile, decompile, check f-string preserved.

For each repro_NN_*.py:
  1. py_compile to .pyc
  2. decompile via pycdc
  3. parse the decompiled output
  4. check that the f-string assignment has the expected number of segments

A repro is DEFECT-REPRO if the decompiled f-string has fewer segments than
the source (i.e., the COMPARE_OP heuristic truncated it).
"""
import os, sys, py_compile, ast, glob, re

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

REPRO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minimal_repros')
if not os.path.isdir(REPRO_DIR):
    REPRO_DIR = os.path.dirname(os.path.abspath(__file__))

def count_fstring_segments(source):
    """Count BUILD_STRING segments by inspecting the source AST."""
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            count = max(count, len(node.values))
    return count

def count_fstring_segments_from_code(code_obj):
    """Count max BUILD_STRING arg in the code object's bytecode."""
    import dis
    max_bs = 0
    for ins in dis.get_instructions(code_obj):
        if ins.opname == 'BUILD_STRING':
            max_bs = max(max_bs, ins.argval if isinstance(ins.argval, int) else ins.arg)
    return max_bs

def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    print(f'Found {len(repros)} repros')
    defects = []
    for rp in repros:
        name = os.path.basename(rp)
        src = open(rp, encoding='utf-8').read()
        # Expected segments from source
        try:
            expected = count_fstring_segments(src)
        except Exception as e:
            print(f'  {name}: SOURCE PARSE ERROR {e}')
            continue
        # Compile to pyc
        pyc = rp + 'c'
        try:
            py_compile.compile(rp, pyc, doraise=True)
        except py_compile.PyCompileError as e:
            print(f'  {name}: COMPILE ERROR {e}')
            continue
        # Decompile
        try:
            decomp = decompile_pyc(pyc)
        except Exception as e:
            print(f'  {name}: DECOMPILE ERROR {e}')
            defects.append((name, 'decompile-error', expected, 0))
            continue
        # Parse decompiled
        try:
            tree = ast.parse(decomp)
        except SyntaxError as e:
            print(f'  {name}: DECOMPILED SYNTAX ERROR {e}')
            defects.append((name, 'syntax-error', expected, 0))
            continue
        actual = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                actual = max(actual, len(node.values))
        status = 'OK' if actual >= expected else 'DEFECT'
        if status == 'DEFECT':
            defects.append((name, 'truncated', expected, actual))
        print(f'  {name}: expected={expected} actual={actual} -> {status}')
        # Cleanup
        try:
            os.remove(pyc)
        except OSError:
            pass
    print(f'\nTotal: {len(repros)} repros, {len(defects)} DEFECT-REPROs')
    for d in defects:
        print(f'  DEFECT: {d[0]} reason={d[1]} expected={d[2]} actual={d[3]}')
    return 0 if not defects else 1

if __name__ == '__main__':
    sys.exit(main())
