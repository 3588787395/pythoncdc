"""
测试 while True: 循环反编译
"""

import os
import sys
import marshal
import py_compile
import tempfile
import traceback
import dis
import types

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def decompile_function(func_code):
    """反编译单个函数"""
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


def verify_function(original_code, decompiled_code, func_name, test_input=None):
    """验证反编译后的函数是否正确"""
    errors = []
    
    try:
        compile(decompiled_code, '<test>', 'exec')
    except SyntaxError as e:
        errors.append(f"语法错误: {e}")
        return False, errors
    
    try:
        namespace = {}
        exec(decompiled_code, namespace)
        
        decompiled_func = namespace.get(func_name)
        if not decompiled_func:
            errors.append(f"找不到反编译后的函数: {func_name}")
            return False, errors
        
        original_func = types.FunctionType(original_code, {})
        
        try:
            if test_input is not None:
                original_result = original_func(test_input)
                decompiled_result = decompiled_func(test_input)
            else:
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


def test_while_true_basic():
    """测试基本的 while True: 循环"""
    print("\n" + "="*70)
    print("测试1: 基本的 while True: 循环（带break）")
    print("="*70)
    
    def test_func():
        i = 0
        while True:
            if i >= 5:
                break
            i += 1
        return i
    
    func_code = test_func.__code__
    func_name = test_func.__name__
    
    print(f"\n原始代码字节码:")
    dis.dis(test_func)
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    success, errors = verify_function(func_code, decompiled_code, func_name)
    
    if success:
        print(f"\n✅ 验证通过")
        return True
    else:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  - {e}")
        return False


def test_while_true_with_else():
    """测试 while True: 循环带else"""
    print("\n" + "="*70)
    print("测试2: while True: 循环带else子句")
    print("="*70)
    
    def test_func():
        i = 0
        while True:
            if i >= 3:
                break
            i += 1
        else:
            i = 100  # 这个不会执行
        return i
    
    func_code = test_func.__code__
    func_name = test_func.__name__
    
    print(f"\n原始代码字节码:")
    dis.dis(test_func)
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    success, errors = verify_function(func_code, decompiled_code, func_name)
    
    if success:
        print(f"\n✅ 验证通过")
        return True
    else:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  - {e}")
        return False


def test_while_true_nested():
    """测试嵌套的 while True: 循环"""
    print("\n" + "="*70)
    print("测试3: 嵌套的 while True: 循环")
    print("="*70)
    
    def test_func():
        total = 0
        i = 0
        while True:
            if i >= 3:
                break
            j = 0
            while True:
                if j >= 3:
                    break
                total += 1
                j += 1
            i += 1
        return total
    
    func_code = test_func.__code__
    func_name = test_func.__name__
    
    print(f"\n原始代码字节码:")
    dis.dis(test_func)
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    success, errors = verify_function(func_code, decompiled_code, func_name)
    
    if success:
        print(f"\n✅ 验证通过")
        return True
    else:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  - {e}")
        return False


def test_while_true_with_continue():
    """测试 while True: 循环带continue"""
    print("\n" + "="*70)
    print("测试4: while True: 循环带continue")
    print("="*70)
    
    def test_func():
        i = 0
        total = 0
        while True:
            i += 1
            if i > 5:
                break
            if i % 2 == 0:
                continue
            total += i
        return total
    
    func_code = test_func.__code__
    func_name = test_func.__name__
    
    print(f"\n原始代码字节码:")
    dis.dis(test_func)
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    success, errors = verify_function(func_code, decompiled_code, func_name)
    
    if success:
        print(f"\n✅ 验证通过")
        return True
    else:
        print(f"\n❌ 验证失败:")
        for e in errors:
            print(f"  - {e}")
        return False


def main():
    print("="*70)
    print("测试 while True: 循环反编译")
    print("="*70)
    
    results = []
    results.append(("基本的 while True", test_while_true_basic()))
    results.append(("while True 带else", test_while_true_with_else()))
    results.append(("嵌套 while True", test_while_true_nested()))
    results.append(("while True 带continue", test_while_true_with_continue()))
    
    print("\n" + "="*70)
    print("测试结果汇总")
    print("="*70)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    print(f"\n总计: {passed_count}/{total_count} 通过")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
