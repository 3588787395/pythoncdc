#!/usr/bin/env python3
"""R36 test: decompile IQEngine/utils/trade_schedule.pyc and check functions."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pycdc import decompile_pyc

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

source = decompile_pyc(PYC_PATH)

with open('_r36_iqe_ts_out.py', 'w', encoding='utf-8') as f:
    f.write(source)

lines = source.split('\n')

def extract_func(lines, func_name):
    in_func = False
    func_lines = []
    func_indent = 0
    for i, line in enumerate(lines):
        if f'def {func_name}' in line:
            in_func = True
            func_indent = len(line) - len(line.lstrip())
            func_lines.append(line)
            continue
        if in_func:
            if line.strip() == '':
                func_lines.append(line)
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= func_indent and line.strip() and not line.strip().startswith('#'):
                break
            func_lines.append(line)
    return func_lines

results = []
for fname in ['is_stock_trade_time_now', 'is_future_trade_time_now', 'get_trading_time_tuple', 'is_stock_trade_trigger', 'is_future_trade_trigger']:
    func_lines = extract_func(lines, fname)
    results.append(f"=== {fname} ===")
    results.extend(func_lines)
    results.append("=== END ===")
    results.append("")

with open('_r36_iqe_func_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print("Done. Output written to _r36_iqe_func_output.txt")

# Now compare bytecodes
with open(PYC_PATH, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

def get_instructions_bytes(code_obj):
    return [(instr.opname, instr.argval, instr.offset) for instr in dis.get_instructions(code_obj)]

try:
    decomp_code = compile(source, '<decompiled>', 'exec')
except SyntaxError as e:
    print(f"SyntaxError compiling decompiled: {e}")
    decomp_code = None

if decomp_code:
    func_names = ['trading_time_to_str', 'get_trading_schedule', 'get_trading_time_tuple', 
                   'is_stock_trade_time_now', 'is_future_trade_time_now',
                   'is_stock_trade_trigger', 'is_future_trade_trigger']
    match_count = 0
    total = 0
    for fname in func_names:
        orig = find_code(orig_code, fname)
        decomp = find_code(decomp_code, fname)
        if orig is None:
            print(f"  {fname}: NOT IN ORIGINAL")
            continue
        total += 1
        if decomp is None:
            print(f"  {fname}: NOT IN DECOMPILED")
            continue
        orig_bytes = get_instructions_bytes(orig)
        decomp_bytes = get_instructions_bytes(decomp)
        if orig_bytes == decomp_bytes:
            print(f"  {fname}: MATCH ({len(orig_bytes)} instructions)")
            match_count += 1
        else:
            print(f"  {fname}: MISMATCH (orig={len(orig_bytes)}, decomp={len(decomp_bytes)})")
            # Show first difference
            for i, (o, d) in enumerate(zip(orig_bytes, decomp_bytes)):
                if o != d:
                    print(f"    First diff at instruction {i}:")
                    print(f"      orig:  {o}")
                    print(f"      decomp: {d}")
                    break
            if len(orig_bytes) != len(decomp_bytes):
                print(f"    Length mismatch: orig={len(orig_bytes)}, decomp={len(decomp_bytes)}")
    
    print(f"\nMatch rate: {match_count}/{total} = {match_count/total*100:.2f}%")
