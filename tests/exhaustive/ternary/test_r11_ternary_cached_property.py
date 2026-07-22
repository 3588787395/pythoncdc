import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryCachedProperty(ExhaustiveTestCase):
    """Bug R11 (new): functools.cached_property + ternary in body.

    原始:
        from functools import cached_property
        class C:
            def __init__(self):
                self._x = None
            @cached_property
            def x(self):
                return (a if c else b)
    缺陷: @cached_property 装饰器 + ternary return。cached_property 装饰的
         方法在首次访问时计算并缓存结果。装饰器调用栈 PUSH_NULL + LOAD_NAME
         cached_property + LOAD_CONST x_code + MAKE_FUNCTION + PRECALL +
         CALL + STORE_NAME x。x 的 code object 内 ternary merge 块
         RETURN_VALUE 是 Return(IfExp)。
    """
    SOURCE_CODE = """from functools import cached_property
class C:
    def __init__(self):
        self._x = None
    @cached_property
    def x(self):
        return (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
