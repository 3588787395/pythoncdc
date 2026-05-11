# Quick test: decompile and verify specific tests
import sys, os, py_compile

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

test_dir = r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1'

tests = [
    'test_l04_while_break',
    'test_l05_while_continue',
    'test_l10_while_break_else',
    'test_l12_while_break_continue',
    'test_r1_while_break_simple',
    'test_r1_while_break_continue',
    'test_l01_for_break',
    'test_l15_nested_for_break',
    'test_n11_try_while_continue',
    'test_n15_while_if_while_break',
    'test_l18_while_with_for',
]

passed = 0
failed = 0
sem_ok_diff = 0

for t in tests:
    py_path = os.path.join(test_dir, t + '.py')
    pyc_path = py_path + 'c'
    
    try:
        py_compile.compile(py_path, pyc_path, doraise=True)
    except Exception as e:
        print(f"  {t}: COMPILE ERROR: {e}")
        continue
    
    from pycdc import decompile_pyc
    try:
        src = decompile_pyc(pyc_path)
        lines = src.split('\n')
        clean = []
        for line in lines:
            if line.startswith('# Source') or line.startswith('# File:'):
                continue
            clean.append(line)
        clean_src = '\n'.join(clean).strip()
        
        ns = {}
        exec(compile(clean_src, '<decompiled>', 'exec'), ns)
        result = ns['test']()
        
        with open(py_path, 'r') as f:
            orig_src = f.read()
        ns2 = {}
        exec(compile(orig_src, '<orig>', 'exec'), ns2)
        expected = ns2['test']()
        
        if result == expected:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"
        
        print(f"  {t}: {status} (got {result}, expected {expected})")
        if status == "FAIL":
            print(f"    Decompiled:\n{clean_src}")
            print()
    except Exception as e:
        failed += 1
        print(f"  {t}: ERROR: {e}")
        import traceback
        traceback.print_exc()
        print()

print(f"\nPassed: {passed}, Failed: {failed}")
