#!/usr/bin/env python3
"""Disassemble mismatched functions from IQEngine trade_schedule.pyc."""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

# Disassemble the mismatched functions
for fname in ['get_trading_schedule', 'get_trading_time_tuple', 'is_stock_trade_trigger', 'is_future_trade_trigger']:
    co = find_code(code, fname)
    if co:
        print(f"\n{'='*60}")
        print(f"=== Original {fname} bytecode ===")
        print(f"{'='*60}")
        print(f"co_consts: {co.co_consts}")
        print(f"co_names: {co.co_names}")
        print(f"co_varnames: {co.co_varnames}")
        print()
        dis.dis(co)
        print()

# Also compile the reference OK source and disassemble
ref_path = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_scheduleOK.py')
with open(ref_path, 'r', encoding='utf-8') as f:
    ref_source = f.read()
# Remove header comments
lines = ref_source.split('\n')
start = 0
for i, line in enumerate(lines):
    if line.startswith('import ') or line.startswith('from ') or line.startswith('STOCK') or line.startswith('FUTURE'):
        start = i
        break
ref_source = '\n'.join(lines[start:])

try:
    ref_code = compile(ref_source, '<reference>', 'exec')
    for fname in ['get_trading_schedule', 'get_trading_time_tuple', 'is_stock_trade_trigger', 'is_future_trade_trigger']:
        co = find_code(ref_code, fname)
        if co:
            print(f"\n{'='*60}")
            print(f"=== Reference {fname} bytecode ===")
            print(f"{'='*60}")
            print(f"co_consts: {co.co_consts}")
            print(f"co_names: {co.co_names}")
            print(f"co_varnames: {co.co_varnames}")
            print()
            dis.dis(co)
            print()
except SyntaxError as e:
    print(f"SyntaxError in reference: {e}")
