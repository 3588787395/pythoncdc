#!/usr/bin/env python3
"""R90 最小复现实例：验证入口块中 UNPACK_SEQUENCE 解包赋值在 IfRegion/BoolOpRegion 入口块中的正确处理"""
import sys, os, marshal, types, dis
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

# 最小复现实例：函数入口块包含元组解包赋值 + if 条件
# 这个模式在 klinedata.pyc 的 get_kline_by_count_new 中出现
# 关键特征：
# 1. 入口块包含 a, b = f(...) (UNPACK_SEQUENCE)
# 2. 入口块同时是 BoolOpRegion 和 IfRegion 的 entry
# 3. IfRegion 的 condition_block 不是入口块（BoolOpRegion 跨块条件）

test_cases = [
    # Case 1: 简单元组解包 + if 条件
    '''
def test_unpack_if(a, b):
    x, y = func(a, b)
    if x is None or y is not None:
        return 1
    return 0
''',
    # Case 2: 元组解包 + 多语句 + if 条件
    '''
def test_unpack_multi(a, b):
    result = dict()
    x, y = func(a, b)
    if x is None or y is not None:
        return result
    return None
''',
    # Case 3: 元组解包 + 赋值后直接使用
    '''
def test_unpack_use(a, b):
    x, y = get_values(a, b)
    if x is None:
        return y
    return x
''',
]

print("=== R90 最小复现实例验证 ===\n")
for i, src in enumerate(test_cases):
    print(f"--- Case {i+1} ---")
    print(src.strip())
    
    # Compile source
    code = compile(src, f'<test_{i}>', 'exec')
    
    # Find the function
    func_code = None
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name.startswith('test_'):
            func_code = const
            break
    
    if func_code is None:
        print("  ERROR: Function not found!")
        continue
    
    # Decompile using pycdc
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
        f.write(b'\x6f\x0d\x0d\x0a' + b'\x00' * 12)  # header
        marshal.dump(func_code, f)
        pyc_path = f.name
    
    try:
        decomp_src = decompile_pyc(pyc_path)
        if decomp_src:
            print("Decompiled:")
            print(decomp_src.strip())
            
            # Compile decompiled source and compare
            decomp_code = compile(decomp_src, '<decomp>', 'exec')
            decomp_func = None
            for const in decomp_code.co_consts:
                if isinstance(const, types.CodeType) and const.co_name.startswith('test_'):
                    decomp_func = const
                    break
            
            if decomp_func:
                result = compare_bytecode(func_code, decomp_func)
                match = result['match'] or (not result['true_diffs'] and result.get('jump_only'))
                print(f"\nBytecode match: {match}")
                if result['true_diffs']:
                    print(f"  true_diffs: {len(result['true_diffs'])}")
                    fd = result['true_diffs'][0]
                    print(f"  first: idx={fd.get('index','?')} orig={fd.get('orig_op','?')}({fd.get('orig_arg','?')}) decomp={fd.get('decomp_op','?')}({fd.get('decomp_arg','?')})")
                if result['jump_diffs']:
                    print(f"  jump_diffs: {len(result['jump_diffs'])}")
            else:
                print("  ERROR: Decompiled function not found!")
        else:
            print("  ERROR: Decompilation failed!")
    finally:
        os.unlink(pyc_path)
    print()
