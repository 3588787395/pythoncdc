"""
简单elif测试
"""
import sys
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.ast_generator_v2 import ASTGeneratorV2
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


def test_single_elif():
    """单个elif"""
    x = 1
    if x == 1:
        print("one")
    elif x == 2:
        print("two")


def test_multiple_elif():
    """多个elif"""
    x = 1
    if x == 1:
        print("one")
    elif x == 2:
        print("two")
    elif x == 3:
        print("three")
    elif x == 4:
        print("four")


def test_elif_with_else():
    """elif带else"""
    x = 1
    if x == 1:
        print("one")
    elif x == 2:
        print("two")
    else:
        print("other")


def decompile_and_check(func, name, expected_elif):
    """反编译并检查elif数量"""
    print(f"\n=== {name} ===")
    
    cfg = build_cfg(func.__code__, func.__name__)
    analyzer = StructuredAnalyzer(cfg)
    structures = analyzer.analyze()
    
    ast_gen = ASTGeneratorV2(cfg)
    ast_gen.structures = structures
    func_ast_dict = ast_gen.generate()
    
    converter = CFGASTConverter()
    func_ast = converter.convert(func_ast_dict)
    
    code_gen = CFGCodeGenerator()
    func_code_str = code_gen.generate(func_ast, in_function=True)
    
    print(f"反编译代码:\n{func_code_str}")
    
    elif_count = func_code_str.count('elif')
    print(f"elif数量: {elif_count} (期望{expected_elif})")
    
    if elif_count == expected_elif:
        print("✓ 测试通过!")
        return True
    else:
        print("✗ 测试失败!")
        return False


if __name__ == "__main__":
    results = []
    # 注意：elif数量包括if和elif，所以期望值为实际条件分支数
    results.append(decompile_and_check(test_single_elif, "单个elif", 2))  # 1 if + 1 elif
    results.append(decompile_and_check(test_multiple_elif, "多个elif", 4))  # 1 if + 3 elif
    results.append(decompile_and_check(test_elif_with_else, "elif带else", 2))  # 1 if + 1 elif
    
    print("\n" + "="*50)
    passed = sum(results)
    total = len(results)
    print(f"总计: {passed}/{total} 测试通过")
    if passed == total:
        print("✓ 所有测试通过!")
    else:
        print(f"✗ {total - passed} 个测试失败")
