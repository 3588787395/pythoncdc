"""Disassemble decompiled validate_data"""
import dis

py_path = 'decompiler_test_comprehensive_decompiled.py'
with open(py_path, 'r', encoding='utf-8') as f:
    src = f.read()

code = compile(src, '<decompiled>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'validate_data':
                print(f"=== validate_data (decompiled) ===")
                dis.dis(cc)
                print(f"\nException table:")
                for entry in cc.co_exceptiontable:
                    print(f"  {entry}")
                break
        break
