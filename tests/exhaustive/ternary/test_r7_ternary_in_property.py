import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInProperty(ExhaustiveTestCase):
    """Bug R7: property getter 中 return ternary — 字节码不一致。

    原始:
        class C:
            @property
            def x(self):
                return self._x if c else 0
    缺陷: property 装饰器 + return ternary。property 装饰器在字节码层
         是 LOAD_NAME property + MAKE_FUNCTION + CALL，装饰后的
         getter 方法 code object 内部 return ternary。期望 ternary
         正确归约；当前疑似装饰器调用序列与 getter code object 边界
         与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """class C:
    @property
    def x(self):
        return self._x if c else 0
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
