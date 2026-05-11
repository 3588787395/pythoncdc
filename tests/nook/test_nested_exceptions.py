#!/usr/bin/env python3
"""测试嵌套异常处理"""

import sys
import os

# 添加 pythoncdc 目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
pythoncdc_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, pythoncdc_dir)

from tests.batch12.test_utils import test_bytecode_match

# 测试用例 1: 嵌套 try-except
def test_nested_try_except():
    def func():
        try:
            try:
                x = 1 / 0
            except ZeroDivisionError:
                print("内层除零错误")
        except Exception:
            print("外层异常")
    return func

# 测试用例 2: try-except-finally 嵌套
def test_try_except_finally_nested():
    def func():
        try:
            try:
                x = 1 / 0
            except ZeroDivisionError:
                print("除零错误")
            finally:
                print("内层 finally")
        except Exception:
            print("外层异常")
        finally:
            print("外层 finally")
    return func

# 测试用例 3: 多个 except 子句
def test_multiple_except():
    def func():
        try:
            x = 1 / 0
        except ZeroDivisionError:
            print("除零错误")
        except ValueError:
            print("值错误")
        except Exception as e:
            print(f"其他错误: {e}")
    return func

# 测试用例 4: 带 else 的异常处理
def test_except_with_else():
    def func():
        try:
            x = 1 / 1
        except ZeroDivisionError:
            print("除零错误")
        else:
            print("没有错误")
    return func

# 测试用例 5: 完整的异常处理
def test_full_exception():
    def func():
        try:
            x = 1 / 0
        except ZeroDivisionError:
            print("除零错误")
        except Exception as e:
            print(f"其他错误: {e}")
        else:
            print("没有错误")
        finally:
            print("清理资源")
    return func

# 测试用例 6: 循环中的异常处理
def test_exception_in_loop():
    def func():
        for i in range(10):
            try:
                x = 1 / i
            except ZeroDivisionError:
                print(f"除零错误 at {i}")
            finally:
                print(f"迭代 {i} 完成")
    return func

# 测试用例 7: 异常处理中的循环
def test_loop_in_exception():
    def func():
        try:
            for i in range(10):
                if i == 5:
                    raise ValueError("i is 5")
        except ValueError:
            print("值错误")
    return func

# 测试用例 8: 嵌套异常处理中的 return
def test_return_in_nested_exception():
    def func():
        try:
            try:
                return 1
            except:
                return 2
        except:
            return 3
    return func

# 测试用例 9: 异常处理中的条件
def test_condition_in_exception():
    def func():
        try:
            x = 1 / 0
        except ZeroDivisionError:
            if True:
                print("除零错误")
            else:
                print("其他")
    return func

# 测试用例 10: 复杂的嵌套异常
def test_complex_nested():
    def func():
        try:
            try:
                try:
                    x = 1 / 0
                except ZeroDivisionError:
                    print("最内层除零错误")
                    raise
            except ZeroDivisionError:
                print("中间层除零错误")
        except Exception:
            print("最外层异常")
    return func

if __name__ == '__main__':
    test_cases = [
        test_nested_try_except,
        test_try_except_finally_nested,
        test_multiple_except,
        test_except_with_else,
        test_full_exception,
        test_exception_in_loop,
        test_loop_in_exception,
        test_return_in_nested_exception,
        test_condition_in_exception,
        test_complex_nested,
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        try:
            func = test_case()
            if test_bytecode_match(func):
                print(f"✓ {test_case.__name__}")
                passed += 1
            else:
                print(f"✗ {test_case.__name__} - 字节码不匹配")
                failed += 1
        except Exception as e:
            print(f"✗ {test_case.__name__} - {e}")
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
