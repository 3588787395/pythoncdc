import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInYieldFrom(ExhaustiveTestCase):
    """Bug R2-28: ternary 在 yield from 表达式中 — 字节码不一致。

    原始:
        def g():
            yield from (items if cond else [])
    缺陷: ternary 在 yield from 中时，GET_YIELD_FROM_ITER + SEND 循环
         消费 ternary 结果。反编译器可能丢失 yield from 结构。
    """
    SOURCE_CODE = """def g():
    yield from (items if cond else [])
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
