#!/usr/bin/env python3
"""Analyze match_region test failures by decompiling and comparing with expected output."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def decompile(src):
    result = build_cfg_from_source(src)
    cfg = result[0] if isinstance(result, (list, tuple)) else result
    gen = RegionASTGenerator(cfg)
    ast_result = gen.generate()
    source = CodeGenerator().generate(ast_result)
    return source

# Test cases from the task description (with function wrapper)
tests = {
    'm054': 'def f(x):\n    match x:\n        case 1:\n            try: a = risky()\n            except ValueError: a = -1',
    'm061': 'def f(x):\n    match x:\n        case 1:\n            try: a = risky()\n            except ValueError: a = -1\n        case 2: a = x',
    'm069': 'def f(x):\n    match x:\n        case 1:\n            try: a = risky()\n            except ValueError as e: a = str(e)\n            except TypeError: a = -1',
    'm075': 'def f(x):\n    match x:\n        case 1 if x > 0: a = 1\n        case 1: a = -1',
    'm083': '''def f(value):
    match value:
        case int() as n if n > 0:
            result = f'positive integer: {n}'
        case int() as n if n < 0:
            result = f'negative integer: {n}'
        case str() as s if s:
            result = f'non-empty string: {s}'
        case list() as lst if len(lst) > 0:
            result = f'non-empty list: {len(lst)} items'
        case _:
            result = 'other'
''',
}

# Also test with actual test file source codes
actual_tests = {
    'm054_actual': 'match x:\n    case 1:\n        try:\n            y = 1\n        except:\n            z = 2\n    case _:\n        pass',
    'm061_actual': 'match x:\n    case 1:\n        try:\n            y = risky()\n        except:\n            y = 0\n    case _:\n        y = -1',
    'm069_actual': 'match x:\n    case 1:\n        try:\n            x = risky()\n        except ValueError:\n            x = 0\n        except TypeError:\n            x = -1\n    case _:\n        x = 0',
    'm075_actual': 'match x:\n    case 1:\n        if a and b:\n            y = 1\n        elif a or c:\n            y = 2\n        else:\n            y = 3\n    case _:\n        y = 0',
    'm083_actual': '''match value:
    case int() as n if n > 0:
        result = f'positive integer: {n}'
    case int() as n if n < 0:
        result = f'negative integer: {n}'
    case str() as s if s:
        result = f'non-empty string: {s}'
    case list() as lst if len(lst) > 0:
        result = f'non-empty list: {len(lst)} items'
    case _:
        result = 'other'
''',
}

for name, src in {**tests, **actual_tests}.items():
    print(f'\n{"="*60}')
    print(f'TEST: {name}')
    print(f'{"="*60}')
    print(f'SOURCE:')
    print(src)
    print(f'\nDECOMPILED:')
    try:
        result = decompile(src)
        print(result)
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
