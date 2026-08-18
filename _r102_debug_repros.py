#!/usr/bin/env python3
"""调试复现实例的字节码差异"""
import dis
import marshal
import sys
import types
import os

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def find_code_by_name(code, name):
    if code.co_name == name:
        return code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result = find_code_by_name(const, name)
            if result:
                return result
    return None

def print_instructions(code, label):
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")
    for instr in dis.get_instructions(code):
        argval = instr.argval
        if isinstance(argval, types.CodeType):
            argval = '<code>'
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else '':>4} {argval if argval is not None else ''}")

project_root = os.path.dirname(os.path.abspath(__file__))
repro_dir = os.path.join(project_root, '.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros')

# 测试特定的复现实例
targets = [
    'repro_01_try_for_else_break_return',
    'repro_05_try_else_finally_return',
    'repro_09_try_except_else_return',
    'repro_12_finally_position',
]

for target in targets:
    pyc_path = os.path.join(repro_dir, target + '.pyc')
    decomp_path = os.path.join(repro_dir, target + '_decompiled.py')
    
    if not os.path.exists(pyc_path) or not os.path.exists(decomp_path):
        print(f"Skipping {target}: files missing")
        continue
    
    orig_code = load_code_from_pyc(pyc_path)
    
    with open(decomp_path, 'r', encoding='utf-8') as f:
        source = f.read()
    decomp_code = compile(source, decomp_path, 'exec')
    
    # 找到目标函数
    for co_orig, co_decomp in [(orig_code, decomp_code)]:
        # 找第一个非module函数
        for const in co_orig.co_consts:
            if isinstance(const, types.CodeType) and const.co_name != '<module>':
                print_instructions(const, f"ORIGINAL: {target}::{const.co_name}")
                break
        for const in co_decomp.co_consts:
            if isinstance(const, types.CodeType) and const.co_name != '<module>':
                print_instructions(const, f"DECOMPILED: {target}::{const.co_name}")
                break
