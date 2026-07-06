#!/usr/bin/env python3
"""
测试嵌套if-else结构的反编译
"""

import dis
import marshal
import tempfile
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pycdc import PycDecompiler


def test_simple_if_elif_else():
    """测试简单的if-elif-else结构"""
    # 创建测试代码
    source_code = '''
def test_func(x):
    if x > 10:
        result = 'greater than 10'
    elif x == 10:
        result = 'equal to 10'
    else:
        result = 'less than 10'
    return result
'''
    
    # 编译为pyc
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_py = f.name
    
    temp_pyc = temp_py + 'c'
    import py_compile
    py_compile.compile(temp_py, temp_pyc, doraise=True)
    
    try:
        # 反编译
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_pyc):
            print("✗ 加载pyc文件失败")
            return False
        
        from io import StringIO
        output = StringIO()
        if not decompiler.decompile(output):
            print("✗ 反编译失败")
            return False
        
        decompiled_code = output.getvalue()
        print("反编译结果:")
        print(decompiled_code)
        
        # 检查是否包含elif
        if 'elif' in decompiled_code:
            print("✓ 正确识别elif")
            return True
        else:
            print("✗ 未识别elif结构")
            return False
            
    finally:
        os.unlink(temp_py)
        if os.path.exists(temp_pyc):
            os.unlink(temp_pyc)


def test_nested_if_else():
    """测试嵌套if-else结构"""
    source_code = '''
def test_func(x, y):
    if x > 0:
        if y > 0:
            result = 'both positive'
        else:
            result = 'x positive y negative'
    else:
        result = 'x not positive'
    return result
'''
    
    # 编译为pyc
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_py = f.name
    
    temp_pyc = temp_py + 'c'
    import py_compile
    py_compile.compile(temp_py, temp_pyc, doraise=True)
    
    try:
        # 反编译
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_pyc):
            print("✗ 加载pyc文件失败")
            return False
        
        from io import StringIO
        output = StringIO()
        if not decompiler.decompile(output):
            print("✗ 反编译失败")
            return False
        
        decompiled_code = output.getvalue()
        print("反编译结果:")
        print(decompiled_code)
        
        # 检查语法
        try:
            compile(decompiled_code, '<test>', 'exec')
            print("✓ 语法正确")
            return True
        except SyntaxError as e:
            print(f"✗ 语法错误: {e}")
            return False
            
    finally:
        os.unlink(temp_py)
        if os.path.exists(temp_pyc):
            os.unlink(temp_pyc)


def test_loop_with_continue():
    """测试带continue的循环"""
    source_code = '''
def test_func():
    for i in range(10):
        if i == 3:
            continue
        if i == 7:
            break
        print(i)
'''
    
    # 编译为pyc
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_py = f.name
    
    temp_pyc = temp_py + 'c'
    import py_compile
    py_compile.compile(temp_py, temp_pyc, doraise=True)
    
    try:
        # 反编译
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_pyc):
            print("✗ 加载pyc文件失败")
            return False
        
        from io import StringIO
        output = StringIO()
        if not decompiler.decompile(output):
            print("✗ 反编译失败")
            return False
        
        decompiled_code = output.getvalue()
        print("反编译结果:")
        print(decompiled_code)
        
        # 检查语法
        try:
            compile(decompiled_code, '<test>', 'exec')
            print("✓ 语法正确")
            return True
        except SyntaxError as e:
            print(f"✗ 语法错误: {e}")
            return False
            
    finally:
        os.unlink(temp_py)
        if os.path.exists(temp_pyc):
            os.unlink(temp_pyc)


if __name__ == '__main__':
    print("=" * 80)
    print("测试1: 简单的if-elif-else结构")
    print("=" * 80)
    test_simple_if_elif_else()
    
    print("\n" + "=" * 80)
    print("测试2: 嵌套if-else结构")
    print("=" * 80)
    test_nested_if_else()
    
    print("\n" + "=" * 80)
    print("测试3: 带continue/break的循环")
    print("=" * 80)
    test_loop_with_continue()
