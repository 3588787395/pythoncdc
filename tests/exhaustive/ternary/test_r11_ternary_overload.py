import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryOverload(ExhaustiveTestCase):
    """Bug R10-11 (re-verify in R11): typing.overload + ternary in body.

    原始:
        from typing import overload
        @overload
        def f(x: int) -> int: ...
        @overload
        def f(x: str) -> str: ...
        def f(x):
            return (a if c else b)
    缺陷: 多个 @overload 装饰器 + 最终实现函数 return ternary。3 个 f 定义
         共享同名，前两个用 @overload 装饰（body 是 Ellipsis），第三个
         return ternary。MAKE_FUNCTION + STORE_NAME f 三次。ternary merge 块
         在第三个 f 的 code object 内，return ternary 是 Return(IfExp)。
    """
    SOURCE_CODE = """from typing import overload
@overload
def f(x: int) -> int: ...
@overload
def f(x: str) -> str: ...
def f(x):
    return (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
