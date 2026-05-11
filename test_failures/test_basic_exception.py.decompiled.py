# Source Generated with Decompyle++ (Python version)
# File: test_basic_exception.cpython-311.pyc (Python 3.11)

__doc__ = '\n第2批：异常处理测试 - 基础异常处理\n测试try-except/try-except-else的反编译效果\n'
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.cfg import build_cfg, generate_ast
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)
class TestSimpleExcept:
    __doc__ = '测试简单try-except'
    def test_simple_except(self):
        """测试简单try-except"""
        source = "\ndef test_simple_except():\n    try:\n        result = 1 / 0\n    except ZeroDivisionError:\n        result = 'error'\n    return result\n"
        cfg = build_cfg_from_source(source, 'test_simple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_except_with_message(self):
        """测试带异常消息的except"""
        source = "\ndef test_except_with_message():\n    try:\n        raise ValueError('test error')\n    except ValueError as e:\n        return str(e)\n"
        cfg = build_cfg_from_source(source, 'test_except_with_message')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_multiple_except(self):
        """测试多个except子句"""
        source = "\ndef test_multiple_except(x):\n    try:\n        if x == 1:\n            raise ValueError('value error')\n        elif x == 2:\n            raise TypeError('type error')\n        elif x == 3:\n            raise RuntimeError('runtime error')\n    except ValueError:\n        return 'value'\n    except TypeError:\n        return 'type'\n    except RuntimeError:\n        return 'runtime'\n    return 'ok'\n"
        cfg = build_cfg_from_source(source, 'test_multiple_except')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_except_tuple(self):
        """测试元组形式的except"""
        source = "\ndef test_except_tuple():\n    try:\n        raise ValueError('test')\n    except (ValueError, TypeError):\n        return 'caught'\n    return 'ok'\n"
        cfg = build_cfg_from_source(source, 'test_except_tuple')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_bare_except(self):
        """测试裸except"""
        source = "\ndef test_bare_except():\n    try:\n        result = 1 / 0\n    except:\n        result = 'any error'\n    return result\n"
        cfg = build_cfg_from_source(source, 'test_bare_except')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
class TestExceptElse:
    __doc__ = '测试try-except-else'
    def test_except_else(self):
        """测试try-except-else"""
        source = "\ndef test_except_else():\n    try:\n        result = 10 / 2\n    except ZeroDivisionError:\n        result = 'error'\n    else:\n        result = 'success'\n    return result\n"
        cfg = build_cfg_from_source(source, 'test_except_else')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_except_else_no_exception(self):
        """测试无异常时的else执行"""
        source = "\ndef test_except_else_no_exception():\n    try:\n        x = 10\n    except:\n        x = 'error'\n    else:\n        x = 'no error'\n    return x\n"
        cfg = build_cfg_from_source(source, 'test_except_else_no_exception')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_except_else_with_exception(self):
        """测试有异常时的else不执行"""
        source = "\ndef test_except_else_with_exception():\n    try:\n        x = 1 / 0\n    except ZeroDivisionError:\n        x = 'caught'\n    else:\n        x = 'not executed'\n    return x\n"
        cfg = build_cfg_from_source(source, 'test_except_else_with_exception')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
class TestExceptAs:
    __doc__ = '测试except as语法'
    def test_except_as(self):
        """测试except as"""
        source = "\ndef test_except_as():\n    try:\n        raise ValueError('test message')\n    except ValueError as e:\n        return e.args[0]\n"
        cfg = build_cfg_from_source(source, 'test_except_as')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_except_as_multiple(self):
        """测试多个except as"""
        source = "\ndef test_except_as_multiple(x):\n    try:\n        if x == 1:\n            raise ValueError('value')\n        else:\n            raise TypeError('type')\n    except ValueError as ve:\n        return str(ve)\n    except TypeError as te:\n        return str(te)\n"
        cfg = build_cfg_from_source(source, 'test_except_as_multiple')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
class TestBasicExceptionDecompilation:
    __doc__ = '测试基础异常处理反编译'
    def test_simple_except_decompile(self):
        """测试简单except反编译"""
        source = "\ndef test_simple_except():\n    try:\n        result = 1 / 0\n    except ZeroDivisionError:\n        result = 'error'\n    return result\n"
        cfg = build_cfg_from_source(source, 'test_simple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    def test_multiple_except_decompile(self):
        """测试多个except反编译"""
        source = "\ndef test_multiple_except(x):\n    try:\n        if x == 1:\n            raise ValueError('value')\n    except ValueError:\n        return 'value'\n    except TypeError:\n        return 'type'\n    return 'ok'\n"
        cfg = build_cfg_from_source(source, 'test_multiple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
if __name__ == '__main__':
    unittest.main()
