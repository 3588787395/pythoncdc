#!/usr/bin/env python3
"""Find all code object names in the pyc"""

import marshal
import types
import io

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_all(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    result = {name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            new_prefix = name + "." if name != "<module>" else ""
            result.update(extract_all(const, new_prefix))
    return result

orig = load_code_from_pyc("decompiler_test_comprehensive.cpython-311.pyc")
codes = extract_all(orig)

output = io.StringIO()
for name in sorted(codes.keys()):
    print(f"  {name}: {len(list(__import__('dis').get_instructions(codes[name])))} instructions", file=output)

with open("r03_func_list.txt", "w", encoding="utf-8") as f:
    f.write(output.getvalue())

print("Function list written to r03_func_list.txt")