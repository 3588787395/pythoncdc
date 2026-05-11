"""
嵌套elif测试 - 测试多层嵌套的复杂场景
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


def test_simple_nested_if():
    """简单嵌套if"""
    x = 1
    y = 2
    if x > 0:
        if y > 0:
            print("x>0, y>0")
        else:
            print("x>0, y<=0")
    elif x < 0:
        if y > 0:
            print("x<0, y>0")
        else:
            print("x<0, y<=0")
    else:
        print("x==0")


def test_elif_in_elif():
    """elif中的elif"""
    x = 1
    y = 2
    if x == 0:
        print("x is 0")
    elif x == 1:
        if y == 1:
            print("x=1, y=1")
        elif y == 2:
            print("x=1, y=2")
        else:
            print("x=1, y=other")
    elif x == 2:
        print("x is 2")


def test_deeply_nested_elif():
    """深层嵌套elif"""
    a = 1
    b = 2
    c = 3
    if a == 1:
        if b == 2:
            if c == 3:
                print("a=1, b=2, c=3")
            elif c == 4:
                print("a=1, b=2, c=4")
            else:
                print("a=1, b=2, c=other")
        elif b == 3:
            print("a=1, b=3")
        else:
            print("a=1, b=other")
    elif a == 2:
        print("a=2")
    else:
        print("a=other")


def test_multiple_nested_levels():
    """多层嵌套"""
    x = 1
    if x == 0:
        print("level 1: 0")
    elif x == 1:
        print("level 1: 1")
        if x == 1:
            print("level 2: 1")
            if x == 1:
                print("level 3: 1")
            elif x == 2:
                print("level 3: 2")
        elif x == 2:
            print("level 2: 2")
    elif x == 2:
        print("level 1: 2")


def test_complex_nested_structure():
    """复杂嵌套结构"""
    x = 1
    y = 2
    z = 3
    if x > 0:
        if y > 0:
            if z > 0:
                print("all positive")
            elif z < 0:
                print("x>0, y>0, z<0")
            else:
                print("x>0, y>0, z=0")
        elif y < 0:
            if z > 0:
                print("x>0, y<0, z>0")
            else:
                print("x>0, y<0, z<=0")
        else:
            print("x>0, y=0")
    elif x < 0:
        if y > 0:
            print("x<0, y>0")
        else:
            print("x<0, y<=0")
    else:
        print("x=0")


def test_elif_chain_in_nested():
    """嵌套中的elif链"""
    x = 1
    y = 2
    if x == 0:
        print("x is 0")
    elif x == 1:
        if y == 0:
            print("x=1, y=0")
        elif y == 1:
            print("x=1, y=1")
        elif y == 2:
            print("x=1, y=2")
        elif y == 3:
            print("x=1, y=3")
        else:
            print("x=1, y=other")
    elif x == 2:
        print("x is 2")
    elif x == 3:
        print("x is 3")


def test_mixed_nesting():
    """混合嵌套"""
    a = 1
    b = 2
    if a == 1:
        if b == 1:
            print("a=1, b=1")
        else:
            print("a=1, b!=1")
    elif a == 2:
        if b == 1:
            print("a=2, b=1")
        elif b == 2:
            print("a=2, b=2")
        else:
            print("a=2, b=other")
    elif a == 3:
        print("a=3")


def run_tests():
    """运行所有测试"""
    tests = [
        ("简单嵌套if", test_simple_nested_if, 1),
        ("elif中的elif", test_elif_in_elif, 3),
        ("深层嵌套elif", test_deeply_nested_elif, 3),
        ("多层嵌套", test_multiple_nested_levels, 3),
        ("复杂嵌套结构", test_complex_nested_structure, 3),
        ("嵌套中的elif链", test_elif_chain_in_nested, 6),
        ("混合嵌套", test_mixed_nesting, 3),
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
