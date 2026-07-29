"""R23 测试工程师：验证_sb_has_body对get_trading_day_by_date的影响"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import (
    RegionAnalyzer, FORWARD_CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS,
    NOISE_OPS, MatchRegion
)

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    co = pyc_codes['get_trading_day_by_date']

    builder = CFGBuilder()
    cfg = builder.build(co)

    analyzer = RegionAnalyzer(cfg)

    # Get Block 1 (the start block)
    block1 = None
    for b in cfg.blocks.values():
        if b.start_offset == 0:
            block1 = b
            break

    print(f"Block 1 (offset={block1.start_offset}):")
    for ins in block1.instructions:
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")

    _sb_last = block1.get_last_instruction()
    print(f"\n_sb_last: {_sb_last.opname} {_sb_last.argval}")
    print(f"_sb_last in FORWARD_CONDITIONAL_JUMP_OPS: {_sb_last.opname in FORWARD_CONDITIONAL_JUMP_OPS}")

    # Check _sb_has_body (R22-N3)
    _sb_has_body = any(
        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                     'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
                     'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
                     'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')
        for i in block1.instructions
        if i.offset < _sb_last.offset
    )
    print(f"\n_sb_has_body (current check): {_sb_has_body}")

    # Show which instructions trigger _sb_has_body
    print("\nInstructions triggering _sb_has_body:")
    for i in block1.instructions:
        if i.offset < _sb_last.offset and i.opname in (
                'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
                'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
                'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR'):
            print(f"  {i.offset:4d}  {i.opname:35s} {i.argval!r}")

    # Check if the STORE_FAST is preceded by IMPORT_FROM
    print("\nChecking if STORE_FAST is part of import:")
    instrs = [i for i in block1.instructions if i.offset < _sb_last.offset]
    for idx, i in enumerate(instrs):
        if i.opname == 'STORE_FAST' and idx > 0:
            prev = instrs[idx - 1]
            print(f"  STORE_FAST at {i.offset} preceded by {prev.opname} at {prev.offset}")
            if prev.opname == 'IMPORT_FROM':
                print(f"    -> This STORE_FAST is part of import statement!")

    # Try calling _detect_boolop_conditional_chain directly
    print("\n=== Trying _detect_boolop_conditional_chain ===")
    chain = analyzer._detect_boolop_conditional_chain(block1, set())
    print(f"chain result: {chain}")
    if chain:
        print(f"  chain length: {len(chain)}")
        for b, op in chain:
            print(f"  Block {b.id} (offset={b.start_offset}): op={op}")


if __name__ == '__main__':
    main()
