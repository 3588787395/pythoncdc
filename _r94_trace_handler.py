#!/usr/bin/env python3
"""R94: Trace the actual execution path through _generate_handler_body_statements"""
import sys, types, marshal
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import get_bytecode_instructions, _filter_noise_instrs

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

orig_code = load_pyc(pyc_path)

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
orig_co = orig_map['get_kline_by_date_one']
orig_instrs = _filter_noise_instrs(get_bytecode_instructions(orig_co))

# Get the except handler block (from PUSH_EXC_INFO to the end)
# In a real CFG, the handler would be a separate block
# Let's find where PUSH_EXC_INFO is and look at the block boundaries
for i, instr in enumerate(orig_instrs):
    if instr.opname == 'PUSH_EXC_INFO':
        print(f"PUSH_EXC_INFO at idx {i}, offset {instr.offset}")
        # Print all instructions from here
        print(f"\nAll instructions from PUSH_EXC_INFO:")
        for j in range(i, min(i + 35, len(orig_instrs))):
            instr_j = orig_instrs[j]
            argval = instr_j.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"  [{j}] offset={instr_j.offset} {instr_j.opname}({argval})")
        break

# The key question: is the except handler a single block or multiple blocks?
# In CPython 3.11+, the except handler is typically a single basic block
# from PUSH_EXC_INFO to POP_EXCEPT/RERAISE

# But wait - look at the POP_JUMP_FORWARD_IF_FALSE at idx 147 (offset 798)
# This jump target determines if we enter the handler body or skip to next handler
# The handler body starts at offset 800 (POP_TOP)

# The key issue: does _generate_handler_body_statements receive a SINGLE block
# containing ALL these instructions? Or are there multiple blocks?

# In the CFG, blocks are split at jump targets. The PUSH_EXC_INFO block 
# typically extends from PUSH_EXC_INFO to the next jump target or block boundary.

# Let's check: the POP_JUMP_FORWARD_IF_NOT_NONE at offset 882 is a conditional jump.
# This would split the block.

# So the handler block from PUSH_EXC_INFO to POP_JUMP_FORWARD_IF_NOT_NONE would be:
# PUSH_EXC_INFO, LOAD_GLOBAL BaseException, CHECK_EXC_MATCH, POP_JUMP_FORWARD_IF_FALSE,
# POP_TOP, LOAD_GLOBAL get_traceback_message, CALL 0, STORE_FAST error_info,
# LOAD_GLOBAL system_log, LOAD_ATTR error, LOAD_FAST symbol, FORMAT_VALUE,
# LOAD_CONST, LOAD_FAST error_info, FORMAT_VALUE, BUILD_STRING 3, CALL 1,
# POP_TOP, LOAD_FAST fields, POP_JUMP_FORWARD_IF_NOT_NONE

# If POP_JUMP_FORWARD_IF_NOT_NONE splits the block, then:
# Block 1: PUSH_EXC_INFO ... POP_TOP (CALL result discard)
# Block 2: LOAD_FAST fields, POP_JUMP_FORWARD_IF_NOT_NONE ... (the if/else part)

# In Block 1, the POP_TOP at offset 878 would be the LAST meaningful instruction
# before the block boundary. But POP_JUMP_FORWARD_IF_NOT_NONE is the actual
# block terminator (conditional jump).

# The question is: does _generate_handler_body_statements see ONE block or TWO?
# If ONE: the trace I did earlier is correct, and STORE_FAST at 18742 should fire
# BEFORE POP_TOP at 18207.
# If TWO (split at POP_JUMP_FORWARD_IF_NOT_NONE): Block 1 ends with 
# POP_JUMP_FORWARD_IF_NOT_NONE, and _generate_handler_body_statements processes
# the block. The POP_TOP at 878 would still be in the same block as STORE_FAST.

# Let me check what _generate_handler_body_statements receives by looking at
# the actual CFG blocks

print("\n=== Checking block structure ===")
# Find block boundaries based on jump targets
jump_targets = set()
for i, instr in enumerate(orig_instrs):
    if instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                        'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                        'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
                        'JUMP_BACKWARD_NO_INTERRUPT'):
        if instr.argval is not None:
            jump_targets.add(instr.argval)
    if instr.opname in ('PUSH_EXC_INFO', 'POP_EXCEPT', 'RERAISE'):
        pass  # Don't add these as block boundaries

print(f"Jump targets: {sorted(jump_targets)}")

# The handler block starts at PUSH_EXC_INFO (offset 782)
# Find the next block boundary after PUSH_EXC_INFO
handler_start = 782  # PUSH_EXC_INFO offset
block_end = None
for i, instr in enumerate(orig_instrs):
    if instr.offset <= handler_start:
        continue
    if instr.offset in jump_targets:
        block_end = instr.offset
        break

print(f"Handler block: {handler_start} to {block_end}")
if block_end:
    print(f"Instructions in handler block:")
    for i, instr in enumerate(orig_instrs):
        if instr.offset >= handler_start and instr.offset < block_end:
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"  offset={instr.offset} {instr.opname}({argval})")
