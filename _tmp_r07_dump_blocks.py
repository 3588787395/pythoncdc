#!/usr/bin/env python3
"""Round 07: Dump block@474 and its successors."""
import sys, os, dis, types, marshal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg

PYC_PATH = str(PROJECT_ROOT / 'python_syntax_comprehensive_test.pyc')

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    return code

def collect_all_code_objects(code, prefix=''):
    from collections import OrderedDict
    result = OrderedDict()
    name = prefix + code.co_name if prefix else code.co_name
    result[name] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.' if prefix else code.co_name + '.'
            result.update(collect_all_code_objects(const, child_prefix))
    return result

def main():
    orig_code = load_code_from_pyc(PYC_PATH)
    all_codes = collect_all_code_objects(orig_code)
    target_name = '<module>.exception_handling_examples'
    target_code = all_codes[target_name]
    
    cfg = build_cfg(target_code)
    
    for offset in [470, 474, 502, 504, 522, 554, 558, 560, 566, 568, 586, 618, 622, 624, 630]:
        blk = cfg.get_block_by_offset(offset)
        if blk:
            print(f"\nBlock@{offset}:")
            print(f"  instrs: {[(i.opname, i.argval) for i in blk.instructions]}")
            print(f"  successors: {[s.start_offset for s in blk.successors]}")
            print(f"  exception_successors: {[s.start_offset for s in blk.exception_successors]}")
        else:
            print(f"\nBlock@{offset}: NOT FOUND")

if __name__ == '__main__':
    main()
