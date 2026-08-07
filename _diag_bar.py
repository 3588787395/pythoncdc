"""Diagnostic: trace class definition handling in bar.pyc decompilation."""
import sys
import os
import marshal
import dis

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load bar.pyc
pyc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site-packages', 'IQEngine', 'core', 'bar.pyc')
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Check the module-level code object
print("=== Module-level code ===")
print(f"co_name: {code.co_name}")
print(f"co_names: {code.co_names}")
print(f"co_consts types: {[type(c).__name__ for c in code.co_consts]}")

# Find class code objects
for i, const in enumerate(code.co_consts):
    if hasattr(const, 'co_code'):
        print(f"\n  Const [{i}]: code object '{const.co_name}'")
        print(f"    co_names: {const.co_names[:10]}")
        print(f"    co_varnames: {const.co_varnames[:10]}")
        print(f"    co_consts types: {[type(c).__name__ for c in const.co_consts[:10]]}")

# Now let's try to decompile and see what happens
print("\n=== Trying decompilation ===")
from pycdc import decompile_pyc
try:
    source = decompile_pyc(pyc_path)
    print(f"Source length: {len(source)}")
    print("Source:")
    print(source[:2000])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
