import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import py_compile

test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_l05_while_continue.py')
pyc_file = test_file + 'c'
py_compile.compile(test_file, pyc_file, doraise=True)

from base import decompile_pyc

print("=== DECOMPILED ===")
decompiled = decompile_pyc(pyc_file)
print(decompiled)

print("\n=== SEMANTIC TEST ===")
ns = {}
exec(compile(decompiled, '<decompiled>', 'exec'), ns)
print(f"test() returned: {ns['test']()}")

# Run original
ns_orig = {}
exec(open(test_file).read(), ns_orig)
print(f"Original test() returned: {ns_orig['test']()}")

os.remove(pyc_file)
