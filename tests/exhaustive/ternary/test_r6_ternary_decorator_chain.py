import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryDecoratorChain(ExhaustiveTestCase):
    """Bug R6: 多装饰器 + ternary — 字节码不一致。

    原始:
        def deco1(f):
            return f
        def deco2(f):
            return f
        @deco1
        @deco2
        def f():
            pass
    缺陷: 多装饰器装饰链 + ternary 在 body 中。期望多装饰器正确构建
         Call(Call(f, deco2), deco1) 结构；当前疑似装饰器 merge 块与
         ternary merge 块在嵌套函数 code object 内交互产生归属冲突。
    """
    SOURCE_CODE = """def deco1(f):
    return f
def deco2(f):
    return f
@deco1
@deco2
def f():
    x = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
