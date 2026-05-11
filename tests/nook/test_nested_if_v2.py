"""
批次1：简单嵌套if-else测试用例
测试反编译器对嵌套if-else结构的处理能力
"""

import sys
import os
import tempfile
import dis

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pycdc import PycDecompiler
from core.pyc_loader_v2 import load_pyc_file_v2


def compile_and_decompile(source_code, func_name="test_func"):
    """编译源代码并反编译，返回反编译后的代码"""
    # 编译源代码
    code = compile(source_code, '<test>', 'exec')
    
    # 保存到临时pyc文件
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
        temp_path = f.name
        # 写入pyc文件头（Python 3.11）
        import importlib.util
        import importlib.machinery
        
        # 使用正确的pyc格式
        with open(temp_path, 'wb') as pyc_file:
            # 魔数 (Python 3.11)
            pyc_file.write(b'\x6f\x0d\x0d\x0a')
            # 版本号
            pyc_file.write(b'\x00\x00\x00\x00')
            # 时间戳
            import time
            pyc_file.write(int(time.time()).to_bytes(4, 'little'))
            # 代码大小
            import marshal
            marshalled = marshal.dumps(code)
            pyc_file.write(len(marshalled).to_bytes(4, 'little'))
            # 代码对象
            pyc_file.write(marshalled)
    
    try:
        # 反编译
        decompiler = PycDecompiler()
        if not decompiler.load_file(temp_path):
            return None, "加载pyc文件失败"
        
        import io
        output = io.StringIO()
        if not decompiler.decompile(output):
            return None, "反编译失败"
        
        result = output.getvalue()
        return result, None
    finally:
        os.unlink(temp_path)


def test_simple_nested_if():
    """测试用例1：两层嵌套if-else"""
    source = '''
def test_simple_nested(x, y):
    if x > 0:
        if y > 0:
            return 'both positive'
        else:
            return 'x positive, y not'
    else:
        return 'x not positive'
'''
    result, error = compile_and_decompile(source)
    if error:
        return False, f"反编译失败: {error}"
    
    # 检查反编译结果
    checks = [
        "if x > 0:" in result,
        "if y > 0:" in result,
        "else:" in result,
        "return 'both positive'" in result,
        "return 'x positive, y not'" in result,
        "return 'x not positive'" in result,
    ]
    
    if all(checks):
        return True, "通过"
    else:
        return False, f"反编译结果不完整:\n{result}"


def test_triple_nested_if():
    """测试用例2：三层嵌套if-else"""
    source = '''
def test_triple_nested(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return 'all positive'
            else:
                return 'x,y positive, z not'
        else:
            return 'x positive, y not'
    else:
        return 'x not positive'
'''
    result, error = compile_and_decompile(source)
    if error:
        return False, f"反编译失败: {error}"
    
    # 检查反编译结果
    checks = [
        "if x > 0:" in result,
        "if y > 0:" in result,
        "if z > 0:" in result,
        "else:" in result,
        "return 'all positive'" in result,
    ]
    
    if all(checks):
        return True, "通过"
    else:
        return False, f"反编译结果不完整:\n{result}"


def test_if_elif_else_nested():
    """测试用例3：if-elif-else嵌套if"""
    source = '''
def test_if_elif_else_nested(x, y):
    if x > 0:
        if y > 0:
            return 'x>0, y>0'
        else:
            return 'x>0, y<=0'
    elif x < 0:
        return 'x<0'
    else:
        return 'x==0'
'''
    result, error = compile_and_decompile(source)
    if error:
        return False, f"反编译失败: {error}"
    
    # 检查反编译结果
    checks = [
        "if x > 0:" in result,
        "if y > 0:" in result,
        "elif x < 0:" in result,
        "else:" in result,
    ]
    
    if all(checks):
        return True, "通过"
    else:
        return False, f"反编译结果不完整:\n{result}"


def test_if_nested_if_elif_else():
    """测试用例4：if嵌套if-elif-else"""
    source = '''
def test_if_nested_if_elif_else(x, y):
    if x > 0:
        if y > 0:
            return 'x>0, y>0'
        elif y < 0:
            return 'x>0, y<0'
        else:
            return 'x>0, y==0'
    else:
        return 'x<=0'
'''
    result, error = compile_and_decompile(source)
    if error:
        return False, f"反编译失败: {error}"
    
    # 检查反编译结果
    checks = [
        "if x > 0:" in result,
        "if y > 0:" in result,
        "elif y < 0:" in result,
        "else:" in result,
    ]
    
    if all(checks):
        return True, "通过"
    else:
        return False, f"反编译结果不完整:\n{result}"


def run_all_tests():
    """运行所有测试用例"""
    tests = [
        ("测试用例1：两层嵌套if-else", test_simple_nested_if),
        ("测试用例2：三层嵌套if-else", test_triple_nested_if),
        ("测试用例3：if-elif-else嵌套if", test_if_elif_else_nested),
        ("测试用例4：if嵌套if-elif-else", test_if_nested_if_elif_else),
    ]
    
    print("=" * 60)
    print("批次1：简单嵌套if-else测试")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{name}...")
        try:
            success, message = test_func()
            if success:
                print(f"  ✓ {message}")
                passed += 1
            else:
                print(f"  ✗ {message}")
                failed += 1
        except Exception as e:
            print(f"  ✗ 异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
