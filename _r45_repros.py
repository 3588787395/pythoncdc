#!/usr/bin/env python3
"""R45 Test Engineer: Create minimal repros for klinedata.pyc failure patterns."""
import sys
import os
import marshal
import py_compile
import types
import dis
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

REPRO_DIR = Path(".trae/specs/region-comment-multi-pyc-iteration/rounds/round_45/test_engineer/minimal_repros")
REPRO_DIR.mkdir(parents=True, exist_ok=True)

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

def test_repro(name, source):
    """Compile source, decompile, compare bytecode. Returns (defect, details)."""
    # Write source to temp .py file
    py_path = REPRO_DIR / f"{name}.py"
    pyc_path = REPRO_DIR / f"{name}.pyc"
    ok_path = REPRO_DIR / f"{name}OK.py"

    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(source)

    # Compile to .pyc
    try:
        py_compile.compile(str(py_path), str(pyc_path), doraise=True)
    except Exception as e:
        return False, f"COMPILE_ERR: {e}"

    # Load original code
    try:
        orig_code = load_pyc_code(str(pyc_path))
    except Exception as e:
        return False, f"LOAD_ERR: {e}"

    # Decompile
    try:
        decomp_source = decompile_pyc(str(pyc_path))
        if decomp_source is None:
            return False, "DECOMPILE_NULL"
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(decomp_source)
    except Exception as e:
        return False, f"DECOMPILE_ERR: {e}"

    # Compile decompiled
    try:
        cfile = py_compile.compile(str(ok_path), doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        return True, f"RECOMPILE_ERR: {e}"

    # Compare
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    common = set(orig_map.keys()) & set(decomp_map.keys())

    total = len(orig_map)
    matched = 0
    first_diff = None

    for func_name in sorted(common):
        cmp = compare_bytecode(orig_map[func_name], decomp_map[func_name])
        if cmp.get('match') or cmp.get('jump_only'):
            matched += 1
        elif first_diff is None:
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                td = true_diffs[0]
                first_diff = f"{td.get('orig_op','?')}({td.get('orig_arg','?')}) -> {td.get('decomp_op','?')}({td.get('decomp_arg','?')})"
            else:
                first_diff = f"jump_only_diff"

    defect = matched < total
    return defect, f"{matched}/{total} matched" + (f", first_diff: {first_diff}" if first_diff else "")

# ════════════════════════════════════════════════════════════════════
# Minimal Repro Cases
# ════════════════════════════════════════════════════════════════════

repros = []

# Repro 1: try-except with return in except (PUSH_EXC_INFO pattern)
repros.append(("repro_01_try_except_return", '''
def func(x):
    try:
        return x + 1
    except Exception as e:
        return 0
'''))

# Repro 2: try-except-finally with complex body
repros.append(("repro_02_try_except_finally", '''
def func(x):
    try:
        result = x + 1
        return result
    except ValueError:
        return -1
    finally:
        cleanup = True
'''))

# Repro 3: try-except with continue in except inside loop
repros.append(("repro_03_try_except_continue", '''
def func(items):
    for item in items:
        try:
            if item > 0:
                continue
            return item
        except Exception:
            continue
    return None
'''))

# Repro 4: slice expression with None (LOAD_CONST None -> LOAD_GLOBAL slice)
repros.append(("repro_04_slice_none", '''
def func(data):
    return data[None:-1]
'''))

# Repro 5: slice with complex expression
repros.append(("repro_05_slice_complex", '''
def func(data, freq):
    return data[freq[:-1]]
'''))

# Repro 6: tuple swap (SWAP pattern)
repros.append(("repro_06_tuple_swap", '''
def func(a, b):
    a, b = b, a
    return a, b
'''))

# Repro 7: SWAP in conditional
repros.append(("repro_07_swap_conditional", '''
def func(x, y):
    if x > y:
        x, y = y, x
    return x + y
'''))

# Repro 8: for-else loop (GET_ITER pattern)
repros.append(("repro_08_for_else", '''
def func(items):
    for item in items:
        if item == 0:
            return False
    else:
        return True
'''))

# Repro 9: nested try-except in for loop
repros.append(("repro_09_nested_try_for", '''
def func(items):
    result = []
    for item in items:
        try:
            result.append(item * 2)
        except TypeError:
            result.append(0)
    return result
'''))

# Repro 10: with statement + try-except
repros.append(("repro_10_with_try", '''
def func(lock):
    with lock:
        try:
            return 1
        except Exception:
            return 0
'''))

# Repro 11: chained method calls (LOAD_METHOD -> LOAD_FAST pattern)
repros.append(("repro_11_chained_method", '''
def func(df):
    return df.datetime.tolist()[0]
'''))

# Repro 12: complex if-elif chain with method calls
repros.append(("repro_12_if_elif_method", '''
def func(x, freq):
    if freq[-1] == 'd':
        return x.isocalendar()
    elif freq[-1] == 'm':
        return x.month
    else:
        return x.year
'''))

# Run all repros
results = []
for name, source in repros:
    defect, details = test_repro(name, source)
    status = "DEFECT-REPRO" if defect else "NO-DEFECT"
    results.append((name, status, details))
    print(f"  {name:40s}  {status:15s}  {details}")

# Summary
defects = [r for r in results if r[1] == "DEFECT-REPRO"]
print(f"\n=== Summary ===")
print(f"Total repros: {len(results)}")
print(f"DEFECT-REPRO: {len(defects)}")
print(f"NO-DEFECT: {len(results) - len(defects)}")
