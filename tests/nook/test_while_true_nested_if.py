"""
测试 while True: 嵌套 if 的反编译
"""

import os
import sys
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


def test_simple():
    """测试简单的 while True: 嵌套 if"""
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
    
    print("="*70)
    print("原始代码字节码:")
    print("="*70)
    dis.dis(func)
    
    func_code = func.__code__
    func_name = func.__name__
    
    decompiled_code, error = decompile_function(func_code)
    
    if error:
        print(f"\n❌ 反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    # 验证
    try:
        compile(decompiled_code, '<test>', 'exec')
    except SyntaxError as e:
        print(f"\n❌ 语法错误: {e}")
        return False
    
    try:
        namespace = {}
        exec(decompiled_code, namespace)
        decompiled_func = namespace.get(func_name)
        if not decompiled_func:
            print(f"\n❌ 找不到反编译后的函数")
            return False
        
        original_func = types.FunctionType(func_code, {})
        
        # 直接执行（注意：如果反编译代码有无限循环，这会卡住）
        try:
            original_result = original_func()
            decompiled_result = decompiled_func()
            
            if original_result != decompiled_result:
                print(f"\n❌ 结果不一致: 原始={original_result}, 反编译={decompiled_result}")
                return False
                
        except Exception as e:
            print(f"\n❌ 执行错误: {e}")
            return False
            
    except Exception as e:
        print(f"\n❌ 反编译代码执行错误: {e}")
        return False
    
    print(f"\n✅ 验证通过")
    return True


if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)
