"""Disassemble decompiled repro_r2_06"""
import marshal, dis

py_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_06_nested_try_else_decompiled.py'
with open(py_path, 'r', encoding='utf-8') as f:
    src = f.read()

code = compile(src, '<decompiled>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_nested_try_else':
        print(f"=== {c.co_name} (decompiled) ===")
        dis.dis(c)
        print(f"\nException table entries: {len(c.co_exceptiontable)}")
        for entry in c.co_exceptiontable:
            print(f"  {entry}")
        break
