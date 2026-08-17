#!/usr/bin/env python3
"""R93 test: nested if-else where then returns, else doesn't,
followed by code at top level - does this produce LOAD_CONST None?"""
import sys, dis, types

# Pattern matching get_multiminute_his_data:
# if count_min == 0:          # then branch
#     his_data_dict = call()  
#     if len(his_data_dict) == 0:  # nested if
#         return his_data_dict      # then of nested if returns
# else:                           # else of outer if
#     ... lots of code ...
# return his_data_dict  # at top level

# But the decompiled source has:
# if count_min == 0:
#     his_data_dict = call()
#     if len(his_data_dict) == 0:
#         return his_data_dict
#     # NO JUMP_FORWARD here to skip else!
#     # Instead: LOAD_CONST None + RETURN_VALUE
# else:
#     ...
# return his_data_dict

# Let me check: what if there's an explicit "return None" in the then branch?
src_explicit_return = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        return None
    else:
        y = 2
    return get_call()
'''

# What if the code after the nested if is put at top level (no else)?
src_no_else = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        return None
    return get_call()
'''

for name, src in [('Explicit return None', src_explicit_return), ('No else', src_no_else)]:
    code = compile(src, f'<test>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
