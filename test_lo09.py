"""Check if LO09 break is lost."""
import os, sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
os.chdir('f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc
import dis, marshal, types

source = """for category in categories:
    found = False
    for item in category.items:
        if matches(item):
            found = True
            process(item)
            break
    if not found:
        log_no_match(category)"""

code = compile(source, '<test>', 'exec')
pyc_path = 'test_lo09.pyc'
with open(pyc_path, 'wb') as f:
    f.write(b'\x6f\x0d\x0d\x0a')
    f.write(b'\x00\x00\x00\x00')
    f.write(b'\x00\x00\x00\x00')
    f.write(b'\x00\x00\x00\x00')
    marshal.dump(code, f)

decomp = decompile_pyc(pyc_path)
print("=== Decompiled ===")
print(decomp)

print("\n=== Original bytecode ===")
dis.dis(code)
