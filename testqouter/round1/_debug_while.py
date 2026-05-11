import py_compile, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Check test_l04
py_compile.compile('test_l04_while_break.py', 'test_l04_while_break.pyc', doraise=True)
from base import decompile_pyc
print("=== test_l04_while_break ===")
print(decompile_pyc('test_l04_while_break.pyc'))

# Also check if semantic passes by running the decompiled code
src = decompile_pyc('test_l04_while_break.pyc')
ns = {}
exec(compile(src, '<decompiled>', 'exec'), ns)
print(f"test() returned: {ns['test']()}")

print()

# Check test_l05
py_compile.compile('test_l05_while_continue.py', 'test_l05_while_continue.pyc', doraise=True)
print("=== test_l05_while_continue ===")
print(decompile_pyc('test_l05_while_continue.pyc'))
src2 = decompile_pyc('test_l05_while_continue.pyc')
ns2 = {}
exec(compile(src2, '<decompiled>', 'exec'), ns2)
print(f"test() returned: {ns2['test']()}")
