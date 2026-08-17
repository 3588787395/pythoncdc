#!/usr/bin/env python3
"""R94: Debug except handler body statement generation for get_kline_by_date_one"""
import sys, dis, marshal, types
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import get_bytecode_instructions, _filter_noise_instrs

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"

import marshal
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

# Show the full bytecode for get_kline_by_date_one
orig_co = orig_map['get_kline_by_date_one']
orig_instrs = _filter_noise_instrs(get_bytecode_instructions(orig_co))

# Find the except handler entry (PUSH_EXC_INFO)
for i, instr in enumerate(orig_instrs):
    if instr.opname == 'PUSH_EXC_INFO':
        print(f"=== Except handler area (from idx {i}) ===")
        for j in range(i, min(i + 30, len(orig_instrs))):
            instr_j = orig_instrs[j]
            argval = instr_j.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"  [{j}] offset={instr_j.offset} {instr_j.opname}({argval})")
        break

# Now let's manually trace _generate_handler_body_statements logic
print("\n=== Manual trace of _generate_handler_body_statements ===")

# Simulate handler_instrs filtering
_EXC_FRAMEWORK_OPS = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                       'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'WITH_EXCEPT_START', 'EXTENDED_ARG')

# Find the handler block
handler_start_idx = None
for i, instr in enumerate(orig_instrs):
    if instr.opname == 'PUSH_EXC_INFO':
        handler_start_idx = i
        break

if handler_start_idx is not None:
    # Get handler block instructions (from PUSH_EXC_INFO to end or next block)
    handler_block_instrs = orig_instrs[handler_start_idx:]
    
    # Find exc_dispatch_jump_offset
    exc_dispatch_jump_offset = None
    for idx, instr in enumerate(handler_block_instrs):
        if instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
            for next_instr in handler_block_instrs[idx + 1:]:
                if next_instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                         'JUMP_IF_FALSE', 'JUMP_IF_TRUE',
                                         'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
                                         'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                         'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                                         'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE'):
                    exc_dispatch_jump_offset = next_instr.offset
                    break
                elif next_instr.opname not in ('LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_CONST',
                                               'LOAD_ATTR', 'LOAD_DEREF', 'COPY', 'BUILD_LIST',
                                               'SWAP', 'EXTENDED_ARG'):
                    break
            break
    
    print(f"exc_dispatch_jump_offset: {exc_dispatch_jump_offset}")
    
    # Filter handler_instrs
    handler_instrs = [i for i in handler_block_instrs
                      if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                           'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                           'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                           'WITH_EXCEPT_START', 'EXTENDED_ARG')]
    if exc_dispatch_jump_offset is not None:
        handler_instrs = [i for i in handler_instrs if i.offset > exc_dispatch_jump_offset]
    
    print(f"\nFiltered handler_instrs ({len(handler_instrs)}):")
    for i, instr in enumerate(handler_instrs):
        argval = instr.argval
        if isinstance(argval, str) and len(argval) > 40:
            argval = argval[:40] + '...'
        print(f"  [{i}] offset={instr.offset} {instr.opname}({argval})")
    
    # Now trace the main loop
    print(f"\n=== Main loop trace ===")
    stmt_instrs = []
    skip_initial_pop = True  # Initial POP_TOP
    
    for instr in handler_block_instrs:
        if instr.offset in set([i.offset for i in handler_block_instrs if i.offset <= (exc_dispatch_jump_offset or 0)]):
            if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                pass  # skip
                continue
        
        if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
            continue
        
        if instr.opname == 'POP_TOP' and skip_initial_pop:
            print(f"  [{instr.offset}] POP_TOP (skip_initial_pop=True, skipping)")
            skip_initial_pop = False
            continue
        
        if instr.opname == 'POP_TOP' and not skip_initial_pop and stmt_instrs:
            print(f"  [{instr.offset}] POP_TOP (not initial, stmt_instrs={len(stmt_instrs)} items)")
            print(f"    stmt_instrs: {[i.opname for i in stmt_instrs]}")
            # This is where expr_reconstructor.reconstruct is called
            print(f"    -> Would call expr_reconstructor.reconstruct(stmt_instrs)")
            print(f"    -> If reconstruct fails, instructions are LOST!")
            stmt_instrs = []
            continue
        
        if instr.opname == 'POP_EXCEPT':
            print(f"  [{instr.offset}] POP_EXCEPT (processing cleanup)")
            stmt_instrs = []
            skip_initial_pop = True
            continue
        
        if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'WITH_EXCEPT_START'):
            continue
        
        if instr.opname == 'RERAISE':
            print(f"  [{instr.offset}] RERAISE")
            continue
        
        # Add to stmt_instrs
        stmt_instrs.append(instr)
        if instr.opname in ('STORE_FAST', 'STORE_NAME'):
            print(f"  [{instr.offset}] {instr.opname}({instr.argval}) -> added to stmt_instrs (now {len(stmt_instrs)} items)")
        elif instr.opname in ('CALL',):
            print(f"  [{instr.offset}] {instr.opname}({instr.argval}) -> added to stmt_instrs (now {len(stmt_instrs)} items)")
        elif instr.opname in ('LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_ATTR', 'LOAD_CONST', 'FORMAT_VALUE', 'BUILD_STRING'):
            print(f"  [{instr.offset}] {instr.opname}({instr.argval}) -> added to stmt_instrs")
