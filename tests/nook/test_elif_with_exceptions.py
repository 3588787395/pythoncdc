"""
elif与异常处理组合测试
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


def test_elif_with_try_except():
    """elif分支中带try-except"""
    x = 1
    if x == 0:
        try:
            print("zero")
        except:
            pass
    elif x == 1:
        try:
            print("one")
        except:
            pass
    else:
        try:
            print("other")
        except:
            pass


def test_try_except_with_elif():
    """try-except块中的elif"""
    try:
        x = 1
        if x == 0:
            print("zero")
        elif x == 1:
            print("one")
        else:
            print("other")
    except:
        pass


def test_elif_with_raise():
    """elif中带raise"""
    x = 1
    if x == 0:
        print("zero")
    elif x == 1:
        raise ValueError("one")
    elif x == 2:
        raise TypeError("two")
    else:
        print("other")


def test_nested_try_elif():
    """嵌套try中的elif"""
    try:
        try:
            x = 1
            if x == 0:
                print("inner zero")
            elif x == 1:
                print("inner one")
            else:
                print("inner other")
        except ValueError:
            pass
    except:
        pass


def test_elif_with_finally():
    """elif分支中带finally"""
    x = 1
    if x == 0:
        try:
            print("zero")
        finally:
            print("finally zero")
    elif x == 1:
        try:
            print("one")
        finally:
            print("finally one")
    else:
        print("other")


def test_multiple_except_elif():
    """多except与elif"""
    try:
        x = 1
        if x == 0:
            raise ValueError
        elif x == 1:
            raise TypeError
        elif x == 2:
            raise KeyError
        else:
            print("no error")
    except ValueError:
        print("ValueError")
    except TypeError:
        print("TypeError")
    except KeyError:
        print("KeyError")


def test_elif_in_except():
    """except块中的elif"""
    try:
        raise ValueError
    except ValueError:
        x = 1
        if x == 0:
            print("except zero")
        elif x == 1:
            print("except one")
        else:
            print("except other")


def run_tests():
    """运行所有测试"""
    tests = [
        ("elif分支中带try-except", test_elif_with_try_except, 1),
        ("try-except块中的elif", test_try_except_with_elif, 1),
        ("elif中带raise", test_elif_with_raise, 2),
        ("嵌套try中的elif", test_nested_try_elif, 1),
        ("elif分支中带finally", test_elif_with_finally, 1),
        ("多except与elif", test_multiple_except_elif, 3),
        ("except块中的elif", test_elif_in_except, 0),
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
