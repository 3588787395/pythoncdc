"""Debug BoolOp detection for get_price."""
import sys
import dis
import types
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import (
    RegionAnalyzer, IfRegion, BoolOpRegion, TryExceptRegion,
    MatchRegion, LoopRegion, AssertRegion, BasicBlock,
    FORWARD_CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS,
    NONE_CHECK_OPS, NOISE_OPS,
)


def main():
    pyc_path = '/workspace/quotation.pyc'
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'get_price':
            target = const
            break
    if target is None:
        print("get_price not found")
        return

    print(f"=== get_price 字节码 (前80条) ===")
    for ins in dis.get_instructions(target):
        if ins.offset > 200:
            break
        if ins.opname not in ('EXTENDED_ARG', 'CACHE'):
            print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argrepr}")

    builder = CFGBuilder()
    cfg = builder.build(target)

    # Get block@0
    print(f"\n=== Block 0 ===")
    b0 = cfg.get_block_by_offset(0)
    if b0:
        print(f"  Instructions:")
        for i in b0.instructions:
            if i.opname not in ('EXTENDED_ARG', 'CACHE'):
                _arg = getattr(i, 'argrepr', None) or getattr(i, 'argval', None)
                print(f"    {i.offset:4d} {i.opname:30s} {_arg}")
        print(f"  Succs: {[s.start_offset for s in b0.successors]}")
        last = b0.get_last_instruction()
        print(f"  Last: {last.opname if last else None} -> {last.argval if last else None}")

    # Check the _sb_has_body logic directly
    print(f"\n=== Test _sb_has_body for block 0 ===")
    _sb_last = b0.get_last_instruction()
    print(f"  _sb_last: offset={_sb_last.offset}, opname={_sb_last.opname}")
    print(f"  _sb_last in NONE_CHECK_OPS: {_sb_last.opname in NONE_CHECK_OPS}")

    analyzer = RegionAnalyzer(cfg)
    # Manually compute the _cond_start_offset
    if _sb_last.opname in NONE_CHECK_OPS:
        _depth = -1
        _cond_start_offset = _sb_last.offset
        print(f"  Initial: _depth={_depth}, _cond_start_offset={_cond_start_offset}")
        for _ci in reversed(b0.instructions):
            if _ci.offset >= _sb_last.offset:
                continue
            if _ci.opname in ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME'):
                continue
            _cpush, _cpop = analyzer._stack_effect(_ci)
            _depth += _cpush - _cpop
            print(f"    Consider offset={_ci.offset} {_ci.opname}: push={_cpush}, pop={_cpop}, depth={_depth}")
            if _depth <= 0:
                _cond_start_offset = _ci.offset
                print(f"    -> _cond_start_offset = {_ci.offset}")
                break
        print(f"  Final _cond_start_offset: {_cond_start_offset}")

    # Check _import_store_offsets
    _import_store_offsets = set()
    _pre_instrs = [i for i in b0.instructions if i.offset < _sb_last.offset]
    for _idx, _i in enumerate(_pre_instrs):
        if _i.opname in ('IMPORT_FROM', 'IMPORT_NAME'):
            if _idx + 1 < len(_pre_instrs):
                _nxt = _pre_instrs[_idx + 1]
                if _nxt.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _import_store_offsets.add(_nxt.offset)
    print(f"  _import_store_offsets: {_import_store_offsets}")

    # Now check _sb_has_body with the fix
    _sb_has_body_with_fix = any(
        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                     'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
                     'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
                     'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')
        and i.offset not in _import_store_offsets
        and i.offset >= _cond_start_offset
        for i in b0.instructions
        if i.offset < _sb_last.offset
    )
    print(f"  _sb_has_body (with cond_start filter, fix): {_sb_has_body_with_fix}")

    # And without the fix (whole block)
    _sb_has_body_no_fix = any(
        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                     'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
                     'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
                     'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')
        and i.offset not in _import_store_offsets
        for i in b0.instructions
        if i.offset < _sb_last.offset
    )
    print(f"  _sb_has_body (no cond_start filter, original): {_sb_has_body_no_fix}")

    # Test boolop chain detection directly
    print(f"\n=== Direct _detect_boolop_chain_start(b0, set()) ===")
    chain = analyzer._detect_boolop_chain_start(b0, set())
    print(f"  chain result: {chain}")

    # Full analyze
    print(f"\n=== Full analyze ===")
    analyzer2 = RegionAnalyzer(cfg)
    analyzer2.analyze()

    print(f"\n=== Regions containing block 0 ===")
    for r in analyzer2.regions:
        if b0 in r.blocks or (hasattr(r, 'entry') and r.entry == b0):
            rtype = type(r).__name__
            entry = r.entry.start_offset if r.entry else None
            print(f"  {rtype} entry={entry}")
            if isinstance(r, BoolOpRegion):
                print(f"    op_chain: {[(b.start_offset, op) for b, op in r.op_chain]}")
                print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")
            elif isinstance(r, IfRegion):
                print(f"    then_blocks: {[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
                print(f"    elif_conditions: {len(r.elif_conditions) if r.elif_conditions else 0}")
                print(f"    merge: {r.merge_block.start_offset if r.merge_block else None}")


if __name__ == '__main__':
    main()
