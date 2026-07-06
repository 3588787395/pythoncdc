#!/usr/bin/env python3
"""
简单诊断测试
"""
import sys
import os
import dis
import tempfile
import subprocess
import compileall

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def decompile_pyc(pyc_path):
    """使用pycdc反编译pyc文件"""
    pycdc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'pycdc.py')
    result = subprocess.run(
        ['python', pycdc_path, pyc_path],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return result.stdout if result.stdout else result.stderr


def main():
    source = '''
def test_nested_if_3level(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return 'all positive'
            else:
                return 'x,y positive, z not'
        else:
            if z > 0:
                return 'x,z positive, y not'
            else:
                return 'x positive, y,z not'
    else:
        return 'x not positive'
'''
    
    print("原始代码:")
    print(source)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source)
        py_file = f.name
    
    try:
        compileall.compile_file(py_file, quiet=True)
        
        pycache_dir = os.path.join(os.path.dirname(py_file), '__pycache__')
        pyc_file = None
        if os.path.exists(pycache_dir):
            for f in os.listdir(pycache_dir):
                if f.startswith(os.path.basename(py_file).replace('.py', '')) and f.endswith('.pyc'):
                    pyc_file = os.path.join(pycache_dir, f)
                    break
        
        if pyc_file:
            decompiled = decompile_pyc(pyc_file)
            print("\n反编译后的代码:")
            print(decompiled)
            
    finally:
        if os.path.exists(py_file):
            os.remove(py_file)
        if pyc_file and os.path.exists(pyc_file):
            os.remove(pyc_file)


if __name__ == '__main__':
    main()
