# Quick debug for while_break
import sys
import os
import py_compile

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

test_dir = r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1'
tests = [
    'test_l04_while_break',
    'test_l05_while_continue',
    'test_l01_for_break',
    'test_l12_while_break_continue',
]

for t in tests:
    py_path = os.path.join(test_dir, t + '.py')
    pyc_path = py_path + 'c'
    
    py_compile.compile(py_path, pyc_path, doraise=True)
    
    from pycdc import decompile_pyc
    try:
        src = decompile_pyc(pyc_path)
        print(f"=== {t} ===")
        print(src.strip())
        print()
        
        # Try to execute
        import re
        # Strip # Source line
        lines = src.split('\n')
        clean = []
        for line in lines:
            if line.startswith('# Source') or line.startswith('# File:'):
                continue
            clean.append(line)
        clean_src = '\n'.join(clean)
        
        ns = {}
        exec(compile(clean_src, '<decompiled>', 'exec'), ns)
        result = ns['test']()
        print(f"  Result: {result}")
        
        # Expected result
        with open(py_path, 'r') as f:
            orig_src = f.read()
        ns2 = {}
        exec(compile(orig_src, '<orig>', 'exec'), ns2)
        expected = ns2['test']()
        print(f"  Expected: {expected}")
        print(f"  Match: {result == expected}")
        print()
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()
