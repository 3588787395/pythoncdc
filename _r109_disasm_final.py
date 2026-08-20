"""Disassemble final_integration_test original"""
import marshal, dis

pyc_path = 'decompiler_test_comprehensive.cpython-311.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'final_integration_test':
                print(f"=== {cc.co_name} ===")
                dis.dis(cc)
                break
        break
