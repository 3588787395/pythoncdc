import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryAbstractmethod(ExhaustiveTestCase):
    """Bug R9: abstractmethod + ternary default — 字节码不一致。

    原始:
        class C:
            @abstractmethod
            def m(self, x=(a if c else b)):
                pass
    缺陷: abstractmethod 装饰的方法默认参数是 ternary。R5 已测过
         lambda default。R9 测 abstractmethod + ternary default 变体：
         ternary 在外层 code object 计算（默认参数在函数定义时求值），
         MAKE_FUNCTION + STORE_NAME m 与 ternary merge 块的栈顺序可能
         暴露装饰器栈与 ternary 归属的冲突。
    """
    SOURCE_CODE = """class C:
    @abstractmethod
    def m(self, x=(a if c else b)):
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
