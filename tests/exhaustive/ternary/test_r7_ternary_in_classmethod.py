import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInClassmethod(ExhaustiveTestCase):
    """Bug R7: classmethod 中 return ternary — 字节码不一致。

    原始:
        class C:
            @classmethod
            def m(cls):
                return cls.x if c else cls.y
    缺陷: classmethod 装饰器 + return ternary。classmethod 装饰器在
         字节码层是 LOAD_NAME classmethod + MAKE_FUNCTION + CALL，
         装饰后的方法 code object 内部 return ternary。期望 ternary
         正确归约；当前疑似装饰器调用序列与方法 code object 边界
         与 ternary merge 块交互产生归属冲突。R6 已知 decorator chain
         region 边界问题 (R6-16)，R7 测单装饰器 classmethod 变体。
    """
    SOURCE_CODE = """class C:
    @classmethod
    def m(cls):
        return cls.x if c else cls.y
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
