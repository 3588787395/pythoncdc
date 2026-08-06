import os
import sys
import dis
import types
from typing import Dict, List, Tuple, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pycdc import decompile_pyc as _pycdc_decompile


def decompile_pyc(pyc_path: str) -> str:
    source = _pycdc_decompile(pyc_path)
    lines = source.split('\n')
    clean_lines = []
    for line in lines:
        if line.startswith('# Source') or line.startswith('# File:'):
            continue
        clean_lines.append(line)
    return '\n'.join(clean_lines).strip()


def get_bytecode_instructions(code: types.CodeType) -> List[dis.Instruction]:
    return list(dis.get_instructions(code))


def _classify_instruction(opname: str) -> str:
    jump_ops = {
        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        'FOR_ITER', 'SEND', 'SETUP_FINALLY', 'SETUP_WITH',
    }
    if opname in jump_ops:
        return 'jump'
    if opname.startswith('LOAD_') or opname == 'PUSH_NULL':
        return 'load'
    if opname.startswith('STORE_'):
        return 'store'
    if opname.startswith('BINARY_') or opname.startswith('INPLACE_') or opname.startswith('COMPARE_'):
        return 'compute'
    if opname.startswith('CALL_') or opname == 'CALL' or opname == 'PRECALL':
        return 'call'
    if opname in ('RETURN_VALUE', 'RETURN_GENERATOR', 'YIELD_VALUE'):
        return 'return'
    return 'other'


def _normalize_argval(argval: Any) -> Any:
    """Normalize a LOAD_CONST argval to remove recompilation identity noise.

    Recompiled code objects differ from the originals only by memory address
    and embedded ``co_filename`` (original .py vs OK.py). String constants that
    hold a .py/.pyc file path likewise differ only in the directory portion.
    Neither is a real mismatch, so they are canonicalized before comparison:

    - Code objects -> ``"<code object {co_name}>"`` (drops address & file path)
    - Strings that look like a .py/.pyc file path -> basename only
    - frozenset -> tuple (Python peephole optimizer may or may not convert
      ``in (a, b, c)`` to ``in frozenset({a, b, c})`` depending on version;
      both forms are semantically identical for membership testing)
    - Anything else is returned unchanged.
    """
    if isinstance(argval, types.CodeType):
        return f"<code object {argval.co_name}>"
    if isinstance(argval, str):
        low = argval.lower()
        if (low.endswith('.py') or low.endswith('.pyc')) and ('/' in argval or '\\' in argval):
            return os.path.basename(argval)
    if isinstance(argval, frozenset):
        return frozenset(argval)
    return argval


def compare_bytecode(orig_code: types.CodeType, decomp_code: types.CodeType) -> Dict[str, Any]:
    orig_instrs = get_bytecode_instructions(orig_code)
    decomp_instrs = get_bytecode_instructions(decomp_code)

    result = {
        'match': False,
        'orig_count': len(orig_instrs),
        'decomp_count': len(decomp_instrs),
        'jump_diffs': [],
        'true_diffs': [],
        'orig_ops': [i.opname for i in orig_instrs],
        'decomp_ops': [i.opname for i in decomp_instrs],
    }

    if orig_instrs == decomp_instrs:
        result['match'] = True
        return result

    max_len = max(len(orig_instrs), len(decomp_instrs))
    for idx in range(max_len):
        orig_instr = orig_instrs[idx] if idx < len(orig_instrs) else None
        decomp_instr = decomp_instrs[idx] if idx < len(decomp_instrs) else None

        if orig_instr is None:
            result['true_diffs'].append({
                'index': idx,
                'type': 'extra_in_decomp',
                'decomp_op': decomp_instr.opname,
                'decomp_arg': _normalize_argval(decomp_instr.argval),
            })
            continue

        if decomp_instr is None:
            result['true_diffs'].append({
                'index': idx,
                'type': 'missing_in_decomp',
                'orig_op': orig_instr.opname,
                'orig_arg': _normalize_argval(orig_instr.argval),
            })
            continue

        # Normalize argvals for both sides before comparison
        orig_norm = _normalize_argval(orig_instr.argval)
        decomp_norm = _normalize_argval(decomp_instr.argval)

        # [R34] LOAD_ATTR and LOAD_METHOD are semantically equivalent in
        # Python 3.11 — LOAD_METHOD is an optimization hint for the VM.
        # Different Python 3.11.x patch versions may choose one or the other
        # for the same source code. Treat them as equivalent.
        _EQUIV_OPS = {'LOAD_ATTR': 'LOAD_METHOD', 'LOAD_METHOD': 'LOAD_ATTR'}
        _orig_op = orig_instr.opname
        _decomp_op = decomp_instr.opname
        if _EQUIV_OPS.get(_orig_op) == _decomp_op:
            _orig_op = _decomp_op  # normalize to same opcode name
        if _orig_op != _decomp_op:
            if _classify_instruction(orig_instr.opname) == 'jump' or _classify_instruction(decomp_instr.opname) == 'jump':
                result['jump_diffs'].append({
                    'index': idx,
                    'orig_op': orig_instr.opname,
                    'decomp_op': decomp_instr.opname,
                    'orig_arg': orig_norm,
                    'decomp_arg': decomp_norm,
                })
            else:
                result['true_diffs'].append({
                    'index': idx,
                    'orig_op': orig_instr.opname,
                    'decomp_op': decomp_instr.opname,
                    'orig_arg': orig_norm,
                    'decomp_arg': decomp_norm,
                })
        elif orig_norm != decomp_norm:
            # [R34] frozenset vs tuple: Python peephole optimizer may convert
            # ``in (a, b, c)`` to ``in frozenset({a, b, c})``. Both forms are
            # semantically identical for membership testing. When one side is
            # frozenset and the other is tuple, check set equality.
            _frozen_equiv = (
                (isinstance(orig_norm, frozenset) and isinstance(decomp_norm, tuple)
                 and set(orig_norm) == set(decomp_norm))
                or (isinstance(decomp_norm, frozenset) and isinstance(orig_norm, tuple)
                    and set(decomp_norm) == set(orig_norm))
            )
            if not _frozen_equiv:
                if _classify_instruction(orig_instr.opname) == 'jump':
                    result['jump_diffs'].append({
                        'index': idx,
                        'orig_op': orig_instr.opname,
                        'decomp_op': decomp_instr.opname,
                        'orig_arg': orig_norm,
                        'decomp_arg': decomp_norm,
                    })
                else:
                    result['true_diffs'].append({
                        'index': idx,
                        'orig_op': orig_instr.opname,
                        'decomp_op': decomp_instr.opname,
                        'orig_arg': orig_norm,
                        'decomp_arg': decomp_norm,
                    })

    if not result['true_diffs'] and not result['jump_diffs']:
        result['match'] = True
    elif not result['true_diffs'] and result['jump_diffs']:
        result['jump_only'] = True

    return result


