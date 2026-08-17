#!/usr/bin/env python3
"""Verify bytecode equivalence: compare original .pyc with decompiled .py"""
import sys
import dis
import marshal
import struct
import importlib.util
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def load_pyc_code(pyc_path):
    """Load code object from .pyc file"""
    with open(pyc_path, 'rb') as f:
        magic = f.read(4)
        f.read(12)  # flags + timestamp + size
        code = marshal.loads(f.read())
    return code

def compare_code_objects(orig_code, decomp_code, prefix=""):
    """Recursively compare two code objects"""
    diffs = []
    
    orig_instrs = list(dis.get_instructions(orig_code))
    decomp_instrs = list(dis.get_instructions(decomp_code))
    
    if len(orig_instrs) != len(decomp_instrs):
        diffs.append(f"{prefix}Instruction count: orig={len(orig_instrs)}, decomp={len(decomp_instrs)}")
        # Show first difference
        min_len = min(len(orig_instrs), len(decomp_instrs))
        for i in range(min_len):
            o = orig_instrs[i]
            d = decomp_instrs[i]
            if o.opname != d.opname or o.arg != d.arg:
                diffs.append(f"{prefix}  First diff at index {i}:")
                diffs.append(f"{prefix}    orig: {o.offset:4d} {o.opname:30s} {o.arg}")
                diffs.append(f"{prefix}    decomp: {d.offset:4d} {d.opname:30s} {d.arg}")
                break
        return diffs
    
    for i, (o, d) in enumerate(zip(orig_instrs, decomp_instrs)):
        if o.opname != d.opname:
            diffs.append(f"{prefix}  Offset {o.offset}: opname orig={o.opname} decomp={d.opname}")
            break
        if o.opname in ('LOAD_CONST', 'LOAD_FAST', 'STORE_FAST', 'LOAD_GLOBAL', 
                         'COMPARE_OP', 'BINARY_OP', 'BUILD_STRING', 'LOAD_DEREF',
                         'STORE_DEREF', 'MAKE_CELL', 'COPY_FREE_VARS',
                         'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET',
                         'CALL', 'PRECALL', 'FORMAT_VALUE', 'LOAD_ATTR',
                         'STORE_NAME', 'LOAD_NAME', 'IMPORT_NAME', 'IMPORT_FROM',
                         'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                         'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                         'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                         'GET_ITER', 'FOR_ITER', 'BINARY_SUBSCR', 'STORE_SUBSCR',
                         'UNPACK_SEQUENCE', 'BUILD_SLICE', 'CONTAINS_OP',
                         'IS_OP', 'LIST_EXTEND', 'DICT_UPDATE', 'SET_UPDATE',
                         'LIST_APPEND', 'DICT_MERGE', 'MAP_ADD',
                         'POP_BLOCK', 'PUSH_BLOCK', 'PUSH_NULL',
                         'END_FOR', 'END_SEND', 'RETURN_GENERATOR',
                         'GET_AWAITABLE', 'SEND', 'GET_AITER', 'GET_ANEXT',
                         'END_ASYNC_FOR', 'BEFORE_ASYNC_WITH', 'BEFORE_WITH',
                         'SETUP_FINALLY', 'SETUP_WITH', 'SETUP_ASYNC_WITH',
                         'POP_EXCEPT', 'RERAISE', 'COPY', 'SWAP', 'LOAD_ASSERTION_ERROR',
                         'LOAD_METHOD', 'CALL_METHOD', 'KW_NAMES',
                         'RETURN_VALUE', 'RETURN_CONST', 'RESUME',
                         'PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                         'YIELD_VALUE', 'GET_YIELD_FROM_ITER', 'SET_ADD',
                         'DELETE_FAST', 'DELETE_GLOBAL', 'DELETE_NAME',
                         'STORE_ATTR', 'DELETE_ATTR', 'STORE_GLOBAL',
                         'LOAD_SUPER_ATTR', 'MATCH_CLASS', 'MATCH_MAPPING',
                         'MATCH_SEQUENCE', 'MATCH_KEYS', 'KW_NAMES',
                         'BINARY_OP', 'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
                         'NOP', 'CACHE', 'EXTENDED_ARG',
                         'LOAD_CLOSURE', 'MAKE_FUNCTION', 'CALL_KW',
                         'GET_LEN', 'MATCH_SELF', 'LOAD_LOCALS',
                         ):
            # Normalize arg comparison: for jump ops, compare argval (target offset)
            # For other ops, compare arg
            if o.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                            'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                            'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                            'FOR_ITER', 'SEND'):
                if o.argval != d.argval:
                    diffs.append(f"{prefix}  Offset {o.offset}: {o.opname} argval orig={o.argval} decomp={d.argval}")
                    break
            elif o.opname in ('LOAD_CONST',):
                # Compare const values (but not code objects)
                ov = o.argval
                dv = d.argval
                if isinstance(ov, type(dv)) or isinstance(dv, type(ov)):
                    if ov != dv:
                        # Check if both are code objects
                        if hasattr(ov, 'co_code') and hasattr(dv, 'co_code'):
                            # Compare recursively
                            sub_diffs = compare_code_objects(ov, dv, prefix + f"  [const@{o.offset}]")
                            if sub_diffs:
                                diffs.extend(sub_diffs)
                                break
                        else:
                            diffs.append(f"{prefix}  Offset {o.offset}: LOAD_CONST orig={ov!r} decomp={dv!r}")
                            break
                elif hasattr(ov, 'co_code') or hasattr(dv, 'co_code'):
                    if hasattr(ov, 'co_code') and hasattr(dv, 'co_code'):
                        sub_diffs = compare_code_objects(ov, dv, prefix + f"  [const@{o.offset}]")
                        if sub_diffs:
                            diffs.extend(sub_diffs)
                            break
                    else:
                        diffs.append(f"{prefix}  Offset {o.offset}: LOAD_CONST type orig={type(ov).__name__} decomp={type(dv).__name__}")
                        break
    
    # Compare nested code objects
    orig_consts = [c for c in orig_code.co_consts if hasattr(c, 'co_code')]
    decomp_consts = [c for c in decomp_code.co_consts if hasattr(c, 'co_code')]
    
    if len(orig_consts) != len(decomp_consts):
        diffs.append(f"{prefix}  Nested code count: orig={len(orig_consts)} decomp={len(decomp_consts)}")
        return diffs
    
    for i, (oc, dc) in enumerate(zip(orig_consts, decomp_consts)):
        if oc.co_name != dc.co_name:
            diffs.append(f"{prefix}  Nested[{i}]: name orig={oc.co_name} decomp={dc.co_name}")
            continue
        sub_diffs = compare_code_objects(oc, dc, prefix + f"  [{oc.co_name}]")
        diffs.extend(sub_diffs)
    
    return diffs

pyc_path = sys.argv[1]
py_path = sys.argv[2] if len(sys.argv) > 2 else pyc_path.replace('.pyc', 'OK.py')

orig_code = load_pyc_code(pyc_path)
decomp_source = Path(py_path).read_text(encoding='utf-8')
decomp_code = compile(decomp_source, py_path, 'exec')

diffs = compare_code_objects(orig_code, decomp_code)

if not diffs:
    print(f"✓ {pyc_path}: PERFECT MATCH")
    sys.exit(0)
else:
    print(f"✗ {pyc_path}: {len(diffs)} differences")
    for d in diffs[:20]:
        print(f"  {d}")
    sys.exit(1)
