import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryInYieldFrom(ExhaustiveTestCase):
    """Bug R4-18: ternary 在 yield from 表达式（变量对变量）— 字节码不一致。

    原始:
        def g():
            yield from (a if cond else b)
    缺陷: ternary 在 yield from 中时，GET_YIELD_FROM_ITER + SEND 循环
         消费 ternary 结果。R2 已测 (items if cond else [])，R4 用变量对变量
         排除常量折叠干扰，反编译器可能丢失 yield from 结构。
    """
    SOURCE_CODE = """def g():
    yield from (a if cond else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
