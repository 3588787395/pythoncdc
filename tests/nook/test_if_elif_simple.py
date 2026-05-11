#!/usr/bin/env python3
"""
测试简单的if-elif-else结构反编译
"""

import py_compile
import tempfile
import os
import sys
from pathlib import Path
from io import StringIO

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pycdc import PycDecompiler


def test_if_elif_else():
    """测试if-elif-else结构"""
    source_code = '''
x = 5
y = 3

def control_flow_examples():
    if x > 10:
        result = 'greater than 10'
    elif x == 10:
        result = 'equal to 10'
    else:
        result = 'less than 10'
    
    if x > 0:
        if y > 0:
            result = 'both positive'
        else:
            result = 'x positive y negative'
    
    return result
'''
    
    # 编译为pyc
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_py = f.name
    
    temp_pyc = temp_py + 'c'
    
    try:
        py_compile.compile(temp_py, temp_pyc, doraise=True)
        
        # 反编译
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_pyc):
            print("✗ 加载pyc文件失败")
            return False
        
        output = StringIO()
        if not decompiler.decompile(output):
            print("✗ 反编译失败")
            return False
        
        decompiled_code = output.getvalue()
        print("反编译结果:")
        print("=" * 60)
        print(decompiled_code)
        print("=" * 60)
        
        # 检查语法
        try:
            compile(decompiled_code, '<test>', 'exec')
            print("✓ 语法检查通过")
        except SyntaxError as e:
            print(f"✗ 语法错误: {e}")
            print(f"  位置: 第{e.lineno}行")
            return False
        
        # 检查elif是否存在
        if 'elif' in decompiled_code:
            print("✓ 包含elif关键字")
        else:
            print("✗ 缺少elif关键字")
            return False
        
        # 检查else是否存在
        if decompiled_code.count('else:') >= 2:
            print("✓ 包含else关键字")
        else:
            print("✗ 缺少else关键字")
            return False
        
        return True
        
    finally:
        os.unlink(temp_py)
        if os.path.exists(temp_pyc):
            os.unlink(temp_pyc)


if __name__ == '__main__':
    print("测试if-elif-else结构反编译")
    print("=" * 60)
    
    if test_if_elif_else():
        print("\n✓ 测试通过")
        sys.exit(0)
    else:
        print("\n✗ 测试失败")
        sys.exit(1)
