import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import ControlFlowGraph
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter

FAIL_TESTS = {
    'A1': ('test_te10nestedtry_indexerror_attributeerror', 'try:\n    try:\n        pass\n    except IndexError:\n        pass\nexcept AttributeError:\n    pass'),
    'A2': ('test_te10nestedtry_stopiteration_zerodivisionerror', 'try:\n    try:\n        pass\n    except StopIteration:\n        pass\nexcept ZeroDivisionError:\n    pass'),
    'A3': ('test_te10nestedtry_valueerror_typeerror', 'try:\n    try:\n        pass\n    except ValueError:\n        pass\nexcept TypeError:\n    pass'),
    'B1': ('test_te13tryfinallyreturn', 'def f():\n    try:\n        return 1\n    finally:\n        pass'),
    'C1': ('test_te040', 'try:\n    if a:\n        x = 1\n    elif b:\n        x = 2\n    else:\n        x = 3\nexcept:\n    x = 0'),
    'C2': ('test_te047', 'try:\n    for i in range(3):\n        if i == 1:\n            continue\n        x = i\nexcept:\n    x = 0'),
    'C3': ('test_te050', 'try:\n    for i in range(3):\n        try:\n            x = 1 / i\n        except ZeroDivisionError:\n            x = 0\nexcept:\n    x = -1'),
    'C4': ('test_te080', 'try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3'),
    'C5': ('test_te081', 'try:\n    x = 1\nfinally:\n    try:\n        y = 2\n    except:\n        z = 3'),
    'C6': ('test_te083', 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'),
    'C7': ('test_te100', 'try:\n    try:\n        try:\n            x = 1\n        except:\n            y = 2\n    except:\n        z = 3\nexcept:\n    w = 4'),
    'D1': ('test_te104', "def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()"),
    'D2': ('test_try06_nested_try', 'try:\n    try:\n        inner_work()\n    except InnerError:\n        inner_fix()\nexcept OuterError:\n    outer_fix()'),
    'D3': ('test_try11_try_if', 'try:\n    if condition:\n        risky()\n    else:\n        safe()\nexcept Error:\n    handle()'),
    'D4': ('test_try15_try_return', 'def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default'),
    'D5': ('test_try16_multi_nested', 'try:\n    try:\n        level2()\n    except Error2:\n        try:\n            level3_recover()\n        except Error3:\n            deep_fix()\nexcept Error1:\n    top_fix()'),
    'D6': ('test_try20_complex_pattern', 'def robust_process(items):\n    results = []\n    errors = []\n    for i, item in enumerate(items):\n        try:\n            if not valid(item):\n                raise ValueError(f"Invalid at {i}")\n            result = transform(item)\n            if result is None:\n                continue\n            results.append(result)\n        except ValueError as e:\n            errors.append((i, str(e)))\n        except TransformError:\n            errors.append((i, "transform failed"))\n    return results, errors'),
}

def get_bytecode_info(code_obj):
    instrs = list(dis.get_instructions(code_obj))
    return [(i.opname, i.argval) for i in instrs]

def decompile_source(source):
    code = compile(source, '<test>', 'exec')
    cfg = ControlFlowGraph(code)
    gen = RegionASTGenerator(cfg)
    ast_dict = gen.generate()
    converter = CFGASTConverter()
    result = converter.convert(ast_dict)
    return result, code

for key in sorted(FAIL_TESTS.keys()):
    name, source = FAIL_TESTS[key]
    print(f"\n{'='*60}")
    print(f"[{key}] {name}")
    print(f"SOURCE: {source!r}")
    print(f"{'='*60}")
    try:
        code = compile(source, '<test>', 'exec')
        orig_instrs = get_bytecode_info(code)
        print(f"ORIGINAL BYTECODE ({len(orig_instrs)} instrs):")
        for i, (op, arg) in enumerate(orig_instrs):
            print(f"  {i}: {op} {arg!r}")
        
        cfg = ControlFlowGraph(code)
        gen = RegionASTGenerator(cfg)
        ast_dict = gen.generate()
        converter = CFGASTConverter()
        result = converter.convert(ast_dict)
        
        recompiled = compile(result, '<recompiled>', 'exec')
        recomp_instrs = get_bytecode_info(recompiled)
        print(f"\nRECOMPILED BYTECODE ({len(recomp_instrs)} instrs):")
        for i, (op, arg) in enumerate(recomp_instrs):
            print(f"  {i}: {op} {arg!r}")
        
        print(f"\nDECOMPILED SOURCE:")
        print(result)
        
        # Show differences
        print(f"\nDIFF:")
        max_len = max(len(orig_instrs), len(recomp_instrs))
        for i in range(max_len):
            orig = orig_instrs[i] if i < len(orig_instrs) else ('MISSING', '')
            recomp = recomp_instrs[i] if i < len(recomp_instrs) else ('MISSING', '')
            marker = "  " if orig == recomp else "**"
            print(f"  {marker} {i}: {orig[0]} {orig[1]!r} vs {recomp[0]} {recomp[1]!r}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
