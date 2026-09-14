"""Repro 21: while-else inside except handler context - else boundary confused

In kill_trade_process, the while-else is inside a try block and
the else block's JUMP_FORWARD target overlaps with the except
handler. The decompiler can't properly separate the else block
from the exception handling flow.

Key pattern: while-else JUMP_FORWARD target == except handler start
"""
def while_else_except_overlap(data, limit):
    result = []
    try:
        count = 0
        while count < limit:
            item = data[count] if count < len(data) else None
            if item == 'stop':
                break
            result.append(item)
            count += 1
        else:
            result.append('exhausted')
    except IndexError:
        result.append('index_error')
    return result

code = while_else_except_overlap.__code__
import dis
print("=== while-else with except overlap ===")
dis.dis(code)
