"""
elif与循环组合测试
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


def test_elif_in_for_loop():
    """for循环中的elif"""
    for i in range(10):
        if i == 0:
            print("zero")
        elif i == 1:
            print("one")
        elif i == 2:
            print("two")
        else:
            print("other")


def test_elif_in_while_loop():
    """while循环中的elif"""
    i = 0
    while i < 10:
        if i == 0:
            print("zero")
        elif i == 1:
            print("one")
        elif i == 2:
            print("two")
        else:
            print("other")
        i += 1


def test_elif_with_break():
    """elif中带break"""
    for i in range(10):
        if i == 0:
            print("zero")
        elif i == 1:
            print("one")
            break
        elif i == 2:
            print("two")
        else:
            print("other")


def test_elif_with_continue():
    """elif中带continue"""
    for i in range(10):
        if i == 0:
            continue
        elif i == 1:
            print("one")
        elif i == 2:
            continue
        else:
            print("other")


def test_nested_loop_with_elif():
    """嵌套循环中的elif"""
    for i in range(3):
        for j in range(3):
            if i == j:
                print("equal")
            elif i > j:
                print("greater")
            else:
                print("less")


def test_elif_with_loop_in_branch():
    """elif分支中包含循环"""
    x = 1
    if x == 0:
        for i in range(3):
            print(i)
    elif x == 1:
        for i in range(5):
            print(i)
    else:
        for i in range(10):
            print(i)


def test_complex_loop_elif():
    """复杂循环elif组合"""
    for i in range(100):
        if i < 10:
            print("single digit")
        elif i < 20:
            print("teens")
        elif i < 30:
            print("twenties")
        elif i < 40:
            print("thirties")
        elif i < 50:
            print("forties")
        else:
            print("fifty or more")


def test_while_with_multiple_elif():
    """while循环多elif"""
    x = 0
    while x < 100:
        if x < 25:
            print("quarter 1")
        elif x < 50:
            print("quarter 2")
        elif x < 75:
            print("quarter 3")
        else:
            print("quarter 4")
        x += 10


def run_tests():
    """运行所有测试"""
    tests = [
        ("for循环中的elif", test_elif_in_for_loop, 2),
        ("while循环中的elif", test_elif_in_while_loop, 2),
        ("elif中带break", test_elif_with_break, 2),
        ("elif中带continue", test_elif_with_continue, 2),
        ("嵌套循环中的elif", test_nested_loop_with_elif, 1),
        ("elif分支中包含循环", test_elif_with_loop_in_branch, 1),
        ("复杂循环elif组合", test_complex_loop_elif, 4),
        ("while循环多elif", test_while_with_multiple_elif, 2),
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n总计: {passed}/{len(tests)} 测试通过")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
