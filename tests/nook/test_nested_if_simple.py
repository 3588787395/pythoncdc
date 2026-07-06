"""
测试嵌套if的while True: 
"""
import sys
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def decompile_function(func_code):
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


def test_nested_if():
    """while True: 嵌套两个if"""
    def func():
        i = 0
        total = 0
        while True:
            if i >= 3:
                break
            if i % 2 == 0:
                total += i
            i += 1
        return total
    
    print("原始代码:")
    import inspect
    print(inspect.getsource(func))
    
    decompiled_code, error = decompile_function(func.__code__)
    
    if error:
        print(f"\n反编译失败: {error}")
        return False
    
    print(f"\n反编译代码:")
    print(decompiled_code)
    
    # 检查是否包含 i += 1
    if 'i += 1' not in decompiled_code:
        print("\n❌ 反编译代码缺少 'i += 1'")
        return False
    
    print("\n✅ 反编译代码包含 'i += 1'")
    return True


if __name__ == "__main__":
    success = test_nested_if()
    sys.exit(0 if success else 1)
