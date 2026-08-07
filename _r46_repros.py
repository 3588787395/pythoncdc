#!/usr/bin/env python3
"""R46: Analyze arg_checker.pyc mismatches and create minimal repros."""
import sys, os, marshal, py_compile, types, dis
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_code_objects(code_obj, prefix=""):
    result = {}
    name = prefix + code_obj.co_name if prefix else (code_obj.co_name or '<module>')
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = (prefix + code_obj.co_name + ".") if prefix else (code_obj.co_name + ".")
            result.update(extract_code_objects(const, child_prefix))
    return result

REPRO_DIR = Path(".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros")
REPRO_DIR.mkdir(parents=True, exist_ok=True)

def test_repro(name, source):
    py_path = REPRO_DIR / f"{name}.py"
    pyc_path = REPRO_DIR / f"{name}.pyc"
    ok_path = REPRO_DIR / f"{name}OK.py"
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write(source)
    try:
        py_compile.compile(str(py_path), str(pyc_path), doraise=True)
    except Exception as e:
        return False, f"COMPILE_ERR: {e}"
    try:
        orig_code = load_pyc_code(str(pyc_path))
    except Exception as e:
        return False, f"LOAD_ERR: {e}"
    try:
        decomp_source = decompile_pyc(str(pyc_path))
        if decomp_source is None:
            return False, "DECOMPILE_NULL"
        with open(ok_path, 'w', encoding='utf-8') as f:
            f.write(decomp_source)
    except Exception as e:
        return False, f"DECOMPILE_ERR: {e}"
    try:
        cfile = py_compile.compile(str(ok_path), doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except Exception as e:
        return True, f"RECOMPILE_ERR: {e}"
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
                first_diff = "jump_only_diff"
    defect = matched < total
    return defect, f"{matched}/{total} matched" + (f", first_diff: {first_diff}" if first_diff else "")

repros = [
    ("repro_01_raise_valueerror", 'def func(x):\n    if x < 0:\n        raise ValueError("invalid")\n    return x\n'),
    ("repro_02_raise_in_except", 'def func(x):\n    try:\n        return x + 1\n    except ValueError:\n        raise ValueError("re-raise")\n'),
    ("repro_03_raise_typeerror", 'def func(x):\n    if not isinstance(x, int):\n        raise TypeError("not int")\n    return x\n'),
    ("repro_04_nested_raise", 'def func(x):\n    if x < 0:\n        raise ValueError("negative")\n    elif x > 100:\n        raise OverflowError("too large")\n    return x\n'),
    ("repro_05_closure", 'def outer(rules):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            return func(*args, **kwargs)\n        return wrapper\n    return decorator\n'),
    ("repro_06_closure_simple", 'def outer(x):\n    def inner():\n        return x + 1\n    return inner\n'),
    ("repro_07_closure_multiple", 'def outer(a, b):\n    def inner():\n        return a + b\n    return inner\n'),
    ("repro_08_simple_raise", 'def func():\n    raise Exception("error")\n'),
    ("repro_09_try_except_pass", 'def func(x):\n    try:\n        return x\n    except:\n        pass\n'),
    ("repro_10_try_except_raise", 'def func(x):\n    try:\n        return x\n    except Exception:\n        raise\n'),
    ("repro_11_closure_cell", 'def make_adder(n):\n    def adder(x):\n        return x + n\n    return adder\n'),
    ("repro_12_nested_closure", 'def make_counter():\n    count = 0\n    def counter():\n        nonlocal count\n        count += 1\n        return count\n    return counter\n'),
]

results = []
for name, source in repros:
    defect, details = test_repro(name, source)
    status = "DEFECT-REPRO" if defect else "NO-DEFECT"
    results.append((name, status, details))
    print(f"  {name:40s}  {status:15s}  {details}")

defects = [r for r in results if r[1] == "DEFECT-REPRO"]
print(f"\n=== Summary ===")
print(f"Total repros: {len(results)}")
print(f"DEFECT-REPRO: {len(defects)}")
print(f"NO-DEFECT: {len(results) - len(defects)}")
