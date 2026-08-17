#!/usr/bin/env python3
"""Round 07: Debug CFG structure for exception_handling_examples."""
import sys, os, dis, types, marshal, struct
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

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
    
    # Print blocks
    print(f"=== CFG Blocks for {target_name} ===")
    for block in cfg.get_blocks_in_order():
        blk_instrs = [(i.offset, i.opname, i.argval) for i in block.instructions 
                   if i.opname not in ('RESUME', 'NOP', 'CACHE')]
        print(f"  Block@{block.start_offset}: succs={[s.start_offset for s in block.successors]}")
        for off, op, arg in blk_instrs:
            print(f"    {off:4d} {op:30s} {arg}")
    
    # Run region analyzer
    gen = RegionASTGenerator(cfg, recursive=False, parent_code=target_code)
    gen.region_analyzer.analyze()
    
    print(f"\n=== Regions for {target_name} ===")
    for r in gen.region_analyzer.regions:
        rtype = type(r).__name__
        entry = r.entry.start_offset if r.entry else None
        blocks = [b.start_offset for b in r.blocks]
        merge = r.merge_block.start_offset if hasattr(r, 'merge_block') and r.merge_block else None
        value_target = getattr(r, 'value_target', None)
        print(f"  {rtype}: entry={entry}, blocks={blocks}, merge={merge}, value_target={value_target}")
        if hasattr(r, 'try_entry') and r.try_entry:
            print(f"    try_entry={r.try_entry.start_offset}")
        if hasattr(r, 'try_body_blocks') and r.try_body_blocks:
            print(f"    try_body_blocks={[b.start_offset for b in r.try_body_blocks]}")
        if hasattr(r, 'except_handlers') and r.except_handlers:
            for eh in r.except_handlers:
                if isinstance(eh, dict):
                    print(f"    except_handler: entry={eh.get('entry').start_offset if eh.get('entry') else None}, "
                          f"type={eh.get('exc_type')}, blocks={[b.start_offset for b in eh.get('blocks', [])]}")
                elif isinstance(eh, (tuple, list)):
                    print(f"    except_handler: {eh}")
        if hasattr(r, 'else_blocks') and r.else_blocks:
            print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
        if hasattr(r, 'finally_blocks') and r.finally_blocks:
            print(f"    finally_blocks={[b.start_offset for b in r.finally_blocks]}")
        if hasattr(r, 'condition_block') and r.condition_block:
            print(f"    condition_block={r.condition_block.start_offset}")
    
    print(f"\n=== block_to_region ===")
    for blk, reg in gen.region_analyzer.block_to_region.items():
        print(f"  Block@{blk.start_offset} -> {type(reg).__name__}(entry={reg.entry.start_offset if reg.entry else None})")

if __name__ == '__main__':
    main()
