#!/usr/bin/env python3
"""Round 07: Trace _collect_body for TryExceptRegion(entry=474)."""
import sys, os, dis, types, marshal, struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

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
    ra = RegionAnalyzer(cfg, parent_code=target_code)
    
    # Parse exception table
    handler_infos = ra._parse_exception_table()
    
    print("=== Handler Infos ===")
    for hi in handler_infos:
        print(f"  try_start={hi.get('try_start')}, try_end={hi.get('try_end')}, "
              f"handler_start={hi.get('handler_start')}, "
              f"type={hi.get('handler_type')}")
    
    # Find the handler info for entry=474 (start=474, end=502, handler=504)
    for hi in handler_infos:
        if hi.get('try_start') == 474:
            print(f"\n=== Tracing _collect_handler_chain for handler_start=504 ===")
            handler_entry = cfg.get_block_by_offset(504)
            print(f"  handler_entry: Block@{handler_entry.start_offset}")
            print(f"  handler_entry instrs: {[(i.opname, i.argval) for i in handler_entry.instructions]}")
            
            # Call _extract_except_handler
            exc_type, exc_name, handler_body = ra._extract_except_handler(handler_entry)
            print(f"  exc_type: {exc_type}")
            print(f"  exc_name: {exc_name}")
            print(f"  handler_body: {[b.start_offset for b in handler_body]}")
            
            # Call _follow_except_chain
            chain_handlers, chain_entries = ra._follow_except_chain(handler_entry)
            print(f"  chain_handlers: {[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in chain_handlers]}")
            print(f"  chain_entries: {[b.start_offset for b in chain_entries]}")
            
            # Calculate all_handler_blocks_set
            all_handler_blocks_set = set(handler_body) | {handler_entry}
            for _, _, body in chain_handlers:
                all_handler_blocks_set |= set(body)
            for heb in chain_entries:
                all_handler_blocks_set.add(heb)
            print(f"  all_handler_blocks_set: {[b.start_offset for b in all_handler_blocks_set]}")
            break

if __name__ == '__main__':
    main()
