import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR9TernaryClassDecoratorArg(ExhaustiveTestCase):
    """Bug R9: class decorator 参数是 ternary — 字节码不一致。

    原始:
        @deco(a if c else b)
        class C:
            pass
    缺陷: 类装饰器参数是 ternary。R3/R5 已测过函数装饰器 ternary。
         R9 测类装饰器变体：ternary merge 块的栈输出作为类装饰器调用
         的参数，与 LOAD_BUILD_CLASS + MAKE_FUNCTION + CALL 构建类的
         栈帧顺序可能冲突。
    """
    SOURCE_CODE = """@deco(a if c else b)
class C:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
