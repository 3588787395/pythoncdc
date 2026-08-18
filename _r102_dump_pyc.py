#!/usr/bin/env python3
"""Dump pyc bytecode for analysis."""
import sys, os, dis, types, marshal, struct

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        flags = struct.unpack('<I', f.read(4))[0]
        if flags & 0x1:
            f.read(8)
        else:
            f.read(8)
        code = marshal.load(f)
    return code

def get_all_code_objects(code, prefix=''):
    result = {}
    result[prefix or '<module>'] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            name = f"{prefix}.{const.co_name}" if prefix else const.co_name
            result.update(get_all_code_objects(const, name))
    return result

pyc_path = sys.argv[1] if len(sys.argv) > 1 else 'site-packages/IQCommon/__init__.pyc'
code = load_pyc_code(pyc_path)
funcs = get_all_code_objects(code)

for name, func_code in funcs.items():
    print(f"\n=== {name} ===")
    print(f"  co_consts: {func_code.co_consts[:5]}...")
    print(f"  co_names: {func_code.co_names}")
    print(f"  Exception table:")
    if hasattr(func_code, 'co_exceptiontable') and func_code.co_exceptiontable:
        for entry in func_code.co_exceptiontable:
            print(f"    start={entry.start}, end={entry.end}, target={entry.target}, depth={entry.depth}, lasti={entry.lasti}")
    print(f"  Instructions:")
    for instr in dis.get_instructions(func_code):
        print(f"    {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
