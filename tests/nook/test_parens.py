"""测试多余括号问题"""
import sys
import os
sys.path.insert(0, '../..')
from pycdc import decompile_pyc

# 创建一个简单的测试类
test_code = '''
class Test:
    def __init__(self):
        self.items = []
    
    def add(self, item):
        self.items.append(item)
'''

# 编译并保存
import tempfile
import py_compile

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(test_code)
    py_file = f.name

pyc_file = py_file.replace('.py', '.pyc')
py_compile.compile(py_file, pyc_file, doraise=True)

# 反编译
decompiled = decompile_pyc(pyc_file, use_cfg=True, cfg_hybrid=False)
print("=== 反编译结果 ===")
print(decompiled)

# 清理
os.unlink(py_file)
os.unlink(pyc_file)
