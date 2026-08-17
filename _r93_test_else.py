#!/usr/bin/env python3
"""R93 test: what source structure generates LOAD_CONST None + RETURN_VALUE
instead of JUMP_FORWARD when if-then has nested if-else with returns"""
import sys, dis, types

# The decompiled source around the problematic area:
# if count_min == 0:      # offset 794
#     his_data_dict = get_kline_by_count_new(...)  # offset 730-814
#     if len(his_data_dict) == 0:  # offset 814, POP_JUMP_IF_FALSE to 820
#         return his_data_dict     # offset 816-818
# else:                          # offset 820 should be JUMP_FORWARD to 2758
#     ...                        # offset 824+ (else body)

# The issue: at offset 820, the original has JUMP_FORWARD to 2758
# (skip else body, go to merge point)
# But the decompiled has LOAD_CONST None + RETURN_VALUE
# This means Python thinks the then branch of "if count_min == 0:" ends
# with a return (implicit return None), and there's no else to skip.

# Let me test: what if the else is at the wrong indentation level?
src_correct = '''
def test():
    if True:
        x = 1
        if len(x) == 0:
            return x
        else:
            y = 2
    return get_call()
'''

src_else_at_top = '''
def test():
    if True:
        x = 1
        if len(x) == 0:
            return x
    else:
        y = 2
    return get_call()
'''

for name, src in [('Correct (else inside if)', src_correct), ('Wrong (else at top)', src_else_at_top)]:
    code = compile(src, f'<test>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
