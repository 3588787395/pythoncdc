"""Disassemble repro_r2_10 original and decompiled"""
import marshal, dis

print("=== ORIGINAL ===")
pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_try_wrap_for_else_break':
        dis.dis(c)
        break

print("\n=== DECOMPILED ===")
py_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break_decompiled.py'
with open(py_path, 'r', encoding='utf-8') as f:
    src = f.read()
code2 = compile(src, '<decompiled>', 'exec')
for c in code2.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_try_wrap_for_else_break':
        dis.dis(c)
        break
