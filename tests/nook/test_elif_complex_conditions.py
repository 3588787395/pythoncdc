"""
复杂条件测试 - 测试复合条件（AND/OR）与elif的交互
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


def test_and_conditions():
    """AND条件"""
    x = 1
    y = 2
    if x > 0 and y > 0:
        print("both positive")
    elif x < 0 and y < 0:
        print("both negative")
    else:
        print("mixed")


def test_or_conditions():
    """OR条件"""
    x = 1
    y = 2
    if x > 0 or y > 0:
        print("at least one positive")
    elif x < 0 or y < 0:
        print("at least one negative")
    else:
        print("both zero")


def test_mixed_and_or():
    """混合AND和OR"""
    x = 1
    y = 2
    z = 3
    if x > 0 and y > 0 and z > 0:
        print("all positive")
    elif x < 0 or y < 0 or z < 0:
        print("at least one negative")
    elif x == 0 and y == 0 and z == 0:
        print("all zero")
    else:
        print("mixed")


def test_complex_boolean():
    """复杂布尔表达式"""
    x = 1
    y = 2
    if (x > 0 and y > 0) or (x < 0 and y < 0):
        print("same sign")
    elif x == 0 or y == 0:
        print("at least one zero")
    else:
        print("different signs")


def test_not_conditions():
    """NOT条件"""
    x = 1
    if not x > 0:
        print("not positive")
    elif not x < 0:
        print("not negative")
    else:
        print("zero")


def test_chained_comparison():
    """链式比较"""
    x = 5
    if 0 < x < 10:
        print("between 0 and 10")
    elif 10 <= x < 20:
        print("between 10 and 20")
    elif 20 <= x < 30:
        print("between 20 and 30")
    else:
        print("out of range")


def test_function_call_conditions():
    """函数调用条件"""
    def check(x):
        return x > 0
    
    x = 1
    if check(x):
        print("positive")
    elif check(-x):
        print("negative")
    else:
        print("zero")


def test_method_call_conditions():
    """方法调用条件"""
    s = "hello"
    if s.startswith('h'):
        print("starts with h")
    elif s.endswith('o'):
        print("ends with o")
    elif s.isalpha():
        print("all alphabetic")
    else:
        print("other")


def test_complex_expressions():
    """复杂表达式"""
    x = 1
    y = 2
    z = 3
    if x + y > z and y + z > x and z + x > y:
        print("valid triangle")
    elif x + y == z or y + z == x or z + x == y:
        print("degenerate triangle")
    else:
        print("invalid triangle")


def test_nested_boolean():
    """嵌套布尔表达式"""
    a = True
    b = False
    c = True
    if a and (b or c):
        print("a and (b or c)")
    elif (a and b) or c:
        print("(a and b) or c")
    elif not a and not b:
        print("not a and not b")
    else:
        print("other")


def run_tests():
    """运行所有测试"""
    tests = [
        ("AND条件", test_and_conditions, 0),
        ("OR条件", test_or_conditions, 1),
        ("混合AND和OR", test_mixed_and_or, 0),
        ("复杂布尔表达式", test_complex_boolean, 6),
        ("NOT条件", test_not_conditions, 1),
        ("链式比较", test_chained_comparison, 2),
        ("函数调用条件", test_function_call_conditions, 1),
        ("方法调用条件", test_method_call_conditions, 2),
        ("复杂表达式", test_complex_expressions, 0),
        ("嵌套布尔表达式", test_nested_boolean, 6),
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
