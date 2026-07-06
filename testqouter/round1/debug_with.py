import os, sys, py_compile, dis, json, struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base import decompile_pyc, compile_and_compare, test_semantic_equivalence

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_exception_table(code_obj):
    """Parse Python 3.11+ exception table from co_exceptiontable bytes."""
    result = []
    exctable = getattr(code_obj, 'co_exceptiontable', None)
    if not exctable:
        return result
    try:
        data = memoryview(exctable)
        pos = 0
        while pos < len(data):
            start = struct.unpack_from('<H', data, pos)[0] * 2
            end = struct.unpack_from('<H', data, pos + 2)[0] * 2
            target = struct.unpack_from('<H', data, pos + 4)[0] * 2
            depth = struct.unpack_from('<H', data, pos + 6)[0]
            result.append({'start': start, 'end': end, 'target': target, 'depth': depth})
            pos += 8
    except Exception:
        pass
    return result

failing_tests = [
    'test_w04_nested_with',
    'test_w05_with_with_try',
    'test_w06_try_with_with',
    'test_r1_try_with',
]

for test_name in failing_tests:
    py_path = os.path.join(TEST_DIR, test_name + '.py')
    pyc_path = py_path + 'c'

    print('=' * 70)
    print(f'TEST: {test_name}')
    print('=' * 70)

    with open(py_path, 'r', encoding='utf-8') as f:
        orig_source = f.read()
    print('--- Original Source ---')
    print(orig_source.strip())

    py_compile.compile(py_path, pyc_path, doraise=True)

    orig_code = compile(orig_source, '<original>', 'exec')
    test_func = None
    for const in orig_code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'test':
            test_func = const
            break

    if test_func:
        print('\n--- Original Bytecode (test function) ---')
        for instr in dis.get_instructions(test_func):
            target_hex = ''
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE') and instr.argval is not None:
                if isinstance(instr.argval, int):
                    target_hex = f' -> {instr.argval:#x}'
            offset_hex = f'{instr.offset:#x}'
            line_str = f'  L{instr.starts_line}' if instr.starts_line else ''
            print(f'  {offset_hex:>6s}{line_str:<5s} {instr.opname:<25s} {str(instr.argval):<15s}{target_hex}')

        print('\n--- Exception Table ---')
        for entry in parse_exception_table(test_func):
            print(f'  start={entry["start"]:#x} end={entry["end"]:#x} target={entry["target"]:#x} depth={entry["depth"]}')

    try:
        decompiled = decompile_pyc(pyc_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'\n--- DECOMPILE FAILED: {e} ---')
        if os.path.exists(pyc_path):
            os.remove(pyc_path)
        continue

    print('\n--- Decompiled Source ---')
    print(decompiled)

    try:
        compile(decompiled, '<decompiled>', 'exec')
        print('\n--- Syntax: OK ---')
    except SyntaxError as e:
        print(f'\n--- Syntax: FAIL - {e} ---')

    decomp_code = compile(decompiled, '<decompiled>', 'exec')
    decomp_func = None
    for const in decomp_code.co_consts:
        if hasattr(const, 'co_name') and const.co_name == 'test':
            decomp_func = const
            break

    if decomp_func:
        print('\n--- Decompiled Bytecode (test function) ---')
        for instr in dis.get_instructions(decomp_func):
            target_hex = ''
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE') and instr.argval is not None:
                if isinstance(instr.argval, int):
                    target_hex = f' -> {instr.argval:#x}'
            offset_hex = f'{instr.offset:#x}'
            line_str = f'  L{instr.starts_line}' if instr.starts_line else ''
            print(f'  {offset_hex:>6s}{line_str:<5s} {instr.opname:<25s} {str(instr.argval):<15s}{target_hex}')

    semantic = test_semantic_equivalence(py_path, decompiled)
    print(f'\n--- Semantic ---')
    print(json.dumps(semantic, indent=2, default=str))

    if os.path.exists(pyc_path):
        os.remove(pyc_path)

    print()
