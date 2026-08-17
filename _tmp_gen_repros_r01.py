#!/usr/bin/env python3
"""Round 01: Generate and verify 10+ minimal repro instances for python_syntax_comprehensive_test.pyc mismatches.

Mismatches found:
1. <module>: multiline string with special escape chars (\t\n\r'"\\) - string quoting issue
2. control_flow_examples: for-else + while-else + nested if/elif/else - control flow reconstruction
3. exception_handling_examples: try/except/else/finally + nested try - exception handling
4. multiple_coroutines: async function body dropped - async decompilation
5. complex_expressions: 1 jump_diff - minor jump target difference
"""
import sys, os, dis, types, marshal, struct, py_compile, io
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from testqouter.round1.base import compare_bytecode, decompile_pyc

REPRO_DIR = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'rounds' / 'round_01' / 'test_engineer' / 'minimal_repros'

# 10+ minimal repro source files
REPROS = {
    # Pattern S1: Multiline string with special escape characters
    'repro_01_s1_multiline_string_escapes': '''# Multiline string with \\t\\n\\r'"\\\\ escapes
msg = """
This is a multiline string.
Special chars: \\t\\n\\r'"\\\\
Unicode: \\u2705
"""
''',

    # Pattern S2: String with backslash and quotes
    'repro_02_s2_string_backslash_quotes': r'''# String with backslashes and mixed quotes
path = 'C:\\Users\\Name\\file.txt'
regex = "\\d+\\.\\d+"
mixed = 'It\\'s a "test"\\n'
''',

    # Pattern CF1: for-else with break
    'repro_03_cf1_for_else_break': '''# for-else with break
def test():
    for item in [1, 2, 3]:
        if item == 2:
            break
    else:
        print("not found")
    return "done"
''',

    # Pattern CF2: while-else with break
    'repro_04_cf2_while_else_break': '''# while-else with break
def test():
    counter = 0
    while counter < 10:
        if counter == 5:
            break
        counter += 1
    else:
        print("loop completed")
    return counter
''',

    # Pattern CF3: Nested for-else + while-else
    'repro_05_cf3_nested_for_else_while_else': '''# Nested for-else + while-else
def test():
    for item in [1, 2, 3]:
        if item == 2:
            break
    else:
        print("for else")
        counter = 0
        while counter < 5:
            if counter == 3:
                break
            counter += 1
        else:
            print("while else")
    return "done"
''',

    # Pattern CF4: for-else with continue + nested if/elif/else
    'repro_06_cf4_for_continue_elif': '''# for loop with continue and elif
def test():
    for i in range(10):
        if i == 3:
            continue
        elif i == 7:
            break
        else:
            print(i)
    return "done"
''',

    # Pattern TE1: try-except-else-finally
    'repro_07_te1_try_except_else_finally': '''# try-except-else-finally
def test():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        result = "error"
    else:
        print("success")
    finally:
        print("cleanup")
    return result
''',

    # Pattern TE2: Nested try-except
    'repro_08_te2_nested_try_except': '''# Nested try-except
def test():
    try:
        try:
            risky_call()
        except ValueError:
            print("inner")
    except Exception:
        print("outer")
    return "done"
''',

    # Pattern TE3: try-except with multiple handlers + else
    'repro_09_te3_multi_except_else': '''# try with multiple except + else
def test():
    try:
        value = int("abc")
    except ValueError:
        value = "value error"
    except TypeError:
        value = "type error"
    else:
        print("no error")
    return value
''',

    # Pattern AS1: async function with await call
    'repro_10_as1_async_await_body': '''# async function with await
import asyncio
async def test():
    results = await asyncio.gather(task1(), task2())
    return results
''',

    # Pattern AS2: async function body drop
    'repro_11_as2_async_gather': '''# async gather pattern
import asyncio
async def coro1():
    return 1
async def coro2():
    return 2
async def gather_results():
    results = await asyncio.gather(coro1(), coro2())
    return results
''',

    # Pattern CE1: chained comparison + ternary
    'repro_12_ce1_chained_compare_ternary': '''# Chained comparison + ternary
def test():
    x = 50
    result = "positive" if x > 0 else "non-positive"
    if 0 < x < 100:
        result = "in range"
    return result
''',
}

def compile_source(source):
    """Compile source string to code object."""
    return compile(source, '<repro>', 'exec')

def write_and_compile_repro(name, source):
    """Write repro to .py file and compile to .pyc."""
    py_path = REPRO_DIR / f'{name}.py'
    pyc_path = REPRO_DIR / f'{name}.pyc'

    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(source)

    # Compile to pyc
    py_compile.compile(str(py_path), str(pyc_path), '<repro>')
    return pyc_path

