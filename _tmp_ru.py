import sys, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions
import dis

pyc_path = r'F:\Downloads\pythoncdc-main\site-packages\IQCommon\util\replace_utils.pyc'
orig_map, decomp_map = get_bytecode_instructions(pyc_path)

fname = 'decrypt_database_url'
print("=== ORIGINAL ===")
for i, instr in enumerate(orig_map[fname]):
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname} {instr.argrepr}")
print()
print("=== DECOMPILED ===")
for i, instr in enumerate(decomp_map[fname]):
    print(f"  {i:3d}: {instr.offset:4d} {instr.opname} {instr.argrepr}")
