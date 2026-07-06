#!/usr/bin/env python3
"""
测试control_flow_examples函数的反编译
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


def test_control_flow():
    """测试control_flow_examples函数"""
    source_code = '''
x = 10
y = 3.14
my_list = [1, 2, 3, 4, 5]

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
    
    for i in range(5):
        print(f"Loop: {i}")
    
    for item in my_list:
        if item == 3:
            break
    else:
        print('Not found 3')
    
    counter = 0
    while counter < 5:
        print(f"Counter: {counter}")
        counter += 1
    
    counter = 0
    while counter < 10:
        if counter == 7:
            break
        counter += 1
    else:
        print('Loop finished normally')
    
    for i in range(10):
        if i == 3:
            continue
        if i == 7:
            break
        print(i)
    
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
        
        # 检查关键结构
        checks = [
            ('elif x == 10:' in decompiled_code, "包含elif分支"),
            ('else:' in decompiled_code, "包含else分支"),
            ('counter = 0' in decompiled_code, "包含counter变量初始化"),
            ('continue' in decompiled_code, "包含continue语句"),
        ]
        
        all_pass = True
        for check, msg in checks:
            if check:
                print(f"✓ {msg}")
            else:
                print(f"✗ {msg}")
                all_pass = False
        
        return all_pass
        
    finally:
        os.unlink(temp_py)
        if os.path.exists(temp_pyc):
            os.unlink(temp_pyc)


if __name__ == '__main__':
    print("测试control_flow_examples函数反编译")
    print("=" * 60)
    
    if test_control_flow():
        print("\n✓ 测试通过")
        sys.exit(0)
    else:
        print("\n✗ 测试失败")
        sys.exit(1)
