"""Quick test for W079 fix"""
import sys
sys.path.insert(0, 'f:/pythoncdc')

from core.decompiler import PyDecompiler

code = 'for i in range(3):\n    with ctx:\n        if i > 1:\n            break'
expected = code

decompiler = PyDecompiler()
decompiled = decompiler.decompile(code)

print("=== Expected ===")
print(expected)
print()
print("=== Decompiled ===")
print(decompiled)
print()

if "break" in decompiled and "with ctx:" in decompiled and "if i > 1:" in decompiled:
    print("SUCCESS: break, with ctx, and if statement found")
else:
    print("FAIL: missing expected elements")
