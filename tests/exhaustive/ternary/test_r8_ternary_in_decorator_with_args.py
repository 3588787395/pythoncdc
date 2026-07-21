import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryInDecoratorWithArgs(ExhaustiveTestCase):
    """Bug R8: 装饰器带 ternary 参数 — 字节码不一致。

    原始:
        @deco(a if c else b)
        def f():
            pass
    缺陷: 装饰器调用参数是 ternary。R3/R5 已测过 ternary 在装饰器
         位置。R8 测装饰器带参数变体：ternary merge 块的栈输出作为
         装饰器调用的参数，与 MAKE_FUNCTION + CALL 装饰器栈帧顺序
         可能冲突。
    """
    SOURCE_CODE = """@deco(a if c else b)
def f():
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
