"""Trace what instructions are passed to expr_reconstructor.reconstruct
for the user_code assignment (the BUILD_STRING 25 chain).

Monkey-patch ExpressionReconstructor.reconstruct to log input instrs
when they contain a BUILD_STRING with arg >= 20.
"""
import sys, marshal
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

import core.cfg.ast_generator_v2 as agv2
_OrigReconstruct = agv2.ExpressionReconstructor.reconstruct

def _hooked_reconstruct(self, instructions, initial_stack=None):
    has_big_bs = any(getattr(i, 'opname', '') == 'BUILD_STRING' and (i.arg or 0) >= 20 for i in instructions)
    if has_big_bs:
        print(f'\n*** reconstruct called with {len(instructions)} instrs containing big BUILD_STRING ***')
        for i, ins in enumerate(instructions):
            argval = repr(ins.argval)[:40] if ins.argval is not None else ''
            print(f'  [{i:3d}] off={ins.offset:5d} {ins.opname:25s} arg={ins.arg!s:5s} {argval}')
        result = _OrigReconstruct(self, instructions, initial_stack)
        print(f'*** reconstruct result type: {type(result).__name__ if result else None} ***')
        if isinstance(result, dict):
            print(f'*** result: type={result.get("type")} ***')
            if result.get('type') == 'Assign':
                val = result.get('value', {})
                print(f'*** value type={val.get("type") if isinstance(val, dict) else None} ***')
                if isinstance(val, dict) and val.get('type') == 'JoinedStr':
                    print(f'*** JoinedStr values_count={len(val.get("values",[]))} ***')
        return result
    return _OrigReconstruct(self, instructions, initial_stack)

agv2.ExpressionReconstructor.reconstruct = _hooked_reconstruct

# Also patch the reference in region_ast_generator (it imports the class)
import core.cfg.region_ast_generator as rag
rag.ExpressionReconstructor = agv2.ExpressionReconstructor

from pycdc import decompile_pyc
PYC = r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtest.pyc'
try:
    src = decompile_pyc(PYC)
    print('\n=== DECOMPILE OK ===')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('\n=== DECOMPILE FAILED ===')