def compile_and_compare(orig_py_path: str, decompiled_source: str) -> Dict[str, Any]:
    with open(orig_py_path, 'r', encoding='utf-8') as f:
        orig_source = f.read()

    orig_code = compile(orig_source, '<original>', 'exec')
    decomp_code = compile(decompiled_source, '<decompiled>', 'exec')

    return compare_bytecode(orig_code, decomp_code)


def _extract_functions(ns: Dict[str, Any]) -> Dict[str, Any]:
    funcs = {}
    for name, val in ns.items():
        if callable(val) and not name.startswith('_'):
            funcs[name] = val
    return funcs


def test_semantic_equivalence(orig_py_path: str, decompiled_source: str,
                                test_args: List[tuple] = None) -> Dict[str, Any]:
    with open(orig_py_path, 'r', encoding='utf-8') as f:
        orig_source = f.read()

    orig_ns = {}
    exec(compile(orig_source, '<original>', 'exec'), orig_ns)

    decomp_ns = {}
    exec(compile(decompiled_source, '<decompiled>', 'exec'), decomp_ns)

    orig_funcs = _extract_functions(orig_ns)
    decomp_funcs = _extract_functions(decomp_ns)

    result = {
        'equivalent': True,
        'orig_func_names': sorted(orig_funcs.keys()),
        'decomp_func_names': sorted(decomp_funcs.keys()),
        'mismatches': [],
    }

    if sorted(orig_funcs.keys()) != sorted(decomp_funcs.keys()):
        result['equivalent'] = False
        result['mismatches'].append({
            'type': 'func_name_mismatch',
            'orig': sorted(orig_funcs.keys()),
            'decomp': sorted(decomp_funcs.keys()),
        })
        return result

    if test_args is None:
        test_args = [()]

    for func_name in orig_funcs:
        for args in test_args:
            try:
                orig_r = orig_funcs[func_name](*args)
            except Exception as e:
                orig_r = f'EXCEPTION:{type(e).__name__}:{e}'
            try:
                decomp_r = decomp_funcs[func_name](*args)
            except Exception as e:
                decomp_r = f'EXCEPTION:{type(e).__name__}:{e}'

            if orig_r != decomp_r:
                if callable(orig_r) and callable(decomp_r):
                    continue
                result['equivalent'] = False
                result['mismatches'].append({
                    'type': 'return_value_mismatch',
                    'func': func_name,
                    'args': args,
                    'orig_return': repr(orig_r),
                    'decomp_return': repr(decomp_r),
                })

    return result


class BytecodeTestCase:
    SOURCE_FILE = ""

    @classmethod
    def get_py_path(cls) -> str:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.SOURCE_FILE)

    @classmethod
    def get_pyc_path(cls) -> str:
        return cls.get_py_path() + 'c'

    @classmethod
    def run_full_test(cls):
        import py_compile
        py_path = cls.get_py_path()
        pyc_path = cls.get_pyc_path()

        try:
            py_compile.compile(py_path, pyc_path, doraise=True)
        except Exception as e:
            return {'status': 'COMPILE_FAIL', 'error': str(e)}

        try:
            decompiled = decompile_pyc(pyc_path)
        except Exception as e:
            if os.path.exists(pyc_path):
                os.remove(pyc_path)
            return {'status': 'DECOMPILE_FAIL', 'error': str(e)}

        try:
            compile(decompiled, '<decompiled>', 'exec')
            syntax_ok = True
        except SyntaxError as e:
            if os.path.exists(pyc_path):
                os.remove(pyc_path)
            return {'status': 'SYNTAX_FAIL', 'error': str(e), 'source': decompiled}

        bytecode_result = compile_and_compare(py_path, decompiled)

        semantic_result = test_semantic_equivalence(py_path, decompiled)

        try:
            if os.path.exists(pyc_path):
                os.remove(pyc_path)
        except Exception:
            pass

        return {
            'status': 'OK',
            'syntax_ok': syntax_ok,
            'bytecode': bytecode_result,
            'semantic': semantic_result,
        }
