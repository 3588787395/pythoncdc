"""
基本elif测试 - 覆盖各种基本场景
"""
import sys
import os
# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# 添加pythoncdc目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pythoncdc'))

from pythoncdc.core.cfg.cfg_builder import build_cfg
from pythoncdc.core.cfg.structured_analyzer import StructuredAnalyzer
from pythoncdc.core.cfg.ast_generator_v2 import ASTGeneratorV2
from pythoncdc.core.cfg.ast_converter import convert_cfg_ast
from pythoncdc.core.cfg.code_generator import CFGCodeGenerator


def test_simple_if():
    """简单if语句"""
    x = 1
    if x > 0:
        print("positive")


def test_if_else():
    """if-else语句"""
    x = 1
    if x > 0:
        print("positive")
    else:
        print("non-positive")


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


def test_elif_only_no_else():
    """只有elif没有else"""
    x = 1
    if x == 1:
        print("one")
    elif x == 2:
        print("two")
    elif x == 3:
        print("three")


def test_empty_branches():
    """空分支"""
    x = 1
    if x > 0:
        pass
    elif x < 0:
        pass
    else:
        pass


def test_only_if():
    """只有if"""
    x = 1
    if x > 0:
        print("positive")


def run_tests():
    """运行所有测试"""
    tests = [
        ("简单if语句", test_simple_if, 0),
        ("if-else语句", test_if_else, 0),
        ("单个elif", test_single_elif, 1),
        ("多个elif", test_multiple_elif, 3),
        ("elif带else", test_elif_with_else, 1),
        ("只有elif没有else", test_elif_only_no_else, 2),
        ("空分支", test_empty_branches, 1),
        ("只有if", test_only_if, 0),
    ]
    
    passed = 0
    failed = 0
    
    for name, func, expected_elif in tests:
        try:
            cfg = build_cfg(func.__code__, func.__name__)
            analyzer = StructuredAnalyzer(cfg)
            structures = analyzer.analyze()
            
            ast_gen = ASTGeneratorV2(cfg, analyzer)
            ast_dict = ast_gen.generate()
            ast_root = convert_cfg_ast(ast_dict)
            code_gen = CFGCodeGenerator()
            result = code_gen.generate(ast_root)
            
            # 计算elif数量
            elif_count = result.count('elif')
            
            if elif_count == expected_elif:
                print(f"✓ {name}: {elif_count} elif(s)")
                passed += 1
            else:
                print(f"✗ {name}: 期望{expected_elif} elif(s), 得到{elif_count} elif(s)")
                print(f"  输出:\n{result}")
                failed += 1
        except Exception as e:
            print(f"✗ {name}: 异常 - {e}")
            failed += 1
    
    print(f"\n总计: {passed}/{len(tests)} 测试通过")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
