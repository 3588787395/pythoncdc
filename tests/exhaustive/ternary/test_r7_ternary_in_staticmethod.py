import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInStaticmethod(ExhaustiveTestCase):
    """Bug R7: staticmethod 中 return ternary — 字节码不一致。

    原始:
        class C:
            @staticmethod
            def m():
                return a if c else b
    缺陷: staticmethod 装饰器 + return ternary。staticmethod 装饰器
         在字节码层是 LOAD_NAME staticmethod + MAKE_FUNCTION + CALL，
         装饰后的方法 code object 内部 return ternary，无 self/cls
         参数。期望 ternary 正确归约；当前疑似装饰器调用序列与方法
         code object 边界与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """class C:
    @staticmethod
    def m():
        return a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
