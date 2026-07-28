"""Debug BoolOp detection for get_price - detailed trace."""
import sys
import dis
import types
import os
os.environ['R23N21_DEBUG'] = '1'
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

    builder = CFGBuilder()
    cfg = builder.build(target)

    b0 = cfg.get_block_by_offset(0)
    print(f"=== Block 0 ===")
    for i in b0.instructions:
        if i.opname not in ('EXTENDED_ARG', 'CACHE'):
            _arg = getattr(i, 'argrepr', None) or getattr(i, 'argval', None)
            print(f"  {i.offset:4d} {i.opname:30s} {_arg}")
    print(f"  Succs: {[s.start_offset for s in b0.successors]}")

    b1 = cfg.get_block_by_offset(38)
    print(f"\n=== Block 38 ===")
    for i in b1.instructions:
        if i.opname not in ('EXTENDED_ARG', 'CACHE'):
            _arg = getattr(i, 'argrepr', None) or getattr(i, 'argval', None)
            print(f"  {i.offset:4d} {i.opname:30s} {_arg}")
    print(f"  Succs: {[s.start_offset for s in b1.successors]}")

    b76 = cfg.get_block_by_offset(76)
    print(f"\n=== Block 76 ===")
    for i in b76.instructions:
        if i.opname not in ('EXTENDED_ARG', 'CACHE'):
            _arg = getattr(i, 'argrepr', None) or getattr(i, 'argval', None)
            print(f"  {i.offset:4d} {i.opname:30s} {_arg}")
    print(f"  Succs: {[s.start_offset for s in b76.successors]}")

    # Create analyzer and trace _detect_boolop_conditional_chain
    analyzer = RegionAnalyzer(cfg)

    # Check block@0 last instr
    b0_last = b0.get_last_instruction()
    print(f"\nb0 last: {b0_last.opname} argval={b0_last.argval}")
    print(f"b0_last in FORWARD_CONDITIONAL_JUMP_OPS: {b0_last.opname in FORWARD_CONDITIONAL_JUMP_OPS}")
    print(f"b0_last in SHORT_CIRCUIT_JUMP_OPS: {b0_last.opname in SHORT_CIRCUIT_JUMP_OPS}")
    print(f"b0 in claimed: {b0 in set()}")

    # Monkey-patch to add traces
    orig_method = analyzer._detect_boolop_conditional_chain

    def traced_method(start_block, claimed, skip_claimed_check=False):
        print(f"\n--- _detect_boolop_conditional_chain(start={start_block.start_offset}, skip_claimed={skip_claimed_check}) ---", flush=True)
        result = orig_method(start_block, claimed, skip_claimed_check=skip_claimed_check)
        print(f"--- result: {[(b.start_offset, op) for b, op in result] if result else None} ---", flush=True)
        return result

    analyzer._detect_boolop_conditional_chain = traced_method

    # Also trace _detect_boolop_chain_start
    orig_chain_start = analyzer._detect_boolop_chain_start

    def traced_chain_start(block, claimed):
        print(f"\n=== _detect_boolop_chain_start(block={block.start_offset}, claimed_size={len(claimed)}) ===", flush=True)
        # Check what path it will take
        _last = block.get_last_instruction()
        print(f"  block last: {_last.opname if _last else None}", flush=True)
        print(f"  block in claimed: {block in claimed}", flush=True)
        result = orig_chain_start(block, claimed)
        print(f"=== chain_start result: {[(b.start_offset, op) for b, op in result] if result else None} ===", flush=True)
        return result

    analyzer._detect_boolop_chain_start = traced_chain_start

    print(f"\n=== Calling _detect_boolop_chain_start(b0, set()) ===")
    chain = analyzer._detect_boolop_chain_start(b0, set())
    print(f"\nFinal chain: {[(b.start_offset, op) for b, op in chain] if chain else None}")


if __name__ == '__main__':
    main()
