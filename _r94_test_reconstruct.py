#!/usr/bin/env python3
"""R94: Test expr_reconstructor.reconstruct with system_log.error call instructions"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.ast_generator_v2 import ExpressionReconstructor
from core.cfg.basic_block import Instruction

# Create mock instructions for: system_log.error(f'{symbol} ...: {error_info}')
stmt_instrs = [
    Instruction(offset=830, opcode=0, opname='LOAD_GLOBAL', arg=0, argval='system_log'),
    Instruction(offset=842, opcode=0, opname='LOAD_ATTR', arg=0, argval='error'),
    Instruction(offset=852, opcode=0, opname='LOAD_FAST', arg=0, argval='symbol'),
    Instruction(offset=854, opcode=0, opname='FORMAT_VALUE', arg=0, argval=('<class str>', False)),
    Instruction(offset=856, opcode=0, opname='LOAD_CONST', arg=0, argval='获取数据异常: '),
    Instruction(offset=858, opcode=0, opname='LOAD_FAST', arg=0, argval='error_info'),
    Instruction(offset=860, opcode=0, opname='FORMAT_VALUE', arg=0, argval=('<class str>', False)),
    Instruction(offset=862, opcode=0, opname='BUILD_STRING', arg=3, argval=3),
    Instruction(offset=868, opcode=0, opname='CALL', arg=1, argval=1),
]

reconstructor = ExpressionReconstructor()
result = reconstructor.reconstruct(stmt_instrs)
print(f"Result: {result}")
if result:
    print(f"Type: {result.get('type')}")
    if result.get('type') == 'Call':
        func = result.get('func', {})
        print(f"Func: {func.get('type')} {func.get('id', func.get('attr', ''))}")
        args = result.get('args', [])
        print(f"Args: {len(args)}")
        for arg in args:
            print(f"  arg type: {arg.get('type')}")
