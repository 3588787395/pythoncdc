"""Trace api_get_financial B10 handler processing"""
import sys
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'


def main():
    module = load_pyc_file_v2(PYC)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()

    target = None
    def walk(co):
        nonlocal target
        if co.co_name == 'api_get_financial':
            target = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                walk(const)
    walk(code_obj)

    cfg = build_cfg(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()

    # Find B10 (offset 456) and B40 (offset 552)
    b10 = None
    b40 = None
    b41 = None
    for b in cfg.blocks.values():
        if b.start_offset == 456:
            b10 = b
        elif b.start_offset == 552:
            b40 = b
        elif b.start_offset == 554:
            b41 = b

    print(f"B10 succs: {[s.id for s in b10.successors]}")
    print(f"B40 instructions: {[(i.opname, i.argval) for i in b40.instructions]}")
    print(f"B41 instructions: {[(i.opname, i.argval) for i in b41.instructions]}")

    gen = RegionASTGenerator(cfg, analyzer)
    # Find return chain via successors from B10
    chain = gen._find_return_chain_via_successors(b10)
    print(f"\n_find_return_chain_via_successors(B10): {[b.id for b in chain] if chain else None}")

    # Test _is_cleanup_with_return on B41
    print(f"\nB41 cleanup_with_return test:")
    _cleanup_only_ops = {
        'SWAP', 'POP_EXCEPT', 'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
        'STORE_GLOBAL', 'STORE_DEREF', 'DELETE_FAST', 'DELETE_NAME',
        'DELETE_GLOBAL', 'DELETE_DEREF', 'POP_TOP', 'COPY', 'PRECALL', 'CALL',
        'PUSH_EXC_INFO', 'RERAISE', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
        'WITH_EXCEPT_START', 'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'JUMP_BACKWARD_NO_INTERRUPT',
    }
    instrs = [i for i in b41.instructions
              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
    print(f"  B41 instrs: {[(i.opname, i.argval) for i in instrs]}")
    for i in instrs:
        in_set = i.opname in _cleanup_only_ops
        is_ret = i.opname in ('RETURN_VALUE', 'RETURN_CONST')
        print(f"    {i.opname}: in_cleanup_ops={in_set}, is_return={is_ret}")


if __name__ == '__main__':
    main()
