import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8Ternary3LevelNestedFunc(ExhaustiveTestCase):
    """Bug R8: 3 层嵌套函数 + ternary 赋值 — 字节码不一致。

    原始:
        def outer():
            def middle():
                def inner():
                    y = a if c else b
                    return y
                return inner
            return middle
    缺陷: 3 层嵌套函数，最内层含 ternary 赋值。R7 已测过 nested_func_3level。
         R8 测变体确认是否仍稳定：3 层 code object 嵌套，每层 MAKE_FUNCTION
         + STORE + RETURN，最内层 ternary merge 块与 inner code object
         边界可能冲突。
    """
    SOURCE_CODE = """def outer():
    def middle():
        def inner():
            y = a if c else b
            return y
        return inner
    return middle
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
