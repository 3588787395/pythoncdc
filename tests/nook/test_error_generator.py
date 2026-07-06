"""
错误驱动测试生成器 - 创建使反编译错误的实例
"""

import os
import sys
import dis
import types
import traceback

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def decompile_function(func_code):
    """反编译单个函数"""
    try:
        cfg = build_cfg(func_code, func_code.co_name)
        analyzer = StructuredAnalyzer(cfg)
        structures = analyzer.analyze()
        ast_gen = ASTGeneratorV2(cfg)
        ast_gen.structures = structures
        func_ast_dict = ast_gen.generate()
        
        if not func_ast_dict:
            return None, "AST生成失败"
        
        converter = CFGASTConverter()
        func_ast = converter.convert(func_ast_dict)
        
        if not func_ast:
            return None, "AST转换失败"
        
        code_gen = CFGCodeGenerator()
        func_code_str = code_gen.generate(func_ast, in_function=True)
        
        return func_code_str, None
    except Exception as e:
        return None, f"反编译异常: {e}\n{traceback.format_exc()}"


def verify_function(original_code, decompiled_code, func_name):
    """验证反编译后的函数是否正确"""
    errors = []
    
    # 1. 检查语法是否正确
    try:
        compile(decompiled_code, '<test>', 'exec')
    except SyntaxError as e:
        errors.append(f"语法错误: {e}")
        return False, errors
    
    # 2. 尝试执行反编译后的代码
    try:
        namespace = {}
        exec(decompiled_code, namespace)
        
        decompiled_func = namespace.get(func_name)
        if not decompiled_func:
            errors.append(f"找不到反编译后的函数: {func_name}")
            return False, errors
        
        original_func = types.FunctionType(original_code, {})
        
        # 3. 对比执行结果
        try:
            original_result = original_func()
            decompiled_result = decompiled_func()
            
            if original_result != decompiled_result:
                errors.append(f"结果不一致: 原始={original_result}, 反编译={decompiled_result}")
                return False, errors
                
        except Exception as e:
            errors.append(f"执行错误: {e}")
            return False, errors
            
    except Exception as e:
        errors.append(f"反编译代码执行错误: {e}")
        return False, errors
    
    return True, []


def test_case(name, func):
    """运行单个测试用例"""
    print(f"\n{'='*70}")
    print(f"测试: {name}")
    print(f"{'='*70}")
    
    func_code = func.__code__
    func_name = func.__name__
    
    print(f"\n原始代码:")
    import inspect
    print(inspect.getsource(func))
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False, error
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    success, errors = verify_function(func_code, decompiled_code, func_name)
    
    if success:
        print(f"\n✅ 验证通过")
        return True, None
    else:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  - {e}")
        return False, "; ".join(errors)


# ============ 测试用例 ============

def test_while_true_nested_if():
    """while True 嵌套 if"""
    def func():
        i = 0
        total = 0
        while True:
            if i >= 5:
                break
            if i % 2 == 0:
                total += i
            i += 1
        return total
    return test_case("while True 嵌套 if", func)


def test_while_true_multiple_breaks():
    """while True 多个 break 条件"""
    def func():
        i = 0
        j = 0
        while True:
            if i >= 3:
                break
            if j >= 10:
                break
            i += 1
            j += 2
        return i + j
    return test_case("while True 多个 break", func)


def test_while_true_with_return():
    """while True 内部 return"""
    def func():
        i = 0
        while True:
            if i >= 5:
                return i
            i += 1
        return -1  # 不会执行
    return test_case("while True 内部 return", func)


def test_while_with_complex_condition():
    """while 复杂条件"""
    def func():
        i = 0
        j = 0
        while i < 3 and j < 5:
            i += 1
            j += 2
        return i + j
    return test_case("while 复杂条件", func)


def test_for_range_break():
    """for range 带 break"""
    def func():
        total = 0
        for i in range(10):
            if i >= 5:
                break
            total += i
        return total
    return test_case("for range 带 break", func)


def test_for_range_continue():
    """for range 带 continue"""
    def func():
        total = 0
        for i in range(10):
            if i % 2 == 0:
                continue
            total += i
        return total
    return test_case("for range 带 continue", func)


def test_nested_for():
    """嵌套 for 循环"""
    def func():
        total = 0
        for i in range(3):
            for j in range(3):
                total += 1
        return total
    return test_case("嵌套 for 循环", func)


def test_while_else():
    """while 带 else"""
    def func():
        i = 0
        while i < 3:
            i += 1
        else:
            i = 100
        return i
    return test_case("while 带 else", func)


def test_for_else():
    """for 带 else（正常完成）"""
    def func():
        total = 0
        for i in range(3):
            total += i
        else:
            total = 100
        return total
    return test_case("for 带 else", func)


def test_for_else_with_break():
    """for 带 else（被 break）"""
    def func():
        total = 0
        for i in range(10):
            if i >= 3:
                break
            total += i
        else:
            total = 100
        return total
    return test_case("for 带 else（被 break）", func)


def test_do_while_simulation():
    """do-while 模拟"""
    def func():
        i = 0
        while True:
            i += 1
            if i >= 5:
                break
        return i
    return test_case("do-while 模拟", func)


def test_infinite_loop_with_exception():
    """无限循环带异常（会被 break）"""
    def func():
        i = 0
        while True:
            try:
                if i >= 3:
                    break
                i += 1
            except:
                pass
        return i
    return test_case("while True 带 try-except", func)


def main():
    print("="*70)
    print("错误驱动测试 - 发现反编译问题")
    print("="*70)
    
    tests = [
        test_while_true_nested_if,
        test_while_true_multiple_breaks,
        test_while_true_with_return,
        test_while_with_complex_condition,
        test_for_range_break,
        test_for_range_continue,
        test_nested_for,
        test_while_else,
        test_for_else,
        test_for_else_with_break,
        test_do_while_simulation,
        test_infinite_loop_with_exception,
    ]
    
    results = []
    for test in tests:
        try:
            passed, error = test()
            results.append((test.__name__, passed, error))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            traceback.print_exc()
            results.append((test.__name__, False, str(e)))
    
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    
    passed_count = 0
    failed_tests = []
    
    for name, passed, error in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            failed_tests.append((name, error))
    
    print(f"\n总计: {passed_count}/{len(results)} 通过")
    
    if failed_tests:
        print("\n失败详情:")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
    
    return all(p for _, p, _ in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
