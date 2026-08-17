#!/usr/bin/env python3
"""R94: 查看 get_kline_by_date_one 反编译源码 vs 原始字节码"""
import sys, dis, marshal, types
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import get_bytecode_instructions, _filter_noise_instrs

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
ok_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedataOK.py"

import marshal
def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

orig_code = load_pyc(pyc_path)
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

# Show the decompiled source for get_kline_by_date_one
import ast
decomp_tree = compile(source, ok_path, 'exec', ast.PyCF_ONLY_AST)

for node in ast.walk(decomp_tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'get_kline_by_date_one':
        print("=== Decompiled AST for get_kline_by_date_one ===")
        print(ast.dump(node, indent=2)[:3000])
        break

# Also show the full disassembly of the original
print("\n=== Original bytecode for get_kline_by_date_one (except handler area) ===")
orig_co = orig_map['get_kline_by_date_one']
orig_instrs = _filter_noise_instrs(get_bytecode_instructions(orig_co))
for i in range(140, min(170, len(orig_instrs))):
    instr = orig_instrs[i]
    argval = instr.argval
    if isinstance(argval, str) and len(argval) > 40:
        argval = argval[:40] + '...'
    print(f"  [{i}] {instr.opname}({argval})")

# Show the decompiled bytecode for same area
print("\n=== Decompiled bytecode for get_kline_by_date_one (except handler area) ===")
decomp_co = decomp_map['get_kline_by_date_one']
decomp_instrs = _filter_noise_instrs(get_bytecode_instructions(decomp_co))
for i in range(140, min(170, len(decomp_instrs))):
    instr = decomp_instrs[i]
    argval = instr.argval
    if isinstance(argval, str) and len(argval) > 40:
        argval = argval[:40] + '...'
    print(f"  [{i}] {instr.opname}({argval})")
