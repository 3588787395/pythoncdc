# Dump bytecode for test_l04_while_break
import sys
import os
import py_compile
import dis
import marshal
import types

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

test_dir = r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1'

t = 'test_l04_while_break'
py_path = os.path.join(test_dir, t + '.py')
pyc_path = py_path + 'c'

py_compile.compile(py_path, pyc_path, doraise=True)

with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = f.read(4)
    # Skip timestamp and size for 3.7+
    # For 3.11, read 4 bytes timestamp, 4 bytes size
    import struct
    if sys.version_info >= (3, 12):
        flags_int = struct.unpack('<I', flags)[0]
    f.read(4)  # timestamp
    f.read(4)  # size
    code = marshal.load(f)

print("=== MODULE BYTECODE ===")
dis.dis(code)

# Find the 'test' function
for const in code.co_consts:
    if isinstance(const, types.CodeType):
        print(f"\n=== FUNCTION {const.co_name} BYTECODE ===")
        dis.dis(const)
        
        # Also show offset ranges
        print("\n  Instruction offsets:")
        for i in dis.get_instructions(const):
            print(f"    {i.offset:4d} {i.opname:30s} {i.argrepr}")
