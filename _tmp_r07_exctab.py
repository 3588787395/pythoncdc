#!/usr/bin/env python3
"""Round 07: Check exception table order and handler processing order."""
import sys, types, marshal, dis
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
    
    print("=== Exception table (raw) ===")
    for entry in target_code.co_exceptiontable:
        print(f"  {entry}")
    
    print("\n=== Exception table (parsed via dis) ===")
    try:
        for entry in dis.get_exception_table(target_code):
            print(f"  start={entry.start}, end={entry.end}, target={entry.target}, depth={entry.depth}, lasti={entry.lasti}")
    except:
        pass
    
    cfg = build_cfg(target_code)
    print("\n=== CFG exception table ===")
    for entry in cfg.exception_table:
        print(f"  {entry}")

if __name__ == '__main__':
    main()