def verify_repro(name, source):
    """Compile, decompile, and compare bytecodes for a repro."""
    try:
        pyc_path = write_and_compile_repro(name, source)

        # Load original code
        with open(pyc_path, 'rb') as f:
            f.read(16)  # header
            orig_code = marshal.load(f)

        # Decompile
        decomp_source = decompile_pyc(str(pyc_path))

        # Compile decompiled source
        try:
            decomp_code = compile(decomp_source, '<decompiled>', 'exec')
        except SyntaxError as e:
            return {'name': name, 'status': 'SYNTAX_ERROR', 'detail': str(e)}

        # Compare top-level + all nested code objects
        def collect_codes(code, prefix=''):
            result = {prefix + code.co_name: code}
            for const in code.co_consts:
                if isinstance(const, types.CodeType):
                    child_prefix = prefix + code.co_name + '.'
                    result.update(collect_codes(const, child_prefix))
            return result

        orig_all = collect_codes(orig_code)
        decomp_all = collect_codes(decomp_code)

        all_match = True
        mismatches = []
        for func_name, orig_func in orig_all.items():
            if func_name in decomp_all:
                result = compare_bytecode(orig_func, decomp_all[func_name])
                if not result['match']:
                    all_match = False
                    true_diffs = len(result['true_diffs'])
                    jump_diffs = len(result['jump_diffs'])
                    mismatches.append(f'{func_name}: {true_diffs}td/{jump_diffs}jd')
            else:
                all_match = False
                mismatches.append(f'{func_name}: MISSING')

        if all_match:
            return {'name': name, 'status': 'NO_DEFECT', 'detail': 'All functions match'}
        else:
            return {'name': name, 'status': 'DEFECT-REPRO', 'detail': '; '.join(mismatches)}

    except Exception as e:
        import traceback
        return {'name': name, 'status': 'ERROR', 'detail': str(e)}

def main():
    print("=" * 70)
    print("Round 01: Minimal Repro Generation and Verification")
    print("=" * 70)

    results = []
    for name, source in REPROS.items():
        print(f"\n--- {name} ---")
        result = verify_repro(name, source)
        results.append(result)
        print(f"  Status: {result['status']}")
        print(f"  Detail: {result['detail']}")

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    no_defect = sum(1 for r in results if r['status'] == 'NO_DEFECT')
    defect = sum(1 for r in results if r['status'] == 'DEFECT-REPRO')
    errors = sum(1 for r in results if r['status'] in ('ERROR', 'SYNTAX_ERROR'))
    print(f"Total: {len(results)}")
    print(f"NO_DEFECT: {no_defect}")
    print(f"DEFECT-REPRO: {defect}")
    print(f"ERROR: {errors}")

    # Write report
    report_path = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'rounds' / 'round_01' / 'test_engineer' / 'decompile_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Round 01 Decompile Report\n\n")
        f.write("## Test Target\n")
        f.write("`python_syntax_comprehensive_test.pyc`\n\n")
        f.write("## Baseline Results\n")
        f.write("- Total functions: 79\n")
        f.write("- Matched: 74\n")
        f.write("- Success rate: 93.67%\n")
        f.write("- Mismatches: 5\n\n")
        f.write("## Mismatched Functions\n\n")
        f.write("| Function | true_diffs | jump_diffs | Root Cause |\n")
        f.write("|----------|-----------|-----------|------------|\n")
        f.write("| `<module>` | 1 | 0 | Multiline string with special escape chars (\\t\\n\\r'\"\\\\) not properly quoted in code generator |\n")
        f.write("| `control_flow_examples` | 47 | 28 | for-else + while-else + nested if/elif/else control flow reconstruction |\n")
        f.write("| `exception_handling_examples` | 60 | 16 | try/except/else/finally + nested try exception handling |\n")
        f.write("| `multiple_coroutines` | 18 | 0 | async function body dropped (asyncio.gather call missing) |\n")
        f.write("| `complex_expressions` | 0 | 1 | Minor jump target difference (jump_only) |\n\n")
        f.write("## Minimal Repro Instances\n\n")
        f.write("| # | Name | Status | Detail |\n")
        f.write("|---|------|--------|--------|\n")
        for i, r in enumerate(results, 1):
            f.write(f"| {i} | {r['name']} | {r['status']} | {r['detail']} |\n")
        f.write(f"\n**Summary**: {len(results)} total, {no_defect} NO_DEFECT, {defect} DEFECT-REPRO, {errors} ERROR\n\n")
        f.write("## Success Rate\n\n")
        f.write(f"- Current: 74/79 = 93.67%\n")
        f.write(f"- Target: 79/79 = 100%\n")

    print(f"\nReport saved to {report_path}")

if __name__ == '__main__':
    main()
