import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInDecorator(ExhaustiveTestCase):
    """Bug R5-09: ternary 在装饰器中（带嵌套函数）— 字节码不一致。

    原始:
        @(deco1 if c else deco2)
        def f():
            return 1
    缺陷: R3 已通过简单装饰器 ternary 场景（test_r3_ternary_decorator）。
         R5 用带 return 语句的嵌套函数加重复杂度。期望：装饰器表达式正确归约为
         IfExp(deco1, c, deco2) 包裹 def f；当前疑似退化为 if-else + 装饰器。
    """
    SOURCE_CODE = """@(deco1 if c else deco2)
def f():
    return 1
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
