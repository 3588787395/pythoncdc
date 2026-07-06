#!/usr/bin/env python3
"""
最小测试：if-elif-else结构
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


def test_minimal_if_elif_else():
    """测试最简单的if-elif-else"""
    source_code = '''
x = 5

def test():
    if x > 10:
        a = 1
    elif x == 10:
        a = 2
    else:
        a = 3
    return a
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_py = f.name
    
    temp_pyc = temp_py + 'c'
    
    try:
        py_compile.compile(temp_py, temp_pyc, doraise=True)
        
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_pyc):
            print("✗ 加载失败")
            return False
        
        output = StringIO()
        if not decompiler.decompile(output):
            print("✗ 反编译失败")
            return False
        
        result = output.getvalue()
        print("反编译结果:")
        print(result)
        print()
        
        # 检查
        checks = [
            ('elif' in result, "包含elif"),
            (result.count('else:') >= 1, "包含else"),
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
    if test_minimal_if_elif_else():
        print("\n✓ 测试通过")
        sys.exit(0)
    else:
        print("\n✗ 测试失败")
        sys.exit(1)
