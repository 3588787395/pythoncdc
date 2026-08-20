"""Disassemble repro_r2_06 original and decompiled"""
import marshal, dis, sys

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_06_nested_try_else.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_nested_try_else':
        print(f"=== {c.co_name} (orig) ===")
        dis.dis(c)
        print(f"\nException table:")
        for entry in c.co_exceptiontable:
            print(f"  {entry}")
        break
